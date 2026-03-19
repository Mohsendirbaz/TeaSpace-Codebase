# Generalized Duration-Atomic Time Model

**TEA Space — Nanosecond-Resolution Efficacy Period Specification**
**Date:** March 18, 2026 | **Prepared for:** Mohsen Dirbaz

---

## 1. Motivation and Scope

Certain techno-economic applications involve registered events at sub-second timescales — high-frequency chemical reactions, photovoltaic transient phenomena, battery cycling kinetics, semiconductor fabrication steps — where each event carries its own economic profile identical in structure to the annual parameters TEA Space already accommodates. The current year-atomic model correctly solves the general case; this specification generalizes the atomic unit to **duration** at arbitrary resolution, with the nanosecond (10⁻⁹ s) as the finest leaf.

The key insight: **the CFA engine does not inherently care about the semantic meaning of its time index.** It iterates a configuration matrix whose rows have `start`, `end`, and `length` fields. Whether those indices represent years, months, or nanoseconds is a matter of encoding and presentation, not computation. The generalization is therefore primarily a representation and navigation problem, not an algorithmic one.

---

## 2. Hierarchical Time Model

### 2.1 The 15-Level Hierarchy

The progression from Year to Nanosecond follows calendar conventions through seconds, then orders of magnitude to 10⁻⁹:

```
Depth  Level              Symbol   Fanout   Duration per unit
─────  ─────────────────  ──────   ──────   ─────────────────
  0    Year               Y        root     3.156 × 10⁷ s
  1    Month              M        12       ~2.63 × 10⁶ s
  2    Day                D        28–31    8.64 × 10⁴ s
  3    Hour               H        24       3.60 × 10³ s
  4    Minute             Min      60       60 s
  5    Second             S        60       1 s
  6    Decisecond         ds       10       10⁻¹ s
  7    Centisecond        cs       10       10⁻² s
  8    Millisecond        ms       10       10⁻³ s
  9    10⁻⁴ second        t4       10       10⁻⁴ s
 10    10⁻⁵ second        t5       10       10⁻⁵ s
 11    Microsecond        μs       10       10⁻⁶ s
 12    10⁻⁷ second        t7       10       10⁻⁷ s
 13    10⁻⁸ second        t8       10       10⁻⁸ s
 14    Nanosecond         ns       10       10⁻⁹ s
```

### 2.2 Address Space Analysis

For a 20-year plant lifetime:

| Metric | Value |
|--------|-------|
| Total nanosecond leaves | ~6.31 × 10¹⁷ |
| Bits required for absolute offset | 60 |
| 64-bit integer capacity | 9.22 × 10¹⁸ (covers 292 years) |
| Maximum fanout at any level | 60 (Minute→Second) |
| Maximum navigation depth | 14 clicks |
| Maximum children displayed | 60 (never more) |

The critical observation: **the fanout never exceeds 60.** This means at any point in the navigation hierarchy, the user sees at most 60 items — a manageable cognitive load comparable to minutes on a clock face. The 6.31 × 10¹⁷ leaf space is never enumerated; only the current level's children are instantiated.

### 2.3 Absolute Nanosecond Encoding

Every time instant is represented as a single `int64` — the number of nanoseconds from the plant-lifetime epoch (start of Year 1):

```
Absolute ns offset = (Y-1)×Mns + (M-1)×Dns + (D-1)×86400×10⁹
                   + H×3600×10⁹ + Min×60×10⁹ + S×10⁹
                   + ds×10⁸ + cs×10⁷ + ms×10⁶ + t4×10⁵
                   + t5×10⁴ + μs×10³ + t7×10² + t8×10 + ns
```

where `Mns` and `Dns` are the nanosecond widths of the respective year and month (accounting for varying month lengths).

Reconstructing the hierarchical address from an absolute offset is pure integer division at each level — no floating point, no ambiguity.

---

## 3. Nested Directory Interface

### 3.1 Design Principle: Horizontal Folder Navigation

