# Duration Visualization — Integration Plan

**Document:** Generalized Duration Configuration Visualization
**Source file:** `src/generalized_duration_visualization.html`
**Target:** Full React/Jotai integration into TEA-MD
**Date:** March 18, 2026

---

## 1. What the HTML Does (Summary)

The standalone HTML is a complete, self-contained visualization with:

- **Parameter matrix** — sticky-column table where rows are variables (parameters) and columns are time units (years by default), each cell showing a fill bar representing efficacy coverage.
- **Hierarchical column expansion** — clicking any column header drills it down into children (Year → Months → Days → Hours → … → Nanosecond), one expansion chain active at a time.
- **3D tile directory explorer** — a modal overlay with `perspective: 1600px` glassmorphic tiles at each hierarchy depth; clicking a tile navigates the expansion path.
- **Cell inspector** — right-side panel showing full details of the selected cell: coverage percentage, nanosecond range, all overlapping efficacy periods, resolution precedence.
- **Path parser / Locate feature** — toolbar input accepts `Y3/Jun/D15/08h` style paths, navigates the table and scrolls to the target cell.
- **Tooltip** — transient card on cell hover (hides on mouse-out).
- **BigInt nanosecond math** — all time calculations use ES2020 `BigInt`, covering all 15 levels from Year to Nanosecond.

The HTML has **no external dependencies** — no React, no Jotai, no CDN links. All state lives in a single `state` object; rendering is pure `innerHTML` assignment.

---

## 2. Target Integration Architecture

### New component

```
src/components/modules/DurationConfigMatrix.jsx    ← main React component
src/styles/HomePage.CSS/DurationConfigMatrix.css   ← extracted CSS
src/utils/durationUnits.js                         ← BigInt math utilities (new file)
```

### Files to modify

| File | Change |
|------|--------|
| `src/HomePage.js` | Add import, tab button, tab case |
| `src/Consolidated2.js` | Add `resolution` field to `efficacyPeriod`, add migration helper |
| `src/components/modules/Efficacy.js` | Add resolution selector + sub-second path navigator |
| `src/services/MatrixSubmissionService.js` | Add BigInt-serialized start/end + resolution to payload |
| `src/services/CapacityTrackingService.js` | Resolution-aware conflict detection |

---

## 3. File-by-File Changes

### 3.1 New file — `src/utils/durationUnits.js`

Extract the following verbatim from the HTML's `<script>` block:

- `LEVELS` array (all 15 entries with `key`, `title`, `symbol`, `nextTitle`)
- `LEVEL_INDEX` lookup object
- `SUB_NS` object (BigInt nanosecond values for ds through ns)
- `PLANT_EPOCH_NS` — **change**: derive from `plantLifetime` arg, not hardcoded 2026
- All pure utility functions:
  - `pathEntry`, `clonePath`, `pathToObject`
  - `formatLevelValue`, `levelSymbol`, `pathToString`, `pathTokenString`, `pathKey`, `pathsEqual`, `isPrefix`
  - `getDaysInMonth`, `calendarStartDate`, `pathToStartNs`, `nextStartNs`, `pathRange`
  - `nsToDisplay`, `formatInt`, `formatPercent`
  - `overlapLength`, `unionLength`
  - `parsePathString`, `validatePath`
  - `makePeriod`
  - `getChildren`
  - `buildVisibleColumns`
  - `computeCell`

Export all of them. None of these functions touch the DOM or hold state; they are pure and portable as-is.

**Critical change:** `PLANT_EPOCH_NS` is currently:
```js
// HTML version (hardcoded)
const PLANT_EPOCH_NS = BigInt(Date.UTC(2026, 0, 1, 0, 0, 0, 0)) * 1000000n;
```
Change to a factory function:
```js
// durationUnits.js
export function makePlantEpoch(baseYear) {
  return BigInt(Date.UTC(baseYear, 0, 1, 0, 0, 0, 0)) * 1_000_000n;
}
```
Pass this through to any function that currently reads the module-level constant.

---

### 3.2 New file — `src/utils/durationUnits.js` — Data shape bridge

The app's existing `efficacyPeriod` shape (from `Consolidated2.js` / `Efficacy.js`):
```js
// CURRENT (year-integer based)
efficacyPeriod: {
  start: { value: 3 },   // year index, 1-based
  end:   { value: 7 },
  isCustomized: false
}
```

