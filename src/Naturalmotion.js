// Naturalmotion.js — 15-Level Hierarchy Shelf Visualizer
// TEA-Space Generalized Duration-Atomic Time Model
//
// "Natural motion" pattern (per Naturalmotion.md):
//   Each tile is an independent glassmorphic card. On hover it rotates around
//   its Y-axis (rotateY) — exactly as the original SpatialTransformComponent did
//   at 60 deg — giving the sensation of pulling a book off a shelf.
//   The "tilted shelf" emerges from the *individual* card tilt on hover, not from
//   a parent-level rotateX that distorts hit-test areas and breaks navigation.

import React, { useState, useCallback, useEffect } from 'react';
import UnifiedTooltip from './unified-tooltip';
import './styles/HomePage.CSS/Consolidated.css';

/* ── 15-Level Hierarchy ──────────────────────────────────────────────────────── */
const LEVELS = [
  { depth:  0, name: 'Year',         symbol: 'Y',   fanout: 20,  duration: '3.156×10⁷ s', group: 'calendar'  },
  { depth:  1, name: 'Month',        symbol: 'M',   fanout: 12,  duration: '2.628×10⁶ s', group: 'calendar'  },
  { depth:  2, name: 'Day',          symbol: 'D',   fanout: 31,  duration: '8.640×10⁴ s', group: 'calendar'  },
  { depth:  3, name: 'Hour',         symbol: 'H',   fanout: 24,  duration: '3.600×10³ s', group: 'calendar'  },
  { depth:  4, name: 'Minute',       symbol: 'Min', fanout: 60,  duration: '60 s',         group: 'calendar'  },
  { depth:  5, name: 'Second',       symbol: 'S',   fanout: 60,  duration: '1 s',          group: 'second'    },
  { depth:  6, name: 'Decisecond',   symbol: 'ds',  fanout: 10,  duration: '10⁻¹ s',      group: 'subsecond' },
  { depth:  7, name: 'Centisecond',  symbol: 'cs',  fanout: 10,  duration: '10⁻² s',      group: 'subsecond' },
  { depth:  8, name: 'Millisecond',  symbol: 'ms',  fanout: 10,  duration: '10⁻³ s',      group: 'subsecond' },
  { depth:  9, name: '10⁻⁴ Second',  symbol: 't4',  fanout: 10,  duration: '10⁻⁴ s',      group: 'ultrafine' },
  { depth: 10, name: '10⁻⁵ Second',  symbol: 't5',  fanout: 10,  duration: '10⁻⁵ s',      group: 'ultrafine' },
  { depth: 11, name: 'Microsecond',  symbol: 'μs',  fanout: 10,  duration: '10⁻⁶ s',      group: 'ultrafine' },
  { depth: 12, name: '10⁻⁷ Second',  symbol: 't7',  fanout: 10,  duration: '10⁻⁷ s',      group: 'ultrafine' },
  { depth: 13, name: '10⁻⁸ Second',  symbol: 't8',  fanout: 10,  duration: '10⁻⁸ s',      group: 'ultrafine' },
  { depth: 14, name: 'Nanosecond',   symbol: 'ns',  fanout: 10,  duration: '10⁻⁹ s',      group: 'ultrafine' },
];

const PALETTE = {
  calendar:  ['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e', '#06b6d4'],
  second:    ['#0ea5e9'],
  subsecond: ['#3b82f6', '#6366f1', '#8b5cf6'],
  ultrafine: ['#a855f7', '#d946ef', '#ec4899', '#f43f5e', '#fb923c', '#fbbf24'],
};

const getLevelColor = (level) => {
  const pal = PALETTE[level.group] || ['#94a3b8'];
  const idx = LEVELS.filter(l => l.group === level.group).findIndex(l => l.depth === level.depth);
  return pal[idx % pal.length];
};

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const posLabel = (depth, pos) => {
  if (depth === 0) return `Y${pos + 1}`;
  if (depth === 1) return MONTHS[pos] ?? `M${pos + 1}`;
  if (depth === 2) return `D${pos + 1}`;
  if (depth === 3) return `${String(pos).padStart(2,'0')}h`;
  if (depth === 4) return `${String(pos).padStart(2,'0')}m`;
  if (depth === 5) return `${String(pos).padStart(2,'0')}s`;
  return `${LEVELS[depth].symbol}${pos}`;
};