The interface models time as a **filesystem** where each level is a directory containing its children as subdirectories (or files, at the leaf level). The user navigates horizontally — the breadcrumb path grows rightward as depth increases, and the current level's children are displayed as a flat listing.

```
Path: / Y3 / Jun / D15 / 08h / 30m / 45s / ds3 / cs7 / ms2

┌──────────────────────────────────────────────────────────┐
│  Current: Millisecond (10⁻³ s)    10 entries             │
│                                                          │
│  ▸ 0    ▸ 1    ▸ 2    ▸ 3    ▸ 4                       │
│  ▸ 5    ▸ 6    ▸ 7    ▸ 8    ▸ 9                       │
│                                                          │
│  Each child contains 10⁶ nanosecond leaves               │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Navigation Ergonomics

The maximum depth is 14 clicks, but in practice:

- **Year-resolution analysis** (current TEA Space): 0 clicks beyond root
- **Monthly analysis** (previous modification plan): 1 click
- **Daily analysis**: 2 clicks
- **Second-resolution (e.g., battery cycling)**: 5 clicks
- **Millisecond-resolution (e.g., chemical kinetics)**: 8 clicks
- **Nanosecond-resolution (e.g., semiconductor)**: 14 clicks

Most users will operate within 0–5 levels of depth. The sub-second hierarchy is available but not imposed.

### 3.3 Collapsible/Expandable Behavior in the Time Matrix

The `TimeParameterMatrix` component gains a generalized collapse mechanism:

```
Collapsed (Year-level view, default):
   Y1    Y2    Y3    Y4    Y5    ...
  [  ]  [██]  [██]  [▓▓]  [  ]       param1
  [██]  [██]  [  ]  [  ]  [  ]       param2

  Legend: ██ = fully active  ▓▓ = partially active  [  ] = inactive

Expanded Y3 → Months:
   Y1   Y2   │ J  F  M  A  M  J  J  A  S  O  N  D │  Y4   Y5
  [  ] [██]  │ █  █  █  █  █  █  █  █  █  █  █  █ │ [▓▓] [  ]  param1
  [██] [██]  │ ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  · │ [  ] [  ]  param2

Expanded Y3 → Jun → Days:
   ...  │ 1  2  3  4  5  6  7  8  9 10 11 ... 30 │  ...
        │ █  █  █  █  █  █  █  █  ▓  ·  ·  ... ·  │        param1
```

Each expansion replaces a single column with its children. The matrix remains horizontally scrollable. Only one "expansion chain" is active at a time — expanding a new year at the same depth collapses the previous one to prevent exponential column growth.

### 3.4 Partial-Activity Indicator

A collapsed node whose children are only partially active displays a gradient fill proportional to the fraction of active children:

```javascript
const getCoverage = (item, levelIndex, parentOffset) => {
  const childCount = LEVELS[levelIndex + 1]?.fanout || 1;
  const childDuration = getUnitNanoseconds(levelIndex + 1);
  let activeChildren = 0;

  for (let i = 0; i < childCount; i++) {
    const childStart = parentOffset + i * childDuration;
    const childEnd = childStart + childDuration - 1;
    if (item.efficacyPeriods.some(p => p.end >= childStart && p.start <= childEnd)) {
      activeChildren++;
    }
  }

  return activeChildren / childCount;  // 0.0 to 1.0
};
```

This is rendered as:
- `coverage === 1.0` → solid active color
- `0.0 < coverage < 1.0` → gradient fill (`linear-gradient`)
- `coverage === 0.0` → inactive

---

## 4. Data Model

### 4.1 Efficacy Period Structure

```javascript
efficacyPeriod: {
  start: { value: BigInt },       // absolute nanosecond offset from epoch
  end:   { value: BigInt },       // absolute nanosecond offset (inclusive)
  resolution: 'Y' | 'M' | 'D' | 'H' | 'Min' | 'S' | 'ds' | 'cs' | 'ms'
            | 't4' | 't5' | 'μs' | 't7' | 't8' | 'ns'
}
```

The `resolution` field serves two purposes:
1. **UI rendering**: Determines which level of the hierarchy is the finest displayed.
2. **CFA iteration**: Tells the engine at what granularity to iterate (accumulating into coarser output bins as needed).

### 4.2 Conversion Utilities (`src/utils/durationUnits.js`)

```javascript
// Nanoseconds per unit at each hierarchy level
export const NS_PER_UNIT = {
  Y:   BigInt(365.25 * 24 * 3600 * 1e9),  // ~3.156 × 10¹⁶
  M:   BigInt(30.4375 * 24 * 3600 * 1e9),  // ~2.63 × 10¹⁵
  D:   BigInt(24 * 3600) * BigInt(1e9),     // 8.64 × 10¹³
  H:   BigInt(3600) * BigInt(1e9),          // 3.6 × 10¹²
  Min: BigInt(60) * BigInt(1e9),            // 6 × 10¹⁰
  S:   BigInt(1e9),                         // 10⁹
  ds:  BigInt(1e8),
  cs:  BigInt(1e7),
  ms:  BigInt(1e6),
  t4:  BigInt(1e5),
  t5:  BigInt(1e4),
  μs:  BigInt(1e3),
  t7:  BigInt(100),
  t8:  BigInt(10),
  ns:  BigInt(1),
};

