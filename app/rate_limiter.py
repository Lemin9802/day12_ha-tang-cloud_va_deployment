import time
from collections import defaultdict, deque

from fastapi import HTTPException

from .config import settings


_windows: dict[str, deque[float]] = defaultdict(deque)


def check_rate_limit(user_id: str) -> dict:
    now = time.time()
    window_seconds = 60
    max_requests = settings.rate_limit_per_minute

    window = _windows[user_id]

    while window and window[0] < now - window_seconds:
        window.popleft()

    if len(window) >= max_requests:
        retry_after = int(window[0] + window_seconds - now) + 1
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": max_requests,
                "window_seconds": window_seconds,
                "retry_after_seconds": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    window.append(now)

    return {
        "limit": max_requests,
        "remaining": max_requests - len(window),
        "reset_at": int(now + window_seconds),
    }
