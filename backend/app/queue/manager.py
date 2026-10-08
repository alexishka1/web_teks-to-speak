"""
Lightweight FIFO asynchronous queue manager for CPU-only inference
"""

import asyncio
from typing import Any


class QueueManager:
    def __init__(self, max_concurrent: int = 1):
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._max_concurrent = max_concurrent
        self._active_workers = 0

    async def enqueue_job(self, job_data: dict[str, Any]):
        await self._queue.put(job_data)


queue_manager = QueueManager(max_concurrent=1)
