"""Generate machine-readable build reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Channel, ChannelBuildResult


def write_report(
    results: list[ChannelBuildResult],
    output_path: str | Path,
    playlist_count: int,
) -> None:
    """Write dist/report.json with success and failure details."""

    online_count = sum(1 for result in results if result.status == "online")
    failed = [result for result in results if result.status != "online"]
    payload: dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "online": online_count,
        "offline": len(results) - online_count,
        "playlist_count": playlist_count,
        "failures": [_failure_to_dict(result) for result in failed],
        "channels": [_result_to_dict(result) for result in results],
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _channel_to_dict(channel: Channel) -> dict[str, Any]:
    return {
        "id": channel.id,
        "name": channel.name,
        "group": channel.group,
        "country": channel.country,
        "source_type": channel.source_type,
        "url": channel.url,
        "epg_id": channel.epg_id,
        "allow_offline": channel.allow_offline,
    }


def _result_to_dict(result: ChannelBuildResult) -> dict[str, Any]:
    return {
        "channel": _channel_to_dict(result.channel),
        "resolved_url": result.resolved_url,
        "status": result.status,
        "http_status": result.http_status,
        "resolution_error": result.resolution_error,
        "validation_error": result.validation_error,
        "failure_reason": result.failure_reason,
        "checked_at": result.checked_at,
        "included_in_playlist": result.included_in_playlist,
    }


def _failure_to_dict(result: ChannelBuildResult) -> dict[str, Any]:
    return {
        "id": result.channel.id,
        "name": result.channel.name,
        "source_type": result.channel.source_type,
        "url": result.channel.url,
        "resolved_url": result.resolved_url,
        "reason": result.failure_reason,
        "http_status": result.http_status,
        "checked_at": result.checked_at,
    }

