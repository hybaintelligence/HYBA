# Pool Connection Monitoring and Alerting

## Purpose
This document defines monitoring and alerting procedures for Stratum mining pool connections to ensure operational continuity and rapid issue detection.

## Monitoring Metrics

### Connection Status Metrics
- **Pool Connection State**: connected/disconnected/connecting/error
- **Connection Uptime**: Time since last successful connection
- **Reconnection Attempts**: Number of reconnection attempts
- **Connection Latency**: Round-trip time to pool
- **Protocol Version**: Stratum v1 or v2 in use

### Performance Metrics
- **Shares Submitted**: Total shares submitted to pool
- **Shares Accepted**: Number of accepted shares
- **Shares Rejected**: Number of rejected shares
- **Rejection Rate**: (Rejected / Submitted) * 100
- **Stale Jobs**: Number of stale jobs received
- **Difficulty Target**: Current difficulty target from pool

### Health Metrics
- **Last Share Time**: Timestamp of last accepted share
- **Share Rate**: Shares per minute
- **Hashrate**: Calculated hashrate based on shares
- **Pool Block Height**: Current block height from pool
- **Network Difficulty**: Current network difficulty

## Alerting Thresholds

### Critical Alerts (Immediate Action Required)
- **Pool disconnected** for > 5 minutes
- **Rejection rate** > 10%
- **No shares submitted** for > 10 minutes
- **Connection latency** > 5 seconds
- **Stale job rate** > 5%
- **Protocol errors** > 5/minute

### Warning Alerts (Monitor Closely)
- **Pool disconnected** for > 2 minutes
- **Rejection rate** > 5%
- **No shares submitted** for > 5 minutes
- **Connection latency** > 2 seconds
- **Reconnection attempts** > 3 in 5 minutes

### Info Alerts (Log Only)
- **Pool reconnected** after disconnect
- **Difficulty change** detected
- **Protocol version** changed
- **Pool block height** updated

## Monitoring Implementation

### Backend Monitoring (Python)

Add pool connection monitoring to the mining backend:

```python
# In pythia_mining/stratum_client.py or similar

class PoolConnectionMonitor:
    def __init__(self):
        self.connection_failures = {}
        self.last_share_time = {}
        self.rejection_rates = {}
        self.connection_latencies = {}
        
    def record_connection_failure(self, pool_id: str):
        """Record a connection failure for a pool"""
        if pool_id not in self.connection_failures:
            self.connection_failures[pool_id] = []
        self.connection_failures[pool_id].append({
            'timestamp': time.time(),
            'error': 'Connection failed'
        })
        
        # Alert if too many failures
        recent_failures = [
            f for f in self.connection_failures[pool_id]
            if time.time() - f['timestamp'] < 300  # 5 minutes
        ]
        if len(recent_failures) >= 3:
            self.alert_critical(
                f"Pool {pool_id}: {len(recent_failures)} connection failures in 5 minutes"
            )
    
    def record_share_submission(self, pool_id: str, accepted: bool):
        """Record a share submission result"""
        if pool_id not in self.last_share_time:
            self.last_share_time[pool_id] = {'last': None, 'accepted': 0, 'rejected': 0}
        
        self.last_share_time[pool_id]['last'] = time.time()
        if accepted:
            self.last_share_time[pool_id]['accepted'] += 1
        else:
            self.last_share_time[pool_id]['rejected'] += 1
            
        # Calculate rejection rate
        total = self.last_share_time[pool_id]['accepted'] + self.last_share_time[pool_id]['rejected']
        if total > 0:
            rejection_rate = self.last_share_time[pool_id]['rejected'] / total
            if rejection_rate > 0.10:  # 10% threshold
                self.alert_critical(
                    f"Pool {pool_id}: Rejection rate {rejection_rate:.2%} exceeds 10%"
                )
    
    def check_pool_health(self, pool_id: str):
        """Check pool health and generate alerts"""
        # Check last share time
        if pool_id in self.last_share_time:
            last_share = self.last_share_time[pool_id]['last']
            if last_share and (time.time() - last_share) > 600:  # 10 minutes
                self.alert_critical(
                    f"Pool {pool_id}: No shares submitted for 10 minutes"
                )
        
        # Check connection failures
        if pool_id in self.connection_failures:
            recent_failures = [
                f for f in self.connection_failures[pool_id]
                if time.time() - f['timestamp'] < 300
            ]
            if len(recent_failures) >= 3:
                self.alert_critical(
                    f"Pool {pool_id}: {len(recent_failures)} connection failures in 5 minutes"
                )
    
    def alert_critical(self, message: str):
        """Send critical alert"""
        logger.error(f"🚨 POOL ALERT: {message}")
        # Integrate with your alerting system (PagerDuty, Slack, etc.)
        # self.send_alert_to_pagerduty(message)
        # self.send_alert_to_slack(message)
    
    def alert_warning(self, message: str):
        """Send warning alert"""
        logger.warning(f"⚠️  POOL WARNING: {message}")
```

