/**
 * coreTypes.js — TEA-MD Core Analytical Model
 *
 * Phase 1 of the TEA-MD Overhaul.
 *
 * These are the canonical first-class types for the version-centric,
 * comparison-ready analytical model.  Every new piece of code MUST
 * reason in terms of these types.  Old code (formMatrix / S / V / R /
 * F / RF / zones) is preserved only through the legacyZoneAdapter and
 * explicit backward-compat surfaces until later phases retire them.
 *
 * Design rules (non-negotiable, from CLAUDE.md):
 *  1. Zone is NOT a dimension of the core model.
 *  2. Each version owns exactly one BaselineAssembly.
 *  3. Baseline = direct inputs + ONLY enabled DerivedSummaryFacts.
 *  4. Scaling is the transformation engine.
 *  5. Summary is derived fact.
 *  6. Human and agent changes land in the same model.
 */

// ---------------------------------------------------------------------------
// VersionSlot
// ---------------------------------------------------------------------------

/**
 * Primary container of submitted analytical reality.
 * One slot per version — the version IS the analysis unit.
 *
 * @typedef {Object} VersionSlot
 * @property {string}  id             - Canonical version id, e.g. 'v1'
 * @property {string}  label          - Human-readable label
 * @property {string}  description
 * @property {number}  created        - Unix ms
 * @property {number}  modified       - Unix ms
 * @property {VersionLineage} lineage
 * @property {'human'|'agent'} authorType
 * @property {BaselineAssembly|null} baselineAssembly - null until explicitly assembled
 */

/**
 * @param {Partial<VersionSlot>} overrides
 * @returns {VersionSlot}
 */
export function createVersionSlot(overrides = {}) {
  return {
    id: overrides.id ?? `v${Date.now()}`,
    label: overrides.label ?? 'New Version',
    description: overrides.description ?? '',
    created: overrides.created ?? Date.now(),
    modified: overrides.modified ?? Date.now(),
    lineage: overrides.lineage ?? createVersionLineage(),
    authorType: overrides.authorType ?? 'human',
    baselineAssembly: overrides.baselineAssembly ?? null,
  };
}

// ---------------------------------------------------------------------------
// VersionLineage
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} VersionLineage
 * @property {string|null} parentId     - Version this was branched from
 * @property {string|null} branchPoint  - Semantic label of the branch point
 * @property {string[]}    mutations    - Ordered list of ScopedMutation ids applied
 */

/**
 * @param {Partial<VersionLineage>} overrides
 * @returns {VersionLineage}
 */
export function createVersionLineage(overrides = {}) {
  return {
    parentId: overrides.parentId ?? null,
    branchPoint: overrides.branchPoint ?? null,
    mutations: overrides.mutations ?? [],
  };
}

// ---------------------------------------------------------------------------
// BaselineAssembly
// ---------------------------------------------------------------------------

/**
 * Explicit, deterministic description of what constitutes a submitted baseline.
 *
 * Baseline = directInputs (project/loan/rates) + admittedDerivedFacts (Amount4-7 enabled).
 * It is NOT a raw snapshot of all tab inputs.
 *
 * @typedef {Object} BaselineAssembly
 * @property {string}               versionId
 * @property {number}               assembledAt
 * @property {DirectInputs}         directInputs
 * @property {DerivedSummaryFact[]} admittedDerivedFacts   - enabled Amount4/5/6/7 outputs
 * @property {DerivedSummaryFact[]} excludedDerivedFacts   - disabled Amount4/5/6/7 outputs
 */

/**
 * @typedef {Object} DirectInputs
 * @property {Object} projectConfig    - plantLifetime, constructionTime, capacity, capacityFactor
 * @property {Object} loanConfig       - debtRatio, interestRate, loanTerm
 * @property {Object} ratesFixedCosts  - inflationRate, discountRate, taxRate, costOfCapital, F1-F5
 */

/**
 * @param {Partial<BaselineAssembly>} overrides
 * @returns {BaselineAssembly}
 */