const GROUP_LABELS = {
  calendar:  'Calendar',
  second:    'Second',
  subsecond: 'Sub-Second',
  ultrafine: 'Ultra-Fine',
};

// Group boundary depths — a divider is rendered before these
const GROUP_STARTS = new Set([0, 5, 6, 9]);

/* ── Main Component ──────────────────────────────────────────────────────────── */
const HierarchyShelfComponent = () => {
  const [positions,    setPositions]   = useState(Array(15).fill(0));
  const [values,       setValues]      = useState(Array(15).fill('1.0000'));
  const [activeTile,   setActiveTile]  = useState(null);
  const [editingTile,  setEditingTile] = useState(null);
  const [draft,        setDraft]       = useState('');
  // Per-tile hover state — drives the individual rotateY (natural motion)
  const [hoveredTile,  setHoveredTile] = useState(null);

  useEffect(() => {
    const id = 'hs-injected-styles';
    if (!document.getElementById(id)) {
      const el = document.createElement('style');
      el.id = id;
      el.textContent = SHELF_CSS;
      document.head.appendChild(el);
    }
    return () => { const el = document.getElementById(id); if (el) el.remove(); };
  }, []);

  const navigate = useCallback((depth, dir) => {
    setPositions(prev => {
      const next = [...prev];
      const max  = LEVELS[depth].fanout - 1;
      next[depth] = Math.max(0, Math.min(max, next[depth] + dir));
      return next;
    });
  }, []);

  const startEdit = useCallback((depth, e) => {
    e.stopPropagation();
    setEditingTile(depth);
    setDraft(values[depth]);
  }, [values]);

  const commitEdit = useCallback((depth) => {
    setValues(prev => { const n = [...prev]; n[depth] = draft.trim() || prev[depth]; return n; });
    setEditingTile(null);
  }, [draft]);

  const cancelEdit = useCallback(() => setEditingTile(null), []);

  const bcEnd      = activeTile !== null ? activeTile : 14;
  const breadcrumb = positions.slice(0, bcEnd + 1).map((p, d) => posLabel(d, p)).join(' › ');

  return (
    <div className="hs-root">

      {/* Breadcrumb header */}
      <div className="hs-header">
        <span className="hs-header-label">TEA-Space · Hierarchy Path</span>
        <div className="hs-breadcrumb">
          <span className="hs-bc-icon">⏱</span>
          <span className="hs-bc-text">{breadcrumb}</span>
        </div>
      </div>

      {/* Shelf — perspective set here so each child's rotateY has 3-D depth */}
      <div className="hs-scene">
        <div className="hs-stack">
          {LEVELS.map((level, i) => {
            const color   = getLevelColor(level);
            const pos     = positions[i];
            const val     = values[i];
            const isAct   = activeTile === i;
            const isEdit  = editingTile === i;
            const isHover = hoveredTile === i;

            // rotateY angle: follows the Naturalmotion.md model
            //   hover  → tilt toward viewer (−14 deg, left-anchored = "pull book off shelf")
            //   active → partially pulled out (−6 deg)
            //   rest   → flat (0 deg)
            const rotY = isAct ? -6 : isHover ? -14 : 0;
            const tzVal = isAct ? 8 : isHover ? 12 : 0;

            const tooltipData = {
              level,
              color,
              position:      pos,
              positionLabel: posLabel(i, pos),
              value:         val,
              breadcrumb:    positions.slice(0, i + 1).map((p, d) => posLabel(d, p)).join(' › '),
              groupLabel:    GROUP_LABELS[level.group] || level.group,
            };

            return (
              <React.Fragment key={i}>
                {/* Group divider before each section */}
                {GROUP_STARTS.has(i) && (
                  <div className={`hs-group-divider hs-group-${level.group}`}>
                    <span className="hs-group-label">{GROUP_LABELS[level.group]}</span>
                  </div>
                )}

                <UnifiedTooltip
                  type="hierarchyLevel"
                  data={tooltipData}
                  position="right"
                  width={272}
                  showDelay={350}
                  hideDelay={120}
                >
                  <div
                    className={`hs-tile hs-tile-${level.group}${isAct ? ' hs-tile-active' : ''}`}
                    style={{
                      '--tc': color,
                      transform: `rotateY(${rotY}deg) translateZ(${tzVal}px)`,
                    }}
                    onMouseEnter={() => setHoveredTile(i)}
                    onMouseLeave={() => setHoveredTile(h => h === i ? null : h)}
                    onClick={() => setActiveTile(isAct ? null : i)}
                    role="button"
                    aria-expanded={isAct}
                    tabIndex={0}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') setActiveTile(isAct ? null : i); }}
                  >
                    {/* Left: depth badge + symbol + name */}
                    <div className="hs-tile-left">
                      <span className="hs-depth-badge" style={{ background: color }}>{i}</span>
                      <span className="hs-symbol" style={{ color }}>{level.symbol}</span>
                      <span className="hs-name">{level.name}</span>
                    </div>

                    {/* Center: ◀ position ▶ */}
                    <div className="hs-tile-center">
                      <button
                        className="hs-nav-btn"
                        onClick={e => { e.stopPropagation(); navigate(i, -1); }}
                        disabled={pos === 0}
                        aria-label={`Previous ${level.name}`}
                      >◀</button>
                      <span className="hs-pos-label" style={{ color }}>{posLabel(i, pos)}</span>
                      <button
                        className="hs-nav-btn"
                        onClick={e => { e.stopPropagation(); navigate(i, +1); }}
                        disabled={pos === level.fanout - 1}
                        aria-label={`Next ${level.name}`}
                      >▶</button>
                    </div>

                    {/* Right: value cell + fanout */}
                    <div className="hs-tile-right">
                      {isEdit ? (
                        <input
                          className="hs-value-input"
                          value={draft}
                          autoFocus
                          style={{ '--tc': color }}
                          onChange={e => setDraft(e.target.value)}
                          onBlur={() => commitEdit(i)}
                          onKeyDown={e => {
                            if (e.key === 'Enter')  commitEdit(i);
                            if (e.key === 'Escape') cancelEdit();
                          }}
                          onClick={e => e.stopPropagation()}
                        />
                      ) : (
                        <span
                          className="hs-value-display"
                          onDoubleClick={e => startEdit(i, e)}
                          title="Double-click to edit"
                        >{val}</span>
                      )}
                      <span className="hs-fanout-badge" title={`${level.fanout} children per unit`}>
                        <span className="hs-fanout-num">{level.fanout}</span>
                        <span className="hs-fanout-x">×</span>
                      </span>
                    </div>

                    {/* Expanded detail row */}
                    {isAct && (
                      <div className="hs-tile-detail">
                        <span className="hs-detail-item">
                          <span className="hs-detail-key">Δt</span>
                          <span className="hs-detail-val" style={{ color }}>{level.duration}</span>
                        </span>
                        <span className="hs-detail-item">
                          <span className="hs-detail-key">depth</span>
                          <span className="hs-detail-val">{i}/14</span>
                        </span>
                        <span className="hs-detail-item">
                          <span className="hs-detail-key">group</span>
                          <span className="hs-detail-val">{GROUP_LABELS[level.group]}</span>
                        </span>
                        <span className="hs-detail-item hs-detail-hint">click again to collapse</span>
                      </div>
                    )}

                  </div>
                </UnifiedTooltip>
              </React.Fragment>
            );
          })}
        </div>
      </div>

      <div className="hs-footer">
        <span className="hs-footer-hint">
          hover tile to tilt · ◀ ▶ navigate · double-click value to edit · click to expand
        </span>
      </div>

    </div>
  );
};

