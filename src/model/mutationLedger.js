/**
 * mutationLedger.js — Linear Mutation Ledger
 *
 * Phase 4 of the TEA-MD Overhaul.
 *
 * Converts the `S` (sensitivity) authoring grammar into the unified
 * ScopedMutation model.  Provides the linear ledger that explains:
 *  - what changed
 *  - where (paramId)
 *  - over which scoped duration
 *  - relative to which reference version
 *  - whether it won / was suppressed
 *  - what downstream impact it had
 *
 * Architectural contract:
 *  - S is kept as the operational authoring surface for now
 *  - This module is the bridge: S entries ↔ ScopedMutation objects
 *  - SensitivityMonitor reads from both (legacy S + optional ledger)
 *  - Future: Phase 5 makes agent-generated mutations land here directly
 *
 * Deprecation path:
 *  - Raw `S` as the sole authoring surface is deprecated
 *  - New code creates ScopedMutations directly via createScopedMutation()
 *  - `S` is derived from ScopedMutations for backward compat
 */

import { createScopedMutation } from './coreTypes';

// ---------------------------------------------------------------------------
// S → ScopedMutation conversion
// ---------------------------------------------------------------------------

/**
 * Convert a single `S` entry into a ScopedMutation.
 *
 * S entry shape:
 *   { status: 'on'|'off', enabled: boolean, mode: string,
 *     variation: number, values: any[], compareToVersion?: string }
 *
 * @param {string} sKey          - e.g. 'S10', 'S34', 'S40'
 * @param {Object} sEntry        - value from S state
 * @param {string} versionId     - owning version
 * @param {string} referenceVersionId
 * @returns {import('./coreTypes').ScopedMutation}
 */
export function sEntryToScopedMutation(sKey, sEntry, versionId, referenceVersionId) {
  // Derive paramId from sKey: S10 → Amount10, S34 → Amount34, etc.
  const numericPart = sKey.replace(/\D/g, '');
  const targetId = `Amount${numericPart}`;

  // Determine mutation type
  let mutationType = 'percentage';
  if (sEntry.mode === 'directvalue')       mutationType = 'directvalue';
  if (sEntry.mode === 'absolutedeparture') mutationType = 'absolutedeparture';
  if (sEntry.mode === 'monteCarlo')        mutationType = 'percentage'; // fallback

  // Is this mutation active?
  const isActive = sEntry.enabled === true || sEntry.status === 'on';

  return createScopedMutation({
    id:                  `mut_s_${sKey}_${versionId}`,
    targetId,
    durationPath:        'year:0-20',  // S does not specify scoped duration — uses full plant life
    mutationType,
    value:               sEntry.variation ?? sEntry.values?.[0] ?? 0,
    versionId,
    referenceVersionId,
    authorType:          'human',
    rationale:           sEntry.rationale ?? null,
    precedenceStatus:    isActive ? 'active' : 'suppressed',
  });
}

/**
 * Convert the entire S state object into a ScopedMutation array.
 *
 * @param {Object} S                  - full sensitivity state
 * @param {string} versionId
 * @param {string} [referenceVersionId]
 * @returns {import('./coreTypes').ScopedMutation[]}
 */
export function sStateToScopedMutations(S, versionId, referenceVersionId = versionId) {
  if (!S) return [];
  return Object.entries(S)
    .map(([key, entry]) => sEntryToScopedMutation(key, entry, versionId, referenceVersionId))
    .filter(Boolean);
}

// ---------------------------------------------------------------------------
// ScopedMutation → S conversion (backward compat)
// ---------------------------------------------------------------------------

/**
 * Convert a ScopedMutation back into an `S` entry shape so that
 * SensitivityMonitor continues to work with existing S state.
 *
 * @param {import('./coreTypes').ScopedMutation} mutation
 * @returns {{ key: string, value: Object }}
 */
export function scopedMutationToSEntry(mutation) {
  // Derive S key: Amount10 → S10
  const numericPart = mutation.targetId.replace(/\D/g, '');
  const key = `S${numericPart}`;

  const modeMap = {
    percentage:        'percentage',
    directvalue:       'directvalue',
    absolutedeparture: 'absolutedeparture',
  };

  return {
    key,
    value: {
      status:    mutation.precedenceStatus === 'active' ? 'on' : 'off',
      enabled:   mutation.precedenceStatus === 'active',
      mode:      modeMap[mutation.mutationType] ?? 'percentage',
      variation: typeof mutation.value === 'number' ? mutation.value : 10,
      values:    [mutation.value],
      rationale: mutation.rationale,
    },
  };
}

// ---------------------------------------------------------------------------
// Linear ledger builder
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} LedgerEntry
 * @property {string}  id                 - Mutation id
 * @property {string}  targetId           - paramId
 * @property {string}  targetLabel        - human-readable label (if available)
 * @property {string}  durationPath
 * @property {string}  mutationType
 * @property {any}     value
 * @property {string}  versionId
 * @property {string}  referenceVersionId
 * @property {'human'|'agent'} authorType
 * @property {'active'|'suppressed'} precedenceStatus
 * @property {string|null} rationale
 * @property {string|null} downstreamImpact
 */

/**
 * Build a linear ledger from a ScopedMutation array.
 *
 * The ledger is ordered: active mutations first (sorted by targetId),
 * then suppressed.  This is the canonical view for inspection and audit.
 *
 * @param {import('./coreTypes').ScopedMutation[]} mutations
 * @param {Object}  [labelMap]   - optional { paramId → label } for display
 * @returns {LedgerEntry[]}
 */
export function buildMutationLedger(mutations, labelMap = {}) {
  const entries = mutations.map(m => ({
    id:                 m.id,
    targetId:           m.targetId,
    targetLabel:        labelMap[m.targetId] ?? m.targetId,
    durationPath:       m.durationPath,
    mutationType:       m.mutationType,
    value:              m.value,
    versionId:          m.versionId,
    referenceVersionId: m.referenceVersionId,
    authorType:         m.authorType,
    precedenceStatus:   m.precedenceStatus,
    rationale:          m.rationale,
    downstreamImpact:   null,   // Phase 5 will compute impact from CFA delta
  }));

  // Sort: active first, then suppressed, within each group by targetId
  return [
    ...entries.filter(e => e.precedenceStatus === 'active').sort((a, b) => a.targetId.localeCompare(b.targetId)),
    ...entries.filter(e => e.precedenceStatus === 'suppressed').sort((a, b) => a.targetId.localeCompare(b.targetId)),
  ];
}

/**
 * Summarise the ledger for quick display.
 *
 * @param {LedgerEntry[]} ledger
 * @returns {{ total: number, active: number, suppressed: number, byType: Object }}
 */
export function ledgerSummary(ledger) {
  const byType = {};
  ledger.forEach(e => {
    byType[e.mutationType] = (byType[e.mutationType] ?? 0) + 1;
  });
  return {
    total:      ledger.length,
    active:     ledger.filter(e => e.precedenceStatus === 'active').length,
    suppressed: ledger.filter(e => e.precedenceStatus === 'suppressed').length,
    byType,
  };
}