export function createBaselineAssembly(overrides = {}) {
  return {
    versionId: overrides.versionId ?? '',
    assembledAt: overrides.assembledAt ?? Date.now(),
    directInputs: overrides.directInputs ?? {
      projectConfig: {},
      loanConfig: {},
      ratesFixedCosts: {},
    },
    admittedDerivedFacts: overrides.admittedDerivedFacts ?? [],
    excludedDerivedFacts: overrides.excludedDerivedFacts ?? [],
  };
}

// ---------------------------------------------------------------------------
// DerivedSummaryFact
// ---------------------------------------------------------------------------

/**
 * An output of the scaling pipeline for a single parameter in a single version.
 * Replaces opaque entries in `finalResults`.
 *
 * participationState = 'admitted'  → included in baseline submission
 * participationState = 'excluded'  → disabled by V/R toggle; not submitted
 *
 * @typedef {Object} DerivedSummaryFact
 * @property {string} id
 * @property {string} paramId           - e.g. 'vAmount40'
 * @property {string} versionId
 * @property {'Amount4'|'Amount5'|'Amount6'|'Amount7'} sourceWorkspace
 * @property {string} label
 * @property {any}    resolvedValue
 * @property {'admitted'|'excluded'} participationState
 * @property {'scaling_output'|'direct_input'} sourceType
 * @property {FactProvenance} provenance
 */

/**
 * @typedef {Object} FactProvenance
 * @property {string|null} scalingGroupId
 * @property {string|null} operation
 * @property {string|null} scalingLineage  - human-readable chain description
 */

/**
 * @param {Partial<DerivedSummaryFact>} overrides
 * @returns {DerivedSummaryFact}
 */
export function createDerivedSummaryFact(overrides = {}) {
  return {
    id: overrides.id ?? `dsf_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    paramId: overrides.paramId ?? '',
    versionId: overrides.versionId ?? '',
    sourceWorkspace: overrides.sourceWorkspace ?? 'Amount4',
    label: overrides.label ?? '',
    resolvedValue: overrides.resolvedValue ?? null,
    participationState: overrides.participationState ?? 'excluded',
    sourceType: overrides.sourceType ?? 'scaling_output',
    provenance: overrides.provenance ?? {
      scalingGroupId: null,
      operation: null,
      scalingLineage: null,
    },
  };
}

// ---------------------------------------------------------------------------
// ScopedMutation
// ---------------------------------------------------------------------------

/**
 * A single parameterised change applied over a scoped duration relative
 * to a reference version.  This is the future replacement for raw `S` entries.
 *
 * In Phase 1 this type is introduced but not yet wired to S state.
 * Phase 4 collapses S into this model.
 *
 * @typedef {Object} ScopedMutation
 * @property {string}  id
 * @property {string}  targetId           - paramId being mutated
 * @property {string}  durationPath       - e.g. 'year:0-20', 'year:5-10'
 * @property {'percentage'|'directvalue'|'absolutedeparture'} mutationType
 * @property {any}     value
 * @property {string}  versionId          - version this mutation belongs to
 * @property {string}  referenceVersionId - baseline this is delta'd against
 * @property {'human'|'agent'} authorType
 * @property {string|null} rationale
 * @property {'active'|'suppressed'} precedenceStatus
 */

/**
 * @param {Partial<ScopedMutation>} overrides
 * @returns {ScopedMutation}
 */
export function createScopedMutation(overrides = {}) {
  return {
    id: overrides.id ?? `mut_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    targetId: overrides.targetId ?? '',
    durationPath: overrides.durationPath ?? 'year:0-20',
    mutationType: overrides.mutationType ?? 'percentage',
    value: overrides.value ?? 0,
    versionId: overrides.versionId ?? '',
    referenceVersionId: overrides.referenceVersionId ?? '',
    authorType: overrides.authorType ?? 'human',
    rationale: overrides.rationale ?? null,
    precedenceStatus: overrides.precedenceStatus ?? 'active',
  };
}

// ---------------------------------------------------------------------------
// VersionProjection
// ---------------------------------------------------------------------------

/**
 * A read-only view of a version projected onto the comparison surface.
 * Created on-demand from a VersionSlot + its BaselineAssembly.
 *
 * @typedef {Object} VersionProjection
 * @property {string}           versionId
 * @property {number}           projectedAt
 * @property {ComparisonCell[]} cells
 */

