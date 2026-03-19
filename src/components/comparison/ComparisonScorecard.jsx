/**
 * ComparisonScorecard.jsx — Scorecard panel for version comparison
 *
 * Phase 5 of the TEA-MD Overhaul.
 *
 * Displays a per-candidate breakdown of comparison statistics including:
 *   - author type (human / agent) badge
 *   - identical / positive / negative / not-comparable cell counts
 *   - governance wins and losses
 *   - mean absolute delta
 *
 * Props:
 *   scorecard       - Scorecard object from buildScorecard()
 *   versionRegistry - Map<id, VersionSlot> for label resolution
 */

import React from 'react';

// ── Author badge ──────────────────────────────────────────────────────────────

function AuthorBadge({ authorType }) {
  return authorType === 'agent'
    ? <span className="cs-badge cs-agent">agent</span>
    : <span className="cs-badge cs-human">human</span>;
}

// ── Delta bar (visual proportion) ────────────────────────────────────────────

function DeltaBar({ positive, negative, identical, total }) {
  if (!total) return null;
  const pctPos  = Math.round((positive  / total) * 100);
  const pctNeg  = Math.round((negative  / total) * 100);
  const pctSame = Math.round((identical / total) * 100);
  const pctRest = 100 - pctPos - pctNeg - pctSame;

  return (
    <div className="cs-bar" title={`+${pctPos}% / −${pctNeg}% / =${pctSame}%`}>
      {pctPos  > 0 && <div className="cs-bar-pos"  style={{ width: `${pctPos}%`  }} />}
      {pctSame > 0 && <div className="cs-bar-same" style={{ width: `${pctSame}%` }} />}
      {pctNeg  > 0 && <div className="cs-bar-neg"  style={{ width: `${pctNeg}%`  }} />}
      {pctRest > 0 && <div className="cs-bar-na"   style={{ width: `${pctRest}%` }} />}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ComparisonScorecard({ scorecard, versionRegistry }) {
  if (!scorecard) return null;

  const versionLabel = (vId) => {
    const slot = versionRegistry?.get(vId) ?? versionRegistry?.get(`v${vId}`);
    return slot ? slot.label : vId;
  };

  return (
    <div className="cs-root">
      <div className="cs-header">
        <h3 className="cs-title">Comparison Scorecard</h3>
        <span className="cs-ref-label">
          Reference: <strong>{versionLabel(scorecard.referenceVersionId)}</strong>
        </span>
        <span className="cs-total-cells">{scorecard.totalCells} cells</span>
      </div>

      {scorecard.candidates.length === 0 ? (
        <p className="cs-empty">No candidates to score.</p>
      ) : (
        <table className="cs-table">
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Author</th>
              <th>Distribution</th>
              <th title="Cells with delta = 0">Identical</th>
              <th title="Cells with delta > 0">↑ Pos</th>
              <th title="Cells with delta < 0">↓ Neg</th>
              <th title="Governance wins">Gov ✓</th>
              <th title="Governance losses">Gov ⚠</th>
              <th title="Mean absolute delta">|Δ| avg</th>
            </tr>
          </thead>
          <tbody>
            {scorecard.candidates.map(c => (
              <tr key={c.versionId} className={`cs-row cs-row-${c.authorType}`}>
                <td className="cs-version-cell">
                  <span className="cs-version-label">{versionLabel(c.versionId)}</span>
                  <code className="cs-version-id">{c.versionId}</code>
                </td>
                <td><AuthorBadge authorType={c.authorType} /></td>
                <td className="cs-bar-cell">
                  <DeltaBar
                    positive={c.positive}
                    negative={c.negative}
                    identical={c.identical}
                    total={c.cellsCompared}
                  />
                </td>
                <td className="cs-num cs-same">{c.identical}</td>
                <td className="cs-num cs-pos">{c.positive}</td>
                <td className="cs-num cs-neg">{c.negative}</td>
                <td className="cs-num cs-gov-win">{c.governanceWins}</td>
                <td className="cs-num cs-gov-loss">{c.governanceLosses}</td>
                <td className="cs-num">
                  {c.meanAbsDelta > 0 ? c.meanAbsDelta.toFixed(3) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <p className="cs-footer">
        Scored at {new Date(scorecard.scoredAt).toLocaleTimeString()}
      </p>
    </div>
  );
}
