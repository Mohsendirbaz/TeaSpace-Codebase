/**
 * validationSuite.js — End-to-end validation for the TEA-MD unified model
 *
 * Phase 5 of the TEA-MD Overhaul.
 *
 * This module exercises the entire analytical pipeline from version creation
 * through comparison, scoring, and governance — for both human and agent
 * versions on the same comparison surface.
 *
 * It is NOT a test framework.  It is a pure-JS validation library that can be
 * called from:
 *   - A browser console (window.runTEAValidation())
 *   - Jest tests (import and call runAllValidations())
 *   - A CI step (node -e "require('./validationSuite').runAllValidations()")
 *
 * All functions return { passed: boolean, label: string, detail: string }.
 *
 * runAllValidations() returns { results, passed, failed, summary }.
 */

import { createVersionSlot, createScopedMutation, cellAddress } from '../model/coreTypes';
import { createAgentCandidate, agentProposalToMutations, applyAgentMutations } from '../model/agentCandidate';
import { buildComparisonSession } from './projectionEngine';
import { buildScorecard, scoreSummary } from '../model/comparisonScorecard';
import { buildMutationLedger, ledgerSummary } from '../model/mutationLedger';

// ── Minimal test helpers ──────────────────────────────────────────────────────

function pass(label, detail = '') {
  return { passed: true, label, detail };
}

function fail(label, detail = '') {
  return { passed: false, label, detail };
}

function check(label, condition, detail = '') {
  return condition ? pass(label, detail) : fail(label, detail);
}

// ── Seed data ─────────────────────────────────────────────────────────────────

/**
 * Produces a minimal formMatrix with two parameters (Amount10, Amount20),
 * each having a matrix entry for both provided versionIds.
 *
 * This is the minimal seed needed to exercise projections and comparisons.
 */
function makeSeedFormMatrix(referenceVersionId, candidateVersionId, candidateValue = 120) {
  const makeParam = (label, refVal, candVal) => ({
    label,
    efficacyPeriod: { start: 0, end: 5 },
    matrix: {
      [referenceVersionId]: { z1: refVal },
      [candidateVersionId]: { z1: candVal },
    },
  });

  return {
    plantLifetimeAmount10: makeParam('Plant Lifetime', 20, 20),
    Amount20: makeParam('Capital Cost', 100, candidateValue),
    Amount30: makeParam('Operating Cost', 50, 50),
  };
}

// ── Individual validations ────────────────────────────────────────────────────

export function validateVersionSlotCreation() {
  const humanSlot = createVersionSlot({ id: 'v1', label: 'Base Case', authorType: 'human' });
  const agentSlot = createAgentCandidate({ id: 'agent-v1', label: 'Agent Proposal', parentId: 'v1' });

  const r1 = check('Human slot has authorType=human', humanSlot.authorType === 'human');
  const r2 = check('Agent slot has authorType=agent', agentSlot.authorType === 'agent');
  const r3 = check('Agent slot lineage points to parent', agentSlot.lineage?.parentId === 'v1');
  const r4 = check('Human slot id preserved', humanSlot.id === 'v1');
  const r5 = check('Agent slot id preserved', agentSlot.id === 'agent-v1');

  return [r1, r2, r3, r4, r5];
}

export function validateAgentMutationCreation() {
  const proposal = [
    { targetId: 'Amount20', mutationType: 'percentage', value: 10, rationale: 'Cost optimisation' },
    { targetId: 'Amount30', mutationType: 'directvalue', value: 45 },
  ];

  const mutations = agentProposalToMutations(proposal, 'agent-v1', 'v1');

  const r1 = check('Two mutations produced', mutations.length === 2);
  const r2 = check('First mutation is percentage', mutations[0].mutationType === 'percentage');
  const r3 = check('First mutation authorType=agent', mutations[0].authorType === 'agent');
  const r4 = check('Second mutation is directvalue', mutations[1].mutationType === 'directvalue');
  const r5 = check('All mutations are active', mutations.every(m => m.precedenceStatus === 'active'));
  const r6 = check('Mutation ids are unique', new Set(mutations.map(m => m.id)).size === 2);

  return [r1, r2, r3, r4, r5, r6];
}

export function validateAgentMutationApplication() {
  const formMatrix = makeSeedFormMatrix('v1', 'agent-v1', 100); // same value initially
  const proposal = [
    { targetId: 'Amount20', mutationType: 'percentage', value: 20 }, // +20% of 100 → 120
  ];
  const mutations = agentProposalToMutations(proposal, 'agent-v1', 'v1');
  const patched = applyAgentMutations(formMatrix, mutations, 'agent-v1', 'v1');

  // Original should be unchanged
  const origVal = formMatrix.Amount20?.matrix?.['agent-v1']?.z1;
  // Patched should have new value
  const newVal = patched.Amount20?.matrix?.['agent-v1']?.z1;

  const r1 = check('Original formMatrix unchanged', origVal === 100);
  const r2 = check('Patched value = 120 (100 * 1.20)', Math.abs(newVal - 120) < 0.001, `got ${newVal}`);
  const r3 = check('Reference value unchanged in patched', patched.Amount20?.matrix?.v1?.z1 === 100);
  const r4 = check('Non-targeted param unchanged', patched.Amount30?.matrix?.['agent-v1']?.z1 === 50);

  return [r1, r2, r3, r4];
}

