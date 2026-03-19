/**
 * CellInspector.jsx — Comparison Cell Inspector Panel
 *
 * Phase 2 of the TEA-MD Overhaul.
 *
 * Renders a right-side inspector that explains a selected comparison cell:
 *  - Stable cell address (targetId + durationPath + versionId)
 *  - Resolved value for each version
 *  - Delta from reference
 *  - Participation state (direct / admitted / excluded)
 *  - Source type
 *  - Precedence status (active / suppressed)
 *  - Lineage hook (ScopedMutation id or DerivedSummaryFact id)
 *  - Governance: winner + suppressed alternatives
 *
 * Props:
 *   cells       - ComparisonCell[] for the selected address (ref first, then candidates)
 *   governance  - Map<"targetId::durationPath", {winner, suppressed}> from projectionEngine
 *   versionRegistry - Map<id, VersionSlot> from VersionStateContext
 *   referenceVersionId - string
 *   onClose     - () => void
 */

import React from 'react';

// Participation badge colour
function participationColour(state) {
  switch (state) {
    case 'admitted':  return '#22c55e'; // green
    case 'excluded':  return '#ef4444'; // red
    case 'direct':    return '#3b82f6'; // blue
    default:          return '#6b7280'; // grey
  }
}

function precedenceIcon(status) {
  return status === 'suppressed' ? '⚠ suppressed' : '✓ active';
}

function formatDelta(delta) {
  if (delta === null || delta === undefined) return '—';
  if (delta === 0) return '± 0 (no change)';
  const sign = delta > 0 ? '+' : '';
  return `${sign}${typeof delta === 'number' ? delta.toFixed(4) : delta}`;
}

function DeltaBadge({ delta }) {
  if (delta === null || delta === undefined) return <span className="ci-delta ci-delta-neutral">—</span>;
  if (delta === 0) return <span className="ci-delta ci-delta-neutral">no change</span>;
  const isPositive = delta > 0;
  return (
    <span className={`ci-delta ${isPositive ? 'ci-delta-pos' : 'ci-delta-neg'}`}>
      {isPositive ? '+' : ''}{typeof delta === 'number' ? delta.toFixed(4) : delta}
    </span>
  );
}

export default function CellInspector({
  cells = [],
  governance,
  versionRegistry,
  referenceVersionId,
  onClose,
}) {
  if (!cells.length) {
    return (
      <aside className="ci-panel ci-empty">
        <div className="ci-header">
          <span className="ci-title">Cell Inspector</span>
          {onClose && <button className="ci-close" onClick={onClose}>×</button>}
        </div>
        <p className="ci-hint">Select a cell in the comparison matrix to inspect it.</p>
      </aside>
    );
  }

  const firstCell = cells[0];
  const cellKey   = `${firstCell.targetId}::${firstCell.durationPath}`;
  const gov       = governance?.get(cellKey);

  function slotLabel(vId) {
    const slot = versionRegistry?.get(vId) ?? versionRegistry?.get(`v${vId}`);
    return slot ? `${slot.label} (${vId})` : vId;
  }

  return (
    <aside className="ci-panel">
      <div className="ci-header">
        <span className="ci-title">Cell Inspector</span>
        {onClose && <button className="ci-close" onClick={onClose}>×</button>}
      </div>

      {/* Stable cell address */}
      <section className="ci-section">
        <h4 className="ci-section-title">Cell Address</h4>
        <div className="ci-row">
          <span className="ci-label">Parameter</span>
          <code className="ci-value">{firstCell.targetId}</code>
        </div>
        <div className="ci-row">
          <span className="ci-label">Duration path</span>
          <code className="ci-value">{firstCell.durationPath || 'root'}</code>
        </div>
      </section>

      {/* Values per version */}
      <section className="ci-section">
        <h4 className="ci-section-title">Values by Version</h4>
        {cells.map(cell => {
          const isRef = cell.versionId === referenceVersionId;
          return (
            <div key={cell.versionId} className={`ci-version-row ${isRef ? 'ci-ref' : 'ci-candidate'}`}>
              <div className="ci-version-label">
                <span className="ci-ver-badge">{isRef ? 'REF' : 'CAND'}</span>
                {slotLabel(cell.versionId)}
              </div>
              <div className="ci-version-data">
                <div className="ci-row">
                  <span className="ci-label">Value</span>
                  <span className="ci-value">
                    {cell.resolvedValue !== null && cell.resolvedValue !== undefined
                      ? String(cell.resolvedValue) : '—'}
                  </span>
                </div>
                {!isRef && (
                  <div className="ci-row">
                    <span className="ci-label">Delta</span>
                    <DeltaBadge delta={cell.deltaFromReference} />
                  </div>
                )}
                <div className="ci-row">
                  <span className="ci-label">Participation</span>
                  <span
                    className="ci-value"
                    style={{ color: participationColour(cell.participationState) }}
                  >
                    {cell.participationState}
                  </span>
                </div>
                <div className="ci-row">
                  <span className="ci-label">Source</span>
                  <span className="ci-value">{cell.sourceType}</span>
                </div>
                <div className="ci-row">
                  <span className="ci-label">Precedence</span>
                  <span className={`ci-value ${cell.precedenceStatus === 'suppressed' ? 'ci-warn' : 'ci-ok'}`}>
                    {precedenceIcon(cell.precedenceStatus)}
                  </span>
                </div>
                {cell.lineageRef && (
                  <div className="ci-row">
                    <span className="ci-label">Lineage ref</span>
                    <code className="ci-value">{cell.lineageRef}</code>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </section>

      {/* Governance */}
      {gov && (
        <section className="ci-section">
          <h4 className="ci-section-title">Governance</h4>
          <div className="ci-row">
            <span className="ci-label">Winner</span>
            <span className="ci-value ci-ok">{slotLabel(gov.winner)}</span>
          </div>
          {gov.suppressed.length > 0 && (
            <div className="ci-row">
              <span className="ci-label">Suppressed</span>
              <span className="ci-value ci-warn">
                {gov.suppressed.map(v => slotLabel(v)).join(', ')}
              </span>
            </div>
          )}
          {gov.suppressed.length === 0 && (
            <div className="ci-row">
              <span className="ci-label">Conflicts</span>
              <span className="ci-value ci-ok">none</span>
            </div>
          )}
          <p className="ci-governance-note">
            Phase 4 will refine governance with ScopedMutation precedence rules.
          </p>
        </section>
      )}
    </aside>
  );
}
