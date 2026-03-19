import React from 'react';
import '../../styles/HomePage.CSS/HCSS.css';

const SelectionPanel = ({
  available,
  selected,
  filtered,
  searchQuery,
  error,
  loading,
  onSelect,
  onSelectAll,
  onSelectNone,
  onSearch,
  onRefresh
}) => {
  return (
    <div className="selection-panel">
      <div className="selection-panel__header">
        <h3 className="selection-panel__title">Select CFA Versions</h3>
        <div className="selection-panel__actions">
          <button
            className="action-button refresh"
            onClick={onRefresh}
            disabled={loading}
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="selection-panel__search">
        <input
          type="text"
          placeholder="Search versions..."
          value={searchQuery}
          onChange={(e) => onSearch(e.target.value)}
          disabled={loading}
        />
      </div>

      <div className="selection-panel__bulk-actions">
        <button
          className="action-button"
          onClick={onSelectAll}
          disabled={loading || filtered.length === 0}
        >
          Select All
        </button>
        <button
          className="action-button"
          onClick={onSelectNone}
          disabled={loading || selected.length === 0}
        >
          Clear Selection
        </button>
      </div>

      {error ? (
        <div className="selection-panel__error">
          {error}
        </div>
      ) : loading ? (
        <div className="selection-panel__loading">
          Loading versions...
        </div>
      ) : filtered.length === 0 ? (
        <div className="selection-panel__empty">
          No versions found
        </div>
      ) : (
        <div className="selection-panel__list">
          {filtered.map(version => (
            <div
              key={version}
              className={`version-item ${selected.includes(version) ? 'selected' : ''}`}
              onClick={() => onSelect(version)}
            >
              <span className="version-name">Version {version}</span>
              <span className="selection-indicator">
                {selected.includes(version) ? '✓' : ''}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="selection-panel__footer">
        <div className="selection-count">
          {selected.length} version{selected.length !== 1 ? 's' : ''} selected
        </div>
      </div>
    </div>
  );
};

export default SelectionPanel;
