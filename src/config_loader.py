"""Load and validate channel configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Channel, SourceType


class ConfigError(ValueError):
    """Raised when a configuration file cannot be loaded or validated."""


REQUIRED_FIELDS = {
    "id",
    "name",
    "group",
    "country",
    "logo",
    "source_type",
    "url",
    "epg_id",
    "enabled",
}

OPTIONAL_FIELDS = {"allow_offline"}
SUPPORTED_SOURCE_TYPES = {"hls", "youtube", "m3u"}


def load_channels(config_path: str | Path, include_disabled: bool = False) -> list[Channel]:
    """Load channels from a YAML file and filter disabled entries by default."""

    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc

    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ConfigError("Channel config must be a YAML list")

    channels = [_parse_channel(item, index) for index, item in enumerate(raw, start=1)]
    if include_disabled:
        return channels
    return [channel for channel in channels if channel.enabled]


def _parse_channel(item: Any, index: int) -> Channel:
    if not isinstance(item, dict):
        raise ConfigError(f"Channel #{index} must be a mapping")

    missing = sorted(REQUIRED_FIELDS.difference(item))
    if missing:
        raise ConfigError(f"Channel #{index} is missing required fields: {', '.join(missing)}")

    for field_name in REQUIRED_FIELDS - {"enabled"}:
        value = item[field_name]
        if not isinstance(value, str):
            raise ConfigError(f"Channel #{index} field '{field_name}' must be a string")
        if field_name != "logo" and not value.strip():
            raise ConfigError(f"Channel #{index} field '{field_name}' cannot be empty")

    enabled = item["enabled"]
    if not isinstance(enabled, bool):
        raise ConfigError(f"Channel #{index} field 'enabled' must be true or false")

    allow_offline = item.get("allow_offline", False)
    if not isinstance(allow_offline, bool):
        raise ConfigError(f"Channel #{index} field 'allow_offline' must be true or false")

    source_type = item["source_type"].strip().lower()
    if source_type not in SUPPORTED_SOURCE_TYPES:
        supported = ", ".join(sorted(SUPPORTED_SOURCE_TYPES))
        raise ConfigError(
            f"Channel #{index} has unsupported source_type '{item['source_type']}'. "
            f"Supported values: {supported}"
        )

    known_fields = REQUIRED_FIELDS | OPTIONAL_FIELDS
    extra = {key: value for key, value in item.items() if key not in known_fields}

    return Channel(
        id=item["id"].strip(),
        name=item["name"].strip(),
        group=item["group"].strip(),
        country=item["country"].strip().upper(),
        logo=item["logo"].strip(),
        source_type=source_type,  # type: ignore[arg-type]
        url=item["url"].strip(),
        epg_id=item["epg_id"].strip(),
        enabled=enabled,
        allow_offline=allow_offline,
        extra=extra,
    )

