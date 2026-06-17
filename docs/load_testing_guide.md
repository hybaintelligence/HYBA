# Load Testing Guide

This guide describes how to conduct load testing on the HYBA Genesis API to validate performance and scalability before production deployment.

## Objectives

- Measure baseline performance (latency, throughput) under expected and peak loads.  
- Identify bottlenecks in the API and mining core.  
- Validate that rate limits and CPU/memory limits protect the service.  
- Ensure heavy background tasks do not block the event loop.

## Tools

We recommend using one of the following open‑source tools:

### Locust (Python)

Locust allows you to define user behaviour as Python coroutines and generate HTTP traffic.

```bash
# Install locust in a virtual environment
pip install locust

# Write a locustfile.py
from locust import HttpUser, task

class ApiUser(HttpUser):
    @task
    def health(self):
        self.client.get("/health")

    @task
    def mining_status(self):
        self.client.get("/api/mining/status")

# Run the test targeting your backend
locust -f locustfile.py --host=http://localhost:3001 --users=100 --spawn-rate=10
```

Observe response times and error rates in the Locust UI.  Gradually increase users until latency exceeds acceptable thresholds.

### k6 (JavaScript)

k6 is a modern load testing tool with a JavaScript DSL and CI‑friendly output.

```bash
npm install -g k6

# Write a script.js
import http from 'k6/http';
import { sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 50 },  // ramp-up
    { duration: '5m', target: 50 },  // steady
    { duration: '2m', target: 0 },   // ramp-down
  ],
};

export default function () {
  http.get('http://localhost:3001/api/health/ready');
  http.get('http://localhost:3001/api/mining/status');
  sleep(1);
}

# Run the test
k6 run script.js
```

The summary output provides requests per second, response time percentiles, and error counts.  Export results to Prometheus for further analysis.

## Best practices

- **Use realistic scenarios**: Simulate patterns of usage that reflect actual operator interactions and mining load.
- **Start small, scale gradually**: Identify failure points and adjust concurrency limits or resource allocations accordingly.
- **Isolate components**: Load test the API separately from the mining core to pinpoint bottlenecks.
- **Automate tests**: Integrate load testing into CI pipelines to catch performance regressions early.
- **Document outcomes**: Record metrics and observations; update capacity planning documents and adjust rate limits.

For sustained load, consider using dedicated performance test environments that mirror production resource allocations.