The HTML visualization expects a `period` object with:
```js
{
  startPath,    // [{ key:'Y', value:3 }, ...]  parsed path array
  endPath,      // [{ key:'Y', value:7 }]
  start,        // BigInt nanoseconds
  end,          // BigInt nanoseconds
  resolution,   // 'Y' | 'M' | 'D' | ... | 'ns'
  label,        // string (parameter label)
  detail,       // string (unit or description)
  value         // numeric value
}
```

Add a migration helper in `durationUnits.js`:
```js
export function legacyPeriodToVisualization(old, paramLabel, paramUnit, baseYear = 2026) {
  const epoch = makePlantEpoch(baseYear);
  const startPath = [{ key: 'Y', value: old.start.value }];
  const endPath   = [{ key: 'Y', value: old.end.value   }];
  return {
    startPath,
    endPath,
    start: pathToStartNs(startPath, epoch),
    end:   nextStartNs(endPath, epoch) - 1n,
    resolution: old.resolution ?? 'Y',
    label: paramLabel,
    detail: paramUnit ?? '',
    value: old.scaledValue ?? old.baseValue ?? 0,
  };
}
```

This lets the visualization render the existing app data immediately on the first integration pass, before any schema migration.

---

### 3.3 New file — `src/components/modules/DurationConfigMatrix.jsx`

**Port strategy:** The HTML has 5 rendering functions and a `state` object. Each render function becomes a React sub-component (or returns JSX). The `state` object becomes `useState`/`useAtom` hooks.

#### Props interface

```jsx
<DurationConfigMatrix
  formValues={formValues}           // from useMatrixFormValues
  activeVersion={versions.active}   // from versionsAtom
  activeZone={zones.active}         // from zonesAtom
  plantLifetime={plantLifetime}     // number (from plantLifetimeAmount10)
  baseYear={2026}                   // or from app config
/>
```

#### State (useState hooks inside component)

| HTML `state` field | React equivalent |
|--------------------|------------------|
| `state.expansionPath` | `const [expansionPath, setExpansionPath] = useState([])` |
| `state.explorerPath` | `const [explorerPath, setExplorerPath] = useState([])` |
| `state.selectedCell` | `const [selectedCell, setSelectedCell] = useState(null)` |
| `state.visibleColumns` | derived via `useMemo` from `expansionPath` |
| `state.tooltipCell` | `const [tooltipCell, setTooltipCell] = useState(null)` |
| `state.pendingLocate` | `const [pendingLocate, setPendingLocate] = useState(null)` |

#### Rows (parameter data)

Replace `seedRows()` / `MODEL.rows` with a `useMemo` that builds rows from `formValues`:

```jsx
const rows = useMemo(() => {
  if (!formValues) return [];
  return Object.entries(formValues)
    .filter(([, item]) => item?.efficacyPeriod)
    .map(([paramId, item]) => ({
      id: paramId,
      name: item.label ?? paramId,
      unit: item.unit ?? '',
      description: item.description ?? '',
      periods: [
        legacyPeriodToVisualization(
          item.efficacyPeriod,
          item.label ?? paramId,
          item.unit ?? '',
          baseYear
        )
      ]
    }));
}, [formValues, baseYear]);
```

When the app eventually upgrades `efficacyPeriod` to BigInt (Phase 2 per the spec), drop `legacyPeriodToVisualization` and pass the periods directly.

#### MODEL equivalents

```jsx
const yearCount = plantLifetime;            // from prop
const baseYear  = props.baseYear ?? 2026;
const plantEpoch = useMemo(() => makePlantEpoch(baseYear), [baseYear]);
```

Pass `plantEpoch` as a parameter to `pathToStartNs`, `nextStartNs`, `pathRange` (which you added the parameter to in step 3.1).

#### Sub-component breakdown

```
DurationConfigMatrix
├── MatrixShell          ← wraps the scrollable table
│   ├── MatrixHeader     ← sticky thead, one th per column
│   └── MatrixBody       ← tbody rows (one per parameter)
│       └── MatrixCell   ← fill bar + badge, cell click handler
├── InspectorPanel       ← right sidebar (360px fixed)
│   ├── InspectionSection (coverage/path/duration/abs ns)
│   ├── VisibleBranchSection
│   └── OverlapsList     ← list of overlap-cards
├── DirectoryModal       ← 3D tile explorer (position:fixed)
│   ├── BreadcrumbBar
│   └── TileShelf        ← grid of .tile elements with 3D transforms
├── TooltipCard          ← position:fixed, opacity-animated
└── ToolbarBar           ← reset, collapse, open-directory, locate controls
```

#### CSS extraction — `src/styles/HomePage.CSS/DurationConfigMatrix.css`

