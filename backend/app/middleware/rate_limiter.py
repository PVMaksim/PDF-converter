from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from ..config import settings

# Rate limiter keyed by client IP
limiter = Limiter(key_func=get_remote_address)

FREE_LIMIT = f"{settings.RATE_LIMIT_FREE_PER_HOUR}/hour"
PRO_LIMIT = f"{settings.RATE_LIMIT_PRO_PER_HOUR}/hour"


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please wait before sending another request.",
            "retry_after": str(exc.retry_after),
        },
    )
