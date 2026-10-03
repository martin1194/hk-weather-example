"""Command-line entrypoint for current Hong Kong weather."""

from __future__ import annotations

import argparse
import sys

from hk_weather.hko import (
    WeatherError,
    fetch_current,
    fetch_forecast,
    fetch_forecast_day,
    fetch_coldest,
    fetch_hottest,
    fetch_humidity,
    fetch_lightning,
    fetch_nine_day,
    fetch_psr,
    fetch_quakes,
    fetch_rain,
    fetch_stations,
    fetch_wettest,
    fetch_temps,
    fetch_tide,
    fetch_tips,
    fetch_today,
    fetch_tomorrow,
    fetch_uv,
    fetch_visibility,
    fetch_warning_info,
    fetch_warnings,
    fetch_weekend,
    fetch_wind,
    filter_stations,
    format_day_miss,
    format_forecast,
    format_coldest,
    format_coldest_miss,
    format_hottest,
    format_hottest_miss,
    format_humidity,
    format_json,
    format_lightning,
    format_place_miss,
    format_nine_day,
    format_places,
    format_psr,
    format_quakes,
    format_rain,
    format_short,
    format_report,
    format_stations,
    format_temps,
    format_tide,
    format_tide_miss,
    format_tips,
    format_today_miss,
    format_tomorrow,
    format_tomorrow_miss,
    format_uv,
    format_visibility,
    format_warning_info,
    format_wettest,
    format_wettest_miss,
    format_warnings,
    format_weekend,
    format_weekend_miss,
    format_wind,
)


