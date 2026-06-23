"""Validate resolved stream URLs with conservative HTTP checks."""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from .models import ValidationResult

DEFAULT_HEADERS = {
    "User-Agent": "open-tv-aggregator/0.1 (+https://github.com/)",
    "Accept": "*/*",
}


def validate_stream(
    url: str | None,
    timeout: int = 10,
    user_agent: str | None = None,
    referrer: str | None = None,
) -> ValidationResult:
    """Return online/offline for a stream URL.

    The validator tries HEAD first, then falls back to GET with a small Range
    request because many CDNs reject HEAD for HLS playlists.
    """

    checked_at = datetime.now(timezone.utc).isoformat()
    if not url:
        return ValidationResult("offline", None, "empty stream URL", checked_at)

    head_result = _request("HEAD", url, timeout=timeout, user_agent=user_agent, referrer=referrer)
    if _is_online_status(head_result.status_code):
        return ValidationResult("online", head_result.status_code, None, checked_at)

    get_result = _request(
        "GET",
        url,
        timeout=timeout,
        range_request=True,
        user_agent=user_agent,
        referrer=referrer,
    )
    if _is_online_status(get_result.status_code):
        return ValidationResult("online", get_result.status_code, None, checked_at)

    error = get_result.error or head_result.error
    status_code = get_result.status_code or head_result.status_code
    if error is None and status_code is not None:
        error = f"HTTP status {status_code}"
    return ValidationResult("offline", status_code, error or "validation failed", checked_at)


class _RequestResult:
    def __init__(self, status_code: int | None, error: str | None) -> None:
        self.status_code = status_code
        self.error = error


def _request(
    method: str,
    url: str,
    timeout: int,
    range_request: bool = False,
    user_agent: str | None = None,
    referrer: str | None = None,
) -> _RequestResult:
    headers = DEFAULT_HEADERS.copy()
    if user_agent:
        headers["User-Agent"] = user_agent
    if referrer:
        headers["Referer"] = referrer
    if range_request:
        headers["Range"] = "bytes=0-1023"

    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )
        try:
            return _RequestResult(response.status_code, None)
        finally:
            response.close()
    except requests.RequestException as exc:
        return _RequestResult(None, str(exc))


def _is_online_status(status_code: int | None) -> bool:
    return status_code is not None and 200 <= status_code < 400
