/**
 * projectionEngine.js — Version Projection Engine
 *
 * Phase 2 of the TEA-MD Overhaul.
 *
 * Converts VersionSlot + formMatrix → VersionProjection + ComparisonCell[]
 * for the generalized-duration comparison workspace.
 *
 * This is the analytical core of Phase 2: it makes versions comparable
 * on the same duration surface.  The UI (ComparisonWorkspace.jsx) consumes
 * the output of these functions.
 *
 * Design rules honoured:
 *  - Generalized duration is the canonical comparison fabric (not just UI)
 *  - Cell addressing is stable: targetId + durationPath + versionId
 *  - Delta is computed here, not in the render layer
 *  - formMatrix[paramId].matrix[versionId] is a direct value (no zone dimension)
 */

import {
  createVersionProjection,
  createComparisonCell,
  cellAddress,
} from '../model/coreTypes';

import {
  makeDurationContext,
  legacyPeriodToVisualization,
  buildVisibleColumns,
  computeCell,
  pathKey,
  pathTokenString,
} from './durationUnits';

// ---------------------------------------------------------------------------
// Row building — single version
// ---------------------------------------------------------------------------

/**
 * Build duration rows from formMatrix for a single version.
 * These are the same rows DurationConfigMatrix builds internally,
 * extracted here so the projection engine can use them independently.
 *
 * @param {Object} formMatrix       - from useMatrixFormValues
 * @param {string} versionId        - version to project
 * @param {Object} ctx              - duration context from makeDurationContext
 * @param {string} [zoneId]
 * @returns {Array} rows ready for computeCell
 */
export function buildRowsForVersion(formMatrix, versionId, ctx) {
  const rows = [];
  Object.entries(formMatrix).forEach(([paramId, item]) => {
    if (!item?.efficacyPeriod) return;

    // Direct flat access — no zone dimension
    const rawValue = item.matrix?.[versionId] ?? null;

    // Build a copy of the efficacyPeriod with the version-specific value
    const efficacyWithValue = {
      ...item.efficacyPeriod,
      scaledValue: rawValue,
      baseValue:   rawValue,
      value:       rawValue,
      resolution:  item.efficacyPeriod.resolution ?? 'Y',
    };

    rows.push({
      id:          paramId,
      name:        item.label ?? paramId,
      unit:        item.unit ?? '',
      description: item.description ?? '',
      versionId,
      resolvedValue: rawValue,
      periods: [
        legacyPeriodToVisualization(
          efficacyWithValue,
          item.label ?? paramId,
          item.unit ?? '',
          ctx,
        ),
      ],
    });
  });
  return rows;
}

// ---------------------------------------------------------------------------
// VersionProjection builder
// ---------------------------------------------------------------------------

/**
 * Build a VersionProjection for a single version.
 *
 * Projects all formMatrix parameters with efficacyPeriod onto the
 * generalized-duration comparison surface.
 *
 * Phase 3: now accepts an optional derivedFacts map so that Amount4-7 cells
 * carry the correct participationState ('admitted' | 'excluded') from the
 * baseline assembly.
 *
 * @param {string}  versionId
 * @param {Object}  formMatrix
 * @param {Object}  ctx                - duration context
 * @param {Array}   columns            - visible columns from buildVisibleColumns
 * @param {Object}  [derivedFacts]     - Phase 3: { workspace: DerivedSummaryFact[] }
 * @returns {import('../model/coreTypes').VersionProjection}
 */
export function buildVersionProjection(
  versionId, formMatrix, ctx, columns, derivedFacts = null
) {
  const rows = buildRowsForVersion(formMatrix, versionId, ctx);

  // Build lookup: paramId → DerivedSummaryFact (for Amount4-7)
  const factLookup = new Map();
  if (derivedFacts) {
    ['Amount4', 'Amount5', 'Amount6', 'Amount7'].forEach(ws => {
      (derivedFacts[ws] ?? []).forEach(f => {
        if (f.versionId === versionId || !f.versionId) {
          factLookup.set(f.paramId, f);
        }
      });
    });
  }

  const cells = [];

  rows.forEach(row => {
    columns.forEach(col => {
      const computed = computeCell(row, col, ctx);
      const dp = pathTokenString(col.path) || 'root';

      // Phase 3: resolve participationState from derivedFacts if available
      const fact = factLookup.get(row.id);
      const participationState = fact
        ? fact.participationState   // 'admitted' | 'excluded'
        : 'direct';                 // direct input (project/loan/rates)
      const sourceType = fact ? 'scaling_output' : 'direct_input';
      const lineageRef = fact ? (fact.provenance?.scalingGroupId ?? null) : null;

      cells.push(createComparisonCell({
        targetId:           row.id,
        durationPath:       dp,
        versionId,
        resolvedValue:      row.resolvedValue,
        participationState,
        sourceType,
        precedenceStatus:   'active',
        lineageRef,
        deltaFromReference: null,   // Filled in by computeDeltas
        _computed:          computed,
      }));
    });
  });

  return createVersionProjection({ versionId, cells });
}

// ---------------------------------------------------------------------------
// Delta computation
// ---------------------------------------------------------------------------

/**
 * Compute deltas between a reference projection and one or more candidate
 * projections.  Returns new candidate projections with deltaFromReference set.
 *
 * Delta is:
 *  - null           if either value is null or non-numeric
 *  - resolvedValue - referenceValue   (numeric difference)
 *
 * @param {import('../model/coreTypes').VersionProjection}   reference
 * @param {import('../model/coreTypes').VersionProjection[]} candidates
 * @returns {import('../model/coreTypes').VersionProjection[]} candidates with deltas
 */
