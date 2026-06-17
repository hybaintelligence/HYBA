"""Locust load test script for HYBA Genesis API.

This script defines a simple user behaviour model for load testing the
FastAPI backend.  It issues GET requests to health and mining endpoints
with a small delay between requests.  To execute the test, run:

    locust -f load_testing/locustfile.py --host=http://localhost:3001 --users=50 --spawn-rate=5

Refer to ``docs/load_testing_guide.md`` for more details and best practices.
"""

from locust import HttpUser, task, between


class ApiUser(HttpUser):
    # Simulate think time between requests
    wait_time = between(1, 3)

    @task
    def health(self) -> None:
        """Ping the health endpoint."""
        self.client.get("/health")

    @task
    def mining_status(self) -> None:
        """Check the mining status."""
        self.client.get("/api/mining/status")

    @task
    def substrate(self) -> None:
        """Fetch substrate readiness information."""
        self.client.get("/api/substrate")
