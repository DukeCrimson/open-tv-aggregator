"""Resolve configured source URLs to playable stream URLs."""

from __future__ import annotations

import logging
import subprocess
from shutil import which

from .models import Channel, ResolutionResult

LOGGER = logging.getLogger(__name__)


def resolve_channel(channel: Channel, ytdlp_path: str = "yt-dlp", timeout: int = 30) -> ResolutionResult:
    """Resolve one channel to a URL that can be placed in a playlist."""

    if channel.source_type == "hls":
        return ResolutionResult(channel=channel, stream_url=channel.url)

    if channel.source_type == "youtube":
        return _resolve_youtube(channel, ytdlp_path=ytdlp_path, timeout=timeout)

    if channel.source_type == "m3u":
        return ResolutionResult(
            channel=channel,
            stream_url=None,
            error="source_type=m3u is reserved; remote playlist parsing is not implemented yet",
        )

    return ResolutionResult(
        channel=channel,
        stream_url=None,
        error=f"unsupported source_type={channel.source_type}",
    )


def _resolve_youtube(channel: Channel, ytdlp_path: str, timeout: int) -> ResolutionResult:
    if which(ytdlp_path) is None:
        return ResolutionResult(
            channel=channel,
            stream_url=None,
            error=f"yt-dlp executable not found: {ytdlp_path}",
        )

    command = [
        ytdlp_path,
        "-g",
        "--no-playlist",
        "--skip-download",
        channel.url,
    ]
    LOGGER.debug("Resolving YouTube channel %s with yt-dlp", channel.id)

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ResolutionResult(
            channel=channel,
            stream_url=None,
            error=f"yt-dlp timed out after {timeout}s",
        )
    except OSError as exc:
        return ResolutionResult(channel=channel, stream_url=None, error=str(exc))

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "yt-dlp failed"
        return ResolutionResult(channel=channel, stream_url=None, error=message)

    candidates = [line.strip() for line in completed.stdout.splitlines() if line.strip().startswith("http")]
    if not candidates:
        return ResolutionResult(channel=channel, stream_url=None, error="yt-dlp returned no playable URL")

    hls_candidates = [url for url in candidates if ".m3u8" in url.lower()]
    return ResolutionResult(channel=channel, stream_url=(hls_candidates or candidates)[0])

