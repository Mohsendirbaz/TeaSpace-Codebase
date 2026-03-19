/**
 * agentCandidate.js — Agent candidate creation and mutation application
 *
 * Phase 5 of the TEA-MD Overhaul.
 *
 * An agent candidate is a first-class VersionSlot with authorType: 'agent'.
 * Agents propose changes through ScopedMutations; the same comparison surface
 * handles both human and agent versions without special-casing.
 *
 * Functions:
 *   createAgentCandidate(config)                          — VersionSlot with authorType:'agent'
 *   agentProposalToMutations(proposal, candidateId, refId) — raw proposal → ScopedMutation[]
 *   applyAgentMutations(formMatrix, mutations, candidateId, referenceId) — patched formMatrix
 */

import { createVersionSlot, createVersionLineage, createScopedMutation } from './coreTypes';

// ── Agent candidate factory ───────────────────────────────────────────────────

/**
 * Creates a VersionSlot representing an agent-authored candidate.
 *
 * @param {object}   config
 * @param {string}   config.id              — slot id (e.g. 'agent-v1')
 * @param {string}   config.label           — human-readable display label
 * @param {string}   [config.description]   — rationale / system prompt summary
 * @param {string}   [config.parentId]      — id of the human baseline this derives from
 * @param {string[]} [config.mutationIds]   — ids of ScopedMutations applied in this candidate
 * @param {object}   [config.meta]          — free-form agent metadata (model name, run id, etc.)
 * @returns {VersionSlot}
 */
export function createAgentCandidate({
  id,
  label,
  description = '',
  parentId = null,
  mutationIds = [],
  meta = {},
}) {
  const lineage = parentId
    ? createVersionLineage({
        parentId,
        branchPoint: new Date().toISOString(),
        mutations: mutationIds,
      })
    : null;

  return createVersionSlot({
    id,
    label,
    description,
    authorType: 'agent',
    lineage,
    meta,
  });
}

// ── Proposal → ScopedMutation conversion ────────────────────────────────────

/**
 * Converts a raw agent proposal array into ScopedMutation[].
 *
 * Each proposal entry shape:
 * {
 *   targetId:     'Amount10'                                      (required)
 *   mutationType: 'percentage' | 'directvalue' | 'absolutedeparture'  (default: 'directvalue')
 *   value:        number                                          (required)
 *   rationale:    string                                          (optional)
 *   durationPath: string                                          (default: 'root')
 * }
 *
 * @param {object[]} agentProposal
 * @param {string}   candidateVersionId
 * @param {string}   referenceVersionId
 * @returns {ScopedMutation[]}
 */
export function agentProposalToMutations(agentProposal, candidateVersionId, referenceVersionId) {
  return agentProposal.map((entry, idx) =>
    createScopedMutation({
      id: `agent-${candidateVersionId}-m${idx}`,
      targetId: entry.targetId,
      durationPath: entry.durationPath ?? 'root',
      mutationType: entry.mutationType ?? 'directvalue',
      value: entry.value,
      versionId: candidateVersionId,
      referenceVersionId,
      authorType: 'agent',
      rationale: entry.rationale ?? '',
      precedenceStatus: 'active',
    })
  );
}

// ── Mutation application ──────────────────────────────────────────────────────

/**
 * Applies active ScopedMutations to formMatrix, returning a shallow-patched
 * copy with the agent candidate's values injected.
 *
 * Does NOT mutate the original formMatrix.
 *
 * Mutation semantics:
 *   directvalue       — replace with mutation.value directly
 *   percentage        — refValue * (1 + value/100)
 *   absolutedeparture — refValue + value
 *
 * Only mutations with precedenceStatus === 'active' are applied.
 *
 * @param {object}         formMatrix          — current formMatrix from useMatrixFormValues
 * @param {ScopedMutation[]} mutations          — mutations to apply (agent-authored)
 * @param {string}         candidateVersionId   — agent candidate's slot id
 * @param {string}         referenceVersionId   — baseline to read reference values from
 * @param {string}         [zoneId]             — canonical zone (default 'z1')
 * @returns {object}  patchedFormMatrix
 */
export function applyAgentMutations(
  formMatrix,
  mutations,
  candidateVersionId,
  referenceVersionId,
  zoneId = 'z1',
) {
  const patched = { ...formMatrix };

  const activeMutations = mutations.filter(m => m.precedenceStatus === 'active');

  for (const mutation of activeMutations) {
    const { targetId, mutationType, value } = mutation;

    // Locate the formMatrix key whose numeric suffix matches targetId (Amount10 → key containing 10)
    const paramKey = Object.keys(formMatrix).find(k => {
      const num = k.replace(/\D/g, '');
      return num && `Amount${num}` === targetId;
    });
    if (!paramKey) continue;

    const param = formMatrix[paramKey];
    if (!param?.matrix) continue;

    // Resolve reference value (collapse zone)
    const refSlot = param.matrix[referenceVersionId];
    let refValue = null;
    if (refSlot !== null && refSlot !== undefined) {
      if (typeof refSlot === 'object') {
        refValue = Object.prototype.hasOwnProperty.call(refSlot, zoneId)
          ? refSlot[zoneId]
          : Object.values(refSlot)[0] ?? null;
      } else {
        refValue = refSlot;
      }
    }

    // Compute new value
    let newValue;
    if (mutationType === 'directvalue') {
      newValue = value;
    } else if (mutationType === 'percentage' && typeof refValue === 'number') {
      newValue = refValue * (1 + value / 100);
    } else if (mutationType === 'absolutedeparture' && typeof refValue === 'number') {
      newValue = refValue + value;
    } else {
      newValue = value;
    }

    // Inject the new value for the candidate version only
    patched[paramKey] = {
      ...param,
      matrix: {
        ...param.matrix,
        [candidateVersionId]: { [zoneId]: newValue },
      },
    };
  }

  return patched;
}
