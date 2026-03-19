/**
 * durationUnits.js
 *
 * Pure utility functions for the 15-level Year→Nanosecond hierarchy.
 * Extracted from src/generalized_duration_visualization.html.
 *
 * All functions that previously read the module-level MODEL object now
 * accept a context: { yearCount, baseYear, plantEpoch }.
 * Create one with makeDurationContext(yearCount, baseYear).
 */

export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export const SUB_NS = {
  ds: 100000000n,
  cs: 10000000n,
  ms: 1000000n,
  t4: 100000n,
  t5: 10000n,
  us: 1000n,
  t7: 100n,
  t8: 10n,
  ns: 1n,
};

export const LEVELS = [
  { key: 'Y',   title: 'Year',         symbol: 'Y',   nextTitle: 'Months'        },
  { key: 'M',   title: 'Month',        symbol: 'M',   nextTitle: 'Days'          },
  { key: 'D',   title: 'Day',          symbol: 'D',   nextTitle: 'Hours'         },
  { key: 'H',   title: 'Hour',         symbol: 'H',   nextTitle: 'Minutes'       },
  { key: 'Min', title: 'Minute',       symbol: 'Min', nextTitle: 'Seconds'       },
  { key: 'S',   title: 'Second',       symbol: 'S',   nextTitle: 'Deciseconds'   },
  { key: 'ds',  title: 'Decisecond',   symbol: 'ds',  nextTitle: 'Centiseconds'  },
  { key: 'cs',  title: 'Centisecond',  symbol: 'cs',  nextTitle: 'Milliseconds'  },
  { key: 'ms',  title: 'Millisecond',  symbol: 'ms',  nextTitle: '10⁻⁴ seconds'  },
  { key: 't4',  title: '10⁻⁴ second',  symbol: 't4',  nextTitle: '10⁻⁵ seconds'  },
  { key: 't5',  title: '10⁻⁵ second',  symbol: 't5',  nextTitle: 'Microseconds'  },
  { key: 'us',  title: 'Microsecond',  symbol: 'μs',  nextTitle: '10⁻⁷ seconds'  },
  { key: 't7',  title: '10⁻⁷ second',  symbol: 't7',  nextTitle: '10⁻⁸ seconds'  },
  { key: 't8',  title: '10⁻⁸ second',  symbol: 't8',  nextTitle: 'Nanoseconds'   },
  { key: 'ns',  title: 'Nanosecond',   symbol: 'ns',  nextTitle: 'Leaf'          },
];

export const LEVEL_INDEX = Object.fromEntries(LEVELS.map((level, i) => [level.key, i]));

// ── Context factory ───────────────────────────────────────────────────────────

export function makePlantEpoch(baseYear) {
  return BigInt(Date.UTC(baseYear, 0, 1, 0, 0, 0, 0)) * 1_000_000n;
}

export function makeDurationContext(yearCount = 8, baseYear = 2026) {
  return { yearCount, baseYear, plantEpoch: makePlantEpoch(baseYear) };
}

// ── Path primitives (context-free) ───────────────────────────────────────────

export function pathEntry(key, value) {
  return { key, value };
}

export function clonePath(path) {
  return path.map(entry => ({ ...entry }));
}

export function pathToObject(path) {
  return path.reduce((acc, part) => { acc[part.key] = part.value; return acc; }, {});
}

export function formatLevelValue(key, value) {
  switch (key) {
    case 'Y':   return `Y${value}`;
    case 'M':   return MONTHS[value - 1];
    case 'D':   return `D${String(value).padStart(2, '0')}`;
    case 'H':   return `${String(value).padStart(2, '0')}h`;
    case 'Min': return `${String(value).padStart(2, '0')}m`;
    case 'S':   return `${String(value).padStart(2, '0')}s`;
    case 'us':  return `μs${value}`;
    case 't4':  return `t4_${value}`;
    case 't5':  return `t5_${value}`;
    case 't7':  return `t7_${value}`;
    case 't8':  return `t8_${value}`;
    default:    return `${key}${value}`;
  }
}

export function levelSymbol(key) {
  return LEVELS[LEVEL_INDEX[key]].symbol;
}

export function pathToString(path) {
  if (!path.length) return '/';
  return `/ ${path.map(part => formatLevelValue(part.key, part.value)).join(' / ')}`;
}

export function pathTokenString(path) {
  return path.map(part => formatLevelValue(part.key, part.value)).join('/');
}

export function pathKey(path) {
  return path.map(part => `${part.key}:${part.value}`).join('|');
}