// Hierarchical address → absolute ns offset
export function addressToNs(address) {
  // address = { Y: 3, M: 5, D: 15, H: 8, Min: 30, S: 45, ... }
  let offset = BigInt(0);
  for (const [key, val] of Object.entries(address)) {
    offset += BigInt(val) * NS_PER_UNIT[key];
  }
  return offset;
}

// Absolute ns offset → hierarchical address
export function nsToAddress(ns) {
  const address = {};
  let remaining = BigInt(ns);
  const keys = ['Y','M','D','H','Min','S','ds','cs','ms','t4','t5','μs','t7','t8','ns'];
  for (const key of keys) {
    const unitNs = NS_PER_UNIT[key];
    address[key] = Number(remaining / unitNs);
    remaining = remaining % unitNs;
  }
  return address;
}

// Snap an ns offset to the nearest boundary at a given resolution
export function snapToResolution(ns, resolution) {
  const unitNs = NS_PER_UNIT[resolution];
  return (ns / unitNs) * unitNs;  // BigInt floor division
}
```

### 4.3 Backward Compatibility

Legacy year-based efficacy periods migrate losslessly:

```javascript
function migrateLegacyPeriod(old) {
  return {
    start: { value: BigInt(old.start.value - 1) * NS_PER_UNIT.Y },
    end:   { value: BigInt(old.end.value) * NS_PER_UNIT.Y - BigInt(1) },
    resolution: 'Y'
  };
}
```

Year 3 through Year 7 becomes:
- `start`: 2 × 3.156×10¹⁶ = 6.312×10¹⁶ ns
- `end`: 7 × 3.156×10¹⁶ − 1 = 2.209×10¹⁷ ns
- `resolution`: 'Y'

The engine, upon seeing resolution `'Y'`, iterates at year-sized steps, producing identical results to the current system.

### 4.4 Submission Payload

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

Start/end are string-encoded BigInts (JSON has no native 64-bit integer). The backend parses them using Python's arbitrary-precision `int`.

---

## 5. Backend Engine Generalization

### 5.1 Configuration Matrix Invariance

The `generateConfigurationMatrix()` break-point algorithm is **already general**. It operates on `(start, end)` integer pairs and partitions them into non-overlapping segments. Whether those integers represent years, months, or nanoseconds is semantically irrelevant to the algorithm. No modification required.

### 5.2 CFA Iteration Strategy

The engine must support two modes:

**Mode A — Direct Iteration (coarse resolutions: Y, M, D)**

When the resolution is coarse enough that the total number of time steps is manageable (< 10⁶), the engine iterates directly:

```python
for idx, row in config_matrix_df.iterrows():
    start_unit = int(row['start'])
    end_unit = int(row['end'])
    unit_duration_ns = NS_PER_UNIT[resolution]
    num_steps = (end_unit - start_unit) // unit_duration_ns + 1

    for step in range(num_steps):
        t = start_unit + step * unit_duration_ns
        # Calculate revenue, expenses at this time step
        # Accumulate into output bins (yearly CFA matrix)