export function validateCellAddressing() {
  const addr = cellAddress('Amount20', 'year:2026', 'v1');
  const parts = addr.split('::');

  const r1 = check('Cell address has 3 parts', parts.length === 3);
  const r2 = check('Part 0 is targetId', parts[0] === 'Amount20');
  const r3 = check('Part 1 is durationPath', parts[1] === 'year:2026');
  const r4 = check('Part 2 is versionId', parts[2] === 'v1');
  const r5 = check('Same inputs produce same address', addr === cellAddress('Amount20', 'year:2026', 'v1'));

  return [r1, r2, r3, r4, r5];
}

export function validateProjectionEngine() {
  const formMatrix = makeSeedFormMatrix('v1', 'agent-v1', 120);
  let session;
  let error = null;

  try {
    session = buildComparisonSession({
      formMatrix,
      referenceVersionId: 'v1',
      candidateVersionIds: ['agent-v1'],
      plantLifetime: 5,
      baseYear: 2026,
    });
  } catch (e) {
    error = e.message;
  }

  const r1 = check('buildComparisonSession does not throw', !error, error ?? '');
  const r2 = check('Session has referenceProjection', !!session?.referenceProjection);
  const r3 = check('Session has 1 candidateProjection', session?.candidateProjections?.length === 1);
  const r4 = check('Reference projection has cells', (session?.referenceProjection?.cells?.length ?? 0) > 0);
  const r5 = check('Candidate cells have deltaFromReference', session?.candidateProjections?.[0]?.cells?.every(c => 'deltaFromReference' in c));
  const r6 = check('Governance map is present', session?.governance instanceof Map);

  // At least one cell should show a delta (Amount20 differs: 100 vs 120)
  const hasDelta = session?.candidateProjections?.[0]?.cells?.some(c => c.deltaFromReference !== null && c.deltaFromReference !== 0);
  const r7 = check('At least one cell has non-zero delta', !!hasDelta);

  return [r1, r2, r3, r4, r5, r6, r7];
}

export function validateSharedComparisonSurface() {
  // Human and agent candidates must produce the same projection structure
  const formMatrix = makeSeedFormMatrix('v1', 'agent-v1', 110);

  // Register a second human candidate too
  formMatrix.Amount20.matrix['v2'] = { z1: 115 };
  formMatrix.Amount30.matrix['v2'] = { z1: 50 };
  formMatrix.plantLifetimeAmount10.matrix['v2'] = { z1: 20 };

  let session;
  try {
    session = buildComparisonSession({
      formMatrix,
      referenceVersionId: 'v1',
      candidateVersionIds: ['v2', 'agent-v1'],
      plantLifetime: 5,
      baseYear: 2026,
    });
  } catch (e) {
    return [fail('buildComparisonSession with mixed candidates', e.message)];
  }

  const humanCandidate = session.candidateProjections.find(cp => cp.versionId === 'v2');
  const agentCandidate = session.candidateProjections.find(cp => cp.versionId === 'agent-v1');

  const r1 = check('Both human and agent projections present', !!humanCandidate && !!agentCandidate);
  const r2 = check('Same cell count across candidates',
    humanCandidate?.cells?.length === agentCandidate?.cells?.length,
    `human: ${humanCandidate?.cells?.length}, agent: ${agentCandidate?.cells?.length}`
  );
  const r3 = check('Both have deltaFromReference',
    humanCandidate?.cells?.every(c => 'deltaFromReference' in c) &&
    agentCandidate?.cells?.every(c => 'deltaFromReference' in c)
  );
  const r4 = check('allVersionIds includes both',
    session.allVersionIds.includes('v2') && session.allVersionIds.includes('agent-v1')
  );

  return [r1, r2, r3, r4];
}

export function validateScorecard() {
  const formMatrix = makeSeedFormMatrix('v1', 'agent-v1', 120);

  // Add agent slot to a mock registry
  const agentSlot = createAgentCandidate({ id: 'agent-v1', label: 'Agent Proposal', parentId: 'v1' });
  const humanSlot = createVersionSlot({ id: 'v1', label: 'Base Case', authorType: 'human' });
  const registry = new Map([['v1', humanSlot], ['agent-v1', agentSlot]]);

  const session = buildComparisonSession({
    formMatrix,
    referenceVersionId: 'v1',
    candidateVersionIds: ['agent-v1'],
    plantLifetime: 5,
    baseYear: 2026,
  });

  const scorecard = buildScorecard(
    session.referenceProjection,
    session.candidateProjections,
    session.governance,
    registry,
  );

  const r1 = check('Scorecard has referenceVersionId', scorecard.referenceVersionId === 'v1');
  const r2 = check('Scorecard has 1 candidate', scorecard.candidates.length === 1);
  const r3 = check('Agent candidate score has authorType=agent', scorecard.candidates[0].authorType === 'agent');
  const r4 = check('totalCells > 0', scorecard.totalCells > 0);
  const r5 = check('At least one positive delta recorded', scorecard.candidates[0].positive > 0);
  const r6 = check('scoredAt is a string', typeof scorecard.scoredAt === 'string');

  const summary = scoreSummary(scorecard);
  const r7 = check('scoreSummary includes agent label', summary.includes('agent-v1') && summary.includes('agent'));

  return [r1, r2, r3, r4, r5, r6, r7];
}

