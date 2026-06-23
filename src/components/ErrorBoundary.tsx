import React, { Component, ReactNode, ErrorInfo } from "react";
import { AlertTriangle, RefreshCcw, Copy } from "lucide-react";
import { classifyError, logError, HybaError } from "../utils/errorHandler";

interface Props {
  children: ReactNode;
  onError?: (error: HybaError, errorInfo: ErrorInfo) => void;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorId?: string;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  constructor(props: Props) {
    super(props);
  }

  public static getDerivedStateFromError(error: Error): State {
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return { hasError: true, error, errorId };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const classifiedError = classifyError(error);
    logError(classifiedError, {
      componentStack: errorInfo.componentStack,
      errorBoundary: true,
      errorId: this.state.errorId,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(classifiedError, errorInfo);
    }
  }

  private copyErrorDetails = () => {
    if (this.state.error) {
      const errorDetails = {
        message: this.state.error.message,
        stack: this.state.error.stack,
        errorId: this.state.errorId,
        timestamp: new Date().toISOString(),
        userAgent: typeof window !== "undefined" ? window.navigator.userAgent : "unknown",
        url: typeof window !== "undefined" ? window.location.href : "unknown",
      };

      navigator.clipboard.writeText(JSON.stringify(errorDetails, null, 2));
    }
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-sand flex flex-col items-center justify-center p-6 text-center">
          <div className="bg-white border-2 border-red-200 rounded-2xl p-8 max-w-md shadow-xl">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
            <h1 className="text-2xl font-bold font-sans text-oxford mb-2">
              Substrate Interface Discontinuity
            </h1>
            <p className="text-gray-600 mb-4 font-mono text-sm">
              The neural interface encountered a critical rendering exception. Phi-resonance
              destabilized.
            </p>

            {this.state.errorId && (
              <div className="bg-gray-100 px-3 py-1 rounded-full text-xs font-mono text-gray-600 mb-4 inline-block">
                Error ID: {this.state.errorId}
              </div>
            )}

            <div className="bg-red-50 p-4 rounded-lg mb-6 text-left overflow-auto max-h-32">
              <code className="text-xs text-red-700 font-mono break-words">
                {this.state.error?.message || "Unknown execution anomaly"}
              </code>
            </div>

            <div className="flex gap-3 justify-center">
              <button
                onClick={() => window.location.reload()}
                className="bg-oxford text-white px-6 py-2.5 rounded-lg flex items-center justify-center gap-2 font-mono text-sm hover:bg-lux-slate transition-colors"
              >
                <RefreshCcw className="w-4 h-4" />
                REBOOT INTERFACE
              </button>
              <button
                onClick={this.copyErrorDetails}
                className="bg-gray-200 text-gray-700 px-4 py-2.5 rounded-lg flex items-center justify-center gap-2 font-mono text-sm hover:bg-gray-300 transition-colors"
                title="Copy error details to clipboard"
              >
                <Copy className="w-4 h-4" />
                COPY
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
