import time
import logging
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("spellbook")
_rate_store: dict = defaultdict(list)
RATE_LIMIT = 120
RATE_WINDOW = 60

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        logger.info(f"{request.method} {request.url.path} → {response.status_code} ({ms:.1f}ms)")
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        _rate_store[ip] = [t for t in _rate_store[ip] if t > now - RATE_WINDOW]
        if len(_rate_store[ip]) >= RATE_LIMIT:
            retry = int(RATE_WINDOW - (now - _rate_store[ip][0]))
            return JSONResponse(status_code=429, content={"detail": f"Too many requests. Retry in {retry}s."})
        _rate_store[ip].append(now)
        return await call_next(request)