```

**Mode B — Aggregate Iteration (fine resolutions: S through ns)**

When operating at sub-second resolution, direct iteration over billions of nanoseconds is computationally infeasible. Instead, the engine uses **analytical accumulation**:

```python
def aggregate_cfa(config_row, resolution):
    """
    For a config row spanning [start_ns, end_ns] at the given resolution,
    compute total revenue/expenses analytically rather than iteratively.

    The economics at nanosecond scale are assumed to be:
    - Constant rate within each efficacy period (no compounding within period)
    - Inflation applied at the coarsest natural boundary (year)
    """
    duration_ns = config_row['end'] - config_row['start'] + 1
    duration_years = duration_ns / NS_PER_YEAR  # fractional

    # Revenue = rate × duration
    total_revenue = config_row['unit_rate'] * duration_years

    # Accumulate into the yearly CFA output bin
    year_start = config_row['start'] // NS_PER_YEAR
    year_end = config_row['end'] // NS_PER_YEAR

    for year in range(year_start, year_end + 1):
        overlap_start = max(config_row['start'], year * NS_PER_YEAR)
        overlap_end = min(config_row['end'], (year + 1) * NS_PER_YEAR - 1)
        fraction = (overlap_end - overlap_start + 1) / NS_PER_YEAR
        CFA_matrix[year]['Revenue'] += total_revenue * fraction / duration_years
```

This is the critical architectural choice: **computation is analytical, not iterative, at fine resolutions.** The CFA output matrix remains at yearly resolution for NPV, depreciation, and tax calculations, which are inherently annual.

### 5.3 Resolution-Adaptive Compounding

| Resolution | Compounding Strategy |
|------------|---------------------|
| Y, M       | Standard annual/monthly compounding |
| D through S | Daily/continuous compounding: `e^(r × t)` |
| ds through ns | Flat rate within period (no compounding at sub-second scale) |

The economic rationale: at nanosecond timescales, the time-value-of-money within a single event is negligible. Compounding matters only across events that span different years.

---

## 6. Nested Directory as Filesystem Path

### 6.1 Path Notation

Every time instant has a canonical filesystem path:

```
/Y3/Jun/D15/08h/30m/45s/ds3/cs7/ms2/t4_5/t5_0/μs8/t7_1/t8_4/ns7
```

This path uniquely identifies a single nanosecond within the plant lifetime. The path is human-readable, sortable, and directly maps to the hierarchical address.

### 6.2 Config Module File Naming

Currently: `V_config_module_{start_year}.json`

Generalized: `V_config_module_{start_ns}.json` where `start_ns` is the absolute nanosecond offset (zero-padded to 18 digits for lexicographic sorting):

```
V3_config_module_000063072000000000.json
V3_config_module_000063072000001000.json
```

Alternatively, for human readability at coarse resolutions, the filename can use the path notation:

```
V3_config_module_Y3-Jun-D15-08h-30m-45s.json
```

The system detects the resolution from the path depth and parses accordingly.

### 6.3 Backend Storage Directory Structure

The batch directory structure mirrors the time hierarchy:

```
Original/
└── Batch(3)/
    └── ConfigurationPlotSpec(3)/
        ├── U_configurations(3).py           ← full config (legacy)
        └── modules/
            ├── Y1/                           ← year-level modules
            │   └── config_module.json
            ├── Y3/
            │   ├── config_module.json        ← year-level aggregate
            │   ├── Jun/
            │   │   ├── config_module.json    ← month-level
            │   │   └── D15/
            │   │       └── 08h/
            │   │           └── config_module.json  ← hour-level
            │   └── Jul/
            │       └── config_module.json
            └── Y4/
                └── config_module.json