export function pathsEqual(a, b) {
  if (a.length !== b.length) return false;
  return a.every((part, i) => part.key === b[i].key && part.value === b[i].value);
}

export function isPrefix(prefix, full) {
  if (prefix.length > full.length) return false;
  return prefix.every((part, i) => part.key === full[i].key && part.value === full[i].value);
}

// ── Numeric / display utilities (context-free) ────────────────────────────────

export function formatInt(n) {
  return new Intl.NumberFormat('en-US').format(Number(n));
}

export function formatPercent(value) {
  return `${(value * 100).toFixed(value === 1 || value === 0 ? 0 : value > 0.1 ? 1 : 2)}%`;
}

export function nsToDisplay(ns) {
  const abs  = ns < 0n ? -ns : ns;
  const sign = ns < 0n ? '-' : '';
  const units = [
    { label: 'y',  value: 31536000000000000n },
    { label: 'd',  value:    86400000000000n },
    { label: 'h',  value:     3600000000000n },
    { label: 'm',  value:       60000000000n },
    { label: 's',  value:        1000000000n },
    { label: 'ms', value:           1000000n },
    { label: 'μs', value:              1000n },
    { label: 'ns', value:                1n },
  ];
  for (const unit of units) {
    if (abs >= unit.value) {
      const scaled = Number((abs * 100n) / unit.value) / 100;
      return `${sign}${scaled.toLocaleString('en-US')} ${unit.label}`;
    }
  }
  return `${sign}${abs.toString()} ns`;
}

export function overlapLength(aStart, aEnd, bStart, bEnd) {
  const start = aStart > bStart ? aStart : bStart;
  const end   = aEnd   < bEnd   ? aEnd   : bEnd;
  return end >= start ? end - start + 1n : 0n;
}

export function unionLength(intervals) {
  if (!intervals.length) return 0n;
  const sorted = [...intervals].sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
  let total = 0n;
  let currentStart = sorted[0].start;
  let currentEnd   = sorted[0].end;
  for (let i = 1; i < sorted.length; i++) {
    const iv = sorted[i];
    if (iv.start <= currentEnd + 1n) {
      if (iv.end > currentEnd) currentEnd = iv.end;
    } else {
      total += currentEnd - currentStart + 1n;
      currentStart = iv.start;
      currentEnd   = iv.end;
    }
  }
  total += currentEnd - currentStart + 1n;
  return total;
}

// ── Context-dependent time utilities ─────────────────────────────────────────

export function getDaysInMonth(path, ctx) {
  const parts = pathToObject(path);
  const year  = ctx.baseYear + ((parts.Y || 1) - 1);
  const mIdx  = (parts.M || 1) - 1;
  return new Date(Date.UTC(year, mIdx + 1, 0)).getUTCDate();
}

export function calendarStartDate(parts, ctx) {
  const year   = ctx.baseYear + ((parts.Y || 1) - 1);
  const month  = (parts.M || 1) - 1;
  const day    = parts.D   || 1;
  const hour   = parts.H   || 0;
  const minute = parts.Min || 0;
  const second = parts.S   || 0;
  return new Date(Date.UTC(year, month, day, hour, minute, second, 0));
}

export function pathToStartNs(path, ctx) {
  if (!path.length) return 0n;
  const parts = pathToObject(path);
  const date  = calendarStartDate(parts, ctx);
  let ns = BigInt(date.getTime()) * 1_000_000n;
  ns += BigInt(parts.ds || 0) * SUB_NS.ds;
  ns += BigInt(parts.cs || 0) * SUB_NS.cs;
  ns += BigInt(parts.ms || 0) * SUB_NS.ms;
  ns += BigInt(parts.t4 || 0) * SUB_NS.t4;
  ns += BigInt(parts.t5 || 0) * SUB_NS.t5;
  ns += BigInt(parts.us || 0) * SUB_NS.us;
  ns += BigInt(parts.t7 || 0) * SUB_NS.t7;
  ns += BigInt(parts.t8 || 0) * SUB_NS.t8;
  ns += BigInt(parts.ns || 0) * SUB_NS.ns;
  return ns - ctx.plantEpoch;
}

