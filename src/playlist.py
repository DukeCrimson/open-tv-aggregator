"""Generate APTV-compatible M3U playlists."""

from __future__ import annotations

from pathlib import Path

from .models import ChannelBuildResult


def select_playlist_results(
    results: list[ChannelBuildResult],
    include_offline: bool = False,
) -> list[ChannelBuildResult]:
    """Return channels that should be written to playlist.m3u."""

    selected: list[ChannelBuildResult] = []
    for result in results:
        if not result.resolved_url:
            continue
        if result.status == "online" or result.channel.allow_offline or include_offline:
            selected.append(result)
    return selected


def write_playlist(
    results: list[ChannelBuildResult],
    output_path: str | Path,
    epg_url: str = "epg.xml",
) -> None:
    """Write playlist.m3u using extended M3U IPTV attributes."""

    lines = [f'#EXTM3U x-tvg-url="{_attr(epg_url)}"']
    for result in results:
        channel = result.channel
        lines.append(
            "#EXTINF:-1 "
            f'tvg-id="{_attr(channel.tvg_id)}" '
            f'tvg-name="{_attr(channel.name)}" '
            f'tvg-logo="{_attr(channel.logo)}" '
            f'group-title="{_attr(channel.group)}" '
            f'tvg-country="{_attr(channel.country)}",'
            f"{channel.name}"
        )
        lines.append(result.resolved_url or channel.url)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _attr(value: str) -> str:
    return value.replace('"', "'").replace("\n", " ").strip()

