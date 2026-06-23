"""Pipeline orchestration for Open TV Aggregator."""

from __future__ import annotations

import logging
from pathlib import Path

from .config_loader import load_channels
from .epg import write_epg
from .models import Channel, ChannelBuildResult
from .playlist import select_playlist_results, write_playlist
from .report import write_report
from .resolver import resolve_channel
from .validator import validate_stream

LOGGER = logging.getLogger(__name__)


def build(
    config_path: str | Path = "config/channels.yml",
    dist_dir: str | Path = "dist",
    timeout: int = 10,
    ytdlp_path: str = "yt-dlp",
    include_offline: bool = False,
) -> list[ChannelBuildResult]:
    """Run the full build pipeline and write playlist, EPG, and report files."""

    channels = load_channels(config_path)
    LOGGER.info("Loaded %s enabled channels", len(channels))

    results = process_channels(channels, timeout=timeout, ytdlp_path=ytdlp_path)
    playlist_results = select_playlist_results(results, include_offline=include_offline)
    included_ids = {result.channel.id for result in playlist_results}
    for result in results:
        result.included_in_playlist = result.channel.id in included_ids

    dist = Path(dist_dir)
    write_playlist(playlist_results, dist / "playlist.m3u")
    write_epg(playlist_results, dist / "epg.xml")
    write_report(results, dist / "report.json", playlist_count=len(playlist_results))

    LOGGER.info(
        "Build complete: %s online, %s in playlist, %s total",
        sum(1 for result in results if result.status == "online"),
        len(playlist_results),
        len(results),
    )
    return results


def validate(
    config_path: str | Path = "config/channels.yml",
    timeout: int = 10,
    ytdlp_path: str = "yt-dlp",
) -> list[ChannelBuildResult]:
    """Resolve and validate channels without writing playlist or EPG files."""

    channels = load_channels(config_path)
    return process_channels(channels, timeout=timeout, ytdlp_path=ytdlp_path)


def list_channels(config_path: str | Path = "config/channels.yml", include_disabled: bool = False) -> list[Channel]:
    """Load channels for display."""

    return load_channels(config_path, include_disabled=include_disabled)


def process_channels(
    channels: list[Channel],
    timeout: int = 10,
    ytdlp_path: str = "yt-dlp",
) -> list[ChannelBuildResult]:
    """Resolve and validate a channel list."""

    results: list[ChannelBuildResult] = []
    for channel in channels:
        LOGGER.info("Resolving %s (%s)", channel.name, channel.source_type)
        resolution = resolve_channel(channel, ytdlp_path=ytdlp_path, timeout=timeout)
        result = ChannelBuildResult(
            channel=channel,
            resolved_url=resolution.stream_url,
            resolution_error=resolution.error,
        )

        if not resolution.ok:
            LOGGER.warning("Resolve failed for %s: %s", channel.id, resolution.error)
            results.append(result)
            continue

        LOGGER.info("Validating %s", channel.name)
        validation = validate_stream(
            resolution.stream_url,
            timeout=timeout,
            user_agent=_optional_string(channel.extra.get("user_agent")),
            referrer=_optional_string(channel.extra.get("referrer")),
        )
        result.status = validation.status
        result.http_status = validation.status_code
        result.validation_error = validation.error
        result.checked_at = validation.checked_at
        if validation.status == "offline":
            LOGGER.warning("Validation failed for %s: %s", channel.id, validation.error)
        results.append(result)

    return results


def _optional_string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
