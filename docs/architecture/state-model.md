# TEA-MD State Model — Old-to-New Mapping

**Phase 1 of the TEA-MD Overhaul**
Date: 2026-03-18

---

## Summary

The old model was fragmented across parallel stores:
`formMatrix`, `S`, `V`, `R`, `F`, `RF`, `scalingGroups`, `finalResults`, `zones`.

The new model is version-centric:
Each `VersionSlot` is the primary container of analytical reality.
One slot = one baseline = one explicit assembly.

---

## Old → New mapping

### `versions` (object with list/active/metadata)

| Old | New |
|-----|-----|
| `versions.list` | `versionSlots.keys()` |
| `versions.active` | `activeVersionSlot.id` (via VersionStateContext) |
| `versions.metadata[id]` | `versionSlots.get(id)` — a full `VersionSlot` |

Migration: `versionSlotFromLegacy(id, meta)` in `src/model/coreTypes.js`

---

### `zones` (object with list/active/metadata)

| Old | New |
|-----|-----|
| `zones` entire object | **QUARANTINED** — not a core concept |
| `formMatrix[id].matrix[vId][zId]` | `resolveValue(param, vId)` from `legacyZoneAdapter` |
| `createZone()` | No replacement — zone creation is deprecated |
| `setActiveZone()` | No replacement — zone is collapsed to canonical `z1` |

All zone reads route through `src/adapters/legacyZoneAdapter.js`.
Zone state in `Consolidated2` is kept only to avoid breaking existing initialisation.

---

### `formMatrix`

| Old | New |
|-----|-----|
| `formMatrix[paramId].matrix[vId][zId]` | `resolveValue(formMatrix[paramId], vId)` |
| No baseline partitioning | `BaselineAssembly.directInputs` (project/loan/rates) + `admittedDerivedFacts` |
| All entries treated equally | Split: direct-input params vs. scaling-output (Amount4-7) params |

---

### `S` (sensitivity state)

| Old | New |
|-----|-----|
| `S[sKey] = {status, mode, variation, values}` | Target: `ScopedMutation` objects (Phase 4) |
| Phase 1 disposition | **Kept as-is** — tagged `@deprecated` for Phase 4 collapse |

`S` remains the operational sensitivity authoring surface through Phase 3.
Phase 4 will express the same modeling power via `ScopedMutation`.

---

### `V`, `R`, `F`, `RF` (participation toggle flags)

| Old | New |
|-----|-----|
| `V['V1'] = 'on'/'off'` | `DerivedSummaryFact.participationState = 'admitted'/'excluded'` |
| Implicit toggle checked at run time | Explicit admission in `BaselineAssembly.admittedDerivedFacts` |
| Phase 1 disposition | Kept as runtime toggles; `assembleBaseline()` reads them |

---

### `scalingGroups` + `finalResults`

| Old | New |
|-----|-----|
| `finalResults[workspace]` = flat array | `DerivedSummaryFact[]` per workspace (Phase 3 formalises) |
| `scalingGroups` = array of group configs | Provenance source for `DerivedSummaryFact.provenance.scalingGroupId` |
| Phase 1 disposition | Kept as-is; `assembleBaseline()` converts them to `DerivedSummaryFact` |

---

### `VersionStateContext`

| Old | New |
|-----|-----|
| `version` (string) | `version` **kept** + `activeVersionSlot` (VersionSlot object) |
| `selectedVersions` (string[]) | **kept** + `comparisonSession` (ComparisonSession object) |
| No comparison state | `comparisonSession`, `openComparisonSession`, `updateComparisonSession` |
| No version registry | `versionRegistry` (Map<id, VersionSlot>), `registerVersionSlot`, `updateVersionSlot` |

---

## New type locations

| Type | File |
|------|------|
| `VersionSlot` | `src/model/coreTypes.js` |
| `VersionLineage` | `src/model/coreTypes.js` |
| `BaselineAssembly` | `src/model/coreTypes.js` |
| `DirectInputs` | `src/model/coreTypes.js` |
| `DerivedSummaryFact` | `src/model/coreTypes.js` |
| `ScopedMutation` | `src/model/coreTypes.js` (wired in Phase 4) |
| `VersionProjection` | `src/model/coreTypes.js` (wired in Phase 2) |
| `ComparisonCell` | `src/model/coreTypes.js` (wired in Phase 2) |
| `ComparisonSession` | `src/model/coreTypes.js` |

---

## Deprecated / quarantined

| Item | Location | Replacement |
|------|----------|-------------|
| `zones` state | `Consolidated2.js` | Removed from new code; adapter only |
| `createZone()` | `Consolidated2.js` | None — zone not needed |
| `setActiveZone()` | `Consolidated2.js` | None |
| `VersionZoneManager` (zone panel) | `src/managers/VersionZoneManager.js` | Do not add consumers |
| `zonesAtom` | `src/atoms/matrixFormValues.js` | Subordinated — tooltip only |

---

## Baseline assembly rules (from architectural directives)

Direct inputs (always included):
- Project config: `plantLifetimeAmount10`, `constructionTimeAmount11`, `plantCapacityAmount12`, `plantCapacityFactorAmount13`
- Loan config: `debtRatioAmount20`, `interestRateAmount21`, `loanTermAmount22`
- Rates & fixed costs: `inflationRateAmount30`-`33`, `F1Amount34`-`F5Amount38`

Derived facts (Amount4-7 only, only if enabled):
- `Amount4` — Process Quantities (V toggle)
- `Amount5` — Process Costs (V toggle)
- `Amount6` — Additional Revenue Quantities (R toggle)
- `Amount7` — Additional Revenue Prices (R toggle)

Everything else (intermediate scaling state, plot options, etc.) is NOT part of baseline.
