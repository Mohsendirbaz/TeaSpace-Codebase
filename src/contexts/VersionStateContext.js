/**
 * VersionStateContext.js — Version-Centric Analytical Context
 *
 * Phase 1 of the TEA-MD Overhaul.
 *
 * This context is no longer a thin string-version holder.
 * It is the primary analytical state context for the new model:
 *
 *   VersionSlot registry  — canonical version objects
 *   ComparisonSession     — active comparison workspace state
 *   activeVersionSlot     — the currently focused VersionSlot
 *
 * BACKWARD COMPATIBILITY:
 *   `version` and `setVersion` remain exported and function as before
 *   (they shadow the active slot id).  Code that was using the old
 *   VersionStateContext continues to work without modification.
 *   Migrate consumers to `activeVersionSlot` and `versionRegistry` in
 *   subsequent phases.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import {
  createVersionSlot,
  createComparisonSession,
  versionSlotFromLegacy,
} from '../model/coreTypes';
import { createAgentCandidate } from '../model/agentCandidate';

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const VersionStateContext = createContext(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

/**
 * @param {{ children: React.ReactNode }} props
 */
export function VersionStateProvider({ children }) {

  // ── Legacy backward-compat state (Phase 1: kept as-is) ──────────────────

  /** @type {[string, Function]} */
  const [version, setVersion] = useState('1');

  /**
   * Selected version ids for batch operations / comparison.
   * Legacy shape: string[] of numeric-string ids like ['1', '2'].
   * @type {[string[], Function]}
   */
  const [selectedVersions, setSelectedVersions] = useState([]);

  // ── New: VersionSlot registry ─────────────────────────────────────────────

  /**
   * Map<versionSlotId, VersionSlot>
   * The canonical registry of all version slots.
   * Initialized with 'v1' to match legacy Consolidated2 default.
   *
   * @type {[Map<string, import('../model/coreTypes').VersionSlot>, Function]}
   */
  const [versionRegistry, setVersionRegistry] = useState(() => {
    const initialSlot = createVersionSlot({
      id: 'v1',
      label: 'Base Case',
      description: 'Default financial case',
    });
    return new Map([['v1', initialSlot]]);
  });

  // ── New: ComparisonSession ────────────────────────────────────────────────

  /**
   * The active comparison session.  null = no comparison active.
   * @type {[import('../model/coreTypes').ComparisonSession|null, Function]}
   */
  const [comparisonSession, setComparisonSession] = useState(null);

  // ── Derived: activeVersionSlot ────────────────────────────────────────────

  /**
   * The VersionSlot corresponding to the currently active version.
   * Derived from versionRegistry + version (legacy string id).
   *
   * Legacy version ids are numeric strings ('1', '2', …).
   * Slot ids follow 'v1', 'v2', … pattern.
   * Bridge: try direct match first, then prepend 'v'.
   *
   * @returns {import('../model/coreTypes').VersionSlot|null}
   */
  const activeVersionSlot = (() => {
    // Try direct key
    if (versionRegistry.has(version)) return versionRegistry.get(version);
    // Try 'v' + legacy numeric string
    const withV = `v${version}`;
    if (versionRegistry.has(withV)) return versionRegistry.get(withV);
    return null;
  })();

  // ── Registry operations ───────────────────────────────────────────────────

  /**
   * Register a new VersionSlot in the registry.
   * Also updates the legacy `version` string to match.
   *
   * @param {import('../model/coreTypes').VersionSlot} slot
   */
  const registerVersionSlot = useCallback((slot) => {
    setVersionRegistry(prev => {
      const next = new Map(prev);
      next.set(slot.id, slot);
      return next;
    });
  }, []);

  /**
   * Update an existing VersionSlot (e.g. after baseline assembly).
   *
   * @param {string} slotId
   * @param {Partial<import('../model/coreTypes').VersionSlot>} patch
   */
  const updateVersionSlot = useCallback((slotId, patch) => {
    setVersionRegistry(prev => {
      const existing = prev.get(slotId);
      if (!existing) return prev;
      const next = new Map(prev);
      next.set(slotId, { ...existing, ...patch, modified: Date.now() });
      return next;
    });
  }, []);

  /**
   * Bootstrap the registry from a legacy `versions` object (from Consolidated2).
   * Call this once when the hook initializes if the registry is empty.
   *
   * @param {{ list: string[], metadata: Object }} legacyVersions
   */
  const bootstrapFromLegacy = useCallback((legacyVersions) => {
    setVersionRegistry(prev => {
      const next = new Map(prev);
      (legacyVersions.list ?? []).forEach(id => {
        if (!next.has(id)) {
          const meta = legacyVersions.metadata?.[id] ?? {};
          next.set(id, versionSlotFromLegacy(id, meta));
        }
      });
      return next;
    });
  }, []);

  // ── Comparison session operations ─────────────────────────────────────────

  /**
   * Open a new comparison session.
   *
   * @param {string} referenceVersionId
   * @param {string[]} candidateVersionIds
   * @param {'overlay'|'delta'|'governance'|'lineage'} [mode]
   */
  const openComparisonSession = useCallback((
    referenceVersionId,
    candidateVersionIds = [],
    mode = 'overlay'
  ) => {
    setComparisonSession(
      createComparisonSession({ referenceVersionId, candidateVersionIds, mode })
    );
  }, []);

  /**
   * Update the active comparison session (e.g. change mode or selected cell).
   *
   * @param {Partial<import('../model/coreTypes').ComparisonSession>} patch
   */
  const updateComparisonSession = useCallback((patch) => {
    setComparisonSession(prev => prev ? { ...prev, ...patch } : null);
  }, []);

  /** Close / dismiss the active comparison session. */
  const closeComparisonSession = useCallback(() => {
    setComparisonSession(null);
  }, []);

  // ── Phase 5: Agent candidate registration ─────────────────────────────────

  /**
   * Register an agent-authored candidate version slot.
   * The slot is created with authorType:'agent' and added to the registry.
   * Immediately available in the comparison surface.
   *
   * @param {object} config — same as createAgentCandidate config
   * @returns {import('../model/coreTypes').VersionSlot}  the created slot
   */
  const registerAgentCandidate = useCallback((config) => {
    const slot = createAgentCandidate(config);
    setVersionRegistry(prev => {
      const next = new Map(prev);
      next.set(slot.id, slot);
      return next;
    });
    return slot;
  }, []);

  // ── Context value ─────────────────────────────────────────────────────────

  const value = {
    // ── Legacy (backward-compat — do not remove until all consumers migrated) ──
    version,
    setVersion,
    selectedVersions,
    setSelectedVersions,

    // ── New Phase-1 surface ───────────────────────────────────────────────────
    /** @type {Map<string, import('../model/coreTypes').VersionSlot>} */
    versionRegistry,
    /** @type {import('../model/coreTypes').VersionSlot|null} */
    activeVersionSlot,
    registerVersionSlot,
    updateVersionSlot,
    bootstrapFromLegacy,

    /** @type {import('../model/coreTypes').ComparisonSession|null} */
    comparisonSession,
    openComparisonSession,
    updateComparisonSession,
    closeComparisonSession,

    // Phase 5
    registerAgentCandidate,
  };

  return (
    <VersionStateContext.Provider value={value}>
      {children}
    </VersionStateContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Access the version context.  Works for both legacy consumers (version,
 * selectedVersions) and new-model consumers (versionRegistry,
 * activeVersionSlot, comparisonSession).
 */
export function useVersionState() {
  const context = useContext(VersionStateContext);
  if (!context) {
    throw new Error('useVersionState must be used within a VersionStateProvider');
  }
  return context;
}
