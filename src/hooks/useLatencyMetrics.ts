import { useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "hyba_latency_history";

export interface LatencyPoint {
  time: string;
  latency: number;
}

// Centralized static state to share across all hook visualizer instances
const globalListeners: Set<() => void> = new Set();
let globalIsConnected = true;
let globalLatencyMs = 0;
let globalIsToastDismissed = false;
let globalLatencyHistory: LatencyPoint[] = [];

// Initialize history from sessionStorage symmetrically
try {
  const stored = sessionStorage.getItem(STORAGE_KEY);
  if (stored) {
    globalLatencyHistory = JSON.parse(stored);
  }
} catch {
  globalLatencyHistory = [];
}

function notifyListeners() {
  globalListeners.forEach((listener) => listener());
}

export function recordPing(latency: number, success: boolean) {
  if (!success) {
    globalIsConnected = false;
  } else {
    globalIsConnected = true;
    globalLatencyMs = latency;
    const now = new Date().toISOString().substring(11, 19);
    globalLatencyHistory = [...globalLatencyHistory, { time: now, latency }].slice(-50); // Exact 50 points
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(globalLatencyHistory));
    } catch (e) {
      console.error("Error writing to sessionStorage:", e);
    }
  }
  notifyListeners();
}

// Singleton Background Ping Loop with same-origin bridge defaults.
// Frontend code should call the Node bridge on the current origin; the bridge owns
// backend routing to FastAPI via PULVINI_BACKEND_URL. This keeps the browser SPA
// and backend API off separate pages/ports for UAT unless an operator explicitly
// supplies a relative or absolute override.
let pingIntervalId: ReturnType<typeof setInterval> | null = null;

function normalizeBackendBaseUrl(value: string | undefined): string {
  const trimmed = value?.trim();
  if (!trimmed) return "/api";
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
}

export function getFrontendBackendBaseUrl(): string {
  const metaEnv = (import.meta as unknown as { env?: Record<string, string> }).env || {};
  return normalizeBackendBaseUrl(metaEnv.VITE_HYBA_BACKEND_URL || metaEnv.VITE_PULVINI_BACKEND_URL);
}

export function ensurePingInterval() {
  if (pingIntervalId) return;

  const runPing = async () => {
    const start = performance.now();
    try {
      const backendUrl = getFrontendBackendBaseUrl();
      const response = await fetch(`${backendUrl}/health`);
      const latency = performance.now() - start;
      recordPing(latency, response.ok);
    } catch {
      recordPing(performance.now() - start, false);
    }
  };

  runPing();
  pingIntervalId = setInterval(runPing, 30000); // 30s core keep-alive ping
}

export function useLatencyMetrics() {
  const [, setTick] = useState(0);

  useEffect(() => {
    const forceUpdate = () => setTick((tick) => tick + 1);
    globalListeners.add(forceUpdate);
    ensurePingInterval();

    return () => {
      globalListeners.delete(forceUpdate);
    };
  }, []);

  const setIsToastDismissed = useCallback((val: boolean) => {
    globalIsToastDismissed = val;
    notifyListeners();
  }, []);

  return {
    isConnected: globalIsConnected,
    latencyMs: globalLatencyMs,
    latencyHistory: globalLatencyHistory,
    isToastDismissed: globalIsToastDismissed,
    setIsToastDismissed,
    recordPing,
  };
}
