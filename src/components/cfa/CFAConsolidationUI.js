import React, { useState, useCallback, useEffect } from 'react';
import '../../styles/HomePage.CSS/HCSS.css';
import '../../styles/HomePage.CSS/CFAConsolidationUI.css';
import SelectionPanel from './SelectionPanel';
import ProcessingPanel from './ProcessingPanel';
import ResultsPanel from './ResultsPanel';
import IndividualResultsPanel from './IndividualResultsPanel';

const CFAConsolidationUI = () => {
  // State management with proper initialization
  const [selectionState, setSelectionState] = useState({
    available: [],
    selected: [],
    filtered: [],
    searchQuery: '',
    error: null,
    loading: false
  });

  const [processingState, setProcessingState] = useState({
    status: 'idle',
    progress: 0,
    messages: [],
    error: null
  });

  const [resultsState, setResultsState] = useState({
    data: null,
    selectedCell: null,
    inspectorVisible: false,
    inspectorPosition: { x: 0, y: 0 },
    cellDetails: null,
    viewMode: 'individual' // 'individual' or 'consolidated'
  });

  const switchToIndividualView = useCallback(() => {
    setResultsState(prev => ({
      ...prev,
      viewMode: 'individual'
    }));
  }, []);

  const switchToConsolidatedView = useCallback(() => {
    setResultsState(prev => ({
      ...prev,
      viewMode: 'consolidated'
    }));
  }, []);

  // Load available versions on mount
  useEffect(() => {
    loadVersions();
  }, []);

  const loadVersions = async () => {
    setSelectionState(prev => ({
      ...prev,
      loading: true,
      error: null
    }));

    try {
      const response = await fetch('http://localhost:4560/api/versions', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (!data.versions || data.versions.length === 0) {
        setSelectionState(prev => ({
          ...prev,
          loading: false,
          available: [],
          filtered: [],
          error: 'No CFA versions found. Please check the server configuration.'
        }));
        return;
      }

      setSelectionState(prev => ({
        ...prev,
        loading: false,
        available: data.versions,
        filtered: data.versions,
        error: null
      }));
    } catch (error) {
      console.error('Failed to load CFA versions:', error);
      setSelectionState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load versions. Please try again.'
      }));
    }
  };

  const handleVersionSelect = useCallback((version) => {
    setSelectionState(prev => ({
      ...prev,
      selected: prev.selected.includes(version)
        ? prev.selected.filter(v => v !== version)
        : [...prev.selected, version]
    }));
  }, []);

  const handleSelectAll = useCallback(() => {
    setSelectionState(prev => ({
      ...prev,
      selected: prev.filtered.length > 0 ? [...prev.filtered] : [...prev.available]
    }));
  }, []);

  const handleSelectNone = useCallback(() => {
    setSelectionState(prev => ({
      ...prev,
      selected: []
    }));
  }, []);

  const handleSearch = useCallback((query) => {
    setSelectionState(prev => ({
      ...prev,
      searchQuery: query,
      filtered: prev.available.filter(version => 
        version.toLowerCase().includes(query.toLowerCase())
      )
    }));
  }, []);

  const startProcessing = useCallback(async () => {
    if (selectionState.selected.length === 0) return;

    setProcessingState({
      status: 'processing',
      progress: 0,
      messages: ['Starting consolidation...'],
      error: null
    });

    try {
      const consolidationResponse = await fetch('http://localhost:4560/api/consolidate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          versions: selectionState.selected
        })
      });

      if (!consolidationResponse.ok) {
        throw new Error(`Consolidation failed! Status: ${consolidationResponse.status}`);
      }

      const consolidationId = await consolidationResponse.json();

      let completed = false;
      let lastProgress = 0;
      let stallCount = 0;
      let pollDelay = 1000; // Start with 1 second
      const maxPollDelay = 5000; // Max 5 seconds between polls
      const maxStallCount = 10; // Allow more stall cycles

      while (!completed) {
        try {
          const progressResponse = await fetch(`http://localhost:4560/api/consolidate/status/${consolidationId}`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json'
            }
          });

          if (!progressResponse.ok) {
            throw new Error(`Failed to fetch progress! Status: ${progressResponse.status}`);
          }

          const progressData = await progressResponse.json();

          if (progressData.progress === lastProgress) {
            stallCount++;
            pollDelay = Math.min(pollDelay * 1.5, maxPollDelay);

            if (stallCount > maxStallCount) {
              setProcessingState(prev => ({
                ...prev,
                messages: [...prev.messages, "Processing is taking longer than expected. Please wait..."]
              }));
            }
          } else {
            stallCount = 0;
            pollDelay = 1000;
            lastProgress = progressData.progress;
          }

          setProcessingState(prev => ({
            ...prev,
            progress: progressData.progress,
            messages: [...prev.messages.filter(m => m !== progressData.message), progressData.message]
          }));

          if (progressData.status === 'complete') {
            completed = true;

            const resultsResponse = await fetch(`http://localhost:4560/api/consolidate/results/${consolidationId}`, {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json'
              }
            });

            if (!resultsResponse.ok) {
              throw new Error(`Failed to fetch results! Status: ${resultsResponse.status}`);
            }

            const resultsData = await resultsResponse.json();
            setResultsState(prev => ({
              ...prev,
              data: {
                years: resultsData.years,
                columns: resultsData.columns,
                values: resultsData.values,
                sources: resultsData.sources
              }
            }));

            setProcessingState(prev => ({
              ...prev,
              status: 'complete',
              messages: [...prev.messages, 'Consolidation complete']
            }));
          } else if (progressData.status === 'error') {
            throw new Error(progressData.error || 'Consolidation failed');
          } else {
            await new Promise(resolve => setTimeout(resolve, pollDelay));
          }
        } catch (error) {
          throw error;
        }
      }
    } catch (error) {
      console.error('Processing error:', error);
      setProcessingState(prev => ({
        ...prev,
        status: 'error',
        error: error.message,
        messages: [...prev.messages, `Error: ${error.message}`]
      }));
    }
  }, [selectionState.selected]);

  const cancelProcessing = useCallback(() => {
    setProcessingState({
      status: 'idle',
      progress: 0,
      messages: [],
      error: null
    });
  }, []);

  const resetProcessing = useCallback(() => {
    setProcessingState({
      status: 'idle',
      progress: 0,
      messages: [],
      error: null
    });
    setResultsState(prev => ({
      ...prev,
      data: null,
      selectedCell: null,
      inspectorVisible: false,
      cellDetails: null
    }));
  }, []);

  const handleCellClick = useCallback(async (cell, event) => {
    setResultsState(prev => ({
      ...prev,
      selectedCell: cell,
      inspectorVisible: true,
      inspectorPosition: {
        x: event.clientX,
        y: event.clientY
      },
      cellDetails: null
    }));

    try {
      const response = await fetch(`http://localhost:4560/api/cell-details`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          year: cell.year,
          column: cell.column,
          rowIndex: cell.rowIndex,
          colIndex: cell.colIndex
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch cell details! Status: ${response.status}`);
      }

      const detailsData = await response.json();
      setResultsState(prev => ({
        ...prev,
        cellDetails: detailsData
      }));
    } catch (error) {
      console.error('Failed to fetch cell details:', error);
      setResultsState(prev => ({
        ...prev,
        cellDetails: { error: error.message }
      }));
    }
  }, []);

  const closeInspector = useCallback(() => {
    setResultsState(prev => ({
      ...prev,
      inspectorVisible: false,
      selectedCell: null,
      cellDetails: null
    }));
  }, []);

  return (
    <div className="cfa-consolidation">
      <div className="cfa-consolidation__panels">
        <div className="cfa-consolidation__left">
          <SelectionPanel
            available={selectionState.available}
            selected={selectionState.selected}
            filtered={selectionState.filtered}
            searchQuery={selectionState.searchQuery}
            error={selectionState.error}
            loading={selectionState.loading}
            onSelect={handleVersionSelect}
            onSelectAll={handleSelectAll}
            onSelectNone={handleSelectNone}
            onSearch={handleSearch}
            onRefresh={loadVersions}
          />
        </div>
        <div className="cfa-consolidation__right">
          <ProcessingPanel
            status={processingState.status}
            progress={processingState.progress}
            messages={processingState.messages}
            error={processingState.error}
            onStart={startProcessing}
            onCancel={cancelProcessing}
            onReset={resetProcessing}
            disabled={selectionState.selected.length === 0 || processingState.status === 'processing'}
            showReset={processingState.status === 'complete' || processingState.status === 'error'}
          />

          <div className="view-switcher">
            <button
              className={`view-button ${resultsState.viewMode === 'consolidated' ? 'active' : ''}`}
              onClick={switchToConsolidatedView}
              disabled={!resultsState.data || processingState.status !== 'complete'}
            >
              Consolidated View
            </button>
            <button
              className={`view-button ${resultsState.viewMode === 'individual' ? 'active' : ''}`}
              onClick={switchToIndividualView}
              disabled={!resultsState.data || processingState.status !== 'complete'}
            >
              Individual View
            </button>
          </div>

          <div className="results-section">
            {resultsState.data && processingState.status === 'complete' ? (
              resultsState.viewMode === 'individual' ? (
                <IndividualResultsPanel
                  data={resultsState.data}
                  selectedCell={resultsState.selectedCell}
                  inspectorVisible={resultsState.inspectorVisible}
                  inspectorPosition={resultsState.inspectorPosition}
                  cellDetails={resultsState.cellDetails}
                  onCellClick={handleCellClick}
                  onCloseInspector={closeInspector}
                  selectedVersions={selectionState.selected}
                />
              ) : (
                <ResultsPanel
                  data={resultsState.data}
                  selectedCell={resultsState.selectedCell}
                  inspectorVisible={resultsState.inspectorVisible}
                  inspectorPosition={resultsState.inspectorPosition}
                  cellDetails={resultsState.cellDetails}
                  onCellClick={handleCellClick}
                  onCloseInspector={closeInspector}
                  selectedVersions={selectionState.selected}
                />
              )
            ) : (
              <div className="results-placeholder">
                Select versions and start consolidation to view results
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CFAConsolidationUI;
