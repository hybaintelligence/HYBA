"""Async execution helpers for CPU-bound tasks.

This module provides utility functions to run synchronous, CPU-intensive functions in a non-blocking manner.  Use these helpers to offload heavy computations from the FastAPI event loop.  By running CPU-bound work in a thread or process pool, you prevent long computations from blocking other requests.

Example usage:

    from pythia_mining.async_executor import run_in_thread

    def compute_heavy(x):
        # expensive computation
        return x ** 2

    async def handle_request(x: int) -> int:
        result = await run_in_thread(compute_heavy, x)
        return result

These helpers can be extended or replaced with more sophisticated job queues (e.g., Celery, RQ) when decoupling heavy computation into separate services.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, TypeVar

T = TypeVar("T")

async def run_in_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Execute a synchronous function in a background thread.

    Args:
        func: A CPU-bound function to run.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The return value of the function.
    """
    return await asyncio.to_thread(func, *args, **kwargs)

async def run_in_process_pool(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Execute a synchronous function in a process pool executor.

    Use this when the task is CPU-intensive and needs to bypass the Global Interpreter Lock (GIL).

    Args:
        func: A CPU-bound function to run.
        *args: Positional arguments.
        **kwargs: Keyword arguments.

    Returns:
        The return value of the function.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)
