/**
 * Pool Selector Component
 * ========================
 * 
 * Manages mining pool selection from frontend.
 * Default: Brains Pool
 * Selectable: All enabled pools
 */

import React, { useEffect, useState } from 'react';

interface PoolConfig {
  name: string;
  url: string;
  stratum_version: number;
  username?: string;
  password?: string;
  worker: string;
  priority: number;
  enabled: boolean;
  is_default: boolean;
  description?: string;
  btc_address?: string;
}

interface PoolListResponse {
  default_pool: string;
  pools: Record<string, PoolConfig>;
  timestamp: string;
}

interface PoolStatus {
  active_pool: string;
  connected: boolean;
  shares_submitted: number;
  last_share_time?: string;
  uptime_seconds: number;
}

export const PoolSelector: React.FC = () => {
  const [pools, setPools] = useState<Record<string, PoolConfig>>({});
  const [activePool, setActivePool] = useState<string>('brains');
  const [defaultPool, setDefaultPool] = useState<string>('brains');
  const [status, setStatus] = useState<PoolStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load pools on mount
  useEffect(() => {
    fetchPools();
    fetchStatus();
    
    // Poll status every 5 seconds
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchPools = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/pools/list');
      if (!response.ok) throw new Error('Failed to fetch pools');
      
      const data: PoolListResponse = await response.json();
      setPools(data.pools);
      setDefaultPool(data.default_pool);
      setActivePool(data.default_pool);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/v1/pools/status');
      if (response.ok) {
        const data: PoolStatus = await response.json();
        setStatus(data);
      }
    } catch (err) {
      // Silently fail on status fetch
    }
  };

  const switchPool = async (poolName: string) => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/pools/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pool_name: poolName }),
      });
      
      if (!response.ok) throw new Error('Failed to switch pool');
      
      setActivePool(poolName);
      setError(null);
      fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to switch pool');
    } finally {
      setLoading(false);
    }
  };

  const enabledPools = Object.entries(pools).filter(([_, config]) => config.enabled);

  return (
    <div className="pool-selector">
      <div className="pool-header">
        <h2>Mining Pool Selection</h2>
        <span className="default-badge">Default: {defaultPool.toUpperCase()}</span>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {loading && <div className="loading">Loading pools...</div>}

      <div className="pools-grid">
        {enabledPools.map(([poolName, config]) => (
          <div
            key={poolName}
            className={`pool-card ${activePool === poolName ? 'active' : ''} ${
              poolName === defaultPool ? 'default' : ''
            }`}
            onClick={() => switchPool(poolName)}
          >
            <div className="pool-name">{config.name}</div>
            <div className="pool-description">{config.description || ''}</div>
            
            <div className="pool-details">
              <div className="detail-row">
                <span className="label">URL:</span>
                <span className="value">{config.url}</span>
              </div>
              <div className="detail-row">
                <span className="label">Worker:</span>
                <span className="value">{config.worker}</span>
              </div>
              <div className="detail-row">
                <span className="label">Priority:</span>
                <span className="value">{config.priority}</span>
              </div>
            </div>

            <div className="pool-status">
              {activePool === poolName && status && (
                <>
                  <div className="status-item">
                    <span className="status-label">Shares:</span>
                    <span className="status-value">{status.shares_submitted}</span>
                  </div>
                  <div className="status-item">
                    <span className="status-label">Connected:</span>
                    <span className={`status-value ${status.connected ? 'connected' : 'disconnected'}`}>
                      {status.connected ? '✓ Yes' : '✗ No'}
                    </span>
                  </div>
                </>
              )}
            </div>

            <button
              className={`select-button ${activePool === poolName ? 'selected' : ''}`}
              disabled={loading || activePool === poolName}
            >
              {activePool === poolName ? '✓ Active' : 'Select'}
              {poolName === defaultPool && <span className="default-star">★</span>}
            </button>
          </div>
        ))}
      </div>

      <style>{`
        .pool-selector {
          padding: 20px;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          border-radius: 8px;
          color: #fff;
        }

        .pool-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 10px;
          border-bottom: 2px solid #0f3460;
        }

        .pool-header h2 {
          margin: 0;
          font-size: 24px;
          color: #00d4ff;
        }

        .default-badge {
          background: #00d4ff;
          color: #1a1a2e;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: bold;
        }

        .error-message {
          background: #ff3333;
          color: #fff;
          padding: 12px;
          border-radius: 4px;
          margin-bottom: 15px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .error-icon {
          font-size: 16px;
        }

        .loading {
          text-align: center;
          padding: 20px;
          color: #00d4ff;
        }

        .pools-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 15px;
        }

        .pool-card {
          background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
          border: 2px solid #00d4ff;
          border-radius: 8px;
          padding: 16px;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .pool-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 20px rgba(0, 212, 255, 0.2);
        }

        .pool-card.active {
          border-color: #00ff88;
          background: linear-gradient(135deg, #1a3a2e 0%, #0f3460 100%);
          box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }

        .pool-card.default {
          border-width: 3px;
        }

        .pool-name {
          font-size: 18px;
          font-weight: bold;
          color: #00d4ff;
        }

        .pool-description {
          font-size: 12px;
          color: #aaa;
          min-height: 24px;
        }

        .pool-details {
          background: rgba(0, 0, 0, 0.3);
          padding: 8px;
          border-radius: 4px;
          font-size: 12px;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          margin: 4px 0;
          gap: 8px;
        }

        .detail-row .label {
          color: #888;
          min-width: 60px;
        }

        .detail-row .value {
          color: #00d4ff;
          word-break: break-all;
          text-align: right;
        }

        .pool-status {
          display: flex;
          gap: 12px;
          font-size: 12px;
        }

        .status-item {
          display: flex;
          gap: 4px;
        }

        .status-label {
          color: #888;
        }

        .status-value {
          color: #00ff88;
          font-weight: bold;
        }

        .status-value.disconnected {
          color: #ff3333;
        }

        .select-button {
          background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
          color: #1a1a2e;
          border: none;
          padding: 10px 16px;
          border-radius: 4px;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          font-size: 14px;
        }

        .select-button:hover:not(:disabled) {
          background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
          transform: scale(1.05);
        }

        .select-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .select-button.selected {
          background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
          color: #1a1a2e;
        }

        .default-star {
          color: #ffaa00;
          font-size: 16px;
        }
      `}</style>
    </div>
  );
};

export default PoolSelector;
