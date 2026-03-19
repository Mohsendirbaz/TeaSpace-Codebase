import React, { useCallback, useMemo } from 'react';
import '../../styles/HomePage.CSS/HCSS.css';

const ResultsPanel = ({
  data,
  selectedCell,
  inspectorVisible,
  inspectorPosition,
  cellDetails,
  onCellClick,
  onCloseInspector
}) => {
  // Validate and memoize data
  const validatedData = useMemo(() => {
    if (!data || !data.columns || !data.years || !data.values) {
      return null;
    }
    return data;
  }, [data]);

  if (!validatedData) {
    return (
      <div className="results-panel">
        <div className="results-panel__header">
          <h3 className="results-panel__title">Consolidated Results</h3>
        </div>
        <div className="results-panel__content">
          <div className="error-message">Invalid or incomplete data structure</div>
        </div>
      </div>
    );
  }

  const renderTableHeader = useCallback(() => {
    return (
      <thead>
        <tr>
          <th className="table-header year">Year</th>
          {validatedData.columns.map((column) => (
            <th key={column} className="table-header">
              {column}
            </th>
          ))}
        </tr>
      </thead>
    );
  }, [validatedData]);

  const renderTableBody = useCallback(() => {
    return (
      <tbody>
        {validatedData.years.map((year, rowIndex) => (
          <tr key={year}>
            <td className="table-cell year">{year}</td>
            {validatedData.columns.map((column, colIndex) => {
              const value = validatedData.values[rowIndex][colIndex];
              const isTrackable = column === 'Revenue' || column === 'Operating Expenses';
              const isEmpty = value === null || value === undefined || value === 0;

              return (
                <td
                  key={`${year}-${column}`}
                  className={`table-cell ${isTrackable ? 'trackable' : ''} ${isEmpty ? 'empty' : ''}`}
                  onClick={isTrackable ? (e) => onCellClick({
                    year,
                    column,
                    value,
                    rowIndex,
                    colIndex
                  }, e) : undefined}
                >
                  {isEmpty ? '-' : value.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                  })}
                  {isTrackable && (
                    <span className="cell-indicator">
                      ℹ️
                    </span>
                  )}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    );
  }, [validatedData, onCellClick]);

  const renderCellInspector = useCallback(() => {
    if (!selectedCell || !inspectorVisible) return null;

    // Get source data from cell details or use empty array if not available
    const sourceData = cellDetails?.sources || [];
    const totalValue = cellDetails?.totalValue || selectedCell.value;
    const isLoading = selectedCell && !cellDetails;

    return (
      <div 
        className="cell-inspector"
        style={{
          top: inspectorPosition.y,
          left: inspectorPosition.x
        }}
      >
        <div className="cell-inspector__header">
          <h4 className="cell-inspector__title">
            {selectedCell.column} - Year {selectedCell.year}
          </h4>
          <button
            className="cell-inspector__close"
            onClick={onCloseInspector}
          >
            ×
          </button>
        </div>

        <div className="cell-inspector__content">
          {isLoading ? (
            <div className="cell-inspector__loading">
              Loading cell details...
            </div>
          ) : cellDetails?.error ? (
            <div className="cell-inspector__error">
              {cellDetails.error}
            </div>
          ) : (
            <>
              <div className="cell-inspector__summary">
                <div className="summary-item">
                  <span className="summary-label">Total Value:</span>
                  <span className="summary-value">
                    {totalValue.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    })}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="summary-label">Source Count:</span>
                  <span className="summary-value">{sourceData.length}</span>
                </div>
              </div>

              <div className="cell-inspector__sources">
                <h5 className="sources-title">Source Breakdown</h5>
                {sourceData.length === 0 ? (
                  <div className="sources-empty">
                    No source data available
                  </div>
                ) : (
                  <div className="sources-list">
                    {sourceData.map((source, index) => (
                      <div key={index} className="source-item">
                        <div className="source-header">
                          <span className="source-version">CFA Version {source.version}</span>
                          <span className="source-timestamp">
                            {new Date(source.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <div className="source-value">
                          {source.value.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        <div className="cell-inspector__footer">
          <button
            className="inspector-action"
            onClick={() => {
              // Add export functionality
              console.log('Export cell data:', selectedCell, cellDetails);
            }}
            disabled={isLoading || Boolean(cellDetails?.error)}
          >
            Export Details
          </button>
        </div>
      </div>
    );
  }, [selectedCell, inspectorVisible, inspectorPosition, cellDetails, onCloseInspector]);

  return (
    <div className="results-panel">
      <div className="results-panel__header">
        <h3 className="results-panel__title">Consolidated Results</h3>
        <div className="results-panel__actions">
          <button
            className="action-button-rs"
            onClick={() => {
              // Add export functionality
              console.log('Export table data:', validatedData);
            }}
          >
            Export Table
          </button>
        </div>
      </div>

      <div className="results-panel__content">
        <div className="results-table-container">
          <table className="results-table">
            {renderTableHeader()}
            {renderTableBody()}
          </table>
        </div>
      </div>

      {renderCellInspector()}
    </div>
  );
};

export default ResultsPanel;
