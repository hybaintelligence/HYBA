import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'hyba_latency_history';

export interface LatencyPoint {
  time: string;
  latency: number;
}

// Centralized static state to share across all hook visualizer instances
let globalListeners: Set<() => void> = new Set();
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
  globalListeners.forEach(listener => listener());
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
      console.error('Error writing to sessionStorage:', e);
    }
  }
  notifyListeners();
}

// Singleton Background Ping Loop with environment process variables support
let pingIntervalId: any = null;

export function ensurePingInterval() {
  if (pingIntervalId) return;

  const runPing = async () => {
    const start = performance.now();
    try {
      const metaEnv = (import.meta as any).env || {};
      const backendUrl = (typeof process !== "undefined" && process.env?.HYBA_BACKEND_URL) || 
                         metaEnv.VITE_HYBA_BACKEND_URL || 
                         metaEnv.VITE_PULVINI_BACKEND_URL || 
                         "http://127.0.0.1:8000/api";
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
    const forceUpdate = () => setTick(tick => tick + 1);
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
    recordPing
  };
}
