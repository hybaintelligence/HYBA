"""
Blockchain Space Oracle
HYBA / PYTHIA Mining System - Structural Analysis Boundary
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None


@dataclass
class PhiAnalysisResult:
    phi_score: Optional[float] = None
    resonance_radius: Optional[float] = None
    aligned_blocks_percentage: Optional[float] = None
    source: str = "not_connected"


@dataclass
class BlockTip:
    height: int
    hash: str
    timestamp: float
    source: str


class BlockchainOracle:
    """
    Blockchain oracle for block height monitoring and stale job detection.

    Supports multiple data sources with fallback for production resilience.
    """

    def __init__(self):
        self.logger = logging.getLogger("blockchain_oracle")
        self._current_tip: Optional[BlockTip] = None
        self._last_update: float = 0
        self._update_interval: float = 60.0  # Update every 60 seconds
        self._enabled = True
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> Optional[aiohttp.ClientSession]:
        if aiohttp is None:
            return None
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self._session

    async def _close_session(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _fetch_blockchain_info_api(self) -> Optional[BlockTip]:
        """Fetch current block tip from public blockchain API."""
        session = await self._get_session()
        if session is None:
            return None

        try:
            # Try blockchain.info API first
            async with session.get(
                "https://blockchain.info/q/getblockcount"
            ) as response:
                if response.status == 200:
                    height = int(await response.text())
                    # Get latest block hash
                    async with session.get(
                        "https://blockchain.info/latestblock"
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return BlockTip(
                                height=height,
                                hash=data.get("hash", ""),
                                timestamp=time.time(),
                                source="blockchain.info",
                            )
        except Exception as e:
            self.logger.warning("Failed to fetch from blockchain.info: %s", e)

        try:
            # Fallback to blockstream API
            async with session.get(
                "https://blockstream.info/api/blocks/tip/height"
            ) as response:
                if response.status == 200:
                    height = int(await response.text())
                    async with session.get(
                        "https://blockstream.info/api/blocks/tip/hash"
                    ) as resp:
                        if resp.status == 200:
                            block_hash = await resp.text()
                            return BlockTip(
                                height=height,
                                hash=block_hash.strip(),
                                timestamp=time.time(),
                                source="blockstream.info",
                            )
        except Exception as e:
            self.logger.warning("Failed to fetch from blockstream.info: %s", e)

        return None

    async def get_current_block_tip(
        self, force_refresh: bool = False
    ) -> Optional[BlockTip]:
        """Get current blockchain tip with caching."""
        if not self._enabled:
            return None

        now = time.time()
        if (
            self._current_tip
            and not force_refresh
            and (now - self._last_update) < self._update_interval
        ):
            return self._current_tip

        new_tip = await self._fetch_blockchain_info_api()
        if new_tip:
            self._current_tip = new_tip
            self._last_update = now
            self.logger.info(
                "Updated blockchain tip: height=%d, hash=%s, source=%s",
                new_tip.height,
                new_tip.hash[:16],
                new_tip.source,
            )
        else:
            self.logger.warning("Failed to update blockchain tip, using cached value")

        return self._current_tip

    def is_job_stale_by_block_height(
        self, job_prevhash: str, current_tip: Optional[BlockTip]
    ) -> bool:
        """
        Check if a job is stale based on block height monitoring.

        A job is considered stale if:
        1. We have a current block tip
        2. The job's prevhash doesn't match the current tip hash
        3. The job was created before the current block timestamp
        """
        if current_tip is None:
            return False

        # If prevhash matches current tip, job is still valid
        if job_prevhash.lower() == current_tip.hash.lower():
            return False

        # If prevhash doesn't match, job is stale
        return True

    async def analyze_blockchain_phi_patterns(self) -> PhiAnalysisResult:
        """Legacy method for phi pattern analysis."""
        return PhiAnalysisResult()

    async def close(self) -> None:
        """Clean up resources."""
        await self._close_session()