```

Each directory level only materializes if a parameter's efficacy period operates at that resolution. Year-only scenarios produce the same flat structure as today.

---

## 7. Degree-of-Freedom Constraint at Generalized Resolution

The invariant — **one value per parameter per atomic time unit** — holds at whatever resolution the parameter declares. A parameter at `resolution: 'ms'` is checked for conflicts at millisecond granularity within its efficacy span. A parameter at `resolution: 'Y'` is checked at year granularity. Parameters at different resolutions coexist without conflict because their time units are hierarchically nested:

```
Parameter A:  resolution='Y',  start=Y3, end=Y7
Parameter B:  resolution='ms', start=Y3.Jun.D15.08h.30m.45s.ds3.cs7.ms2,
                                end=Y3.Jun.D15.08h.30m.45s.ds3.cs7.ms5
```

These do not conflict because:
1. Parameter A's value applies uniformly across all nanoseconds within Y3–Y7.
2. Parameter B overrides at ms-level within a 4-millisecond window.
3. The CFA engine resolves conflicts by applying the **finest-resolution value**: within that 4ms window, B's value supersedes A's.

This is the **resolution precedence rule**: finer resolution wins when efficacy periods overlap at different granularities.

---

## 8. Interface: Efficacy.js Generalized Selector

### 8.1 Mode Selection

The selector offers a resolution dropdown at the top:

```
Resolution: [ Year ▼ ]

Options:
  Year        ← current behavior
  Month       ← previous enhancement
  Day
  Hour
  Minute
  Second
  Millisecond
  Microsecond
  Nanosecond
```

Sub-second orders of magnitude (ds, cs, t4, t5, t7, t8) are hidden from the dropdown as they are traversal nodes in the directory, not user-facing selections. The UI jumps from Second → Millisecond → Microsecond → Nanosecond (3 orders of magnitude each), but internally the full 15-level hierarchy is preserved for navigation.

### 8.2 Start/End Selection via Directory Navigation

When a fine resolution is selected, the dual-slider is replaced by the nested directory navigator:

```
┌─────────────────────────────────────────────────────┐
│  Resolution: Millisecond                            │
│                                                     │
│  START: / Y3 / Jun / D15 / 08h / 30m / 45s / ms2   │
│  END:   / Y3 / Jun / D15 / 08h / 30m / 45s / ms5   │
│                                                     │
│  Duration: 4 milliseconds                           │
│  Absolute span: 4,000,000 ns                        │
│                                                     │
│  [Navigator Panel]                                  │
│  Setting: START  ←→  END                            │
│  / Y3 / Jun / D15 / 08h / 30m / 45s /              │
│                                                     │
│  ms0  ms1  [ms2]  ms3  ms4  [ms5]  ms6  ms7 ...    │
│                    ▲start          ▲end              │
└─────────────────────────────────────────────────────┘
```

The user toggles between setting START and END, then clicks through the directory tree to the desired depth. Each click drills one level deeper. The breadcrumb allows instant navigation back to any ancestor.

---

## 9. File Modification Registry

| File | Change | Effort |
|------|--------|--------|
| `src/utils/durationUnits.js` | **New** — BigInt conversion utilities, NS_PER_UNIT table, address⟷ns functions | Medium |
| `src/components/modules/Efficacy.js` | Replace slider with resolution dropdown + directory navigator | High |
| `src/components/modules/TimeParameterMatrix.js` | Generalized collapsible columns, partial-fill at any level | High |
| `src/components/modules/DirectoryNavigator.js` | **New** — reusable nested directory navigation component | High |
| `src/Consolidated2.js` | EfficacyPeriod data model → BigInt start/end + resolution | Medium |
| `src/services/MatrixSubmissionService.js` | String-encoded BigInt payload + resolution field | Low |
| `src/services/CapacityTrackingService.js` | Resolution-aware conflict detection | Medium |
| `backend/Configuration_management/formatter-updated.py` | BigInt parsing, resolution-aware module naming | Medium |
| `backend/Core_calculation_engines/Old_Script.py` | Dual-mode iteration (direct vs. analytical accumulation) | High |
| `backend/Core_calculation_engines/consolidated_cfa_new.py` | Same as above | High |
| Config module storage | Hierarchical directory structure | Medium |

---

## 10. Implementation Phases

```
Phase 1: Duration Primitives
  ├── Create src/utils/durationUnits.js (BigInt utilities)
  ├── Define NS_PER_UNIT lookup table
  ├── Implement address ⟷ ns offset conversions
  └── Write unit tests for round-trip fidelity

