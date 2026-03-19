import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '20px',
          margin: '20px',
          borderRadius: '8px',
          backgroundColor: 'var(--model-color-surface, #f8f9fa)',
          border: '1px solid var(--model-color-border, #dee2e6)',
          color: 'var(--model-color-text, #212529)'
        }}>
          <h2 style={{ color: 'var(--model-color-error, #dc3545)' }}>Something went wrong</h2>
          <details style={{ whiteSpace: 'pre-wrap', marginTop: '10px' }}>
            <summary style={{ cursor: 'pointer', color: 'var(--model-color-primary, #0d6efd)' }}>
              View error details
            </summary>
            <div style={{ marginTop: '10px' }}>
              <p style={{ color: 'var(--model-color-error, #dc3545)' }}>
                {this.state.error && this.state.error.toString()}
              </p>
              <p style={{ color: 'var(--model-color-text-secondary, #6c757d)', marginTop: '10px' }}>
                Component Stack:
              </p>
              <pre style={{
                padding: '10px',
                backgroundColor: 'var(--model-color-background, #f1f3f5)',
                borderRadius: '4px',
                marginTop: '5px'
              }}>
                {this.state.errorInfo && this.state.errorInfo.componentStack}
              </pre>
            </div>
          </details>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '20px',
              padding: '8px 16px',
              backgroundColor: 'var(--model-color-primary, #0d6efd)',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
