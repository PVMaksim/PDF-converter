"""
Rate limiting middleware using slowapi.
Limits API requests based on user plan.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from ..config import settings

# Rate limiter keyed by client IP
limiter = Limiter(key_func=get_remote_address)

# Лимиты для разных тарифов
FREE_LIMIT = f"{settings.RATE_LIMIT_FREE_PER_HOUR}/hour"
PRO_LIMIT = f"{settings.RATE_LIMIT_PRO_PER_HOUR}/hour"


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handler for rate limit exceeded errors.
    Returns 429 with retry_after header.
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please wait before sending another request.",
            "retry_after": str(exc.retry_after),
        },
        headers={"Retry-After": str(exc.retry_after)},
    )


def get_limit_for_plan(is_pro: bool = False) -> str:
    """
    Get rate limit string based on user plan.
    
    Args:
        is_pro: True for PRO users, False for FREE users
    
    Returns:
        Rate limit string for slowapi decorator
    """
    return PRO_LIMIT if is_pro else FREE_LIMIT