Extract the full `<style>` block from the HTML verbatim. Replace the `body` selector rule:
```css
/* HTML version — becomes the component root div */
body { display: grid; grid-template-rows: auto auto 1fr; ... }
```
with:
```css
.dcm-root { display: grid; grid-template-rows: auto auto 1fr; height: 100%; ... }
```

**Important:** All class names in the HTML are generic (`.shell`, `.toolbar`, `.matrix-wrap`, `.tile`). To avoid collisions with existing TEA-MD styles, prefix them:

| HTML class | Prefixed class |
|-----------|---------------|
| `.shell` | `.dcm-shell` |
| `.toolbar` | `.dcm-toolbar` |
| `.workspace` | `.dcm-workspace` |
| `.matrix-wrap` | `.dcm-matrix-wrap` |
| `.tile` | `.dcm-tile` |
| `.inspector` | `.dcm-inspector` |
| `.modal` | `.dcm-modal` |
| `.modal-card` | `.dcm-modal-card` |
| `.tooltip` | `.dcm-tooltip` |
| `.breadcrumb` | `.dcm-breadcrumb` |

All other classes (`.fill-bar`, `.fill-track`, `.sticky-col`, `.explorer-stage`, `.shelf`, `.overlap-card`, `.pill`) should be prefixed similarly with `dcm-`.

The CSS custom properties (`:root` variables) should be scoped to `.dcm-root` instead of `:root` to avoid overriding the app's global theme variables. Map where possible:

| HTML variable | App equivalent (from Consolidated.css/theme) |
|--------------|----------------------------------------------|
| `--text` | `var(--text-color)` |
| `--muted` | `var(--text-secondary)` |
| `--border` | `var(--border-color)` |
| `--accent` | `var(--accent-color)` |
| `--radius` | `var(--model-border-radius-sm)` |
| `--transition` | keep as-is (`240ms cubic-bezier(0.42,0,0.28,0.99)`) |

The 3D transform values on tiles must remain exactly:
- **Resting:** `rotateX(10deg) rotateY(-8deg) translateY(0) scale(1)`
- **Hover:** `rotateX(0deg) rotateY(0deg) translateY(-8px) scale(1.02)`
- **Selected:** `rotateX(0deg) rotateY(0deg) translateY(-6px) scale(1.015)`
- **Perspective:** `perspective: 1600px` on `.dcm-explorer-stage`

These are the visual signature of the component and must not be altered.

---

### 3.4 `src/HomePage.js` — Add tab

Add three things:

**Import** (after HierarchyShelfComponent import):
```jsx
import DurationConfigMatrix from './components/modules/DurationConfigMatrix';
```

**Tab button** (alongside the "Time Hierarchy" button):
```jsx
<button
  className={`tab-button ${activeTab === 'DurationMatrix' ? 'active' : ''}`}
  onClick={() => setActiveTab('DurationMatrix')}
>
  Duration Matrix
</button>
```

**Tab case** (in the `switch(activeTab)` or `renderTabContent` function):
```jsx
case 'DurationMatrix':
  return (
    <DurationConfigMatrix
      formValues={formValues}
      activeVersion={versions.active}
      activeZone={zones.active}
      plantLifetime={plantLifetime}
      baseYear={2026}
    />
  );
```

**Container class** (same pattern used for NaturalMotion):
```jsx
className={`content-container${
  activeTab === 'NaturalMotion' ? ' nm-tab-active' :
  activeTab === 'DurationMatrix' ? ' dcm-tab-active' : ''
}`}
```

Add CSS override in `DurationConfigMatrix.css` (or at the bottom of an existing sheet):
```css
.content-container.dcm-tab-active {
  display: block !important;
  overflow: visible !important;
}
.HomePageTabContent.dcm-tab-active {
  overflow: visible !important;
  height: 100%;
}
```

The `DurationConfigMatrix` component root div should be `height: 100%; overflow: hidden` to fill the tab panel exactly.

---

### 3.5 `src/Consolidated2.js` — Efficacy period schema extension

**Phase 1 (backward-compatible, no breaking change):**

Add an optional `resolution` field to the `efficacyPeriod` initializer in `useMatrixFormValues`:
```js
// existing shape
efficacyPeriod: {
  start: { value: 0 },
  end:   { value: plantLifetime },
  isCustomized: false,
  // ADD:
  resolution: 'Y',   // default keeps current behavior
}
```

The `applyEfficacyToScalingGroups` function reads `.efficacyPeriod.start.value` and `.efficacyPeriod.end.value` as year integers — these remain unchanged. The new `resolution` field is only consumed by:
- `DurationConfigMatrix` (passes to `legacyPeriodToVisualization`)
- `MatrixSubmissionService` (adds to API payload)

