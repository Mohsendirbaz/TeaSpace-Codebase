import React, { useCallback, useState, useMemo } from 'react';
import CustomizableTable from '../modules/CustomizableTable'; // Adjust path as needed
import '../../styles/HomePage.CSS/HCSS.css';

const IndividualResultsPanel = ({
  data,
  selectedCell,
  inspectorVisible,
  inspectorPosition,
  cellDetails,
  onCellClick,
  onCloseInspector,
  selectedVersions = [] // Add this to receive the selected versions
}) => {
  // State for individual table view
  const [viewingVersion, setViewingVersion] = useState(null);
  const [individualTableData, setIndividualTableData] = useState(null);
  const [loadingTable, setLoadingTable] = useState(false);

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

  // Convert consolidated data to format for CustomizableTable
  const consolidatedTableData = useMemo(() => {
    return validatedData.years.map((year, rowIndex) => {
      const rowData = { Year: year };
      validatedData.columns.forEach((column, colIndex) => {
        rowData[column] = validatedData.values[rowIndex][colIndex];
      });
      return rowData;
    });
  }, [validatedData]);

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
                          <div className="value-amount">
                            {source.value.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2
                            })}
                          </div>
                          {source.percentage && (
                            <div className="value-percentage">
                              ({source.percentage}% of total)
                            </div>
                          )}
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

  // Load individual version data
  const loadVersionData = useCallback(async (version) => {
    if (!version) return;

    setLoadingTable(true);
    try {
      const response = await fetch(`http://localhost:4560/api/process/${version}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch version data: ${response.status}`);
      }

      const result = await response.json();
      if (result.error) {
        throw new Error(result.error);
      }

      setIndividualTableData(result.data);
      setViewingVersion(version);
    } catch (error) {
      console.error('Error loading version data:', error);
      setIndividualTableData(null);
      // Show error message to user
    } finally {
      setLoadingTable(false);
    }
  }, []);

  // Close individual version view
  const closeVersionView = useCallback(() => {
    setViewingVersion(null);
    setIndividualTableData(null);
  }, []);

  return (
    <div className="results-panel">
      <div className="results-panel__header">
        <h3 className="results-panel__title">
          {viewingVersion 
            ? `CFA Version ${viewingVersion} Data` 
            : 'Consolidated Results'}
        </h3>
        <div className="results-panel__actions">
          {!viewingVersion ? (
            <>
              <div className="version-selector">
                <label>View Individual Version: </label>
                <select 
                  onChange={(e) => loadVersionData(e.target.value)}
                  value={viewingVersion || ''}
                  disabled={loadingTable}
                >
                  <option value="">Select a version</option>
                  {selectedVersions.map(version => (
                    <option key={version} value={version}>Version {version}</option>
                  ))}
                </select>
              </div>
              <button
                className="action-button"
                onClick={() => {
                  // Add export functionality
                  console.log('Export consolidated data:', consolidatedTableData);
                }}
              >
                Export Table
              </button>
            </>
          ) : (
            <>
              <button
                className="action-button"
                onClick={closeVersionView}
              >
                Back to Consolidated View
              </button>
              <button
                className="action-button"
                onClick={() => {
                  // Add export functionality
                  console.log('Export version data:', individualTableData);
                }}
              >
                Export Version Data
              </button>
            </>
          )}
        </div>
      </div>

      <div className="results-panel__content">
        {loadingTable ? (
          <div className="loading-indicator">Loading version data...</div>
        ) : viewingVersion && individualTableData ? (
          <div className="individual-table-container">
            <CustomizableTable 
              data={individualTableData}
              fileName={`CFA(${viewingVersion})`}
              tableClassName="individual-cfa-table"
            />
          </div>
        ) : (
          <div className="results-table-container">
            {consolidatedTableData.length > 0 ? (
              <CustomizableTable 
                data={consolidatedTableData}
                fileName="CFA(Consolidated)"
                tableClassName="consolidated-cfa-table"
              />
            ) : (
              <table className="results-table">
                {renderTableHeader()}
                {renderTableBody()}
              </table>
            )}
          </div>
        )}
      </div>

      {renderCellInspector()}
    </div>
  );
};

export default IndividualResultsPanel;