### Frontend Monitoring (React)

Add pool status monitoring to the operator console:

```typescript
// In src/components/PoolMonitor.tsx or similar

interface PoolAlert {
  poolId: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: number;
}

export function PoolMonitor() {
  const [alerts, setAlerts] = useState<PoolAlert[]>([]);
  const [poolStatus, setPoolStatus] = useState<Record<string, any>>({});
  
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetchTelemetryData();
        const pools = response.pools?.pools || [];
        
        const newAlerts: PoolAlert[] = [];
        
        pools.forEach((pool: any) => {
          // Check connection status
          if (pool.status === 'disconnected') {
            newAlerts.push({
              poolId: pool.pool_id,
              severity: 'critical',
              message: 'Pool disconnected',
              timestamp: Date.now()
            });
          }
          
          // Check rejection rate
          const rejectionRate = pool.performance?.shares_rejected / 
                              (pool.performance?.shares_submitted || 1);
          if (rejectionRate > 0.10) {
            newAlerts.push({
              poolId: pool.pool_id,
              severity: 'critical',
              message: `Rejection rate ${(rejectionRate * 100).toFixed(1)}% exceeds 10%`,
              timestamp: Date.now()
            });
          }
          
          // Check latency
          if (pool.performance?.latency_ms > 5000) {
            newAlerts.push({
              poolId: pool.pool_id,
              severity: 'critical',
              message: `Latency ${pool.performance.latency_ms}ms exceeds 5 seconds`,
              timestamp: Date.now()
            });
          }
        });
        
        setAlerts(newAlerts);
        setPoolStatus(response.pools);
      } catch (error) {
        console.error('Failed to fetch pool status:', error);
      }
    }, 30000); // Check every 30 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="pool-monitor">
      <h3>Pool Connection Alerts</h3>
      {alerts.length === 0 ? (
        <p className="text-green-600">All pools healthy</p>
      ) : (
        <div className="alerts-list">
          {alerts.map((alert, index) => (
            <div 
              key={index}
              className={`alert alert-${alert.severity}`}
            >
              <span className="font-bold">{alert.poolId}</span>: {alert.message}
              <span className="text-xs text-gray-500">
                {new Date(alert.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

## Alerting Integration

### Prometheus Alerting Rules

```yaml
# prometheus-alerts.yml
groups:
  - name: pool_connection_alerts
    interval: 30s
    rules:
      - alert: PoolDisconnected
        expr: hyba_pool_connection_state == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pool {{ $labels.pool_id }} disconnected"
          description: "Pool {{ $labels.pool_id }} has been disconnected for more than 5 minutes"
      
      - alert: HighRejectionRate
        expr: hyba_pool_rejection_rate > 0.10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High rejection rate for pool {{ $labels.pool_id }}"
          description: "Pool {{ $labels.pool_id }} rejection rate is {{ $value | humanizePercentage }}"
      
      - alert: NoSharesSubmitted
        expr: time() - hyba_pool_last_share_timestamp > 600
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "No shares submitted to pool {{ $labels.pool_id }}"
          description: "Pool {{ $labels.pool_id }} has not submitted shares for 10 minutes"
      
      - alert: HighPoolLatency
        expr: hyba_pool_connection_latency_ms > 5000
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High latency for pool {{ $labels.pool_id }}"
          description: "Pool {{ $labels.pool_id }} latency is {{ $value }}ms"
```

### Slack Integration

```python
# In python_backend or scripts

import requests
import json

def send_slack_alert(webhook_url: str, message: str, severity: str = "warning"):
    """Send alert to Slack webhook"""
    colors = {
        "critical": "#FF0000",
        "warning": "#FFA500",
        "info": "#00FF00"
    }
    
    payload = {
        "attachments": [{
            "color": colors.get(severity, "#FFA500"),
            "title": f"HYBA Pool Alert - {severity.upper()}",
            "text": message,
            "fields": [
                {
                    "title": "Severity",
                    "value": severity,
                    "short": True
                },
                {
                    "title": "Timestamp",
                    "value": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "short": True
                }
            ]
        }]
    }
    
    requests.post(webhook_url, json=payload)
