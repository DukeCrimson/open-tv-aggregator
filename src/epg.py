"""Generate a basic XMLTV EPG file."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

from .models import ChannelBuildResult


def write_epg(results: list[ChannelBuildResult], output_path: str | Path, hours: int = 24) -> None:
    """Write a placeholder XMLTV EPG for playlist channels."""

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    root = ET.Element(
        "tv",
        {
            "generator-info-name": "open-tv-aggregator",
            "generator-info-url": "https://github.com/",
        },
    )

    for result in results:
        channel = result.channel
        channel_node = ET.SubElement(root, "channel", {"id": channel.tvg_id})
        ET.SubElement(channel_node, "display-name").text = channel.name
        if channel.logo:
            ET.SubElement(channel_node, "icon", {"src": channel.logo})

        block_start = now
        while block_start < now + timedelta(hours=hours):
            block_stop = min(block_start + timedelta(hours=6), now + timedelta(hours=hours))
            programme = ET.SubElement(
                root,
                "programme",
                {
                    "start": _xmltv_time(block_start),
                    "stop": _xmltv_time(block_stop),
                    "channel": channel.tvg_id,
                },
            )
            ET.SubElement(programme, "title", {"lang": "en"}).text = "Live Programming"
            ET.SubElement(programme, "desc", {"lang": "en"}).text = (
                "Placeholder schedule generated because no official EPG source is configured."
            )
            block_start = block_stop

    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _xmltv_time(value: datetime) -> str:
    return value.strftime("%Y%m%d%H%M%S %z")

