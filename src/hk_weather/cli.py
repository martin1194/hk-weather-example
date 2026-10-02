"""Command-line entrypoint for current Hong Kong weather."""

from __future__ import annotations

import argparse
import sys

from hk_weather.hko import (
    WeatherError,
    fetch_current,
    fetch_forecast,
    format_forecast,
    format_json,
    format_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hk-weather",
        description=(
            "Print Hong Kong weather from Hong Kong Observatory open data. "
            "Current conditions by default; --forecast prints the local forecast."
        ),
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
    parser.add_argument(
        "--forecast",
        action="store_true",
        help="Print the local weather forecast instead of current conditions",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        print("error: timeout must be greater than 0", file=sys.stderr)
        return 2
    try:
        if args.forecast:
            forecast = fetch_forecast(timeout=args.timeout)
            text = format_json(forecast) if args.json else format_forecast(forecast)
        else:
            weather = fetch_current(timeout=args.timeout)
            text = format_json(weather) if args.json else format_report(weather)
    except WeatherError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0
