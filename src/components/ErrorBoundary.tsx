import React, { Component, ReactNode, ErrorInfo } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  constructor(props: Props) {
    super(props);
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error in HYBA Substrate Interface:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-sand flex flex-col items-center justify-center p-6 text-center">
          <div className="bg-white border-2 border-red-200 rounded-2xl p-8 max-w-md shadow-xl">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
            <h1 className="text-2xl font-bold font-sans text-oxford mb-2">
              Substrate Interface Discontinuity
            </h1>
            <p className="text-gray-600 mb-6 font-mono text-sm">
              The neural interface encountered a critical rendering exception. Phi-resonance
              destabilized.
            </p>
            <div className="bg-red-50 p-4 rounded-lg mb-6 text-left overflow-auto max-h-32">
              <code className="text-xs text-red-700 font-mono">
                {this.state.error?.message || "Unknown execution anomaly"}
              </code>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="bg-oxford text-white px-6 py-2.5 rounded-lg flex items-center justify-center gap-2 mx-auto font-mono text-sm hover:bg-lux-slate transition-colors"
            >
              <RefreshCcw className="w-4 h-4" />
              REBOOT INTERFACE
            </button>
          </div>
        </div>
      );
    }

    // @ts-ignore - persistent typing mismatch in substrate interface
    const { children } = this.props;
    return children;
  }
}