export function validateMutationLedger() {
  const mutations = [
    createScopedMutation({ id: 'm1', targetId: 'Amount20', mutationType: 'percentage', value: 10,
      precedenceStatus: 'active', authorType: 'agent', versionId: 'agent-v1', referenceVersionId: 'v1' }),
    createScopedMutation({ id: 'm2', targetId: 'Amount30', mutationType: 'directvalue', value: 45,
      precedenceStatus: 'suppressed', authorType: 'human', versionId: 'v2', referenceVersionId: 'v1' }),
  ];
  const labelMap = { Amount20: 'Capital Cost', Amount30: 'Operating Cost' };
  const ledger = buildMutationLedger(mutations, labelMap);
  const summary = ledgerSummary(ledger);

  const r1 = check('Ledger has 2 entries', ledger.length === 2);
  const r2 = check('Active entry is first', ledger[0].precedenceStatus === 'active');
  const r3 = check('Suppressed entry is second', ledger[1].precedenceStatus === 'suppressed');
  const r4 = check('Labels resolved', ledger[0].targetLabel === 'Capital Cost');
  const r5 = check('Summary total = 2', summary.total === 2);
  const r6 = check('Summary active = 1', summary.active === 1);
  const r7 = check('Summary suppressed = 1', summary.suppressed === 1);

  return [r1, r2, r3, r4, r5, r6, r7];
}

export function validateGovernance() {
  // Agent proposes +20% on Amount20 → should be suppressed (reference wins in Phase 2/5 rule)
  const formMatrix = makeSeedFormMatrix('v1', 'agent-v1', 120);

  const session = buildComparisonSession({
    formMatrix,
    referenceVersionId: 'v1',
    candidateVersionIds: ['agent-v1'],
    plantLifetime: 5,
    baseYear: 2026,
  });

  // At least one governance entry should suppress agent-v1 (since it has deltas)
  let hasWinner = false, hasSuppressed = false;
  for (const [, gov] of session.governance) {
    if (gov.winner) hasWinner = true;
    if (gov.suppressed.length > 0) hasSuppressed = true;
  }

  const r1 = check('Governance map non-empty', session.governance.size > 0);
  const r2 = check('At least one governance winner', hasWinner);
  const r3 = check('At least one suppressed candidate', hasSuppressed, 'agent-v1 should be suppressed where it differs');

  // Verify reference always wins in current governance rule
  for (const [, gov] of session.governance) {
    if (gov.suppressed.length > 0) {
      const r4 = check('Reference always wins (current rule)', gov.winner === 'v1');
      return [r1, r2, r3, r4];
    }
  }

  return [r1, r2, r3];
}

// ── Test runner ───────────────────────────────────────────────────────────────

const ALL_SUITES = [
  { name: 'VersionSlot creation', fn: validateVersionSlotCreation },
  { name: 'Agent mutation creation', fn: validateAgentMutationCreation },
  { name: 'Agent mutation application', fn: validateAgentMutationApplication },
  { name: 'Cell addressing', fn: validateCellAddressing },
  { name: 'Projection engine', fn: validateProjectionEngine },
  { name: 'Shared comparison surface', fn: validateSharedComparisonSurface },
  { name: 'Scorecard', fn: validateScorecard },
  { name: 'Mutation ledger', fn: validateMutationLedger },
  { name: 'Governance', fn: validateGovernance },
];

/**
 * Runs all validation suites.
 *
 * @returns {{ results: object[], passed: number, failed: number, summary: string }}
 */
export function runAllValidations() {
  const results = [];

  for (const suite of ALL_SUITES) {
    let checks;
    try {
      checks = suite.fn();
    } catch (e) {
      checks = [fail(suite.name, `THREW: ${e.message}`)];
    }

    for (const c of checks) {
      results.push({ suite: suite.name, ...c });
    }
  }

  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;

  const summary = failed === 0
    ? `✓ All ${passed} checks passed`
    : `✗ ${failed} failed, ${passed} passed`;

  // Log to console in a readable format
  console.group('[TEA-MD Validation Suite]');
  for (const r of results) {
    const icon = r.passed ? '✓' : '✗';
    const detail = r.detail ? ` — ${r.detail}` : '';
    console.log(`  ${icon} [${r.suite}] ${r.label}${detail}`);
  }
  console.log(`\n  ${summary}`);
  console.groupEnd();

  return { results, passed, failed, summary };
}

// ── Browser-callable export ───────────────────────────────────────────────────

if (typeof window !== 'undefined') {
  window.runTEAValidation = runAllValidations;
}
