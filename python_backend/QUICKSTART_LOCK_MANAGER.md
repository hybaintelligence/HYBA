# Distributed Lock Manager - Quick Start

## Installation

1. **Ensure Redis is running:**
   ```bash
   docker run -d -p 6379:6379 redis:latest
   # or use your Kubernetes Redis service
   ```

2. **Add dependencies to your project:**
   ```bash
   pip install redis==5.0.1 aioredis==2.0.1
   ```

## 5-Minute Quick Start

### 1. Initialize the Lock Manager

```python
from pythia_mining.distributed_lock_manager import DistributedLockManager

lock_manager = DistributedLockManager(
    redis_url="redis://localhost:6379",  # Your Redis URL
    default_ttl=30,                       # Lock expires after 30 seconds
    enable_metrics=True,                  # Enable metrics collection
)
```

### 2. Use with Context Manager (Recommended)

```python
async def update_critical_resource():
    # Acquire lock automatically on entry, release on exit
    async with lock_manager.with_lock("my_resource_lock", ttl=30):
        # Only one pod can execute this at a time
        print("Critical section protected!")
        await modify_resource()
        # Lock automatically released here, even if exception occurs
```

### 3. Manual Acquire/Release

```python
from pythia_mining.distributed_lock_manager import LockAcquisitionError

async def manual_locking():
    try:
        # Acquire lock
        token = await lock_manager.acquire("my_lock", ttl=30)
        
        # Do work while holding lock
        await critical_work()
        
    except LockAcquisitionError as e:
        print(f"Could not get lock: {e}")
    finally:
        # Always release
        await lock_manager.release("my_lock", token.token)
```

### 4. Monitor Lock Performance

```python
# Get detailed metrics
metrics = lock_manager.get_lock_metrics()

print(f"Success rate: {metrics['success_rate']:.1f}%")
print(f"Active locks: {metrics['active_locks_count']}")
print(f"Contention: {metrics['contention_ratio']:.2f}")
print(f"Avg wait: {metrics['average_wait_time_ms']:.1f}ms")
```

## Common Use Cases

### State File Protection

```python
async with lock_manager.with_lock("state_file", ttl=30):
    state = load_state()
    state['counter'] += 1
    save_state(state)
```

### Database Synchronization

```python
async with lock_manager.with_lock("db_sync", ttl=60):
    primary_data = await fetch_primary()
    replicas = await fetch_replicas()
    if sync_needed(primary_data, replicas):
        await sync_replicas(primary_data)
```

### Batch Job Coordination

```python
async with lock_manager.with_lock("batch_job", ttl=300):
    if not job_running():
        start_batch_job()
```

## Troubleshooting

### "Lock acquisition timeout"
- Increase TTL: `ttl=60` instead of `ttl=30`
- Reduce operation time in critical section
- Check Redis connection: `redis-cli ping`

### "Redis connection refused"
- Verify Redis is running: `docker ps | grep redis`
- Check connection string: Should be `redis://host:port` or `redis://host:port/0`
- Check firewall rules if using remote Redis

### High contention warnings in metrics
- Make critical sections smaller
- Reduce lock TTL to match actual operation time
- Consider sharding by resource ID

## API Reference

### Core Methods

| Method | Purpose |
|--------|---------|
| `acquire(key, ttl)` | Acquire a lock, returns token |
| `release(key, token)` | Release a lock (token prevents mistakes) |
| `with_lock(key, ttl)` | Context manager for automatic cleanup |
| `get_lock_metrics()` | Get contention and performance metrics |

### Exception Types

| Exception | Meaning |
|-----------|---------|
| `LockAcquisitionError` | Couldn't get lock (timeout/deadlock) |
| `LockReleaseError` | Couldn't release lock |
| `DeadlockDetectedError` | Lock held longer than threshold |

## Real-World Example: Pool Response Synchronization

```python
from pythia_mining.lock_manager_integration_example import (
    PoolResponseHistorySynchronizer,
    PoolResponse,
)
from datetime import datetime

# Initialize
sync = PoolResponseHistorySynchronizer(lock_manager, Path("pool_responses.json"))

# Add responses from multiple workers
async def process_pool_responses(responses):
    try:
        # Lock ensures only one pod writes at a time
        success = await sync.add_responses([
            PoolResponse(
                pool_id="pool1",
                timestamp=datetime.now().timestamp(),
                response_data={"shares": 100},
                worker_id="worker1",
            )
            for response in responses
        ])
        
        if success:
            print("Responses synchronized across replicas")
    except LockAcquisitionError:
        print("Could not synchronize - try again later")
```

## Advanced: Enable Real Redis Operations

By default, the lock manager uses mock Redis operations for testing. To use real Redis:

1. Install Redis client:
   ```bash
   pip install aioredis==2.0.1
   ```

2. Update `distributed_lock_manager.py` to use real operations (replace `_redis_*` methods)

See `distributed_lock_manager_redis_impl.py` for reference implementation.

## Performance Tips

1. **Keep locks short:** Sub-second operations are ideal
2. **Use specific lock names:** `"state_lock"` not `"lock1"`
3. **Monitor metrics:** High contention suggests design issues
4. **Set appropriate TTL:** Should match actual operation time
5. **Handle errors:** Always catch and log lock failures

## Next Steps

1. Review `DISTRIBUTED_LOCK_MANAGER_GUIDE.md` for detailed documentation
2. Check `test_distributed_lock_manager.py` for more examples
3. Look at `lock_manager_integration_example.py` for HYBA-specific patterns
4. Enable metrics integration with your monitoring stack

## Support

- Check logs for detailed error messages
- Review metrics with `get_lock_metrics()`
- Verify Redis connectivity: `redis-cli ping`
- Enable debug logging: `log_level="DEBUG"`