**Phase 2 (future, breaking):**
When the app fully migrates to BigInt ns offsets, replace:
```js
// current integer year
efficacyPeriod: { start: { value: 3 }, end: { value: 7 } }
// future BigInt ns
efficacyPeriod: { start: { value: 63072000000000000n }, end: { value: 220752000000000000n }, resolution: 'Y' }
```
Use `migrateLegacyPeriod()` from `durationUnits.js` during migration. The TEA-MD spec doc section 4.3 describes the exact conversion formula.

---

### 3.6 `src/components/modules/Efficacy.js` — Resolution selector

The HTML visualization shows what the data should look like when a user selects sub-second resolution. This feeds back into `Efficacy.js`.

**Phase 1 change (minimal):** Add a resolution dropdown above the year slider:
```jsx
<select value={resolution} onChange={e => setResolution(e.target.value)}>
  <option value="Y">Year</option>
  <option value="M">Month</option>
  <option value="D">Day</option>
  <option value="H">Hour</option>
  <option value="Min">Minute</option>
  <option value="S">Second</option>
  <option value="ms">Millisecond</option>
  <option value="us">Microsecond</option>
  <option value="ns">Nanosecond</option>
</select>
```

Save `resolution` into `efficacyPeriod` via `handleInputChange(e, id, 'efficacyPeriod', 'resolution')`.

**Phase 2 change (full):** When resolution is finer than Year, replace the dual-slider with a path navigator. Reuse `parsePathString` and `getChildren` from `durationUnits.js` to build the navigator UI. The HTML's `#locatePath` input + `handleLocate()` is a working prototype of this navigator.

---

### 3.7 `src/services/MatrixSubmissionService.js` — Payload extension

The HTML spec (section 4.4) defines the extended payload:
```json
{
  "id": "reactionRate_Amount42",
  "value": 0.0034,
  "start": "63072000000000000",
  "end":   "63072000001000000",
  "resolution": "ms",
  "remarks": "Catalyst activation window"
}
```

In `MatrixSubmissionService.js`, modify the parameter-serialization step to:
1. If `efficacyPeriod.resolution` is `'Y'` (or absent), keep existing behavior (integer year start/end).
2. If resolution is anything else, serialize `start`/`end` as string-encoded BigInt from `pathToStartNs`/`nextStartNs`.

Use `legacyPeriodToVisualization` to compute the BigInt values if the internal representation is still year-integers.

---

### 3.8 `src/services/CapacityTrackingService.js` — Resolution-aware conflict detection

Currently conflict detection compares year integers. Per spec section 7:
> A parameter at `resolution: 'ms'` is checked for conflicts at millisecond granularity within its efficacy span.

**Phase 1 (no-op):** Add a check: if two parameters have different resolutions, the conflict check only applies if one period is entirely nested inside another at the coarser resolution. No code change needed for year-only data.

**Phase 2:** Replace the integer year comparison with the `overlapLength` + `unionLength` functions from `durationUnits.js`, operating on BigInt ns values.

---

## 4. Dependency Requirements

All of these already exist in the project or are standard:

| Dependency | Status | Notes |
|-----------|--------|-------|
| `react`, `react-dom` | ✅ existing | JSX rendering |
| `jotai` | ✅ existing | State management (for atoms) |
| `BigInt` | ✅ ES2020 | Already used in HTML; Node 10.4+, all modern browsers |
| `Inter` font | ✅ already loaded | Via existing CSS imports |
| CSS `backdrop-filter` | ✅ supported | Chrome 76+, Safari 9+, Firefox 103+ |
| CSS 3D transforms | ✅ supported | All modern browsers |
| `window.CSS.escape()` | ✅ supported | For `cssEscape` utility |

No new npm packages are required.

---

## 5. Integration Order (Phases)

### Phase 1 — Visual integration, read-only (no data model change)

1. Create `src/utils/durationUnits.js` — copy + refactor pure functions from HTML
2. Create `src/styles/HomePage.CSS/DurationConfigMatrix.css` — extract + prefix all classes
3. Create `src/components/modules/DurationConfigMatrix.jsx` — port HTML to React using `legacyPeriodToVisualization` to bridge existing year-integer `efficacyPeriod` data
4. Edit `src/HomePage.js` — add "Duration Matrix" tab
5. Verify: component renders with real app parameter data, all tiles animate, inspector works, locate feature works

**Acceptance test:** Open "Duration Matrix" tab → see all parameters from `formValues` as rows → Year columns Y1–Y{plantLifetime} → click any cell → inspector updates correctly → open directory explorer → 3D tiles respond to hover.

