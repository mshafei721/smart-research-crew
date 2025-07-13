import React from "react";

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class SSEErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("SSE Error Boundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
            <h3 className="text-red-400 font-semibold">Connection Error</h3>
            <p className="text-sm text-red-300 mt-2">
              Something went wrong with the real-time connection. Please refresh
              the page and try again.
            </p>
            {this.state.error && (
              <details className="mt-2">
                <summary className="text-xs text-red-400 cursor-pointer">
                  Technical Details
                </summary>
                <pre className="text-xs text-red-300 mt-1 overflow-auto">
                  {this.state.error.message}
                </pre>
              </details>
            )}
          </div>
        )
      );
    }

    return this.props.children;
  }
}
