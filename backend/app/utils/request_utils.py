"""HTTP request helpers."""

from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    """Return the best-effort client IP address from a request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is None:
        return None
    return request.client.host
