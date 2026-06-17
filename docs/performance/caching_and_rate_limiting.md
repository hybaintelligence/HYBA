# Caching and Rate Limiting Guidelines

Performance and resilience depend on efficient use of resources. This guide describes strategies for caching and rate limiting in HYBA_FULLSTACK.

## Caching strategies

1. **In‑memory response caching** – For deterministic endpoints with expensive computations (e.g., AI explanations), cache responses in memory or Redis for a short TTL. Libraries such as `fastapi-cache2` can decorate endpoints:

   ```python
   from fastapi_cache import FastAPICache
   from fastapi_cache.backends.redis import RedisBackend
   from fastapi_cache.decorator import cache

   @cache(expire=60)
   async def expensive_api_call(params: dict) -> dict:
       ...
   ```

2. **Data caching** – Cache database query results or computation outputs in Redis or memcached. Use a clear key schema (`experiments:<id>`) and set appropriate TTLs to ensure consistency.

3. **Client‑side caching** – For static assets or infrequently changing configuration, leverage HTTP cache headers (`Cache-Control: public, max-age=3600`) so that browsers and CDNs serve cached responses.

## Rate limiting

To protect the API from abuse and prevent resource exhaustion, implement rate limiting at multiple layers:

1. **Application layer** – Use middleware such as `slowapi` or `fastapi-limiter` to limit requests per IP or API key. For example:

   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
   ```

2. **API gateway / reverse proxy** – Configure Nginx, Traefik or an API gateway to enforce request quotas and burst limits. This offloads work from the application and provides a first line of defence.

3. **Per‑user limits** – Use JWT claims or API keys to assign per‑user or per‑account quotas, and track usage in Redis or your database.

Proper caching and rate limiting improve latency, reduce backend load and mitigate denial‑of‑service attacks. Review usage patterns regularly and tune strategies accordingly.