def _day_number(value: str) -> int:
    """Argparse type: forecast day 1–9, where 1 is the first list entry."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("day must be an integer from 1 to 9") from None
    if number < 1 or number > 9:
        raise argparse.ArgumentTypeError("day must be an integer from 1 to 9")
    return number


def package_version() -> str:
    """Return the installed hk-weather version from package metadata."""
    from importlib.metadata import version

    return version("hk-weather")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hk-weather",
        description=(
            "Print Hong Kong weather from Hong Kong Observatory open data. "
            "Current conditions by default; --forecast prints the local forecast; "
            "--nine-day prints the 9-day forecast; --warnings lists active warnings; "
            "--uv prints the UV index; --tips prints special weather tips; "
            "--stations lists each station; --list-places lists their names; "
            "--place NAME filters those stations; --rain lists district rainfall; "
            "--lightning lists lightning locations; --humidity lists humidity readings; "
            "--temps lists temperatures by place; --wind lists the forecast wind; "
            "--quake lists the latest earthquake message; --today prints today; "
            "--tomorrow prints tomorrow; "
            "--day N prints forecast day N (1 is the first entry); "
            "--psr lists the chance of significant rain; "
            "--warning-info prints detailed warning messages; "
            "--weekend prints Saturday and Sunday; "
            "--visibility lists 10-minute mean visibility; "
            "--hottest prints the warmest place; "
            "--coldest prints the coolest place; "
            "--wettest prints the wettest district; "
            "--tide prints today's high and low tides."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {package_version()}",
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
        "-s",
        "--short",
        action="store_true",
        help="Print current conditions on one line",
    )
    parser.add_argument(
        "--forecast",
        action="store_true",
        help="Print the local weather forecast instead of current conditions",
    )
    parser.add_argument(
        "-n",
        "--nine-day",
        action="store_true",
        help="Print the 9-day forecast",
    )
    parser.add_argument(
        "-Y",
        "--today",
        action="store_true",
        help="Print today's day from the 9-day forecast (Hong Kong calendar date)",
    )
    parser.add_argument(
        "-T",
        "--tomorrow",
        action="store_true",
        help="Print tomorrow's day from the 9-day forecast",
    )
    parser.add_argument(
        "-E",
        "--weekend",
        action="store_true",
        help="Print Saturday and Sunday from the 9-day forecast",
    )
    parser.add_argument(
        "--day",
        type=_day_number,
        metavar="N",
        help="Print day N of the 9-day forecast (1 is the first entry, not tomorrow)",
    )
    parser.add_argument(
        "-P",
        "--psr",
        action="store_true",
        help="Print the chance of significant rain (PSR) for each day of the 9-day forecast",
    )
    parser.add_argument(
        "--wind",
        action="store_true",
        help="Print the forecast wind from the 9-day forecast",
    )
    parser.add_argument(
        "--quake",
        action="store_true",
        help="List the latest Observatory quick earthquake message",
    )
    parser.add_argument(
        "-V",
        "--visibility",
        action="store_true",
        help="Print the latest 10-minute mean visibility",
    )
    parser.add_argument(
        "-I",
        "--tide",
        action="store_true",
        help="Print today's high and low tides at Quarry Bay",
    )
    parser.add_argument(
        "-w",
        "--warnings",
        action="store_true",
        help="Print only active weather warnings",
    )
    parser.add_argument(
        "-W",
        "--warning-info",
        action="store_true",
        help="Print detailed warning messages from the Observatory",
    )
    parser.add_argument(
        "-u",
        "--uv",
        action="store_true",
        help="Print the UV index from the current weather report",
    )
    parser.add_argument(
        "-t",
        "--tips",
        action="store_true",
        help="Print special weather tips",
    )
    parser.add_argument(
        "-r",
        "--rain",
        action="store_true",
        help="Print rainfall by district from the current report",
    )
    parser.add_argument(
        "-R",
        "--wettest",
        action="store_true",
        help="Print the wettest rainfall district from the current report",
    )
    parser.add_argument(
        "--lightning",
        action="store_true",
        help="List lightning locations from the current report",
    )
    parser.add_argument(
        "--humidity",
        action="store_true",
        help="Print humidity readings from the current report",
    )
    parser.add_argument(
        "--temps",
        action="store_true",
        help="Print temperatures by place from the current report",
    )
    parser.add_argument(
        "-H",
        "--hottest",
        action="store_true",
        help="Print the warmest place from the current report",
    )
    parser.add_argument(
        "-C",
        "--coldest",
        action="store_true",
        help="Print the coolest place from the current report",
    )
    parser.add_argument(
        "--stations",
        action="store_true",
        help="List temperature and humidity at each station",
    )
    parser.add_argument(
        "--list-places",
        action="store_true",
        help="List station names from the current report",
    )
    parser.add_argument(
        "--place",
        metavar="NAME",
        help="Print temperature and humidity for stations matching NAME",
    )
    parser.add_argument(
        "--lang",
        choices=("en", "tc", "sc"),
        default="en",
        help="Observatory response language: en, tc, or sc (default: en)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        print("error: timeout must be greater than 0", file=sys.stderr)
        return 2
    try:
        if args.warnings:
            text = format_warnings(
                fetch_warnings(timeout=args.timeout, lang=args.lang),
                as_json=args.json,
            )
        elif args.warning_info:
            text = format_warning_info(
                fetch_warning_info(timeout=args.timeout, lang=args.lang),
                as_json=args.json,
            )
        elif args.forecast:
            forecast = fetch_forecast(timeout=args.timeout, lang=args.lang)
            text = format_json(forecast) if args.json else format_forecast(forecast)
        elif args.nine_day:
            nine_day = fetch_nine_day(timeout=args.timeout, lang=args.lang)
            text = format_json(nine_day) if args.json else format_nine_day(nine_day)
        elif args.today:
            today = fetch_today(timeout=args.timeout, lang=args.lang)
            if today is None:
                text = format_today_miss(as_json=args.json)
            else:
                text = (
                    format_json(today)
                    if args.json
                    else format_tomorrow(today, title="Hong Kong forecast for today")
                )
        elif args.tomorrow:
            tomorrow = fetch_tomorrow(timeout=args.timeout, lang=args.lang)
            if tomorrow is None:
                text = format_tomorrow_miss(as_json=args.json)
            else:
                text = format_json(tomorrow) if args.json else format_tomorrow(tomorrow)
        elif args.weekend:
            weekend = fetch_weekend(timeout=args.timeout, lang=args.lang)
            if not weekend.days:
                text = format_weekend_miss(as_json=args.json)
            else:
                text = format_json(weekend) if args.json else format_weekend(weekend)
        elif args.day is not None:
            forecast_day = fetch_forecast_day(args.day, timeout=args.timeout, lang=args.lang)
            if forecast_day is None:
                text = format_day_miss(args.day, as_json=args.json)
            else:
                title = f"Hong Kong forecast day {args.day}"
                text = (
                    format_json(forecast_day)
                    if args.json
                    else format_tomorrow(forecast_day, title=title)
                )
        elif args.psr:
            psr = fetch_psr(timeout=args.timeout, lang=args.lang)
            text = format_json(psr) if args.json else format_psr(psr)
        elif args.wind:
            wind = fetch_wind(timeout=args.timeout, lang=args.lang)
            text = format_json(wind) if args.json else format_wind(wind)
        elif args.quake:
            quakes = fetch_quakes(timeout=args.timeout, lang=args.lang)
            text = format_json(quakes) if args.json else format_quakes(quakes)
        elif args.visibility:
            visibility = fetch_visibility(timeout=args.timeout, lang=args.lang)
            text = format_json(visibility) if args.json else format_visibility(visibility)
        elif args.tide:
            tide = fetch_tide(timeout=args.timeout, lang=args.lang)
            if not tide.events:
                text = format_tide_miss(as_json=args.json)
            else:
                text = format_json(tide) if args.json else format_tide(tide)
        elif args.uv:
            uv = fetch_uv(timeout=args.timeout, lang=args.lang)
            text = format_json(uv) if args.json else format_uv(uv)
        elif args.tips:
            tips = fetch_tips(timeout=args.timeout, lang=args.lang)
            text = format_json(tips) if args.json else format_tips(tips)
        elif args.rain:
            rain = fetch_rain(timeout=args.timeout, lang=args.lang)
            text = format_json(rain) if args.json else format_rain(rain)
        elif args.wettest:
            wettest = fetch_wettest(timeout=args.timeout, lang=args.lang)
            if wettest is None:
                text = format_wettest_miss(as_json=args.json)
            else:
                text = format_json(wettest) if args.json else format_wettest(wettest)
        elif args.lightning:
            lightning = fetch_lightning(timeout=args.timeout, lang=args.lang)
            text = format_json(lightning) if args.json else format_lightning(lightning)
        elif args.humidity:
            humidity = fetch_humidity(timeout=args.timeout, lang=args.lang)
            text = format_json(humidity) if args.json else format_humidity(humidity)
        elif args.temps:
            temps = fetch_temps(timeout=args.timeout, lang=args.lang)
            text = format_json(temps) if args.json else format_temps(temps)
        elif args.hottest:
            hottest = fetch_hottest(timeout=args.timeout, lang=args.lang)
            if hottest is None:
                text = format_hottest_miss(as_json=args.json)
            else:
                text = format_json(hottest) if args.json else format_hottest(hottest)
        elif args.coldest:
            coldest = fetch_coldest(timeout=args.timeout, lang=args.lang)
            if coldest is None:
                text = format_coldest_miss(as_json=args.json)
            else:
                text = format_json(coldest) if args.json else format_coldest(coldest)
        elif args.stations:
            stations = fetch_stations(timeout=args.timeout, lang=args.lang)
            text = format_json(stations) if args.json else format_stations(stations)
        elif args.list_places:
            places = fetch_stations(timeout=args.timeout, lang=args.lang)
            text = format_places(places, as_json=args.json)
        elif args.place is not None:
            query = args.place.strip()
            if not query:
                print("error: place must not be empty", file=sys.stderr)
                return 2
            matched = filter_stations(
                fetch_stations(timeout=args.timeout, lang=args.lang),
                query,
            )
            if matched.stations:
                text = format_json(matched) if args.json else format_stations(matched)
            else:
                text = format_place_miss(query, matched.update_time, as_json=args.json)
        else:
            weather = fetch_current(timeout=args.timeout, lang=args.lang)
            if args.json:
                text = format_json(weather)
            elif args.short:
                text = format_short(weather)
            else:
                text = format_report(weather)
    except WeatherError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0