Phase 2: Data Model Migration
  ├── Update efficacyPeriod schema (BigInt + resolution)
  ├── Write migration function for legacy year-based data
  └── Update MatrixSubmissionService payload format

Phase 3: Backend Engine Generalization
  ├── Add resolution detection to formatter
  ├── Implement Mode A (direct iteration) for Y through D
  ├── Implement Mode B (analytical accumulation) for H through ns
  ├── Validate: year-resolution scenarios produce identical results
  └── Implement hierarchical config module storage

Phase 4: Directory Navigator Component
  ├── Build DirectoryNavigator.js (reusable)
  ├── Implement breadcrumb navigation
  ├── Implement range selection (start/end)
  └── Unit test: navigation, selection, path encoding

Phase 5: Efficacy Selector Integration
  ├── Add resolution dropdown to Efficacy.js
  ├── Integrate DirectoryNavigator for fine resolutions
  ├── Keep slider mode for Year/Month (backward compatible)
  └── Wire up BigInt efficacy period to form state

Phase 6: Time Parameter Matrix Generalization
  ├── Generalize collapsible columns for any level
  ├── Implement partial-activity indicators at all levels
  ├── Add resolution precedence in conflict detection
  └── Performance: virtualize columns when >60 visible

Phase 7: Integration Testing
  ├── Year-only scenario regression (must match current output exactly)
  ├── Monthly scenario (validate against previous plan)
  ├── Sub-second scenario (synthetic test: ms-level efficacy periods)
  ├── Cross-resolution scenario (year + ms parameters coexisting)
  └── Edge cases: epoch boundaries, month-length variation, leap years
```

---

## 11. Computational Complexity Guarantees

| Operation | Complexity | Bound |
|-----------|-----------|-------|
| Navigation (drill down one level) | O(fanout) | ≤ 60 |
| Range selection at any level | O(1) | Two clicks |
| Conflict detection for one parameter | O(N × R) | N = periods, R = units at resolution |
| CFA Mode A (direct iteration, Y–D) | O(P × T) | P = periods, T = time steps (≤ 10⁶) |
| CFA Mode B (analytical, H–ns) | O(P × Y) | P = periods, Y = years spanned |
| Address → ns conversion | O(15) | Fixed |
| ns → address reconstruction | O(15) | Fixed |

The system never iterates over the full nanosecond address space. Mode B ensures sub-second calculations remain O(P × Y), independent of the resolution depth.

---

## 12. Summary

The generalization rests on three structural pillars:

1. **The break-point algorithm is unit-agnostic.** It partitions integer ranges regardless of their physical meaning. Switching from year-integers to nanosecond-integers requires zero algorithmic change.

2. **The nested directory caps cognitive load at 60.** The maximum fanout at any hierarchy level is 60 (Minute→Second). The user never confronts the 6.31×10¹⁷ leaf space directly — only the current level's children, always ≤ 60 items.

3. **Analytical accumulation makes sub-second CFA tractable.** Rather than iterating 10⁹ nanoseconds per second, the engine computes revenue/expense rates analytically and distributes them across yearly output bins. The CFA matrix remains annual for NPV, depreciation, and tax calculations.

The result is a system where a battery-cycling engineer can define a 200-microsecond efficacy window for a catalyst degradation parameter, a process economist can define a 20-year capital depreciation schedule, and both coexist in the same configuration matrix — resolved by the same engine, navigated through the same interface.
