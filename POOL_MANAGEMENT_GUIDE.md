# Mining Pool Management System
## Brains Pool Default + Frontend Selection

**Date**: June 15, 2026  
**Status**: ✓ DEPLOYED  

---

## Overview

The pool management system allows operators to:
- Start with **Brains Pool** as the default
- Switch between enabled pools from the **frontend UI**
- Track pool statistics and share submissions
- Programmatically manage pool configuration via REST API

---

## Architecture

### 1. Configuration Layer (`config/mining_pools_live.json`)

```json
{
  "default_pool": "brains",
  "pools": {
    "brains": {
      "name": "Brains Pool",
      "url": "stratum+tcp://pool.brains.btc:3333",
      "is_default": true,
      "enabled": true,
      "priority": 1,
      "description": "Brains mining pool - primary choice"
    },
    "ckpool": {
      "name": "CKPool",
      "enabled": true,
      "priority": 2
    },
    "nicehash": {
      "name": "NiceHash",
      "enabled": true,
      "priority": 3
    },
    "slushpool": {
      "name": "SlushPool",
      "enabled": false,
      "priority": 4,
      "description": "SlushPool - optional"
    }
  }
}
```

**Pool Configuration Fields**:
- `name` — Display name in UI
- `url` — Stratum server endpoint
- `stratum_version` — Protocol version (1 or 2)
- `enabled` — Selectable from frontend (true/false)
- `is_default` — Marks Brains as default (true for brains)
- `priority` — Selection order
- `description` — UI tooltip/description
- `btc_address` — Bitcoin address for payouts
- `worker` — Worker name (hendrix_phi)

---

## REST API Endpoints

### Pool Management API
**Base URL**: `/api/v1/pools`

#### 1. List All Pools
```http
GET /api/v1/pools/list
```

**Response**:
```json
{
  "default_pool": "brains",
  "pools": {
    "brains": {
      "name": "Brains Pool",
      "url": "stratum+tcp://pool.brains.btc:3333",
      "enabled": true,
      "is_default": true,
      "priority": 1
    }
  },
  "timestamp": "2026-06-15T13:53:42Z"
}
```

#### 2. Get Default Pool
```http
GET /api/v1/pools/default
```

**Response**:
```json
{
  "pool_name": "brains",
  "pool_config": {
    "name": "Brains Pool",
    "url": "stratum+tcp://pool.brains.btc:3333",
    "is_default": true
  },
  "timestamp": "2026-06-15T13:53:42Z"
}
```

#### 3. Get Currently Active Pool
```http
GET /api/v1/pools/current
```

**Response**:
```json
{
  "active_pool": "brains",
  "pool_config": {...},
  "is_connected": true,
  "timestamp": "2026-06-15T13:53:42Z"
}
```

#### 4. Get Enabled Pools (Frontend Selection)
```http
GET /api/v1/pools/enabled
```

**Response** (only pools with `enabled: true`):
```json
{
  "count": 3,
  "enabled_pools": {
    "brains": {...},
    "ckpool": {...},
    "nicehash": {...}
  },
  "default": "brains",
  "timestamp": "2026-06-15T13:53:42Z"
}
```

#### 5. Switch Active Pool
```http
POST /api/v1/pools/switch
Content-Type: application/json

{
  "pool_name": "ckpool"
}
```

**Response**:
```json
{
  "status": "switched",
  "new_active_pool": "ckpool",
  "pool_config": {...},
  "timestamp": "2026-06-15T13:53:42Z"
}
```

#### 6. Get Pool Connection Status
```http
GET /api/v1/pools/status
```

**Response**:
```json
{
  "active_pool": "brains",
  "connected": true,
  "shares_submitted": 42,
  "last_share_time": "2026-06-15T13:52:10Z",
  "uptime_seconds": 3650.5
}
```

#### 7. Report Share Submission
```http
POST /api/v1/pools/report-share
```

