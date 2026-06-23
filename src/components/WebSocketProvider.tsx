/**
 * WebSocket Provider for Real-Time Telemetry
 * 
 * Replaces 15s polling with live WebSocket updates.
 * Falls back to polling if WebSocket unavailable.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { TelemetryData } from '../apiClient';

interface WebSocketContextValue {
  telemetry: TelemetryData | null;
  isConnected: boolean;
  error: string | null;
  reconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
}

interface WebSocketProviderProps {
  children: React.ReactNode;
  enabled?: boolean;
  fallbackPollInterval?: number;
}

export function WebSocketProvider({
  children,
  enabled = true,
  fallbackPollInterval = 15000,
}: WebSocketProviderProps) {
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (!enabled) return;

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const ws = new WebSocket(`${protocol}//${host}/ws/telemetry`);

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setError(null);
        
        // Stop polling if active
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setTelemetry(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Fallback to polling
        startPolling();

        // Attempt reconnect after delay
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError(err instanceof Error ? err.message : 'WebSocket unavailable');
      startPolling();
    }
  }, [enabled]);

  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return;

    console.log('📡 Fallback to HTTP polling');
    
    const poll = async () => {
      try {
        const response = await fetch('/api/telemetry');
        const data = await response.json();
        setTelemetry(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Telemetry fetch failed');
      }
    };

    poll(); // Initial fetch
    pollIntervalRef.current = setInterval(poll, fallbackPollInterval);
  }, [fallbackPollInterval]);

  const reconnect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    // Reconnect
    connect();
  }, [connect]);

  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      startPolling();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [enabled, connect, startPolling]);

  const value: WebSocketContextValue = {
    telemetry,
    isConnected,
    error,
    reconnect,
  };

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
}
