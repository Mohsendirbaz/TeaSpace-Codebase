/**
 * comparisonScorecard.js — Scorecard model for version comparison
 *
 * Phase 5 of the TEA-MD Overhaul.
 *
 * A Scorecard summarises the analytical comparison between a reference version
 * and one or more candidates (human or agent-authored) on the same surface.
 *
 * Fields per candidate:
 *   versionId, authorType, cellsCompared, identical, positive, negative,
 *   notComparable, governanceWins, governanceLosses, totalDelta, meanAbsDelta
 *
 * Functions:
 *   buildScorecard(referenceProjection, candidateProjections, governance, versionRegistry?)
 *   scoreSummary(scorecard)   — compact text summary (for tests / tooltips)
 */

// ── Types (JSDoc only) ────────────────────────────────────────────────────────

/**
 * @typedef {object} CandidateScore
 * @property {string} versionId
 * @property {string} authorType         - 'human' | 'agent'
 * @property {number} cellsCompared
 * @property {number} identical          - delta === 0
 * @property {number} positive           - delta > 0
 * @property {number} negative           - delta < 0
 * @property {number} notComparable      - delta === null
 * @property {number} governanceWins     - cells where this candidate is governance winner
 * @property {number} governanceLosses   - cells where this candidate is suppressed
 * @property {number} totalDelta         - sum of all numeric deltas
 * @property {number} meanAbsDelta       - mean |delta| over non-null cells
 */

/**
 * @typedef {object} Scorecard
 * @property {string}          referenceVersionId
 * @property {CandidateScore[]} candidates
 * @property {number}          totalCells      - number of cells in reference projection
 * @property {string}          scoredAt        - ISO timestamp
 */

// ── Scorecard builder ─────────────────────────────────────────────────────────

/**
 * Builds a full Scorecard from the outputs of buildComparisonSession.
 *
 * @param {VersionProjection}   referenceProjection
 * @param {VersionProjection[]} candidateProjections  - deltaFromReference already attached
 * @param {Map}                 governance            - Map<key, {winner, suppressed[]}>
 * @param {Map|null}            [versionRegistry]     - for authorType lookup
 * @returns {Scorecard}
 */
export function buildScorecard(
  referenceProjection,
  candidateProjections,
  governance,
  versionRegistry = null,
) {
  const totalCells = referenceProjection.cells.length;

  const candidates = candidateProjections.map(cp => {
    // Resolve authorType from registry
    const slot =
      versionRegistry?.get(cp.versionId) ??
      versionRegistry?.get(`v${cp.versionId}`) ??
      null;
    const authorType = slot?.authorType ?? 'human';

    let identical = 0, positive = 0, negative = 0, notComparable = 0;
    let deltaSum = 0, deltaCount = 0;

    for (const cell of cp.cells) {
      const d = cell.deltaFromReference;
      if (d === null || d === undefined) {
        notComparable++;
      } else if (d === 0) {
        identical++;
      } else if (d > 0) {
        positive++;
        deltaSum += d;
        deltaCount++;
      } else {
        negative++;
        deltaSum += d;
        deltaCount++;
      }
    }

    // Governance tallies
    let governanceWins = 0, governanceLosses = 0;
    for (const [, gov] of governance) {
      if (gov.winner === cp.versionId) governanceWins++;
      if (gov.suppressed.includes(cp.versionId)) governanceLosses++;
    }

    return {
      versionId: cp.versionId,
      authorType,
      cellsCompared: cp.cells.length,
      identical,
      positive,
      negative,
      notComparable,
      governanceWins,
      governanceLosses,
      totalDelta: deltaSum,
      meanAbsDelta: deltaCount > 0 ? Math.abs(deltaSum) / deltaCount : 0,
    };
  });

  return {
    referenceVersionId: referenceProjection.versionId,
    candidates,
    totalCells,
    scoredAt: new Date().toISOString(),
  };
}

// ── Compact summary ───────────────────────────────────────────────────────────

/**
 * Returns a compact text summary of a scorecard.
 * Used in tests, tooltips, and console validation.
 *
 * @param {Scorecard} scorecard
 * @returns {string}
 */
export function scoreSummary(scorecard) {
  if (!scorecard.candidates.length) return `ref: ${scorecard.referenceVersionId} — no candidates`;
  return scorecard.candidates
    .map(c => {
      const pct =
        scorecard.totalCells > 0
          ? Math.round((c.identical / scorecard.totalCells) * 100)
          : 0;
      return (
        `${c.versionId}[${c.authorType}]: ` +
        `${pct}% identical, ` +
        `+${c.positive}/-${c.negative} deltas, ` +
        `${c.governanceWins} gov wins`
      );
    })
    .join(' | ');
}