**Response**:
```json
{
  "status": "recorded",
  "shares_submitted": 43,
  "timestamp": "2026-06-15T13:53:42Z"
}
```

#### 8. Pool Health Check
```http
GET /api/v1/pools/health
```

**Response**:
```json
{
  "status": "healthy",
  "default_pool": "brains",
  "total_pools": 5,
  "enabled_pools": 3,
  "timestamp": "2026-06-15T13:53:42Z"
}
```

---

## Frontend Component: PoolSelector

### Location
`src/components/PoolSelector.tsx`

### Features
- **Default Display**: Brains Pool is marked as default (★ badge)
- **Pool Cards**: Visual cards for each enabled pool
- **Live Status**: Shows active pool, shares submitted, connection status
- **One-Click Switch**: Click to switch pools in real-time
- **Auto-refresh**: Status updates every 5 seconds
- **Error Handling**: User-friendly error messages

### Usage

#### Import
```typescript
import { PoolSelector } from './components/PoolSelector';
```

#### Add to Page
```tsx
export default function MiningDashboard() {
  return (
    <div className="dashboard">
      <PoolSelector />
      {/* other components */}
    </div>
  );
}
```

### UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  Mining Pool Selection          Default: BRAINS         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   BRAINS     │  │   CKPOOL     │  │  NICEHASH    │  │
│  │   ★ Default  │  │              │  │              │  │
│  │              │  │              │  │              │  │
│  │ URL: ...     │  │ URL: ...     │  │ URL: ...     │  │
│  │ Worker: ...  │  │ Worker: ...  │  │ Worker: ...  │  │
│  │              │  │              │  │              │  │
│  │ Shares: 42   │  │              │  │              │  │
│  │ Connected ✓  │  │              │  │              │  │
│  │              │  │              │  │              │  │
│  │ [✓ Active]   │  │  [Select]    │  │  [Select]    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Backend Integration

### File: `python_backend/hyba_genesis_api/api/pool_management.py`

**Imports**:
```python
from hyba_genesis_api.api import pool_management

# In main.py:
app.include_router(pool_management.router)
```

**Global State Tracking**:
- `_active_pool` — Currently active pool (defaults to "brains")
- `_pool_stats` — Share count, last submission time, uptime

**Functions**:
- `load_pools_config()` — Load JSON config
- `get_default_pool()` — Get default pool name
- `switch_pool()` — Switch active pool

---

## Deployment Configuration

### Default Pool: Brains

**On Startup**:
```bash
# Backend automatically loads config/mining_pools_live.json
# Default pool is set to "brains"
# Connected via: stratum+tcp://pool.brains.btc:3333
```

### Pool Status

| Pool | Enabled | Priority | Default |
|------|---------|----------|---------|
| **Brains** | ✓ Yes | 1 | ★ Yes |
| CKPool | ✓ Yes | 2 | — |
| NiceHash | ✓ Yes | 3 | — |
| SlushPool | ✗ No | 4 | — |
| Hiveon | ✗ No | 5 | — |

### Adding New Pools

Edit `config/mining_pools_live.json`:

```json
{
  "pools": {
    "new_pool": {
      "name": "New Pool Name",
      "url": "stratum+tcp://...:3333",
      "stratum_version": 1,
      "enabled": true,
      "priority": 6,
      "description": "Optional description"
    }
  }
}
```

Then restart backend. Frontend will auto-refresh pool list.

---

## Workflow: Switching Pools

### User Perspective
1. Open Mining Dashboard
2. See **PoolSelector** component with enabled pools
3. Brains Pool shows as default (★)
4. Click "Select" on any other enabled pool
5. Mining engine switches immediately
6. Status shows new active pool and share count

### Backend Workflow
```
User clicks "Select" on pool "ckpool"
    ↓
Frontend: POST /api/v1/pools/switch
    ↓
Backend: Validate pool_name in config
    ↓
Backend: Check if pool is enabled
    ↓
Backend: Set _active_pool = "ckpool"
    ↓
Backend: Return confirmation + pool config
    ↓
Frontend: Update UI, show active pool
    ↓
Mining engine: Connect to new pool (via unified_mining_engine)
```