export function computeDeltas(reference, candidates) {
  // Build a lookup from stable cell address → reference cell
  const refLookup = new Map();
  reference.cells.forEach(cell => {
    const key = `${cell.targetId}::${cell.durationPath}`;
    refLookup.set(key, cell);
  });

  return candidates.map(candidate => {
    const patchedCells = candidate.cells.map(cell => {
      const key = `${cell.targetId}::${cell.durationPath}`;
      const refCell = refLookup.get(key);
      if (!refCell) return cell;

      const rv = refCell.resolvedValue;
      const cv = cell.resolvedValue;
      const delta = (typeof rv === 'number' && typeof cv === 'number')
        ? cv - rv
        : null;

      return { ...cell, deltaFromReference: delta };
    });
    return { ...candidate, cells: patchedCells };
  });
}

// ---------------------------------------------------------------------------
// Governance resolution
// ---------------------------------------------------------------------------

/**
 * For each cell address, determine which version's value "wins".
 *
 * For now, Phase 2 rule: the reference version always wins.
 * Candidates with non-null delta are 'suppressed' in governance mode.
 * Phase 4 will refine this with ScopedMutation precedence rules.
 *
 * @param {import('../model/coreTypes').VersionProjection}   reference
 * @param {import('../model/coreTypes').VersionProjection[]} candidates
 * @returns {Map<string, {winner: string, suppressed: string[]}>}
 *   Map from `targetId::durationPath` → governance result
 */
export function computeGovernance(reference, candidates) {
  const governance = new Map();

  reference.cells.forEach(cell => {
    const key = `${cell.targetId}::${cell.durationPath}`;
    const suppressedVersions = [];

    candidates.forEach(candidate => {
      const candidateCell = candidate.cells.find(
        c => c.targetId === cell.targetId && c.durationPath === cell.durationPath
      );
      if (candidateCell && candidateCell.deltaFromReference !== null && candidateCell.deltaFromReference !== 0) {
        suppressedVersions.push(candidate.versionId);
      }
    });

    governance.set(key, {
      winner:     reference.versionId,
      suppressed: suppressedVersions,
    });
  });

  return governance;
}

// ---------------------------------------------------------------------------
// Full comparison session builder
// ---------------------------------------------------------------------------

/**
 * Build everything needed for the comparison workspace from a single call.
 *
 * @param {Object} params
 * @param {Object} params.formMatrix
 * @param {string} params.referenceVersionId
 * @param {string[]} params.candidateVersionIds
 * @param {number} [params.plantLifetime]
 * @param {number} [params.baseYear]
 * @param {Array}  [params.expansionPath] - current drill-down path
 * @param {Object} [params.derivedFacts]  - Phase 3: { workspace: DerivedSummaryFact[] }
 * @returns {{
 *   ctx: Object,
 *   columns: Array,
 *   referenceProjection: import('../model/coreTypes').VersionProjection,
 *   candidateProjections: import('../model/coreTypes').VersionProjection[],
 *   governance: Map<string, {winner: string, suppressed: string[]}>,
 *   allVersionIds: string[],
 * }}
 */
export function buildComparisonSession({
  formMatrix,
  referenceVersionId,
  candidateVersionIds,
  plantLifetime = 20,
  baseYear = 2026,
  expansionPath = [],
  derivedFacts = null,  // Phase 3: typed DerivedSummaryFact[] per workspace
}) {
  const ctx = makeDurationContext(
    Math.max(1, Math.round(plantLifetime)),
    baseYear,
  );

  const columns = buildVisibleColumns([], expansionPath, ctx);

  const referenceProjection = buildVersionProjection(
    referenceVersionId, formMatrix, ctx, columns, derivedFacts
  );

  const rawCandidates = candidateVersionIds.map(vId =>
    buildVersionProjection(vId, formMatrix, ctx, columns, derivedFacts)
  );

  const candidateProjections = computeDeltas(referenceProjection, rawCandidates);
  const governance = computeGovernance(referenceProjection, candidateProjections);

  return {
    ctx,
    columns,
    referenceProjection,
    candidateProjections,
    governance,
    allVersionIds: [referenceVersionId, ...candidateVersionIds],
  };
}

// ---------------------------------------------------------------------------
// Cell lookup helpers
// ---------------------------------------------------------------------------

/**
 * Look up a specific cell from a projection by targetId + durationPath.
 *
 * @param {import('../model/coreTypes').VersionProjection} projection
 * @param {string} targetId
 * @param {string} durationPath
 * @returns {import('../model/coreTypes').ComparisonCell|null}
 */
export function findCell(projection, targetId, durationPath) {
  return projection.cells.find(
    c => c.targetId === targetId && c.durationPath === durationPath
  ) ?? null;
}

/**
 * Collect all cells for a given targetId + durationPath across all projections.
 * Returns an array ordered: reference first, then candidates.
 *
 * @param {import('../model/coreTypes').VersionProjection}   reference
 * @param {import('../model/coreTypes').VersionProjection[]} candidates
 * @param {string} targetId
 * @param {string} durationPath
 * @returns {import('../model/coreTypes').ComparisonCell[]}
 */
export function collectCellsAcrossVersions(reference, candidates, targetId, durationPath) {
  const result = [];
  const refCell = findCell(reference, targetId, durationPath);
  if (refCell) result.push(refCell);
  candidates.forEach(candidate => {
    const cell = findCell(candidate, targetId, durationPath);
    if (cell) result.push(cell);
  });
  return result;
}

/**
 * Stable cell address string for the inspector.
 * Re-exported here for convenience.
 */
export { cellAddress };