/**
 * @param {Partial<VersionProjection>} overrides
 * @returns {VersionProjection}
 */
export function createVersionProjection(overrides = {}) {
  return {
    versionId: overrides.versionId ?? '',
    projectedAt: overrides.projectedAt ?? Date.now(),
    cells: overrides.cells ?? [],
  };
}

// ---------------------------------------------------------------------------
// ComparisonCell
// ---------------------------------------------------------------------------

/**
 * A single addressable cell in the comparison workspace.
 * Stable addressing: targetId + durationPath + versionId is the canonical key.
 *
 * @typedef {Object} ComparisonCell
 * @property {string} targetId          - paramId
 * @property {string} durationPath      - canonical year range
 * @property {string} versionId
 * @property {any}    resolvedValue
 * @property {'admitted'|'excluded'|'direct'} participationState
 * @property {'scaling_output'|'direct_input'|'mutation'} sourceType
 * @property {'active'|'suppressed'} precedenceStatus
 * @property {string|null} lineageRef   - ScopedMutation id or DerivedSummaryFact id
 * @property {any}    deltaFromReference - null for reference version itself
 */

/**
 * @param {Partial<ComparisonCell>} overrides
 * @returns {ComparisonCell}
 */
export function createComparisonCell(overrides = {}) {
  return {
    targetId: overrides.targetId ?? '',
    durationPath: overrides.durationPath ?? 'year:0-20',
    versionId: overrides.versionId ?? '',
    resolvedValue: overrides.resolvedValue ?? null,
    participationState: overrides.participationState ?? 'direct',
    sourceType: overrides.sourceType ?? 'direct_input',
    precedenceStatus: overrides.precedenceStatus ?? 'active',
    lineageRef: overrides.lineageRef ?? null,
    deltaFromReference: overrides.deltaFromReference ?? null,
  };
}

// ---------------------------------------------------------------------------
// ComparisonSession
// ---------------------------------------------------------------------------

/**
 * Active state of the comparison workspace.
 * Lives in VersionStateContext.
 *
 * @typedef {Object} ComparisonSession
 * @property {string}   id
 * @property {string}   referenceVersionId
 * @property {string[]} candidateVersionIds
 * @property {'overlay'|'delta'|'governance'|'lineage'} mode
 * @property {string|null} selectedCellId  - stable cell address string
 */

/**
 * @param {Partial<ComparisonSession>} overrides
 * @returns {ComparisonSession}
 */
export function createComparisonSession(overrides = {}) {
  return {
    id: overrides.id ?? `session_${Date.now()}`,
    referenceVersionId: overrides.referenceVersionId ?? 'v1',
    candidateVersionIds: overrides.candidateVersionIds ?? [],
    mode: overrides.mode ?? 'overlay',
    selectedCellId: overrides.selectedCellId ?? null,
  };
}

// ---------------------------------------------------------------------------
// Utility: stable cell address
// ---------------------------------------------------------------------------

/**
 * Produce the canonical stable string address for a comparison cell.
 * This is the key used for selectedCellId and inspector lookups.
 *
 * @param {string} targetId
 * @param {string} durationPath
 * @param {string} versionId
 * @returns {string}
 */
export function cellAddress(targetId, durationPath, versionId) {
  return `${targetId}::${durationPath}::${versionId}`;
}

// ---------------------------------------------------------------------------
// Utility: derive VersionSlot from legacy versions metadata entry
// ---------------------------------------------------------------------------

/**
 * Convert a legacy `versions.metadata[vId]` object into a VersionSlot.
 * Used by the adapter layer — new code should create VersionSlots directly.
 *
 * @param {string} id
 * @param {Object} legacyMeta
 * @returns {VersionSlot}
 */
export function versionSlotFromLegacy(id, legacyMeta) {
  return createVersionSlot({
    id,
    label: legacyMeta.label ?? id,
    description: legacyMeta.description ?? '',
    created: legacyMeta.created ?? Date.now(),
    modified: legacyMeta.modified ?? Date.now(),
    lineage: createVersionLineage({
      parentId: legacyMeta.baseVersion ?? null,
    }),
    authorType: 'human',
    baselineAssembly: null,
  });
}