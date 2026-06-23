"""Shared data models for the aggregator pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

SourceType = Literal["hls", "youtube", "m3u"]
ChannelStatus = Literal["online", "offline"]


@dataclass(frozen=True)
class Channel:
    """A configured TV channel."""

    id: str
    name: str
    group: str
    country: str
    logo: str
    source_type: SourceType
    url: str
    epg_id: str
    enabled: bool
    allow_offline: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def tvg_id(self) -> str:
        return self.epg_id or self.id


@dataclass(frozen=True)
class ResolutionResult:
    """Result of converting a channel source into a playable URL."""

    channel: Channel
    stream_url: str | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return bool(self.stream_url) and self.error is None


@dataclass(frozen=True)
class ValidationResult:
    """HTTP validation result for a playable URL."""

    status: ChannelStatus
    status_code: int | None
    error: str | None
    checked_at: str


@dataclass
class ChannelBuildResult:
    """Combined pipeline result for one channel."""

    channel: Channel
    resolved_url: str | None = None
    resolution_error: str | None = None
    status: ChannelStatus = "offline"
    http_status: int | None = None
    validation_error: str | None = None
    checked_at: str | None = None
    included_in_playlist: bool = False

    @property
    def failure_reason(self) -> str | None:
        if self.status == "online":
            return None
        return self.resolution_error or self.validation_error or "channel is offline"

