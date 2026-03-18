import asyncio
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from time import monotonic

from app.utils.errors import QueueFullError, RateLimitError


class RequestGuardService:
    def __init__(
        self,
        *,
        max_requests: int,
        window_seconds: int,
        max_concurrent_requests: int,
        acquire_timeout: float,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_concurrent_requests = max_concurrent_requests
        self.acquire_timeout = acquire_timeout
        self._request_history: dict[str, deque[float]] = defaultdict(deque)
        self._rate_limit_lock = asyncio.Lock()
        self._generation_slots = asyncio.Semaphore(max_concurrent_requests)

    async def enforce_rate_limit(self, client_ip: str) -> None:
        now = monotonic()
        async with self._rate_limit_lock:
            bucket = self._request_history[client_ip]
            while bucket and now - bucket[0] > self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                raise RateLimitError(self.max_requests, self.window_seconds)
            bucket.append(now)

    @asynccontextmanager
    async def acquire_generation_slot(self):
        try:
            await asyncio.wait_for(
                self._generation_slots.acquire(),
                timeout=self.acquire_timeout,
            )
        except TimeoutError as exc:
            raise QueueFullError(
                self.max_concurrent_requests,
                self.acquire_timeout,
            ) from exc

        try:
            yield
        finally:
            self._generation_slots.release()
