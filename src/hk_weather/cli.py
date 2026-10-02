"""Command-line entrypoint for current Hong Kong weather."""

from __future__ import annotations

import argparse
import sys

from hk_weather.hko import WeatherError, fetch_current, format_json, format_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hk-weather",
        description="Print current weather for Hong Kong from Hong Kong Observatory open data.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10,
        help="HTTP timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the report as one JSON object",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        print("error: timeout must be greater than 0", file=sys.stderr)
        return 2
    try:
        weather = fetch_current(timeout=args.timeout)
    except WeatherError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        sys.stdout.write(format_json(weather))
    else:
        sys.stdout.write(format_report(weather))
    return 0