---

## Configuration Examples

### Using Brains Pool (Default)
```json
{
  "default_pool": "brains",
  "pools": {
    "brains": {
      "name": "Brains Pool",
      "url": "stratum+tcp://pool.brains.btc:3333",
      "stratum_version": 1,
      "enabled": true,
      "is_default": true,
      "priority": 1
    }
  }
}
```

### Multiple Selectable Pools
```json
{
  "default_pool": "brains",
  "pools": {
    "brains": {"enabled": true, "priority": 1},
    "ckpool": {"enabled": true, "priority": 2},
    "nicehash": {"enabled": true, "priority": 3},
    "test_pool": {"enabled": false, "priority": 99}
  }
}
```

---

## API Integration with Mining Engine

### Share Reporting

When a share is submitted:

```python
# In unified_mining_engine.py
async def on_share_result(self, nonce: int, accepted: bool):
    if accepted:
        # Report to pool management API
        await http_client.post(
            "/api/v1/pools/report-share",
            json={"nonce": nonce}
        )
```

### Pool Switching in Mining Engine

```python
# Switch active pool on request
def set_active_pool(self, pool_name: str):
    self.config = self.load_pool_config(pool_name)
    self.reconnect()  # Reconnect to new pool
```

---

## Monitoring & Troubleshooting

### Check Current Pool
```bash
curl http://localhost:3001/api/v1/pools/current
```

### List All Pools
```bash
curl http://localhost:3001/api/v1/pools/list
```

### Get Status
```bash
curl http://localhost:3001/api/v1/pools/status
```

### Manual Pool Switch
```bash
curl -X POST http://localhost:3001/api/v1/pools/switch \
  -H "Content-Type: application/json" \
  -d '{"pool_name": "ckpool"}'
```

---

## Security Considerations

### Pool Credentials
- Stored in `config/mining_pools_live.json` (local file)
- NOT sent to frontend (API returns config without passwords)
- Passwords always set to "x" (Stratum protocol standard)

### API Access
- All pool endpoints require backend authentication
- Recommend reverse proxy with TLS/SSL
- Use network-level firewall for sensitive endpoints

### Configuration Validation
- Pool name validation on switch request
- Enabled flag checked before switching
- Invalid pool requests return 404/400

---

## Future Enhancements

1. **Pool Statistics Dashboard**
   - Graphical share submission rate
   - Pool uptime trends
   - Earnings per pool

2. **Automatic Pool Failover**
   - Primary pool down? Switch to secondary
   - Configurable failover thresholds

3. **Pool Performance Comparison**
   - Compare share acceptance rates
   - Suggest best performing pool

4. **Pool Custom Configuration**
   - Edit pool settings from frontend
   - Save custom worker names per pool

---

## Files

### Configuration
- `config/mining_pools_live.json` — Pool configuration (Brains default)

### Backend
- `python_backend/hyba_genesis_api/api/pool_management.py` — REST API (8 endpoints)
- `python_backend/hyba_genesis_api/main.py` — Router integration ✓

### Frontend
- `src/components/PoolSelector.tsx` — UI component for pool selection

### Documentation
- `POOL_MANAGEMENT_GUIDE.md` — This file

---

## Summary

✓ **Default**: Brains Pool (automatically on startup)  
✓ **Frontend Selection**: Drop-down/cards for enabled pools  
✓ **Real-time Switching**: Click to change pools instantly  
✓ **Status Tracking**: Live share count and connection status  
✓ **API-driven**: 8 REST endpoints for full management  
✓ **Production Ready**: Deployed and integrated

---

**Status**: ✓ COMPLETE  
**Version**: 1.0  
**Last Updated**: June 15, 2026
