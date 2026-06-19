import React from "react";
import { AlertCircle, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface NetworkToastProps {
  isConnected: boolean;
  latencyMs: number;
  isDismissed: boolean;
  onDismiss: () => void;
}

export const NetworkToast: React.FC<NetworkToastProps> = ({
  isConnected,
  latencyMs,
  isDismissed,
  onDismiss,
}) => {
  const isHighLatency = latencyMs > 500;
  const showToast = (!isConnected || isHighLatency) && !isDismissed;

  return (
    <AnimatePresence>
      {showToast && (
        <motion.div
          initial={{ opacity: 0, y: -20, x: "-50%" }}
          animate={{ opacity: 1, y: 0, x: "-50%" }}
          exit={{ opacity: 0, y: -20, x: "-50%" }}
          className="fixed top-6 left-1/2 z-50 flex items-start gap-3 bg-red-900 border border-red-500 rounded-lg p-4 text-white shadow-xl max-w-md w-full"
        >
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-mono font-bold text-sm">
              {!isConnected
                ? "Connection Lost to HYBA Unified Backend"
                : "High Network Latency Detected"}
            </h4>
            <p className="font-sans text-xs text-red-200 mt-1">
              {!isConnected
                ? "The connection to the core telemetry engine has been severed. Please ensure the backend daemon is running."
                : `Current latency is ${latencyMs.toFixed(0)}ms. Performance may be degraded. Please close intensive background tasks.`}
            </p>
          </div>
          <button
            onClick={onDismiss}
            className="text-red-400 hover:text-white transition-colors cursor-pointer"
            aria-label="Dismiss network status"
          >
            <X className="w-4 h-4" />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
