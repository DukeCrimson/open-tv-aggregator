"""Command-line interface for Open TV Aggregator."""

from __future__ import annotations

import argparse
import logging
import sys

from . import main
from .config_loader import ConfigError


def run(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        if args.command == "build":
            results = main.build(
                config_path=args.config,
                dist_dir=args.dist_dir,
                timeout=args.timeout,
                ytdlp_path=args.yt_dlp,
                include_offline=args.include_offline,
            )
            _print_summary(results)
            return 0

        if args.command == "validate":
            results = main.validate(config_path=args.config, timeout=args.timeout, ytdlp_path=args.yt_dlp)
            _print_results(results)
            return 0 if all(result.status == "online" for result in results) else 1

        if args.command == "list":
            channels = main.list_channels(config_path=args.config, include_disabled=args.include_disabled)
            for channel in channels:
                state = "enabled" if channel.enabled else "disabled"
                print(f"{channel.id}\t{channel.name}\t{channel.group}\t{channel.source_type}\t{state}")
            return 0
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130

    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m src.cli")
    parser.add_argument("--config", default="config/channels.yml", help="Path to channels.yml")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP and resolver timeout in seconds")
    parser.add_argument("--yt-dlp", default="yt-dlp", help="yt-dlp executable path")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build dist/playlist.m3u, dist/epg.xml, dist/report.json")
    build_parser.add_argument("--dist-dir", default="dist", help="Output directory")
    build_parser.add_argument(
        "--include-offline",
        action="store_true",
        help="Include resolved offline channels in playlist; per-channel allow_offline also works",
    )

    subparsers.add_parser("validate", help="Resolve and validate configured channels")

    list_parser = subparsers.add_parser("list", help="List configured channels")
    list_parser.add_argument("--include-disabled", action="store_true", help="Show disabled channels too")
    return parser


def _print_summary(results: list[main.ChannelBuildResult]) -> None:
    online = sum(1 for result in results if result.status == "online")
    included = sum(1 for result in results if result.included_in_playlist)
    print(f"Channels: {len(results)} total, {online} online, {included} written to playlist")


def _print_results(results: list[main.ChannelBuildResult]) -> None:
    for result in results:
        reason = f" ({result.failure_reason})" if result.failure_reason else ""
        print(f"{result.channel.id}\t{result.status}{reason}")


if __name__ == "__main__":
    raise SystemExit(run())