```

## Troubleshooting Pool Connection Issues

### Common Issues and Solutions

**Issue: Pool Connection Refused**
```bash
# Check pool URL and port
telnet pool.host port

# Verify credentials
# Check pool documentation for correct format

# Test with different pool
# Switch to backup pool if available
```

**Issue: High Rejection Rate**
```bash
# Check if difficulty is too high
# Verify worker name format
# Check if pool has changed requirements
# Review pool status page for known issues
```

**Issue: No Shares Being Submitted**
```bash
# Check if mining is actually running
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status

# Check quantum solver status
# Verify PULVINI manifold is operational
# Review backend logs for errors
```

**Issue: Intermittent Disconnections**
```bash
# Check network stability
# Verify firewall rules
# Check if pool has connection limits
# Review Stratum protocol version compatibility
```

## Pool Switching Procedure

### Manual Pool Switch
```bash
# Disconnect from current pool
curl -X POST http://127.0.0.1:3000/api/mining/disconnect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Switch to backup pool
curl -X POST http://127.0.0.1:3000/api/mining/switch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pool_id": "backup_pool_id",
    "capacity_ehs": 1.0,
    "switch": true
  }'

# Verify connection
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status
```

### Automatic Pool Failover
```python
# Implement automatic failover in backend

class PoolFailoverManager:
    def __init__(self, pool_manager):
        self.pool_manager = pool_manager
        self.primary_pool = None
        self.backup_pools = []
        self.failover_threshold = 3  # failures before failover
        self.failure_count = {}
        
    def set_primary_pool(self, pool_id: str):
        self.primary_pool = pool_id
        self.failure_count[pool_id] = 0
        
    def add_backup_pool(self, pool_id: str):
        self.backup_pools.append(pool_id)
        
    def handle_pool_failure(self, pool_id: str):
        """Handle pool failure and trigger failover if needed"""
        if pool_id not in self.failure_count:
            self.failure_count[pool_id] = 0
            
        self.failure_count[pool_id] += 1
        
        if pool_id == self.primary_pool and \
           self.failure_count[pool_id] >= self.failover_threshold:
            logger.critical(f"Primary pool {pool_id} failed {self.failover_threshold} times, initiating failover")
            self.initiate_failover()
    
    def initiate_failover(self):
        """Switch to backup pool"""
        for backup_pool in self.backup_pools:
            try:
                logger.info(f"Attempting failover to {backup_pool}")
                self.pool_manager.switch_pool(backup_pool)
                logger.info(f"Successfully failed over to {backup_pool}")
                self.primary_pool = backup_pool
                self.failure_count[backup_pool] = 0
                return True
            except Exception as e:
                logger.error(f"Failed to switch to {backup_pool}: {e}")
        
        logger.critical("All backup pools failed, manual intervention required")
        return False
```

## Monitoring Dashboard Queries

### Grafana Dashboard Queries

```promql
# Pool Connection Status
sum(hyba_pool_connection_state) by (pool_id)

# Rejection Rate by Pool
rate(hyba_pool_shares_rejected[5m]) / rate(hyba_pool_shares_submitted[5m])

# Share Rate by Pool
rate(hyba_pool_shares_accepted[5m]) by (pool_id)

# Pool Latency
hyba_pool_connection_latency_ms by (pool_id)

# Hashrate by Pool
hyba_pool_hashrate by (pool_id)

# Pool Uptime
time() - hyba_pool_connection_start_timestamp by (pool_id)
```

## Maintenance Procedures

### Pool Credential Rotation
```bash
# 1. Update credentials in secret manager
# 2. Disconnect from pool
curl -X POST http://127.0.0.1:3000/api/mining/disconnect \
  -H "Authorization: Bearer $TOKEN"

# 3. Update pool configuration with new credentials
curl -X POST http://127.0.0.1:3000/api/mining/configure \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pool_id": "pool_id",
    "username": "new_username",
    "password": "new_password"
  }'

# 4. Reconnect to pool
curl -X POST http://127.0.0.1:3000/api/mining/switch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pool_id": "pool_id",
    "switch": true
  }'

# 5. Verify connection and share submission
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status
```

### Pool Maintenance Window
- Coordinate with pool operator if possible
- Schedule during low-hashrate periods
- Have backup pool ready
- Monitor closely after reconnection
- Document any issues

## Emergency Contacts

- Pool Operator Support: [CONTACT]
- Mining Operations Team: [CONTACT]
- On-call Engineering: [CONTACT]
- Network Operations: [CONTACT]