### Phase 2 — Data model migration

6. Edit `src/Consolidated2.js` — add `resolution: 'Y'` to `efficacyPeriod` defaults
7. Edit `src/components/modules/Efficacy.js` — add resolution dropdown, save to `efficacyPeriod`
8. Edit `src/services/MatrixSubmissionService.js` — add BigInt payload fields
9. Edit `src/services/CapacityTrackingService.js` — resolution-aware conflict detection
10. Drop `legacyPeriodToVisualization` from component, use native BigInt period objects directly

### Phase 3 — Sub-second navigator in Efficacy.js

11. Build `DirectoryNavigator` sub-component from HTML's `renderExplorer` / tile shelf logic
12. Integrate into `Efficacy.js` as the start/end picker for resolutions finer than Year

---

## 6. Key Mapping: HTML identifiers → React props/state

| HTML id / variable | React equivalent |
|-------------------|-----------------|
| `MODEL.yearCount` | `props.plantLifetime` |
| `MODEL.baseYear` | `props.baseYear` |
| `MODEL.rows` | `rows` (useMemo from `formValues`) |
| `state.expansionPath` | `useState([])` |
| `state.selectedCell` | `useState(null)` |
| `state.explorerPath` | `useState([])` |
| `state.visibleColumns` | `useMemo(() => buildVisibleColumns(expansionPath, yearCount), [expansionPath, yearCount])` |
| `#summaryGrid` | `<SummaryGrid>` sub-component |
| `#breadcrumb` | `<BreadcrumbBar path={expansionPath} onJump={setExpansionPath}>` |
| `#matrixWrap` | `<MatrixShell>` |
| `#inspector` | `<InspectorPanel cell={selectedCell}>` |
| `#directoryModal` | `<DirectoryModal open={dirOpen} path={explorerPath}>` |
| `#tileShelf` | `<TileShelf children={getChildren(explorerPath)}>` |
| `#tooltip` | `<TooltipCard cell={tooltipCell} target={tooltipTarget}>` |
| `renderAll()` | React re-render (state updates trigger automatically) |
| `attachGlobalEvents()` | `useEffect` with cleanup |

---

## 7. Overflow / Container CSS Notes

The 3D tile transforms (`rotateX`, `rotateY`, `translateY(-8px)`, `scale(1.02)`) require the `dcm-explorer-stage` ancestor chain to have `overflow: visible`. The same issue that was fixed for `Naturalmotion.js` (the `nm-tab-active` class) applies here:

Add to `DurationConfigMatrix.css`:
```css
/* Unlock overflow for 3D transforms on the tab container ancestors */
.content-container.dcm-tab-active {
  display: block !important;
  overflow: visible !important;
}
.HomePageTabContent.dcm-tab-active {
  overflow: visible !important;
}
```

The `dcm-matrix-wrap` (the scrollable table area) must keep `overflow: auto` internally. Only the outer tab containers need `overflow: visible`.

---

## 8. Files Summary

### New files to create

| Path | Source | Notes |
|------|--------|-------|
| `src/utils/durationUnits.js` | Extract from HTML `<script>` | Pure functions, no DOM, no React |
| `src/components/modules/DurationConfigMatrix.jsx` | Port HTML structure to JSX | Main component |
| `src/styles/HomePage.CSS/DurationConfigMatrix.css` | Extract from HTML `<style>` | Prefix all classes with `dcm-` |

### Files to modify (Phase 1 only)

| Path | Change |
|------|--------|
| `src/HomePage.js` | Import + tab button + tab case + `dcm-tab-active` class |

### Files to modify (Phase 2)

| Path | Change |
|------|--------|
| `src/Consolidated2.js` | Add `resolution: 'Y'` to `efficacyPeriod` default |
| `src/components/modules/Efficacy.js` | Resolution dropdown + path navigator |
| `src/services/MatrixSubmissionService.js` | BigInt-serialized fields in payload |
| `src/services/CapacityTrackingService.js` | Resolution-aware overlap checking |

---

## 9. What Not to Change

- The HTML file `src/generalized_duration_visualization.html` — keep as the canonical reference; do not modify it.
- `src/Naturalmotion.js` — the NaturalMotion tab is separate; do not merge.
- The existing `efficacyPeriod` integer-year shape — Phase 1 bridges it without breaking any existing feature.
- `src/components/modules/TimeParameterMatrix.js` — that component visualizes year-level conflicts; `DurationConfigMatrix` is a superset that eventually replaces or augments it, but do not change `TimeParameterMatrix` during Phase 1.
