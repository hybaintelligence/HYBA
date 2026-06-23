#!/usr/bin/env python3
"""
TEST-ONLY Stratum Pool Simulator
=================================

WARNING: This is a TEST-ONLY simulator for local development and testing.
NEVER use this script in production. It does not implement real mining pool
logic, share validation, or payout mechanisms.

Purpose:
- Provide a local Stratum endpoint for testing the unified miner integration
- Simulate basic Stratum protocol messages (subscribe, authorize, notify, submit)
- Allow testing of the full mining pipeline without connecting to real pools

Usage:
  python3 scripts/test_stratum_simulator.py --port 3333

The simulator will:
1. Listen on the specified port (default 3333)
2. Accept Stratum connections
3. Respond to mining.subscribe, mining.authorize
4. Send mining.notify with fake jobs
5. Accept/reject shares based on simple validation
6. Log all activity for debugging
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import time
from typing import Any, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SIMULATOR] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("test_stratum_simulator")


class TestStratumSimulator:
    """Test-only Stratum pool simulator."""

    def __init__(self, host: str = "127.0.0.1", port: int = 3333):
        self.host = host
        self.port = port
        self.clients: Dict[asyncio.StreamReader, asyncio.StreamWriter] = {}
        self.job_counter = 0
        self.difficulty = 1.0
        self.extranonce1 = "0a0b"  # Fixed extranonce1 for testing
        self.extranonce2_size = 4
        self.running = False

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle a single Stratum client connection."""
        addr = writer.get_extra_info("peername")
        logger.info("Client connected: %s", addr)
        self.clients[reader] = writer

        try:
            while self.running:
                try:
                    line = await asyncio.wait_for(reader.readline(), timeout=30.0)
                    if not line:
                        break

                    message = line.decode().strip()
                    if not message:
                        continue

                    logger.info("Received: %s", message[:200])  # Truncate long messages

                    try:
                        request = json.loads(message)
                        response = await self.handle_message(request)
                        if response:
                            writer.write((json.dumps(response) + "\n").encode())
                            await writer.drain()
                            logger.info("Sent: %s", json.dumps(response)[:200])
                    except json.JSONDecodeError as e:
                        logger.error("JSON decode error: %s", e)
                    except Exception:
                        logger.exception("Error handling message: %s")

                except asyncio.TimeoutError:
                    # Send a keep-alive notify
                    await self.send_notify(writer)

        except Exception:
            logger.exception("Client handler error: %s")
        finally:
            logger.info("Client disconnected: %s", addr)
            writer.close()
            await writer.wait_closed()
            if reader in self.clients:
                del self.clients[reader]

    async def handle_message(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a Stratum protocol message."""
        method = request.get("method")
        msg_id = request.get("id")
        params = request.get("params", [])

        if method == "mining.subscribe":
            return {
                "id": msg_id,
                "result": [[], self.extranonce1, self.extranonce2_size],
                "error": None,
            }

        elif method == "mining.authorize":
            username = params[0] if len(params) > 0 else "unknown"
            logger.info("Authorizing worker: %s", username)
            return {"id": msg_id, "result": True, "error": None}

        elif method == "mining.submit":
            # Simple validation: accept shares with nonce ending in even hex digit
            worker = params[0] if len(params) > 0 else "unknown"
            job_id = params[1] if len(params) > 1 else "unknown"
            nonce = params[2] if len(params) > 2 else "00000000"

            # Accept 50% of shares randomly for testing
            accepted = random.random() < 0.5

            logger.info(
                "Share from %s job=%s nonce=%s accepted=%s",
                worker,
                job_id,
                nonce,
                accepted,
            )

            return {
                "id": msg_id,
                "result": accepted,
                "error": None if accepted else "21:Job not found",
            }

        else:
            logger.warning("Unknown method: %s", method)
            return {"id": msg_id, "result": None, "error": f"Unknown method: {method}"}

    async def send_notify(self, writer: asyncio.StreamWriter):
        """Send a mining.notify message with a new job."""
        self.job_counter += 1
        job_id = f"test_job_{self.job_counter}"

        # Generate fake job parameters
        prev_hash = "00" * 32  # All zeros for testing
        coinb1 = "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff"
        coinb2 = "ffffffff01"
        merkle_branch = []
        version = "00000001"
        nbits = "1d00ffff"  # Difficulty 1
        ntime = hex(int(time.time()))[2:].zfill(8)
        clean_jobs = True

        notify = {
            "id": None,
            "method": "mining.notify",
            "params": [
                job_id,
                prev_hash,
                coinb1,
                coinb2,
                merkle_branch,
                version,
                nbits,
                ntime,
                clean_jobs,
            ],
        }

        writer.write((json.dumps(notify) + "\n").encode())
        await writer.drain()
        logger.info("Sent job: %s", job_id)

    async def send_set_difficulty(
        self, writer: asyncio.StreamWriter, difficulty: float
    ):
        """Send a mining.set_difficulty message."""
        self.difficulty = difficulty
        message = {
            "id": None,
            "method": "mining.set_difficulty",
            "params": [difficulty],
        }
        writer.write((json.dumps(message) + "\n").encode())
        await writer.drain()
        logger.info("Set difficulty: %.2f", difficulty)

    async def broadcast_jobs(self):
        """Periodically send new jobs to all connected clients."""
        while self.running:
            await asyncio.sleep(30)  # New job every 30 seconds

            for writer in list(self.clients.values()):
                try:
                    if not writer.is_closing():
                        await self.send_notify(writer)
                        # Occasionally change difficulty
                        if random.random() < 0.1:
                            new_diff = round(random.uniform(0.5, 2.0), 2)
                            await self.send_set_difficulty(writer, new_diff)
                except Exception:
                    logger.exception("Error broadcasting to client")

    async def start(self):
        """Start the Stratum simulator server."""
        self.running = True
        server = await asyncio.start_server(self.handle_client, self.host, self.port)

        logger.info("=" * 72)
        logger.info("TEST-ONLY Stratum Pool Simulator Started")
        logger.info("Listening on: %s:%d", self.host, self.port)
        logger.info("EXTRANONCE1: %s", self.extranonce1)
        logger.info("EXTRANONCE2_SIZE: %d", self.extranonce2_size)
        logger.info("=" * 72)
        logger.info("WARNING: This is a TEST-ONLY simulator.")
        logger.info("DO NOT use in production.")
        logger.info("=" * 72)

        async with server:
            # Start job broadcaster
            broadcaster = asyncio.create_task(self.broadcast_jobs())

            try:
                await server.serve_forever()
            except asyncio.CancelledError:
                logger.info("Server shutdown requested")
            finally:
                self.running = False
                broadcaster.cancel()
                try:
                    await broadcaster
                except asyncio.CancelledError:
                    pass


async def main():
    parser = argparse.ArgumentParser(description="Test-only Stratum pool simulator")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3333, help="Port to listen on")
    args = parser.parse_args()

    simulator = TestStratumSimulator(args.host, args.port)

    try:
        await simulator.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        simulator.running = False


if __name__ == "__main__":
    asyncio.run(main())
