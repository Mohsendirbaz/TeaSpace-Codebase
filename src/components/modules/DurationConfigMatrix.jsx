/**
 * DurationConfigMatrix.jsx
 *
 * React port of src/generalized_duration_visualization.html.
 * Maintains the original layout, interactions, and 3D tile animations
 * faithfully while plugging into real app data via the formValues prop.
 *
 * Props:
 *   formValues    - from useMatrixFormValues (Consolidated2.js)
 *   activeVersion - from versionsAtom
 *   activeZone    - from zonesAtom
 *   plantLifetime - number; defaults to 8 (demo) or plantLifetimeAmount10
 *   baseYear      - first calendar year of the plant; defaults to 2026
 */

import React, {
  useState, useMemo, useRef, useEffect, useCallback,
} from 'react';

import {
  LEVELS, LEVEL_INDEX,
  makeDurationContext,
  pathEntry, clonePath,
  formatLevelValue, levelSymbol,
  pathToString, pathTokenString, pathKey, pathsEqual, isPrefix,
  pathRange, nextStartNs,
  nsToDisplay, formatPercent,
  computeCell,
  buildVisibleColumns, getChildren,
  parsePathString,
  legacyPeriodToVisualization, seedDemoRows,
} from '../../utils/durationUnits';

import '../../styles/HomePage.CSS/DurationConfigMatrix.css';

