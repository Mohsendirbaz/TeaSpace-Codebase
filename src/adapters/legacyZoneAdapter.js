/**
 * legacyZoneAdapter.js — Zone Compatibility Adapter
 *
 * Phase 1 of the TEA-MD Overhaul.
 *
 * Zone is no longer part of the core application model.  This adapter is
 * the ONLY place where zone semantics may survive.  All new code accesses
 * parameter values through this adapter or directly via the new
 * VersionSlot model.
 *
 * Migration path:
 *  - Phase 1: adapter introduced; all new accessors route through here
 *  - Phase 3: scaling pipeline stops using zone keys in outputs
 *  - Future:  delete this file once all consumers are migrated
 *
 * Rule: nothing outside this file may reference `param.matrix[vId][zId]`
 * directly in new code.  Old code that still does so is a regression target.
 */

// ---------------------------------------------------------------------------
// CANONICAL ZONE
// ---------------------------------------------------------------------------

/**
 * The single canonical zone id that the legacy data model uses.
 * All new code collapses multi-zone access to this constant.
 * @type {string}
 */
export const CANONICAL_ZONE = 'z1';

// ---------------------------------------------------------------------------
// Value resolution
// ---------------------------------------------------------------------------

/**
 * Read a parameter value from the legacy `matrix[versionId][zoneId]` structure,
 * collapsing zone to the canonical zone.
 *
 * @param {Object} param       - A formMatrix entry (has .matrix)
 * @param {string} versionId   - Target version id
 * @param {string} [zoneId]    - Optional; defaults to CANONICAL_ZONE
 * @returns {any}              - The stored value, or null if absent
 */
export function resolveValue(param, versionId, zoneId = CANONICAL_ZONE) {
  if (!param?.matrix) return null;
  const vSlot = param.matrix[versionId];
  if (!vSlot) return null;
  // If the matrix already uses the new flat structure (vSlot is not an object
  // keyed by zone, but a plain value), return it directly.
  if (typeof vSlot !== 'object' || vSlot === null) return vSlot;
  // Legacy structure: matrix[vId][zId]
  if (Object.prototype.hasOwnProperty.call(vSlot, zoneId)) {
    return vSlot[zoneId];
  }
  // Fallback: try any zone key (safe during migration)
  const keys = Object.keys(vSlot);
  if (keys.length > 0) return vSlot[keys[0]];
  return null;
}

/**
 * Write a value into the legacy `matrix[versionId][zoneId]` structure.
 * Always writes to the canonical zone so new code is zone-agnostic.
 *
 * Returns a new (shallow-cloned) copy of the param — does not mutate.
 *
 * @param {Object} param       - A formMatrix entry
 * @param {string} versionId
 * @param {any}    value
 * @param {string} [zoneId]
 * @returns {Object}           - Updated param copy
 */
export function writeValue(param, versionId, value, zoneId = CANONICAL_ZONE) {
  const updated = { ...param, matrix: { ...param.matrix } };
  updated.matrix[versionId] = {
    ...(updated.matrix[versionId] ?? {}),
    [zoneId]: value,
  };
  return updated;
}

// ---------------------------------------------------------------------------
// Active-version helpers
// ---------------------------------------------------------------------------

/**
 * Resolve the active value for a parameter using the legacy state shape.
 *
 * @param {Object} param          - formMatrix entry
 * @param {string} activeVersion  - versions.active
 * @param {string} [activeZone]   - zones.active (defaults to CANONICAL_ZONE)
 * @returns {any}
 */
export function resolveActiveValue(param, activeVersion, activeZone = CANONICAL_ZONE) {
  return resolveValue(param, activeVersion, activeZone);
}

// ---------------------------------------------------------------------------
// Flat-value extractor for baseline assembly
// ---------------------------------------------------------------------------

/**
 * Extract a flat { paramId → value } map from the entire formMatrix for
 * a given version.  Zone is always collapsed to canonical.
 *
 * Used by assembleBaselineDirectInputs() in Consolidated2.
 *
 * @param {Object} formMatrix   - Full formMatrix from useMatrixFormValues
 * @param {string} versionId
 * @param {string} [zoneId]
 * @returns {Object.<string, any>}
 */
export function extractFlatValues(formMatrix, versionId, zoneId = CANONICAL_ZONE) {
  const result = {};
  Object.entries(formMatrix).forEach(([paramId, param]) => {
    result[paramId] = resolveValue(param, versionId, zoneId);
  });
  return result;
}

// ---------------------------------------------------------------------------
// Zone deprecation warning (dev-mode only)
// ---------------------------------------------------------------------------