export function nextStartNs(path, ctx) {
  if (!path.length) {
    const date = new Date(Date.UTC(ctx.baseYear + ctx.yearCount, 0, 1, 0, 0, 0, 0));
    return BigInt(date.getTime()) * 1_000_000n - ctx.plantEpoch;
  }
  const parts = pathToObject(path);
  const key   = path[path.length - 1].key;
  if (['Y', 'M', 'D', 'H', 'Min', 'S'].includes(key)) {
    const date = calendarStartDate(parts, ctx);
    if (key === 'Y')   date.setUTCFullYear(date.getUTCFullYear() + 1);
    if (key === 'M')   date.setUTCMonth(date.getUTCMonth() + 1);
    if (key === 'D')   date.setUTCDate(date.getUTCDate() + 1);
    if (key === 'H')   date.setUTCHours(date.getUTCHours() + 1);
    if (key === 'Min') date.setUTCMinutes(date.getUTCMinutes() + 1);
    if (key === 'S')   date.setUTCSeconds(date.getUTCSeconds() + 1);
    return BigInt(date.getTime()) * 1_000_000n - ctx.plantEpoch;
  }
  return pathToStartNs(path, ctx) + SUB_NS[key];
}

export function pathRange(path, ctx) {
  return {
    start: pathToStartNs(path, ctx),
    end:   nextStartNs(path, ctx) - 1n,
  };
}

export function getChildren(path, ctx) {
  const level = path.length;
  if (level >= LEVELS.length) return [];
  const key = LEVELS[level].key;
  let values = [];
  if (key === 'Y')                     for (let i = 1; i <= ctx.yearCount; i++) values.push(i);
  else if (key === 'M')                for (let i = 1; i <= 12; i++) values.push(i);
  else if (key === 'D')                for (let i = 1; i <= getDaysInMonth(path, ctx); i++) values.push(i);
  else if (key === 'H')                for (let i = 0; i < 24; i++) values.push(i);
  else if (key === 'Min' || key === 'S') for (let i = 0; i < 60; i++) values.push(i);
  else                                 for (let i = 0; i < 10; i++) values.push(i);

  return values.map(value => {
    const childPath = [...clonePath(path), pathEntry(key, value)];
    return {
      key,
      value,
      path: childPath,
      label: formatLevelValue(key, value),
      title: LEVELS[level].title,
      nextTitle: LEVELS[level].nextTitle,
      hasChildren: childPath.length < LEVELS.length,
      depth: childPath.length,
    };
  });
}

export function buildVisibleColumns(path, expansionPath, ctx) {
  const children = getChildren(path, ctx);
  if (!children.length) return [];
  const columns = [];
  for (const child of children) {
    if (isPrefix(child.path, expansionPath) && child.path.length <= LEVELS.length - 1) {
      const deeper = getChildren(child.path, ctx);
      if (deeper.length) {
        columns.push(...buildVisibleColumns(child.path, expansionPath, ctx));
        continue;
      }
    }
    columns.push(child);
  }
  return columns;
}

export function validatePath(path, ctx) {
  const parts = pathToObject(path);
  if (parts.Y && (parts.Y < 1 || parts.Y > ctx.yearCount)) throw new Error(`Year must be between 1 and ${ctx.yearCount}`);
  if (parts.M && (parts.M < 1 || parts.M > 12))             throw new Error('Month must be between 1 and 12');
  if (parts.D) {
    const maxDays = getDaysInMonth(path.filter(p => ['Y','M'].includes(p.key)), ctx);
    if (parts.D < 1 || parts.D > maxDays) throw new Error(`Day must be between 1 and ${maxDays}`);
  }
  if (parts.H   !== undefined && (parts.H   < 0 || parts.H   > 23)) throw new Error('Hour must be between 0 and 23');
  if (parts.Min !== undefined && (parts.Min < 0 || parts.Min > 59)) throw new Error('Minute must be between 0 and 59');
  if (parts.S   !== undefined && (parts.S   < 0 || parts.S   > 59)) throw new Error('Second must be between 0 and 59');
  ['ds','cs','ms','t4','t5','us','t7','t8','ns'].forEach(key => {
    if (parts[key] !== undefined && (parts[key] < 0 || parts[key] > 9))
      throw new Error(`${key} must be between 0 and 9`);
  });
}