/* ── Injected CSS ────────────────────────────────────────────────────────────── */
const SHELF_CSS = `
/* ═══════════════════════════════════════════════════════════════════════
   Host container overrides — applied only when NaturalMotion tab is active
   (.nm-tab-active is set by HomePage.js on both content-container and
   HomePageTabContent so that overflow:hidden / overflow:auto do not clip
   the per-tile rotateY tilt effects)
   ═══════════════════════════════════════════════════════════════════════ */

/* content-container normally: grid with 3 cols + overflow:hidden          */
/* With nm-tab-active: single-column block, overflow visible for 3-D tilt  */
.content-container.nm-tab-active {
  display: block !important;
  overflow: visible !important;
  height: auto !important;
  padding: 0 !important;
  gap: 0 !important;
}

/* HomePageTabContent normally: overflow:auto (creates stacking context)    */
.HomePageTabContent.nm-tab-active {
  overflow: visible !important;
  background: transparent !important;
  padding: 24px 16px !important;
  /* remove any border-radius that would clip tilted edges */
  border-radius: 0 !important;
}

/* ═══════════════════════════════════════════════════════════════════════
   Hierarchy Shelf  —  15-Level TEA-Space Time Hierarchy
   Natural motion: each tile rotates on its Y-axis on hover (per
   Naturalmotion.md: rotateY, glassmorphism, cubic-bezier 0.42/0/0.28/0.99)
   ═══════════════════════════════════════════════════════════════════════ */

.hs-root {
  width: 100%;
  max-width: 820px;
  margin: 0 auto;
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  background: linear-gradient(155deg, #0f172a 0%, #1e1b4b 55%, #0f172a 100%);
  border-radius: 16px;
  padding: 14px 0 10px;
  box-shadow:
    0 24px 64px rgba(0,0,0,0.55),
    inset 0 1px 0 rgba(255,255,255,0.06);
  /* NO overflow:hidden — tiles must be free to tilt out of bounds */
}

/* ── Header ────────────────────────────────────────────────────────── */
.hs-header {
  padding: 0 20px 10px;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  margin-bottom: 4px;
}
.hs-header-label {
  display: block;
  font-size: 9.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: rgba(148,163,184,0.6);
  margin-bottom: 5px;
}
.hs-breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
}
.hs-breadcrumb::-webkit-scrollbar { display: none; }
.hs-bc-icon { font-size: 13px; flex-shrink: 0; }
.hs-bc-text {
  font-size: 11px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: rgba(203,213,225,0.88);
  white-space: nowrap;
}

/* ── Scene: perspective lives here so individual rotateY gets depth ── */
.hs-scene {
  padding: 4px 20px 6px;
  perspective: 1000px;
  perspective-origin: 30% 50%;   /* slight left bias = book pulled from left wall */
}

/* ── Stack: flat column, NO parent transform (fixes hit-test for all tiles) ── */
.hs-stack {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* ── Group dividers ──────────────────────────────────────────────────── */
.hs-group-divider {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 4px 2px;
  margin-top: 2px;
}
.hs-group-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(255,255,255,0.08);
}
.hs-group-label {
  font-size: 8.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: rgba(148,163,184,0.45);
  white-space: nowrap;
}
.hs-group-calendar  .hs-group-label { color: rgba(239,68,68,0.55);  }
.hs-group-second    .hs-group-label { color: rgba(14,165,233,0.55); }
.hs-group-subsecond .hs-group-label { color: rgba(99,102,241,0.55); }
.hs-group-ultrafine .hs-group-label { color: rgba(168,85,247,0.55); }

/* ── Tile Base ───────────────────────────────────────────────────────── */
.hs-tile {
  display: flex;
  align-items: center;
  height: 36px;
  min-height: 36px;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  border: 1px solid rgba(255,255,255,0.07);

  /* Glassmorphism (from Naturalmotion.md) */
  background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.06);

  padding: 0 10px 0 0;
  flex-wrap: nowrap;
  flex-shrink: 0;

  /* Natural motion: smooth Y-axis rotation, matching Naturalmotion.md easing */
  transform-origin: left center;
  transform-style: preserve-3d;
  transition:
    transform 0.5s cubic-bezier(0.42, 0, 0.28, 0.99),
    box-shadow 0.3s ease,
    border-color 0.3s ease,
    background 0.3s ease,
    opacity 0.3s ease;
  /* transform is set inline per-tile via React state */
}

/* Left accent bar */
.hs-tile::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--tc, #6366f1);
  border-radius: 6px 0 0 6px;
  opacity: 0.7;
  transition: width 0.3s ease, opacity 0.3s ease;
}

/* Hover state — tile has been tilted by React state (rotateY via inline transform) */
.hs-tile:hover {
  border-color: rgba(255,255,255,0.16);
  box-shadow:
    0 8px 32px rgba(0,0,0,0.4),
    0 0 0 rgba(31,38,135,0.1),
    inset 0 1px 0 rgba(255,255,255,0.10);
  background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  opacity: 0.95;
}
.hs-tile:hover::before { width: 4px; opacity: 1; }

.hs-tile:focus-visible {
  outline: 2px solid var(--tc, #6366f1);
  outline-offset: 2px;
}

/* Active (expanded) tile */
.hs-tile-active {
  height: auto !important;
  min-height: 56px !important;
  border-color: var(--tc, #6366f1) !important;
  background: linear-gradient(135deg, rgba(255,255,255,0.13), rgba(255,255,255,0.07)) !important;
  box-shadow:
    0 0 0 1px var(--tc, #6366f1),
    0 10px 32px rgba(0,0,0,0.45) !important;
  flex-wrap: wrap !important;
}
.hs-tile-active::before { width: 4px !important; opacity: 1 !important; }

/* Group background tints */
.hs-tile-calendar  { --ta: 0.050; }
.hs-tile-second    { --ta: 0.058; }
.hs-tile-subsecond { --ta: 0.062; }
.hs-tile-ultrafine { --ta: 0.068; }

/* ── Left section ────────────────────────────────────────────────────── */
.hs-tile-left {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 185px;
  max-width: 185px;
  padding-left: 10px;
  flex-shrink: 0;
  overflow: hidden;
}
.hs-depth-badge {
  font-size: 9px;
  font-weight: 800;
  min-width: 19px;
  height: 19px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.35);
}
.hs-symbol {
  font-size: 13px;
  font-weight: 800;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  min-width: 26px;
  text-align: center;
  flex-shrink: 0;
}
.hs-name {
  font-size: 11px;
  font-weight: 500;
  color: rgba(203,213,225,0.82);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Center: nav ─────────────────────────────────────────────────────── */
.hs-tile-center {
  display: flex;
  align-items: center;
  gap: 5px;
  flex: 1;
  justify-content: center;
  min-width: 0;
}
.hs-nav-btn {
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.10);
  color: rgba(203,213,225,0.65);
  border-radius: 4px;
  width: 22px;
  height: 22px;
  font-size: 9px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  padding: 0;
  flex-shrink: 0;
  user-select: none;
}
.hs-nav-btn:hover:not(:disabled) {
  background: rgba(255,255,255,0.18);
  color: #fff;
  border-color: rgba(255,255,255,0.28);
}
.hs-nav-btn:active:not(:disabled) { transform: scale(0.88); }
.hs-nav-btn:disabled { opacity: 0.18; cursor: not-allowed; }
.hs-pos-label {
  font-size: 11px;
  font-weight: 700;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  min-width: 52px;
  text-align: center;
  letter-spacing: 0.04em;
  user-select: none;
}

/* ── Right section ───────────────────────────────────────────────────── */
.hs-tile-right {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 130px;
  max-width: 130px;
  justify-content: flex-end;
  flex-shrink: 0;
}
.hs-value-display {
  font-size: 11.5px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-weight: 600;
  color: rgba(226,232,240,0.92);
  min-width: 72px;
  text-align: right;
  cursor: text;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid transparent;
  transition: border-color 0.15s ease, background 0.15s ease;
  user-select: none;
}
.hs-value-display:hover {
  border-color: rgba(255,255,255,0.18);
  background: rgba(255,255,255,0.06);
}
.hs-value-input {
  font-size: 11.5px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-weight: 600;
  color: #fff;
  width: 80px;
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--tc, #6366f1);
  border-radius: 4px;
  padding: 2px 6px;
  outline: none;
  text-align: right;
}
.hs-fanout-badge {
  display: flex;
  align-items: baseline;
  gap: 1px;
  min-width: 28px;
  justify-content: flex-end;
  user-select: none;
}
.hs-fanout-num { font-size: 10.5px; font-weight: 700; color: rgba(148,163,184,0.55); }
.hs-fanout-x  { font-size: 8.5px; color: rgba(148,163,184,0.32); }

/* ── Expanded detail row ─────────────────────────────────────────────── */
.hs-tile-detail {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 5px 10px 5px 38px;
  border-top: 1px solid rgba(255,255,255,0.07);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.hs-detail-item { display: flex; gap: 5px; align-items: center; }
.hs-detail-key {
  font-size: 9px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.10em; color: rgba(148,163,184,0.50);
}
.hs-detail-val {
  font-size: 10.5px; font-family: 'JetBrains Mono', monospace;
  color: rgba(226,232,240,0.88); font-weight: 600;
}
.hs-detail-hint {
  margin-left: auto; font-size: 9px;
  color: rgba(148,163,184,0.35); font-style: italic;
}

/* ── Footer ──────────────────────────────────────────────────────────── */
.hs-footer {
  padding: 7px 20px 0;
  border-top: 1px solid rgba(255,255,255,0.06);
  margin-top: 6px;
}
.hs-footer-hint {
  display: block; font-size: 9.5px;
  color: rgba(148,163,184,0.38); text-align: center; letter-spacing: 0.04em;
}
`;

export default HierarchyShelfComponent;