// ── Helper: CSS-safe attribute selector value ─────────────────────────────────
function cssEsc(value) {
  if (window.CSS && typeof window.CSS.escape === 'function') return window.CSS.escape(value);
  return value.replace(/(["\\|:])/g, '\\$1');
}

// ─────────────────────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────────────────────
export default function DurationConfigMatrix({
  formValues,
  plantLifetime,
  baseYear = 2026,
}) {
  // Determine year count: use plant lifetime from props, or fall back to 8 for demo
  const yearCount = useMemo(() => {
    if (plantLifetime && plantLifetime > 0) return Math.max(1, Math.round(plantLifetime));
    if (formValues) {
      const lt = formValues['plantLifetimeAmount10'];
      const v = lt?.value ?? lt?.matrix?.v1?.z1;
      if (v && Number(v) > 0) return Math.round(Number(v));
    }
    return 8;
  }, [plantLifetime, formValues]);

  const ctx = useMemo(() => makeDurationContext(yearCount, baseYear), [yearCount, baseYear]);

  // ── State ────────────────────────────────────────────────────────────────
  const [expansionPath, setExpansionPath] = useState([]);
  const [explorerPath,  setExplorerPath]  = useState([]);
  const [selectedCell,  setSelectedCell]  = useState(null);
  const [dirOpen,       setDirOpen]       = useState(false);
  const [tooltipState,  setTooltipState]  = useState(null); // { cell, x, y }
  const [locateRowId,   setLocateRowId]   = useState('');
  const [locatePath,    setLocatePath]    = useState('');
  const [pendingLocate, setPendingLocate] = useState(null);

  const matrixWrapRef = useRef(null);

  // ── Build rows ───────────────────────────────────────────────────────────
  const rows = useMemo(() => {
    if (formValues && Object.keys(formValues).length > 0) {
      const built = Object.entries(formValues)
        .filter(([, item]) => item?.efficacyPeriod)
        .map(([paramId, item]) => ({
          id:          paramId,
          name:        item.label ?? paramId,
          unit:        item.unit ?? '',
          description: item.description ?? '',
          periods: [
            legacyPeriodToVisualization(
              item.efficacyPeriod,
              item.label ?? paramId,
              item.unit ?? '',
              ctx,
            ),
          ],
        }));
      if (built.length > 0) return built;
    }
    return seedDemoRows(ctx);
  }, [formValues, ctx]);

  // ── Derived: visible columns ─────────────────────────────────────────────
  const visibleColumns = useMemo(
    () => buildVisibleColumns([], expansionPath, ctx),
    [expansionPath, ctx],
  );

  // ── Computed cells (memoized to avoid re-running BigInt math every render) ─
  const computedCells = useMemo(() => {
    const map = {};
    for (const row of rows) {
      for (const col of visibleColumns) {
        map[`${row.id}::${pathKey(col.path)}`] = computeCell(row, col, ctx);
      }
    }
    return map;
  }, [rows, visibleColumns, ctx]);

  // ── Explorer children ────────────────────────────────────────────────────
  const explorerChildren = useMemo(
    () => getChildren(explorerPath, ctx),
    [explorerPath, ctx],
  );

  // ── Breadcrumbs ──────────────────────────────────────────────────────────
  const crumbs = useMemo(() => [
    { label: 'Root', path: [] },
    ...expansionPath.map((part, i) => ({
      label: formatLevelValue(part.key, part.value),
      path:  expansionPath.slice(0, i + 1),
    })),
  ], [expansionPath]);

  // ── Summary cards ────────────────────────────────────────────────────────
  const summaryCards = useMemo(() => {
    const lastDepth = expansionPath.length ? LEVELS[expansionPath.length - 1].title : 'Year';
    const deepest   = expansionPath.length
      ? formatLevelValue(expansionPath[expansionPath.length - 1].key, expansionPath[expansionPath.length - 1].value)
      : `Y1–Y${ctx.yearCount}`;
    const maxChildren = expansionPath.length ? getChildren(expansionPath, ctx).length : ctx.yearCount;
    return [
      { label: 'Root headers',    value: `${ctx.yearCount} years`,         sub: 'Canonical timescale stays year-based by default.' },
      { label: 'Visible columns', value: String(visibleColumns.length),    sub: 'Current branch replaces one column at a time.' },
      { label: 'Focused depth',   value: `${expansionPath.length} levels`, sub: `${lastDepth} focus${expansionPath.length ? ` at ${deepest}` : ''}.` },
      { label: 'Current fanout',  value: String(maxChildren),              sub: 'Only the active level is instantiated.' },
    ];
  }, [expansionPath, visibleColumns, ctx]);

  // ── Branch info (inspector) ───────────────────────────────────────────────
  const branchInfo = useMemo(() => {
    const children = getChildren(expansionPath, ctx);
    let branchDuration;
    if (expansionPath.length) {
      const r = pathRange(expansionPath, ctx);
      branchDuration = nsToDisplay(r.end - r.start + 1n);
    } else {
      const endNs = nextStartNs([pathEntry('Y', ctx.yearCount)], ctx);
      branchDuration = `${ctx.yearCount} years at root`;
      void endNs;
    }
    return {
      level:      expansionPath.length ? LEVELS[expansionPath.length - 1].title : 'Years',
      path:       pathToString(expansionPath),
      visible:    visibleColumns.length,
      duration:   branchDuration,
      childCount: children.length,
    };
  }, [expansionPath, visibleColumns, ctx]);

  // ── Pending locate (scroll-to-cell after render) ─────────────────────────
  useEffect(() => {
    if (!pendingLocate || !matrixWrapRef.current) return;
    const { rowId, path } = pendingLocate;
    const colKey = pathKey(path);
    const cellEl = matrixWrapRef.current.querySelector(
      `[data-row-id="${cssEsc(rowId)}"][data-column-key="${cssEsc(colKey)}"]`,
    );
    if (cellEl) {
      cellEl.scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' });
      const row = rows.find(r => r.id === rowId);
      const col = visibleColumns.find(c => pathKey(c.path) === colKey);
      if (row && col) setSelectedCell(computedCells[`${rowId}::${colKey}`] ?? computeCell(row, col, ctx));
    }
    setPendingLocate(null);
  }, [pendingLocate, rows, visibleColumns, computedCells, ctx]);

  // ── Initialize locate dropdown ────────────────────────────────────────────
  useEffect(() => {
    if (rows.length && !locateRowId) setLocateRowId(rows[0].id);
  }, [rows, locateRowId]);

  // ── Escape key closes modal ───────────────────────────────────────────────
  useEffect(() => {
    const handler = e => { if (e.key === 'Escape') setDirOpen(false); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  // ── Handlers ─────────────────────────────────────────────────────────────
  const handleColumnClick = useCallback(col => {
    setExpansionPath(clonePath(col.path));
    setExplorerPath(clonePath(col.path));
  }, []);

  const handleCrumbClick = useCallback(crumb => {
    setExpansionPath(crumb.path);
    setExplorerPath(clonePath(crumb.path));
  }, []);

  const handleTileClick = useCallback(child => {
    setExplorerPath(clonePath(child.path));
    setExpansionPath(clonePath(child.path));
  }, []);

  const handleLocate = useCallback(() => {
    try {
      const path = parsePathString(locatePath, ctx);
      setExpansionPath(clonePath(path));
      setExplorerPath(clonePath(path));
      setPendingLocate({ rowId: locateRowId, path });
    } catch (err) {
      window.alert(`Could not locate that path. ${err.message}`);
    }
  }, [locatePath, locateRowId, ctx]);

  // ── Tooltip position ──────────────────────────────────────────────────────
  const tooltipStyle = useMemo(() => {
    if (!tooltipState) return {};
    const pad = 14, w = 300;
    let left = tooltipState.x + 14;
    let top  = tooltipState.y - 70;
    if (left + w + pad > window.innerWidth)  left = tooltipState.x - w - 14;
    if (left < pad) left = pad;
    if (top  < pad) top  = pad;
    if (top + 200 + pad > window.innerHeight) top = window.innerHeight - 200 - pad;
    return { left, top };
  }, [tooltipState]);

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="dcm-root">

      {/* ── Header / Summary ── */}
      <section className="dcm-shell">
        <div className="dcm-title-block">
          <h1>Generalized Duration Configuration Visualization</h1>
          <p>
            Canonical year headers anchor the matrix by default. A single active expansion chain
            replaces one visible time column with its children at each step, while the directory
            explorer and stable inspector keep every cell locatable without losing context.
          </p>
        </div>
        <div className="dcm-summary-grid">
          {summaryCards.map((card, i) => (
            <div key={i} className="dcm-summary-card">
              <div className="dcm-label">{card.label}</div>
              <div className="dcm-value">{card.value}</div>
              <div className="dcm-sub">{card.sub}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Toolbar ── */}
      <section className="dcm-toolbar">
        <div className="dcm-toolbar-left">
          <button onClick={() => { setExpansionPath([]); setExplorerPath([]); }}>
            Reset to years
          </button>
          <button className="dcm-secondary" onClick={() => setExpansionPath(p => p.slice(0, -1))}>
            Collapse one level
          </button>
          <button onClick={() => setDirOpen(true)}>Open tilted directory</button>
          <span className="dcm-path-chip">Path: {pathToString(expansionPath)}</span>
        </div>
        <div className="dcm-toolbar-right">
          <div className="dcm-locate-group">
            <select value={locateRowId} onChange={e => setLocateRowId(e.target.value)}>
              {rows.map(row => (
                <option key={row.id} value={row.id}>{row.name}</option>
              ))}
            </select>
            <input
              value={locatePath}
              onChange={e => setLocatePath(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLocate()}
              placeholder="Locate path, e.g. Y3/Jun or Y3/Jun/D15/08h"
              size={36}
            />
            <button onClick={handleLocate}>Locate cell</button>
          </div>
        </div>
      </section>

      {/* ── Workspace ── */}
      <section className="dcm-workspace">

        {/* Matrix */}
        <div className="dcm-matrix-shell">
          <div className="dcm-matrix-topbar">
            <div>
              <h2>Configuration Matrix</h2>
              <div className="dcm-muted dcm-small">
                {visibleColumns.length} visible columns · one expansion chain active · sticky variable index for stable scanning
              </div>
            </div>
            <div className="dcm-breadcrumb">
              {crumbs.map((crumb, i) => (
                <React.Fragment key={i}>
                  <button onClick={() => handleCrumbClick(crumb)}>{crumb.label}</button>
                  {i < crumbs.length - 1 && <span className="dcm-separator">›</span>}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="dcm-legend">
            <span><span className="dcm-legend-swatch dcm-full"></span> Fully active</span>
            <span><span className="dcm-legend-swatch dcm-partial"></span> Partial coverage</span>
            <span><span className="dcm-legend-swatch dcm-empty"></span> Inactive</span>
            <span className="dcm-muted dcm-small">Hover for transient detail. Click to pin a stable inspection panel.</span>
          </div>

          <div className="dcm-matrix-wrap" ref={matrixWrapRef}>
            <table>
              <thead>
                <tr>
                  <th className="dcm-sticky-col">
                    <div className="dcm-level-tag">Variables</div>
                    <div className="dcm-header-main">All parameters</div>
                    <div className="dcm-header-sub">Sticky first column for row-level continuity</div>
                  </th>
                  {visibleColumns.map(col => {
                    const isSel     = pathsEqual(col.path, expansionPath);
                    const canExpand = getChildren(col.path, ctx).length > 0;
                    return (
                      <th
                        key={pathKey(col.path)}
                        className={isSel ? 'dcm-selected' : ''}
                        data-column-key={pathKey(col.path)}
                        onClick={() => handleColumnClick(col)}
                      >
                        <div className="dcm-level-tag">
                          {col.title}{canExpand ? ' · drill' : ' · leaf'}
                        </div>
                        <div className="dcm-header-main">{col.label}</div>
                        <div className="dcm-header-sub">{pathTokenString(col.path) || 'root'}</div>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {rows.map(row => (
                  <tr key={row.id}>
                    <th className="dcm-sticky-col">
                      <div className="dcm-variable-name">{row.name}</div>
                      <div className="dcm-variable-meta">{row.unit} · {row.description}</div>
                    </th>
                    {visibleColumns.map(col => {
                      const cell    = computedCells[`${row.id}::${pathKey(col.path)}`];
                      if (!cell) return <td key={pathKey(col.path)} />;
                      const width   = `${Math.max(0, Math.min(100, cell.coverage * 100))}%`;
                      const partial = cell.coverage > 0 && cell.coverage < 1;
                      const isCellSel = selectedCell
                        && selectedCell.row.id === row.id
                        && pathKey(selectedCell.column.path) === pathKey(col.path);
                      return (
                        <td
                          key={pathKey(col.path)}
                          className={`dcm-matrix-cell${isCellSel ? ' dcm-selected' : ''}`}
                          data-row-id={row.id}
                          data-column-key={pathKey(col.path)}
                          onClick={() => setSelectedCell(cell)}
                          onMouseEnter={e => setTooltipState({ cell, x: e.clientX, y: e.clientY })}
                          onMouseMove={e  => setTooltipState(p => p ? { ...p, x: e.clientX, y: e.clientY } : null)}
                          onMouseLeave={() => setTooltipState(null)}
                        >
                          <div className="dcm-fill-track">
                            <div className={`dcm-fill-bar${partial ? ' dcm-partial' : ''}`} style={{ width }} />
                            <div className="dcm-cell-label">
                              <span>{cell.coverage === 0 ? '' : cell.display}</span>
                              <span className="dcm-badge">{cell.badge}</span>
                            </div>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Inspector sidebar */}
        <aside className="dcm-inspector">
          <InspectorPanel selectedCell={selectedCell} branchInfo={branchInfo} />
        </aside>
      </section>

      {/* ── Tooltip ── */}
      {tooltipState && (
        <div
          className="dcm-tooltip dcm-tooltip-visible"
          style={tooltipStyle}
        >
          <div className="dcm-tooltip-title">{tooltipState.cell.row.name}</div>
          <div className="dcm-tooltip-grid">
            <div className="dcm-muted">Path</div>
            <div>{pathTokenString(tooltipState.cell.column.path) || '/'}</div>
            <div className="dcm-muted">Coverage</div>
            <div>{formatPercent(tooltipState.cell.coverage)}</div>
            <div className="dcm-muted">Duration</div>
            <div>{nsToDisplay(tooltipState.cell.range.end - tooltipState.cell.range.start + 1n)}</div>
            <div className="dcm-muted">Overlaps</div>
            <div>{tooltipState.cell.overlaps.length}</div>
            <div className="dcm-muted">Resolution</div>
            <div>
              {tooltipState.cell.dominant
                ? LEVELS[LEVEL_INDEX[tooltipState.cell.dominant.resolution]].title
                : 'Inactive'}
            </div>
          </div>
        </div>
      )}

      {/* ── Directory modal ── */}
      {dirOpen && (
        <div
          className="dcm-modal"
          onClick={e => { if (e.target.classList.contains('dcm-modal')) setDirOpen(false); }}
        >
          <div className="dcm-modal-card">
            <div className="dcm-modal-header">
              <div>
                <h2 style={{ margin: 0 }}>Tilted Directory Explorer</h2>
                <div className="dcm-muted dcm-small">
                  Shelf-style tiles provide multi-level traversal without enumerating the full leaf space.
                </div>
              </div>
              <button className="dcm-secondary" onClick={() => setDirOpen(false)}>Close</button>
            </div>

            <div className="dcm-explorer-breadcrumb">
              {crumbs.map((crumb, i) => (
                <React.Fragment key={i}>
                  <button onClick={() => {
                    setExplorerPath(crumb.path);
                    setExpansionPath(clonePath(crumb.path));
                  }}>
                    {crumb.label}
                  </button>
                  {i < crumbs.length - 1 && <span className="dcm-separator">›</span>}
                </React.Fragment>
              ))}
            </div>

            <div className="dcm-explorer-stage">
              <div className="dcm-shelf">
                {explorerChildren.length === 0 ? (
                  <div className="dcm-empty-state">
                    No deeper descendants exist at this path. Use "Focus table" to keep the current leaf selected.
                  </div>
                ) : explorerChildren.map(child => {
                  const isSel     = isPrefix(child.path, expansionPath);
                  const childCount = getChildren(child.path, ctx).length;
                  return (
                    <div
                      key={pathKey(child.path)}
                      className={`dcm-tile${isSel ? ' dcm-selected' : ''}`}
                      onClick={() => handleTileClick(child)}
                    >
                      <div className="dcm-tile-top">
                        <div>
                          <div className="dcm-tile-count">{child.title}</div>
                          <div className="dcm-tile-title">{child.label}</div>
                        </div>
                        <span className="dcm-pill">{child.depth}/{LEVELS.length}</span>
                      </div>
                      <div className="dcm-tile-sub">{pathToString(child.path)}</div>
                      <div className="dcm-status-row">
                        <span className="dcm-pill dcm-accent">
                          {childCount || 0} {childCount === 1 ? 'child' : 'children'}
                        </span>
                        <span className="dcm-pill">{childCount ? child.nextTitle : 'Leaf'}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="dcm-modal-footer">
              <div className="dcm-footer-note">
                {explorerChildren.length
                  ? `${pathToString(explorerPath)} · ${explorerChildren.length} child ${explorerChildren.length === 1 ? 'node' : 'nodes'}`
                  : `${pathToString(explorerPath)} · leaf node reached`}
              </div>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button onClick={() => { setExpansionPath(clonePath(explorerPath)); setDirOpen(false); }}>
                  Focus table on current path
                </button>
                <button className="dcm-secondary" onClick={() => { setExplorerPath([]); setExpansionPath([]); }}>
                  Back to root
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Inspector panel (pure display component)
// ─────────────────────────────────────────────────────────────────────────────
function InspectorPanel({ selectedCell, branchInfo }) {
  return (
    <>
      {/* Status section */}
      <section className="dcm-inspector-section">
        <div className="dcm-inspector-title-row">
          <h2>Stable Inspector</h2>
          <span className="dcm-pill dcm-accent">
            {selectedCell ? `${selectedCell.row.name} · ${selectedCell.column.label}` : 'No cell selected'}
          </span>
        </div>
        {!selectedCell && (
          <div className="dcm-inspector-kv">
            <div className="k">Use</div>
            <div>Select a matrix cell to inspect its exact path, duration window, and overlapping efficacy periods.</div>
            <div className="k">Locate</div>
            <div>Choose a variable and enter a path to expand the table, center the target, and pin its details.</div>
          </div>
        )}
      </section>

      {/* Selection section */}
      <section className="dcm-inspector-section">
        <div className="dcm-inspector-title-row">
          <h2>Selection</h2>
          <span className="dcm-pill">
            {selectedCell ? `Coverage ${formatPercent(selectedCell.coverage)}` : 'Coverage —'}
          </span>
        </div>
        {selectedCell ? (
          <>
            <div className="dcm-inspector-kv">
              <div className="k">Variable</div>    <div>{selectedCell.row.name}</div>
              <div className="k">Path</div>         <div>{pathToString(selectedCell.column.path)}</div>
              <div className="k">Token form</div>   <div>{pathTokenString(selectedCell.column.path) || '/'}</div>
              <div className="k">Duration</div>     <div>{nsToDisplay(selectedCell.range.end - selectedCell.range.start + 1n)}</div>
              <div className="k">Absolute start</div><div>{selectedCell.range.start.toString()} ns</div>
              <div className="k">Absolute end</div>  <div>{selectedCell.range.end.toString()} ns</div>
              <div className="k">Resolved</div>
              <div>
                {selectedCell.dominant
                  ? `${LEVELS[LEVEL_INDEX[selectedCell.dominant.resolution]].title} precedence`
                  : 'Inactive'}
              </div>
            </div>
            <div className="dcm-timeline-note">
              {selectedCell.dominant
                ? `The current view is resolved by the finest overlapping period, here ${LEVELS[LEVEL_INDEX[selectedCell.dominant.resolution]].title.toLowerCase()} scale. Broader periods remain listed below for context.`
                : 'This segment is inactive for the selected variable at the current hierarchy slice.'}
            </div>
          </>
        ) : (
          <div className="dcm-inspector-kv">
            <div className="k">Variable</div><div>—</div>
            <div className="k">Path</div>    <div>—</div>
            <div className="k">Duration</div><div>—</div>
            <div className="k">Resolved</div><div>—</div>
            <div className="k">Cell mode</div>
            <div>Year headers with optional nested replacement.</div>
          </div>
        )}
      </section>

      {/* Visible branch section */}
      <section className="dcm-inspector-section">
        <div className="dcm-inspector-title-row">
          <h2>Visible Branch</h2>
          <span className="dcm-pill">{branchInfo.level}</span>
        </div>
        <div className="dcm-inspector-kv">
          <div className="k">Branch</div>   <div>{branchInfo.path}</div>
          <div className="k">Visible</div>  <div>{branchInfo.visible} columns rendered</div>
          <div className="k">Duration</div> <div>{branchInfo.duration}</div>
          <div className="k">Children</div> <div>{branchInfo.childCount} immediate descendants</div>
        </div>
      </section>

      {/* Overlapping periods section */}
      <section className="dcm-inspector-section">
        <div className="dcm-inspector-title-row">
          <h2>Overlapping Periods</h2>
          <span className="dcm-pill">
            {selectedCell
              ? `${selectedCell.overlaps.length} overlap${selectedCell.overlaps.length === 1 ? '' : 's'}`
              : '0 overlaps'}
          </span>
        </div>
        <div className="dcm-overlap-list">
          {!selectedCell ? (
            <div className="dcm-empty-state">No overlaps yet. Pick any visible cell in the matrix.</div>
          ) : selectedCell.overlaps.length === 0 ? (
            <div className="dcm-empty-state">No efficacy periods overlap the selected cell.</div>
          ) : selectedCell.overlaps.map((overlap, i) => (
            <div key={i} className="dcm-overlap-card">
              <div className="dcm-overlap-header">
                <div>
                  <strong>{overlap.label}</strong>
                  <div className="dcm-overlap-meta">{overlap.detail}</div>
                </div>
                <span className="dcm-pill dcm-accent">
                  {LEVELS[LEVEL_INDEX[overlap.resolution]].title}
                </span>
              </div>
              <div className="dcm-inspector-kv">
                <div className="k">Value</div>
                <div>{overlap.value}</div>
                <div className="k">Defined span</div>
                <div>{pathToString(overlap.startPath)} → {pathToString(overlap.endPath)}</div>
                <div className="k">Overlap</div>
                <div>{nsToDisplay(overlap.overlap)}</div>
                <div className="k">Effective slice</div>
                <div>{overlap.overlapStart.toString()} ns → {overlap.overlapEnd.toString()} ns</div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