export function parsePathString(input, ctx) {
  const raw    = input.trim();
  if (!raw) return [];
  const tokens = raw.split('/').map(t => t.trim()).filter(Boolean);
  const result = [];
  let expectedIndex = 0;
  for (const token of tokens) {
    let match = null;
    let entry = null;
    if      ((match = token.match(/^Y(\d+)$/i)))                           entry = pathEntry('Y',   Number(match[1]));
    else if ((match = token.match(/^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)$/i)))
                                                                            entry = pathEntry('M',   MONTHS.findIndex(m => m.toLowerCase() === match[1].toLowerCase()) + 1);
    else if ((match = token.match(/^D(\d+)$/i)))                           entry = pathEntry('D',   Number(match[1]));
    else if ((match = token.match(/^(\d{1,2})h$/i)))                       entry = pathEntry('H',   Number(match[1]));
    else if ((match = token.match(/^(\d{1,2})m$/i)))                       entry = pathEntry('Min', Number(match[1]));
    else if ((match = token.match(/^(\d{1,2})s$/i)))                       entry = pathEntry('S',   Number(match[1]));
    else if ((match = token.match(/^ds(\d)$/i)))                           entry = pathEntry('ds',  Number(match[1]));
    else if ((match = token.match(/^cs(\d)$/i)))                           entry = pathEntry('cs',  Number(match[1]));
    else if ((match = token.match(/^ms(\d)$/i)))                           entry = pathEntry('ms',  Number(match[1]));
    else if ((match = token.match(/^t4[_-]?(\d)$/i)))                      entry = pathEntry('t4',  Number(match[1]));
    else if ((match = token.match(/^t5[_-]?(\d)$/i)))                      entry = pathEntry('t5',  Number(match[1]));
    else if ((match = token.match(/^(?:μs|us|µs)(\d)$/i)))                 entry = pathEntry('us',  Number(match[1]));
    else if ((match = token.match(/^t7[_-]?(\d)$/i)))                      entry = pathEntry('t7',  Number(match[1]));
    else if ((match = token.match(/^t8[_-]?(\d)$/i)))                      entry = pathEntry('t8',  Number(match[1]));
    else if ((match = token.match(/^ns(\d)$/i)))                           entry = pathEntry('ns',  Number(match[1]));
    if (!entry) throw new Error(`Unrecognized token: ${token}`);
    const entryIndex = LEVEL_INDEX[entry.key];
    if (entryIndex !== expectedIndex) {
      const missing = LEVELS.slice(expectedIndex, entryIndex).map(l => l.key);
      const onlySubSec  = missing.every(k => ['ds','cs','ms','t4','t5','us','t7','t8','ns'].includes(k));
      const inSubSec    = expectedIndex >= LEVEL_INDEX.ds;
      const jumpToSub   = expectedIndex === LEVEL_INDEX.ds && entryIndex >= LEVEL_INDEX.ds;
      if (!(entryIndex > expectedIndex && onlySubSec && (inSubSec || jumpToSub))) {
        throw new Error(`Expected ${LEVELS[expectedIndex].title} after ${
          result.length ? formatLevelValue(result[result.length-1].key, result[result.length-1].value) : 'root'
        }, got ${token}`);
      }
      missing.forEach(k => result.push(pathEntry(k, 0)));
      expectedIndex = entryIndex;
    }
    result.push(entry);
    expectedIndex = entryIndex + 1;
  }
  validatePath(result, ctx);
  return result;
}

export function makePeriod(startPathStr, endPathStr, resolution, label, detail, value, ctx) {
  const startPath  = parsePathString(startPathStr, ctx);
  const endPath    = parsePathString(endPathStr,   ctx);
  const startRange = pathRange(startPath, ctx);
  const endRange   = pathRange(endPath,   ctx);
  return { startPath, endPath, start: startRange.start, end: endRange.end, resolution, label, detail, value };
}

export function computeCell(row, column, ctx) {
  const range    = pathRange(column.path, ctx);
  const overlaps = row.periods
    .map(period => {
      const overlap = overlapLength(range.start, range.end, period.start, period.end);
      if (overlap <= 0n) return null;
      return {
        ...period,
        overlap,
        overlapStart: range.start > period.start ? range.start : period.start,
        overlapEnd:   range.end   < period.end   ? range.end   : period.end,
      };
    })
    .filter(Boolean)
    .sort((a, b) => LEVEL_INDEX[b.resolution] - LEVEL_INDEX[a.resolution]);

  const covered  = unionLength(overlaps.map(o => ({ start: o.overlapStart, end: o.overlapEnd })));
  const total    = range.end - range.start + 1n;
  const coverage = total > 0n ? Number((covered * 10000n) / total) / 10000 : 0;
  const dominant = overlaps[0] || null;

  return {
    row, column, range, overlaps, covered, total, coverage, dominant,
    display: coverage === 0 ? '—' : coverage === 1 ? 'Full' : formatPercent(coverage),
    badge:   dominant ? levelSymbol(dominant.resolution) : '·',
  };
}

// ── Legacy bridge ─────────────────────────────────────────────────────────────
// Converts an app efficacyPeriod { start:{value}, end:{value}, resolution? }
// to the visualization period format.

