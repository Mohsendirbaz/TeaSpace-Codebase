/**
 * ComparisonWorkspace.jsx — Generalized Duration Comparison Workspace
 *
 * Phase 2 of the TEA-MD Overhaul.
 *
 * The canonical comparison surface of TEA-MD.
 * This is NOT a visualization layer — it is the analytical workspace
 * where versions, branches, and agent candidates are compared on a
 * shared duration fabric.
 *
 * Design rules honoured:
 *  1. Generalized duration IS the comparison fabric (not just UI)
 *  2. Canonical year is the default header view; drill-down is available
 *  3. Matrix is stable and cell-inspectable at any drill depth
 *  4. Comparison is a mode of the same workspace (not a detached module)
 *  5. Human and agent-authored versions compare on the same surface
 *
 * Comparison modes:
 *  - overlay    : reference values shown; candidates highlighted where different
 *  - delta      : numeric deltas shown (candidate - reference)
 *  - governance : winner/suppressed per cell
 *  - lineage    : mutation source per cell (Phase 4 wires full content)
 *
 * Props:
 *   formMatrix          - from useMatrixFormValues
 *   versionRegistry     - Map<id, VersionSlot> from VersionStateContext
 *   referenceVersionId  - string
 *   candidateVersionIds - string[]
 *   plantLifetime       - number
 *   baseYear            - number (default 2026)
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  buildComparisonSession,
  collectCellsAcrossVersions,
  cellAddress,
} from '../../utils/projectionEngine';
import {
  pathToString,
  clonePath,
  buildVisibleColumns,
  makeDurationContext,
  pathKey,
  formatLevelValue,
} from '../../utils/durationUnits';
import CellInspector from './CellInspector';
import MutationLedgerView from './MutationLedgerView';
import ComparisonScorecard from './ComparisonScorecard';
import { buildScorecard } from '../../model/comparisonScorecard';
import { useVersionState } from '../../contexts/VersionStateContext';

// ── Comparison mode options ────────────────────────────────────────────────

const MODES = [
  { id: 'overlay',    label: 'Overlay',    description: 'Reference values with candidate highlights' },
  { id: 'delta',      label: 'Δ Delta',    description: 'Numeric difference from reference' },
  { id: 'governance', label: 'Governance', description: 'Winner / suppressed per cell' },
  { id: 'lineage',    label: 'Lineage',    description: 'Mutation source per cell (Phase 4)' },
];

// ── Mutation type display (used in lineage mode) ──────────────────────────
const MUTATION_TYPE_LABELS = {
  percentage:        '% change',
  directvalue:       'direct value',
  absolutedeparture: 'departure',
};

// ── Cell display helpers ───────────────────────────────────────────────────

function formatValue(v) {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return v.toFixed(4).replace(/\.?0+$/, '');
  return String(v);
}

function deltaClass(delta) {
  if (delta === null || delta === undefined) return 'cw-cell-neutral';
  if (delta === 0) return 'cw-cell-same';
  return delta > 0 ? 'cw-cell-pos' : 'cw-cell-neg';
}

// ── Main component ─────────────────────────────────────────────────────────

export default function ComparisonWorkspace({
  formMatrix,
  plantLifetime = 20,
  baseYear = 2026,
  derivedFacts = null,      // Phase 3: typed DerivedSummaryFact[] per workspace
  scopedMutations = [],     // Phase 4: ScopedMutation[] from useMatrixFormValues
  getMutationLedger = null, // Phase 4: ledger builder function
}) {
  const {
    versionRegistry,
    comparisonSession,
    openComparisonSession,
    updateComparisonSession,
    version: activeVersion,
  } = useVersionState();

  // ── Local UI state ─────────────────────────────────────────────────────

  const [mode, setMode] = useState(
    comparisonSession?.mode ?? 'overlay'
  );

  // Reference and candidates driven by comparisonSession when present,
  // otherwise default to active version as reference + first other slot
  const allSlotIds = useMemo(
    () => Array.from(versionRegistry.keys()),
    [versionRegistry]
  );

  // Derive defaults: if there's a comparison session, use it
  const [localRef, setLocalRef] = useState(() => {
    if (comparisonSession?.referenceVersionId) return comparisonSession.referenceVersionId;
    if (allSlotIds.length) return allSlotIds[0];
    return 'v1';
  });

  const [localCandidates, setLocalCandidates] = useState(() => {
    if (comparisonSession?.candidateVersionIds?.length) {
      return comparisonSession.candidateVersionIds;
    }
    return allSlotIds.filter(id => id !== localRef).slice(0, 1);
  });

  // Duration drill-down state
  const [expansionPath, setExpansionPath] = useState([]);

  // Selected cell for inspector
  const [inspectorCellKey, setInspectorCellKey] = useState(
    comparisonSession?.selectedCellId ?? null
  );

  // ── Build comparison session ──────────────────────────────────────────

  const session = useMemo(() => {
    if (!formMatrix || Object.keys(formMatrix).length === 0) return null;
    if (!localRef) return null;

    return buildComparisonSession({
      formMatrix,
      referenceVersionId: localRef,
      candidateVersionIds: localCandidates,
      plantLifetime,
      baseYear,
      expansionPath,
      derivedFacts,  // Phase 3: wire admission state into cells
    });
  }, [formMatrix, localRef, localCandidates, plantLifetime, baseYear, expansionPath]);

  // ── Cell click handler ────────────────────────────────────────────────

  const handleCellClick = useCallback((targetId, durationPath, versionId) => {
    const addr = cellAddress(targetId, durationPath, versionId);
    setInspectorCellKey(addr);
    // Sync to context comparison session
    updateComparisonSession({ selectedCellId: addr });
  }, [updateComparisonSession]);

  // ── Derived: inspector cells ──────────────────────────────────────────

  const inspectorCells = useMemo(() => {
    if (!session || !inspectorCellKey) return [];
    // Parse address: targetId::durationPath::versionId
    const parts = inspectorCellKey.split('::');
    if (parts.length < 2) return [];
    const [targetId, durationPath] = parts;
    return collectCellsAcrossVersions(
      session.referenceProjection,
      session.candidateProjections,
      targetId,
      durationPath,
    );
  }, [session, inspectorCellKey]);

  // ── Version label helper ──────────────────────────────────────────────

  const versionLabel = useCallback((vId) => {
    const slot = versionRegistry.get(vId) ?? versionRegistry.get(`v${vId}`);
    return slot ? `${slot.label}` : vId;
  }, [versionRegistry]);

  // ── Author type helper (Phase 5) ──────────────────────────────────────

  const versionAuthorType = useCallback((vId) => {
    const slot = versionRegistry.get(vId) ?? versionRegistry.get(`v${vId}`);
    return slot?.authorType ?? 'human';
  }, [versionRegistry]);

  // ── Scorecard (Phase 5) ───────────────────────────────────────────────

  const scorecard = useMemo(() => {
    if (!session || session.candidateProjections.length === 0) return null;
    return buildScorecard(
      session.referenceProjection,
      session.candidateProjections,
      session.governance,
      versionRegistry,
    );
  }, [session, versionRegistry]);

  // ── Mode sync to context ──────────────────────────────────────────────

  const handleModeChange = useCallback((newMode) => {
    setMode(newMode);
    updateComparisonSession({ mode: newMode });
  }, [updateComparisonSession]);

  // ── Open comparison session on first render if none exists ────────────

  // Open a comparison session if none is active (runs once on mount)
  const openedRef = React.useRef(false);
  React.useEffect(() => {
    if (!openedRef.current && !comparisonSession && localRef && localCandidates.length > 0) {
      openedRef.current = true;
      openComparisonSession(localRef, localCandidates, mode);
    }
  });

  // ── Render helpers ────────────────────────────────────────────────────

  function renderCellContent(targetId, durationPath, refProjection, candidateProjections) {
    const refCell = refProjection.cells.find(
      c => c.targetId === targetId && c.durationPath === durationPath
    );

    if (mode === 'overlay') {
      return (
        <div className="cw-cell-content cw-overlay">
          <span className="cw-ref-value">{formatValue(refCell?.resolvedValue)}</span>
          {candidateProjections.map(cp => {
            const cCell = cp.cells.find(
              c => c.targetId === targetId && c.durationPath === durationPath
            );
            if (!cCell) return null;
            const hasDelta = cCell.deltaFromReference !== null && cCell.deltaFromReference !== 0;
            return hasDelta ? (
              <span key={cp.versionId} className={`cw-candidate-chip ${deltaClass(cCell.deltaFromReference)}`}>
                {versionLabel(cp.versionId)}: {formatValue(cCell.resolvedValue)}
              </span>
            ) : null;
          })}
        </div>
      );
    }

    if (mode === 'delta') {
      return (
        <div className="cw-cell-content cw-delta">
          {candidateProjections.map(cp => {
            const cCell = cp.cells.find(
              c => c.targetId === targetId && c.durationPath === durationPath
            );
            if (!cCell) return null;
            const d = cCell.deltaFromReference;
            return (
              <span key={cp.versionId} className={`cw-delta-chip ${deltaClass(d)}`}>
                {d === null ? '—' : d === 0 ? '0' : `${d > 0 ? '+' : ''}${typeof d === 'number' ? d.toFixed(3) : d}`}
              </span>
            );
          })}
        </div>
      );
    }

    if (mode === 'governance') {
      const gov = session?.governance?.get(`${targetId}::${durationPath}`);
      if (!gov) return <span className="cw-cell-content">—</span>;
      return (
        <div className="cw-cell-content cw-governance">
          <span className="cw-gov-winner">✓ {versionLabel(gov.winner)}</span>
          {gov.suppressed.map(v => (
            <span key={v} className="cw-gov-suppressed">⚠ {versionLabel(v)}</span>
          ))}
        </div>
      );
    }

    if (mode === 'lineage') {
      // In lineage mode, check if this cell has a ScopedMutation
      const numericPart = targetId.replace(/\D/g, '');
      const mutation = scopedMutations.find(
        m => m.targetId === `Amount${numericPart}` && m.precedenceStatus === 'active'
      );
      return (
        <div className="cw-cell-content cw-lineage">
          {mutation
            ? <span className="cw-candidate-chip cw-cell-pos">{MUTATION_TYPE_LABELS[mutation.mutationType] ?? mutation.mutationType}</span>
            : <span className="cw-lineage-note">—</span>
          }
        </div>
      );
    }

    return null;
  }

  // ── Empty state ───────────────────────────────────────────────────────

  if (!session) {
    return (
      <div className="cw-root cw-empty">
        <h2>Comparison Workspace</h2>
        <p>
          No versions available for comparison yet.
          Add versions in the Input tab, then return here to compare them.
        </p>
      </div>
    );
  }

  const { columns, referenceProjection, candidateProjections } = session;

  // Collect unique row ids from the reference projection
  const rowIds = [...new Set(referenceProjection.cells.map(c => c.targetId))];

  // Build a map of targetId → label for row headers
  const rowLabels = {};
  rowIds.forEach(id => {
    const item = formMatrix[id];
    rowLabels[id] = item?.label ?? id;
  });

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <div className="cw-root">

      {/* ── Control bar ── */}
      <div className="cw-controls">
        <div className="cw-controls-left">
          <span className="cw-control-label">Reference</span>
          <select
            className="cw-select"
            value={localRef}
            onChange={e => setLocalRef(e.target.value)}
          >
            {allSlotIds.map(id => (
              <option key={id} value={id}>{versionLabel(id)} ({id})</option>
            ))}
          </select>

          <span className="cw-control-label">vs.</span>

          <div className="cw-candidate-picker">
            {allSlotIds.filter(id => id !== localRef).map(id => (
              <label key={id} className="cw-candidate-check">
                <input
                  type="checkbox"
                  checked={localCandidates.includes(id)}
                  onChange={e => {
                    setLocalCandidates(prev =>
                      e.target.checked
                        ? [...prev, id]
                        : prev.filter(v => v !== id)
                    );
                  }}
                />
                {versionLabel(id)}
                {versionAuthorType(id) === 'agent' && (
                  <span className="cw-author-chip cw-author-agent" title="Agent-authored candidate">agent</span>
                )}
              </label>
            ))}
          </div>
        </div>

        <div className="cw-controls-right">
          <span className="cw-control-label">Mode</span>
          <div className="cw-mode-tabs">
            {MODES.map(m => (
              <button
                key={m.id}
                className={`cw-mode-btn ${mode === m.id ? 'cw-mode-active' : ''}`}
                title={m.description}
                onClick={() => handleModeChange(m.id)}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Breadcrumb / path navigation ── */}
      <div className="cw-breadcrumb">
        <button
          className="cw-crumb"
          onClick={() => setExpansionPath([])}
        >
          Root
        </button>
        {expansionPath.map((part, i) => (
          <React.Fragment key={i}>
            <span className="cw-crumb-sep">/</span>
            <button
              className="cw-crumb"
              onClick={() => setExpansionPath(expansionPath.slice(0, i + 1))}
            >
              {formatLevelValue(part.key, part.value)}
            </button>
          </React.Fragment>
        ))}
      </div>

      {/* ── Main content: matrix + inspector ── */}
      <div className="cw-body">

        {/* ── Duration matrix ── */}
        <div className="cw-matrix-wrap">
          {rowIds.length === 0 ? (
            <div className="cw-no-rows">
              No parameters with efficacy periods found. Configure efficacy periods in the Input tab.
            </div>
          ) : (
            <table className="cw-matrix">
              <thead>
                <tr>
                  <th className="cw-row-header-cell">Parameter</th>
                  {columns.map(col => (
                    <th
                      key={pathKey(col.path)}
                      className="cw-col-header"
                      onClick={() => setExpansionPath(clonePath(col.path))}
                      title={`Drill into ${col.label} — click to expand`}
                    >
                      {col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rowIds.map(targetId => (
                  <tr key={targetId}>
                    <td className="cw-row-header" title={targetId}>
                      {rowLabels[targetId]}
                    </td>
                    {columns.map(col => {
                      const dp = col.path.length > 0
                        ? col.path.map(p => `${p.key}:${p.value}`).join('/')
                        : 'root';
                      const addr = cellAddress(targetId, dp, localRef);
                      const isSelected = inspectorCellKey?.startsWith(`${targetId}::${dp}`);

                      return (
                        <td
                          key={pathKey(col.path)}
                          className={`cw-cell ${isSelected ? 'cw-cell-selected' : ''}`}
                          data-target={targetId}
                          data-path={dp}
                          onClick={() => handleCellClick(targetId, dp, localRef)}
                        >
                          {renderCellContent(targetId, dp, referenceProjection, candidateProjections)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* ── Cell inspector ── */}
        <CellInspector
          cells={inspectorCells}
          governance={session.governance}
          versionRegistry={versionRegistry}
          referenceVersionId={localRef}
          onClose={() => setInspectorCellKey(null)}
        />
      </div>

      {/* ── Scorecard (Phase 5) — shown in governance mode ── */}
      {mode === 'governance' && scorecard && (
        <ComparisonScorecard
          scorecard={scorecard}
          versionRegistry={versionRegistry}
        />
      )}

      {/* ── Legend ── */}
      <div className="cw-legend">
        <span className="cw-legend-item cw-cell-pos">↑ positive delta</span>
        <span className="cw-legend-item cw-cell-neg">↓ negative delta</span>
        <span className="cw-legend-item cw-cell-same">= no change</span>
        <span className="cw-legend-item cw-cell-neutral">— not comparable</span>
      </div>
    </div>
  );
}
