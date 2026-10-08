"""
Modul Rate Limiter Berbasis IP untuk TaSTP:
- Proteksi CPU laptop Intel Iris dari banjir request bersamaan
- Algoritma sliding window per alamat IP klien
- Mengembalikan HTTP 429 Too Many Requests jika limit terlampaui
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class IPRateLimiter:
    def __init__(self, default_limit: int = 60, window_seconds: int = 60):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        # Mapping: ip -> list of timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)
        # Endpoint custom limits: path_prefix -> (max_requests, window_sec)
        self._path_limits: dict[str, tuple[int, int]] = {
            "/api/tts": (30, 60),
            "/tts": (30, 60),
            "/api/synthesize": (30, 60),
            "/synthesize": (30, 60),
            "/api/voice-clone/upload": (10, 60),
            "/voice-clone/upload": (10, 60),
        }

    def get_client_ip(self, request: Request) -> str:
        """Mengekstrak IP klien (memperhitungkan reverse proxy X-Forwarded-For jika ada)."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def check_rate_limit(self, request: Request) -> None:
        """
        Memeriksa apakah request dari IP ini masih dalam batas kuota.
        Raises HTTPException(429) jika limit terlampaui.
        """
        client_ip = self.get_client_ip(request)
        path = request.url.path
        now = time.time()

        # Tentukan limit untuk path ini
        limit, window = self.default_limit, self.window_seconds
        for prefix, custom in self._path_limits.items():
            if path == prefix or path.startswith(prefix):
                limit, window = custom
                break

        key = f"{client_ip}:{path}"
        timestamps = self._requests[key]

        # Buang timestamp yang sudah lewat jendela waktu
        cutoff = now - window
        valid_timestamps = [t for t in timestamps if t > cutoff]
        self._requests[key] = valid_timestamps

        if len(valid_timestamps) >= limit:
            retry_after = int(window - (now - valid_timestamps[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Batas permintaan terlampaui ({limit} request per {window} detik untuk {client_ip}). Silakan tunggu {retry_after} detik.",
                headers={"Retry-After": str(retry_after)},
            )

        # Catat request saat ini
        self._requests[key].append(now)

    def reset(self) -> None:
        """Mengosongkan riwayat rate limit (untuk keperluan unit testing)."""
        self._requests.clear()


limiter = IPRateLimiter()


def rate_limit_dependency(request: Request):
    """Dependency FastAPI untuk dipasang di router atau endpoint."""
    limiter.check_rate_limit(request)