export function legacyPeriodToVisualization(old, paramLabel, paramUnit, ctx) {
  const resolution  = old.resolution ?? 'Y';
  const startYear   = old.start?.value ?? 1;
  const endYear     = old.end?.value   ?? ctx.yearCount;
  const startPath   = [pathEntry('Y', startYear)];
  const endPath     = [pathEntry('Y', endYear)];
  const startRange  = pathRange(startPath, ctx);
  const endRange    = pathRange(endPath,   ctx);
  return {
    startPath,
    endPath,
    start:      startRange.start,
    end:        endRange.end,
    resolution,
    label:      paramLabel,
    detail:     paramUnit ?? '',
    value:      old.scaledValue ?? old.baseValue ?? old.value ?? 0,
  };
}

// ── Demo data (used when no formValues provided) ──────────────────────────────

export function seedDemoRows(ctx) {
  const mp = (s, e, r, l, d, v) => makePeriod(s, e, r, l, d, v, ctx);
  return [
    {
      id: 'capex', name: 'Capital Depreciation', unit: '$ / year',
      description: 'Annual baseline schedule with a mid-horizon monthly refinement.',
      periods: [
        mp('Y1', 'Y4', 'Y', 'Base annual depreciation', 'Legacy year-scale schedule migrated losslessly.', '$42.0M'),
        mp('Y6/Jul', 'Y7/Mar', 'M', 'Refit depreciation segment', 'Monthly override for a retrofit interval.', '$9.6M'),
      ],
    },
    {
      id: 'battery', name: 'Battery Cycling Rate', unit: 'cycles / hour',
      description: 'Daily and hourly pulses inside a broader operational envelope.',
      periods: [
        mp('Y2/Mar/D10/12h', 'Y2/Mar/D10/14h', 'H', 'Cycle surge window', 'High-load cycling span.', '1.35×'),
        mp('Y2/Mar/D11', 'Y2/Mar/D13', 'D', 'Recovery block', 'Three-day recovery after the surge.', '0.82×'),
      ],
    },
    {
      id: 'catalyst', name: 'Catalyst Activation Window', unit: 'kg / pulse',
      description: 'Millisecond-scale efficacy nested within second-level operations.',
      periods: [
        mp('Y3/Jun/D15/08h/30m/45s/ms2', 'Y3/Jun/D15/08h/30m/45s/ms5', 'ms', 'Catalyst micro-burst', 'Millisecond activation block.', '0.0034'),
        mp('Y3/Jun/D15/08h/30m/45s', 'Y3/Jun/D15/08h/30m/47s', 'S', 'Carrier gas hold', 'Second-level envelope.', 'support'),
      ],
    },
    {
      id: 'pv', name: 'Photovoltaic Transient', unit: 'A / event',
      description: 'Microsecond transients embedded in a specific second.',
      periods: [
        mp('Y4/Aug/D04/11h/07m/12s/ds0/cs0/ms0/t4_0/t5_0/us2', 'Y4/Aug/D04/11h/07m/12s/ds0/cs0/ms0/t4_0/t5_0/us8', 'us', 'Inverter transient', 'Microsecond response slice.', '17.8 A'),
        mp('Y4/Aug/D04/11h/07m/12s', 'Y4/Aug/D04/11h/07m/14s', 'S', 'Second-level irradiance spike', 'Coarser signal frame.', 'spike'),
      ],
    },
    {
      id: 'maintenance', name: 'Maintenance Pulse', unit: 'availability',
      description: 'Monthly and minute windows that demonstrate partial coverage.',
      periods: [
        mp('Y6/Nov', 'Y6/Dec', 'M', 'Late-stage maintenance block', 'Month-scale planning window.', 'planned'),
        mp('Y6/Nov/D16/09h/20m', 'Y6/Nov/D16/09h/50m', 'Min', 'Service interruption', 'Minute-level outage.', 'downtime'),
      ],
    },
    {
      id: 'reaction', name: 'Reaction Rate Coefficient', unit: '1 / s',
      description: 'A mixed-resolution chain spanning year, day, and second levels.',
      periods: [
        mp('Y3', 'Y5', 'Y', 'Macro reaction program', 'Broad process program.', 'base'),
        mp('Y4/Apr/D21', 'Y4/Apr/D24', 'D', 'Batch calibration', 'Daily batch calibration.', 'calibration'),
        mp('Y4/Apr/D22/16h/10m/05s', 'Y4/Apr/D22/16h/10m/18s', 'S', 'High-frequency run', 'Second-scale execution.', 'run'),
      ],
    },
  ];
}
