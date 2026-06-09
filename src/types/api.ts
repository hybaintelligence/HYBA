export interface PingResponse {
  latency_ms: number;
  status: "healthy" | "unhealthy" | "degraded";
  timestamp: string;
}

export interface HashrateHistoryItem {
  timestamp: string;
  hashrate: number; // in Sol/s, H/s, etc.
}

export interface HashrateResponse {
  current_hashrate: number;
  history: HashrateHistoryItem[];
  pool_coherence: number;
}

export interface ConnectionResponse {
  connected: boolean;
  last_sync: string; // ISO timestamp
  server_load?: number;
  active_modules: string[];
}
