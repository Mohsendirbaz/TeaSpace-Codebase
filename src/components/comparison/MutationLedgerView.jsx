/**
 * MutationLedgerView.jsx — Linear Mutation Ledger View
 *
 * Phase 4 of the TEA-MD Overhaul.
 *
 * Renders the linear mutation/delta ledger that explains version differences
 * in terms of the unified ScopedMutation model.
 *
 * Each row explains:
 *  - what changed (parameter label + id)
 *  - mutation type (percentage / directvalue / absolutedeparture)
 *  - value
 *  - scoped duration
 *  - reference version
 *  - whether it won (active) or was suppressed
 *  - author type (human / agent)
 *  - rationale
 *
 * This component reads from `scopedMutations` (from useMatrixFormValues) and
 * calls `getMutationLedger()` to get the ordered ledger.
 *
 * It can also be embedded inside ComparisonWorkspace in lineage mode (Phase 5).
 *
 * Props:
 *   scopedMutations  - ScopedMutation[] from useMatrixFormValues
 *   getMutationLedger - function(labelMap?) => LedgerEntry[]
 *   formValues       - from useMatrixFormValues (for label resolution)
 *   versionRegistry  - Map<id, VersionSlot> from VersionStateContext
 */

import React, { useMemo, useState } from 'react';
import { ledgerSummary } from '../../model/mutationLedger';

// ── Mutation type labels ─────────────────────────────────────────────────────

const MUTATION_TYPE_LABELS = {
  percentage:        '% change',
  directvalue:       'direct value',
  absolutedeparture: 'departure',
};

// ── Precedence badge ─────────────────────────────────────────────────────────

function PrecedenceBadge({ status }) {
  return status === 'active'
    ? <span className="mlv-badge mlv-active">✓ active</span>
    : <span className="mlv-badge mlv-suppressed">⚠ suppressed</span>;
}

// ── Author badge ─────────────────────────────────────────────────────────────

function AuthorBadge({ authorType }) {
  return authorType === 'agent'
    ? <span className="mlv-badge mlv-agent">agent</span>
    : <span className="mlv-badge mlv-human">human</span>;
}

// ── Main component ────────────────────────────────────────────────────────────

export default function MutationLedgerView({
  scopedMutations = [],
  getMutationLedger,
  formValues = {},
  versionRegistry,
}) {
  const [filterActive, setFilterActive] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Build label map from formValues
  const labelMap = useMemo(() => {
    const map = {};
    if (!formValues) return map;
    Object.entries(formValues).forEach(([paramId, item]) => {
      if (item?.label) {
        // Map 'plantLifetimeAmount10' to 'Amount10'
        const numericPart = paramId.replace(/\D/g, '');
        if (numericPart) map[`Amount${numericPart}`] = item.label;
        map[paramId] = item.label;
      }
    });
    return map;
  }, [formValues]);

  // Build ledger
  const ledger = useMemo(() => {
    if (getMutationLedger) return getMutationLedger(labelMap);
    return [];
  }, [getMutationLedger, labelMap]);

  // Filter
  const filteredLedger = useMemo(() => {
    let result = ledger;
    if (filterActive) result = result.filter(e => e.precedenceStatus === 'active');
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(e =>
        e.targetId.toLowerCase().includes(term) ||
        e.targetLabel.toLowerCase().includes(term)
      );
    }
    return result;
  }, [ledger, filterActive, searchTerm]);

  const summary = useMemo(() => ledgerSummary(ledger), [ledger]);

  function versionLabel(vId) {
    const slot = versionRegistry?.get(vId) ?? versionRegistry?.get(`v${vId}`);
    return slot ? slot.label : vId;
  }

  if (!ledger.length) {
    return (
      <div className="mlv-root mlv-empty">
        <h3>Mutation Ledger</h3>
        <p>No mutations configured. Enable sensitivity parameters to see them here.</p>
        <p className="mlv-note">
          Phase 4: S entries are bridged to ScopedMutation objects and shown here
          in a linear, auditable format.
        </p>
      </div>
    );
  }

  return (
    <div className="mlv-root">
      <div className="mlv-header">
        <h3 className="mlv-title">Mutation Ledger</h3>
        <div className="mlv-summary-chips">
          <span className="mlv-chip mlv-chip-total">{summary.total} total</span>
          <span className="mlv-chip mlv-chip-active">{summary.active} active</span>
          <span className="mlv-chip mlv-chip-suppressed">{summary.suppressed} suppressed</span>
          {Object.entries(summary.byType).map(([type, count]) => (
            <span key={type} className="mlv-chip mlv-chip-type">
              {count}× {MUTATION_TYPE_LABELS[type] ?? type}
            </span>
          ))}
        </div>
      </div>

      <div className="mlv-toolbar">
        <input
          className="mlv-search"
          type="text"
          placeholder="Search parameter…"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
        />
        <label className="mlv-filter-check">
          <input
            type="checkbox"
            checked={filterActive}
            onChange={e => setFilterActive(e.target.checked)}
          />
          Active only
        </label>
      </div>

      <table className="mlv-table">
        <thead>
          <tr>
            <th>Parameter</th>
            <th>Type</th>
            <th>Value</th>
            <th>Duration</th>
            <th>Reference</th>
            <th>Status</th>
            <th>Author</th>
            <th>Rationale</th>
          </tr>
        </thead>
        <tbody>
          {filteredLedger.map(entry => (
            <tr
              key={entry.id}
              className={`mlv-row ${entry.precedenceStatus === 'suppressed' ? 'mlv-row-suppressed' : ''}`}
            >
              <td className="mlv-param-cell">
                <span className="mlv-param-label">{entry.targetLabel}</span>
                <code className="mlv-param-id">{entry.targetId}</code>
              </td>
              <td>{MUTATION_TYPE_LABELS[entry.mutationType] ?? entry.mutationType}</td>
              <td className="mlv-value-cell">
                {typeof entry.value === 'number'
                  ? entry.mutationType === 'percentage'
                    ? `${entry.value >= 0 ? '+' : ''}${entry.value}%`
                    : entry.value.toFixed(4).replace(/\.?0+$/, '')
                  : String(entry.value ?? '—')}
              </td>
              <td>
                <code className="mlv-duration">{entry.durationPath}</code>
              </td>
              <td>{versionLabel(entry.referenceVersionId)}</td>
              <td><PrecedenceBadge status={entry.precedenceStatus} /></td>
              <td><AuthorBadge authorType={entry.authorType} /></td>
              <td className="mlv-rationale">{entry.rationale ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="mlv-footer-note">
        Phase 4 bridge: S state → ScopedMutation model. Phase 5 will attach downstream impact scores.
      </p>
    </div>
  );
}
