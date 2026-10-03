"""Command-line entrypoint for current Hong Kong weather."""

from __future__ import annotations

import argparse
import sys

from hk_weather.hko import (
    WeatherError,
    fetch_aqhi,
    fetch_current,
    fetch_driest,
    fetch_forecast,
    fetch_outlook,
    fetch_forecast_period,
    fetch_forecast_desc,
    fetch_forecast_updated,
    fetch_forecast_day,
    fetch_hour_rain,
    fetch_hour_wettest,
    fetch_hour_driest,
    fetch_felt,
    fetch_fire_danger,
    fetch_grass,
    fetch_accum_rain,
    fetch_avg_rain,
    fetch_radiation,
    fetch_bulletin,
    fetch_radiation_note,
    fetch_radiation_weather,
    fetch_coldest,
    fetch_cyclone,
    fetch_hottest,
    fetch_humidest,
    fetch_humidity,
    fetch_icon_time,
    fetch_icon,
    fetch_least_humid,
    fetch_lightning,
    fetch_lunar,
    fetch_moon,
    fetch_month_rain,
    fetch_nine_day,
    fetch_nine_situation,
    fetch_nine_updated,
    fetch_sea_temp,
    fetch_soil_temp,
    fetch_year_rain,
    fetch_noon_rain,
    fetch_overnight,
    fetch_psr,
    fetch_quakes,
    fetch_rain,
    fetch_rain_period,
    fetch_rainstorm,
    fetch_stations,
    fetch_strikes,
    fetch_summary,
    fetch_situation,
    fetch_sunrise,
    fetch_wettest,
    fetch_temps,
    fetch_tc_info,
    fetch_tide,
    fetch_tips,
    fetch_today,
    fetch_tomorrow,
    fetch_uv,
    fetch_visibility,
    fetch_warning_info,
    fetch_warnings,
    fetch_warning_time,
    fetch_weekend,
    fetch_wind,
    fetch_forecast_icon,
    fetch_yesterday,
    filter_stations,
    format_aqhi,
    format_aqhi_miss,
    format_day_miss,
    format_driest,
    format_driest_miss,
    format_forecast,
    format_outlook,
    format_outlook_miss,
    format_forecast_period,
    format_forecast_period_miss,
    format_forecast_desc,
    format_forecast_desc_miss,
    format_forecast_updated,
    format_forecast_updated_miss,
    format_grass,
    format_grass_miss,
    format_accum_rain,
    format_accum_rain_miss,
    format_avg_rain,
    format_avg_rain_miss,
    format_radiation,
    format_radiation_miss,
    format_bulletin,
    format_bulletin_miss,
    format_radiation_note,
    format_radiation_note_miss,
    format_radiation_weather,
    format_radiation_weather_miss,
    format_felt,
    format_felt_miss,
    format_fire_danger,
    format_fire_danger_miss,
    format_coldest,
    format_coldest_miss,
    format_cyclone,
    format_cyclone_miss,
    format_hottest,
    format_hottest_miss,
    format_humidest,
    format_humidest_miss,
    format_humidity,
    format_hour_rain,
    format_hour_rain_miss,
    format_hour_wettest,
    format_hour_driest,
    format_icon_time,
    format_icon_time_miss,
    format_icon,
    format_icon_miss,
    format_least_humid,
    format_least_humid_miss,
    format_json,
    format_lightning,
    format_lunar,
    format_lunar_miss,
    format_moon,
    format_moon_miss,
    format_month_rain,
    format_month_rain_miss,
    format_year_rain,
    format_year_rain_miss,
    format_place_miss,
    format_nine_day,
    format_nine_situation,
    format_nine_situation_miss,
    format_nine_updated,
    format_nine_updated_miss,
    format_sea_temp,
    format_sea_temp_miss,
    format_soil_temp,
    format_soil_temp_miss,
    format_noon_rain,
    format_noon_rain_miss,
    format_overnight,
    format_overnight_miss,
    format_places,
    format_psr,
    format_quakes,
    format_rain,
    format_rain_period,
    format_rain_period_miss,
    format_rainstorm,
    format_rainstorm_miss,
    format_short,
    format_situation,
    format_situation_miss,
    format_summary,
    format_report,
    format_stations,
    format_strikes,
    format_strikes_miss,
    format_sunrise,
    format_sunrise_miss,
    format_temps,
    format_tide,
    format_tide_miss,
    format_tc_info,
    format_tc_info_miss,
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
    format_warning_time,
    format_warning_time_miss,
    format_weekend,
    format_weekend_miss,
    format_wind,
    format_forecast_icon,
    format_forecast_icon_miss,
    format_yesterday,
    format_yesterday_miss,
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
            "Current conditions by default; --summary prints a short briefing; "
            "--forecast prints the local forecast; "
            "--outlook prints the local-forecast outlook; "
            "--forecast-period prints the forecast period; "
            "--forecast-desc prints the forecast description; "
            "--forecast-updated prints when the local forecast was updated; "
            "--situation prints the general situation; "
            "--fire-danger prints the fire danger warning; "
            "--tc-info prints tropical cyclone information from the local forecast; "
            "--nine-day prints the 9-day forecast; --sea-temp prints the sea temperature; "
            "--soil-temp prints soil temperatures; "
            "--nine-situation prints the 9-day general situation; "
            "--nine-updated prints when the 9-day forecast was updated; "
            "--warnings lists active warnings; "
            "--warning-time prints when active warnings were issued; "
            "--uv prints the UV index; --icon-time prints when the weather icon changed; "
            "--icon prints the current weather icon; "
            "--tips prints special weather tips; "
            "--stations lists each station; --list-places lists their names; "
            "--place NAME filters those stations; --rain lists district rainfall; "
            "--rain-period prints the district rainfall window; "
            "--hour-rain lists past-hour rainfall at automatic stations; "
            "--hour-wettest prints the wettest of those stations; "
            "--hour-driest prints the driest of those stations; "
            "--lightning lists lightning locations; --strikes lists hourly lightning counts; "
            "--humidity lists humidity readings; "
            "--temps lists temperatures by place; --wind lists the forecast wind; "
            "--forecast-icon prints each day's weather icon; "
            "--quake lists the latest earthquake message; "
            "--felt prints the locally felt earth tremor; --today prints today; "
            "--yesterday prints yesterday's Observatory summary; "
            "--grass prints yesterday's grass minimum; "
            "--accum-rain prints accumulated rainfall since 1 January; "
            "--avg-rain prints the climatological rainfall normal; "
            "--radiation prints yesterday's gamma radiation report; "
            "--bulletin prints when yesterday's bulletin was issued; "
            "--radiation-note prints the normal radiation range; "
            "--radiation-weather prints how radiation varies with the weather; "
            "--tomorrow prints tomorrow; "
            "--day N prints forecast day N (1 is the first entry); "
            "--psr lists the chance of significant rain; "
            "--warning-info prints detailed warning messages; "
            "--weekend prints Saturday and Sunday; "
            "--visibility lists 10-minute mean visibility; "
            "--hottest prints the warmest place; "
            "--coldest prints the coolest place; "
            "--overnight prints the midnight-to-9am minimum; "
            "--noon-rain prints the midnight-to-noon rainfall note; "
            "--month-rain prints last month's rainfall note; "
            "--year-rain prints the January-to-last-month rainfall note; "
            "--wettest prints the wettest district; "
            "--driest prints the driest district; "
            "--tide prints today's high and low tides; "
            "--aqhi prints the air quality health index; "
            "--sunrise prints today's sunrise and sunset; "
            "--moon prints today's moonrise and moonset; "
            "--lunar prints today's lunar date; "
            "--rainstorm prints the rainstorm reminder; "
            "--cyclone prints the tropical cyclone message; "
            "--humidest prints the most humid place; "
            "--least-humid prints the least humid place."
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
        "-S",
        "--summary",
        action="store_true",
        help="Print conditions, active warnings, and today's high and low",
    )
    parser.add_argument(
        "--forecast",
        action="store_true",
        help="Print the local weather forecast instead of current conditions",
    )
    parser.add_argument(
        "--outlook",
        action="store_true",
        help="Print the outlook from the local weather forecast",
    )
    parser.add_argument(
        "--forecast-period",
        action="store_true",
        help="Print the period covered by the local weather forecast",
    )
    parser.add_argument(
        "--forecast-desc",
        action="store_true",
        help="Print the description from the local weather forecast",
    )
    parser.add_argument(
        "--forecast-updated",
        action="store_true",
        help="Print when the local weather forecast was last updated",
    )
    parser.add_argument(
        "-g",
        "--situation",
        action="store_true",
        help="Print the general situation from the local forecast",
    )
    parser.add_argument(
        "-f",
        "--fire-danger",
        action="store_true",
        help="Print the fire danger warning from the local forecast",
    )
    parser.add_argument(
        "--tc-info",
        action="store_true",
        help="Print tropical cyclone information from the local forecast",
    )
    parser.add_argument(
        "-n",
        "--nine-day",
        action="store_true",
        help="Print the 9-day forecast",
    )
    parser.add_argument(
        "--sea-temp",
        action="store_true",
        help="Print the sea temperature from the 9-day forecast",
    )
    parser.add_argument(
        "--soil-temp",
        action="store_true",
        help="Print soil temperatures from the 9-day forecast",
    )
    parser.add_argument(
        "--nine-situation",
        action="store_true",
        help="Print the general situation from the 9-day forecast",
    )
    parser.add_argument(
        "--nine-updated",
        action="store_true",
        help="Print when the 9-day forecast was last updated",
    )
    parser.add_argument(
        "-Y",
        "--today",
        action="store_true",
        help="Print today's day from the 9-day forecast (Hong Kong calendar date)",
    )
    parser.add_argument(
        "--yesterday",
        action="store_true",
        help="Print yesterday's temperature, rainfall, and humidity at the Observatory",
    )
    parser.add_argument(
        "--grass",
        action="store_true",
        help="Print yesterday's grass minimum temperature at the Observatory",
    )
    parser.add_argument(
        "--accum-rain",
        action="store_true",
        help="Print accumulated rainfall from 1 January through yesterday at the Observatory",
    )
    parser.add_argument(
        "--avg-rain",
        action="store_true",
        help="Print the climatological normal of accumulated rainfall through yesterday",
    )
    parser.add_argument(
        "--radiation",
        action="store_true",
        help="Print yesterday's outdoor gamma radiation report from the Observatory",
    )
    parser.add_argument(
        "--bulletin",
        action="store_true",
        help="Print when yesterday's Observatory weather bulletin was issued",
    )
    parser.add_argument(
        "--radiation-note",
        action="store_true",
        help="Print the note on the normal outdoor radiation range",
    )
    parser.add_argument(
        "--radiation-weather",
        action="store_true",
        help="Print how outdoor radiation varies with the weather",
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
        "--forecast-icon",
        action="store_true",
        help="Print the weather icon for each day of the 9-day forecast",
    )
    parser.add_argument(
        "--quake",
        action="store_true",
        help="List the latest Observatory quick earthquake message",
    )
    parser.add_argument(
        "-q",
        "--felt",
        action="store_true",
        help="Print the latest locally felt earth tremor",
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
        "-A",
        "--aqhi",
        action="store_true",
        help="Print the current Air Quality Health Index by station",
    )
    parser.add_argument(
        "-U",
        "--sunrise",
        action="store_true",
        help="Print today's sunrise, sun transit, and sunset",
    )
    parser.add_argument(
        "-M",
        "--moon",
        action="store_true",
        help="Print today's moonrise, moon transit, and moonset",
    )
    parser.add_argument(
        "--lunar",
        action="store_true",
        help="Print today's lunar date from the Observatory calendar",
    )
    parser.add_argument(
        "-w",
        "--warnings",
        action="store_true",
        help="Print only active weather warnings",
    )
    parser.add_argument(
        "--warning-time",
        action="store_true",
        help="Print issue and expiry times for active weather warnings",
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
        "-i",
        "--icon-time",
        action="store_true",
        help="Print when the current weather icon was last updated",
    )
    parser.add_argument(
        "--icon",
        action="store_true",
        help="Print the current weather icon number and label",
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
        "--rain-period",
        action="store_true",
        help="Print the past-hour window for district rainfall",
    )
    parser.add_argument(
        "--hour-rain",
        action="store_true",
        help="Print past-hour rainfall from automatic weather stations",
    )
    parser.add_argument(
        "--hour-wettest",
        action="store_true",
        help="Print the wettest automatic station from the past hour",
    )
    parser.add_argument(
        "--hour-driest",
        action="store_true",
        help="Print the driest automatic station from the past hour",
    )
    parser.add_argument(
        "-R",
        "--wettest",
        action="store_true",
        help="Print the wettest rainfall district from the current report",
    )
    parser.add_argument(
        "-D",
        "--driest",
        action="store_true",
        help="Print the driest rainfall district from the current report",
    )
    parser.add_argument(
        "--rainstorm",
        action="store_true",
        help="Print the rainstorm reminder from the current report",
    )
    parser.add_argument(
        "-c",
        "--cyclone",
        action="store_true",
        help="Print the tropical cyclone message from the current report",
    )
    parser.add_argument(
        "--lightning",
        action="store_true",
        help="List lightning locations from the current report",
    )
    parser.add_argument(
        "-l",
        "--strikes",
        action="store_true",
        help="Print hourly cloud-to-ground and cloud-to-cloud lightning counts",
    )
    parser.add_argument(
        "--humidity",
        action="store_true",
        help="Print humidity readings from the current report",
    )
    parser.add_argument(
        "--humidest",
        action="store_true",
        help="Print the most humid place from the current report",
    )
    parser.add_argument(
        "--least-humid",
        action="store_true",
        help="Print the least humid place from the current report",
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
        "-O",
        "--overnight",
        action="store_true",
        help="Print the midnight-to-9am minimum temperature from the current report",
    )
    parser.add_argument(
        "-N",
        "--noon-rain",
        action="store_true",
        help="Print the midnight-to-noon rainfall note from the current report",
    )
    parser.add_argument(
        "-L",
        "--month-rain",
        action="store_true",
        help="Print last month's rainfall note from the current report",
    )
    parser.add_argument(
        "-y",
        "--year-rain",
        action="store_true",
        help="Print the January-to-last-month rainfall note from the current report",
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
        elif args.warning_time:
            warning_time = fetch_warning_time(timeout=args.timeout, lang=args.lang)
            if not warning_time.warnings:
                text = format_warning_time_miss(as_json=args.json)
            else:
                text = (
                    format_json(warning_time)
                    if args.json
                    else format_warning_time(warning_time)
                )
        elif args.warning_info:
            text = format_warning_info(
                fetch_warning_info(timeout=args.timeout, lang=args.lang),
                as_json=args.json,
            )
        elif args.forecast:
            forecast = fetch_forecast(timeout=args.timeout, lang=args.lang)
            text = format_json(forecast) if args.json else format_forecast(forecast)
        elif args.outlook:
            outlook = fetch_outlook(timeout=args.timeout, lang=args.lang)
            if outlook is None:
                text = format_outlook_miss(as_json=args.json)
            else:
                text = format_json(outlook) if args.json else format_outlook(outlook)
        elif args.forecast_period:
            forecast_period = fetch_forecast_period(timeout=args.timeout, lang=args.lang)
            if forecast_period is None:
                text = format_forecast_period_miss(as_json=args.json)
            else:
                text = (
                    format_json(forecast_period)
                    if args.json
                    else format_forecast_period(forecast_period)
                )
        elif args.forecast_desc:
            forecast_desc = fetch_forecast_desc(timeout=args.timeout, lang=args.lang)
            if forecast_desc is None:
                text = format_forecast_desc_miss(as_json=args.json)
            else:
                text = (
                    format_json(forecast_desc)
                    if args.json
                    else format_forecast_desc(forecast_desc)
                )
        elif args.forecast_updated:
            forecast_updated = fetch_forecast_updated(timeout=args.timeout, lang=args.lang)
            if forecast_updated is None:
                text = format_forecast_updated_miss(as_json=args.json)
            else:
                text = (
                    format_json(forecast_updated)
                    if args.json
                    else format_forecast_updated(forecast_updated)
                )
        elif args.situation:
            situation = fetch_situation(timeout=args.timeout, lang=args.lang)
            if situation is None:
                text = format_situation_miss(as_json=args.json)
            else:
                text = format_json(situation) if args.json else format_situation(situation)
        elif args.fire_danger:
            fire_danger = fetch_fire_danger(timeout=args.timeout, lang=args.lang)
            if fire_danger is None:
                text = format_fire_danger_miss(as_json=args.json)
            else:
                text = format_json(fire_danger) if args.json else format_fire_danger(fire_danger)
        elif args.tc_info:
            tc_info = fetch_tc_info(timeout=args.timeout, lang=args.lang)
            if tc_info is None:
                text = format_tc_info_miss(as_json=args.json)
            else:
                text = format_json(tc_info) if args.json else format_tc_info(tc_info)
        elif args.nine_day:
            nine_day = fetch_nine_day(timeout=args.timeout, lang=args.lang)
            text = format_json(nine_day) if args.json else format_nine_day(nine_day)
        elif args.sea_temp:
            sea_temp = fetch_sea_temp(timeout=args.timeout, lang=args.lang)
            if sea_temp is None:
                text = format_sea_temp_miss(as_json=args.json)
            else:
                text = format_json(sea_temp) if args.json else format_sea_temp(sea_temp)
        elif args.soil_temp:
            soil_temp = fetch_soil_temp(timeout=args.timeout, lang=args.lang)
            if soil_temp is None:
                text = format_soil_temp_miss(as_json=args.json)
            else:
                text = format_json(soil_temp) if args.json else format_soil_temp(soil_temp)
        elif args.nine_situation:
            nine_situation = fetch_nine_situation(timeout=args.timeout, lang=args.lang)
            if nine_situation is None:
                text = format_nine_situation_miss(as_json=args.json)
            else:
                text = (
                    format_json(nine_situation)
                    if args.json
                    else format_nine_situation(nine_situation)
                )
        elif args.nine_updated:
            nine_updated = fetch_nine_updated(timeout=args.timeout, lang=args.lang)
            if nine_updated is None:
                text = format_nine_updated_miss(as_json=args.json)
            else:
                text = format_json(nine_updated) if args.json else format_nine_updated(nine_updated)
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
        elif args.yesterday:
            yesterday = fetch_yesterday(timeout=args.timeout, lang=args.lang)
            if yesterday is None:
                text = format_yesterday_miss(as_json=args.json)
            else:
                text = format_json(yesterday) if args.json else format_yesterday(yesterday)
        elif args.grass:
            grass = fetch_grass(timeout=args.timeout, lang=args.lang)
            if grass is None:
                text = format_grass_miss(as_json=args.json)
            else:
                text = format_json(grass) if args.json else format_grass(grass)
        elif args.accum_rain:
            accum_rain = fetch_accum_rain(timeout=args.timeout, lang=args.lang)
            if accum_rain is None:
                text = format_accum_rain_miss(as_json=args.json)
            else:
                text = format_json(accum_rain) if args.json else format_accum_rain(accum_rain)
        elif args.avg_rain:
            avg_rain = fetch_avg_rain(timeout=args.timeout, lang=args.lang)
            if avg_rain is None:
                text = format_avg_rain_miss(as_json=args.json)
            else:
                text = format_json(avg_rain) if args.json else format_avg_rain(avg_rain)
        elif args.radiation:
            radiation = fetch_radiation(timeout=args.timeout, lang=args.lang)
            if radiation is None:
                text = format_radiation_miss(as_json=args.json)
            else:
                text = format_json(radiation) if args.json else format_radiation(radiation)
        elif args.bulletin:
            bulletin = fetch_bulletin(timeout=args.timeout, lang=args.lang)
            if bulletin is None:
                text = format_bulletin_miss(as_json=args.json)
            else:
                text = format_json(bulletin) if args.json else format_bulletin(bulletin)
        elif args.radiation_note:
            radiation_note = fetch_radiation_note(timeout=args.timeout, lang=args.lang)
            if radiation_note is None:
                text = format_radiation_note_miss(as_json=args.json)
            else:
                text = (
                    format_json(radiation_note)
                    if args.json
                    else format_radiation_note(radiation_note)
                )
        elif args.radiation_weather:
            radiation_weather = fetch_radiation_weather(timeout=args.timeout, lang=args.lang)
            if radiation_weather is None:
                text = format_radiation_weather_miss(as_json=args.json)
            else:
                text = (
                    format_json(radiation_weather)
                    if args.json
                    else format_radiation_weather(radiation_weather)
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
        elif args.forecast_icon:
            forecast_icon = fetch_forecast_icon(timeout=args.timeout, lang=args.lang)
            if not forecast_icon.days:
                text = format_forecast_icon_miss(as_json=args.json)
            else:
                text = (
                    format_json(forecast_icon)
                    if args.json
                    else format_forecast_icon(forecast_icon)
                )
        elif args.quake:
            quakes = fetch_quakes(timeout=args.timeout, lang=args.lang)
            text = format_json(quakes) if args.json else format_quakes(quakes)
        elif args.felt:
            felt = fetch_felt(timeout=args.timeout, lang=args.lang)
            if felt is None:
                text = format_felt_miss(as_json=args.json)
            else:
                text = format_json(felt) if args.json else format_felt(felt)
        elif args.visibility:
            visibility = fetch_visibility(timeout=args.timeout, lang=args.lang)
            text = format_json(visibility) if args.json else format_visibility(visibility)
        elif args.tide:
            tide = fetch_tide(timeout=args.timeout, lang=args.lang)
            if not tide.events:
                text = format_tide_miss(as_json=args.json)
            else:
                text = format_json(tide) if args.json else format_tide(tide)
        elif args.aqhi:
            aqhi = fetch_aqhi(timeout=args.timeout, lang=args.lang)
            if not aqhi.readings:
                text = format_aqhi_miss(as_json=args.json)
            else:
                text = format_json(aqhi) if args.json else format_aqhi(aqhi)
        elif args.sunrise:
            sunrise = fetch_sunrise(timeout=args.timeout, lang=args.lang)
            if sunrise is None:
                text = format_sunrise_miss(as_json=args.json)
            else:
                text = format_json(sunrise) if args.json else format_sunrise(sunrise)
        elif args.moon:
            moon = fetch_moon(timeout=args.timeout, lang=args.lang)
            if moon is None:
                text = format_moon_miss(as_json=args.json)
            else:
                text = format_json(moon) if args.json else format_moon(moon)
        elif args.lunar:
            lunar = fetch_lunar(timeout=args.timeout, lang=args.lang)
            if lunar is None:
                text = format_lunar_miss(as_json=args.json)
            else:
                text = format_json(lunar) if args.json else format_lunar(lunar)
        elif args.uv:
            uv = fetch_uv(timeout=args.timeout, lang=args.lang)
            text = format_json(uv) if args.json else format_uv(uv)
        elif args.icon_time:
            icon_time = fetch_icon_time(timeout=args.timeout, lang=args.lang)
            if icon_time is None:
                text = format_icon_time_miss(as_json=args.json)
            else:
                text = format_json(icon_time) if args.json else format_icon_time(icon_time)
        elif args.icon:
            icon = fetch_icon(timeout=args.timeout, lang=args.lang)
            if icon is None:
                text = format_icon_miss(as_json=args.json)
            else:
                text = format_json(icon) if args.json else format_icon(icon)
        elif args.tips:
            tips = fetch_tips(timeout=args.timeout, lang=args.lang)
            text = format_json(tips) if args.json else format_tips(tips)
        elif args.rain:
            rain = fetch_rain(timeout=args.timeout, lang=args.lang)
            text = format_json(rain) if args.json else format_rain(rain)
        elif args.rain_period:
            rain_period = fetch_rain_period(timeout=args.timeout, lang=args.lang)
            if rain_period is None:
                text = format_rain_period_miss(as_json=args.json)
            else:
                text = format_json(rain_period) if args.json else format_rain_period(rain_period)
        elif args.hour_rain:
            hour_rain = fetch_hour_rain(timeout=args.timeout, lang=args.lang)
            if not hour_rain.readings:
                text = format_hour_rain_miss(as_json=args.json)
            else:
                text = format_json(hour_rain) if args.json else format_hour_rain(hour_rain)
        elif args.hour_wettest:
            hour_wettest = fetch_hour_wettest(timeout=args.timeout, lang=args.lang)
            if hour_wettest is None:
                text = format_hour_rain_miss(as_json=args.json)
            else:
                text = format_json(hour_wettest) if args.json else format_hour_wettest(hour_wettest)
        elif args.hour_driest:
            hour_driest = fetch_hour_driest(timeout=args.timeout, lang=args.lang)
            if hour_driest is None:
                text = format_hour_rain_miss(as_json=args.json)
            else:
                text = format_json(hour_driest) if args.json else format_hour_driest(hour_driest)
        elif args.wettest:
            wettest = fetch_wettest(timeout=args.timeout, lang=args.lang)
            if wettest is None:
                text = format_wettest_miss(as_json=args.json)
            else:
                text = format_json(wettest) if args.json else format_wettest(wettest)
        elif args.driest:
            driest = fetch_driest(timeout=args.timeout, lang=args.lang)
            if driest is None:
                text = format_driest_miss(as_json=args.json)
            else:
                text = format_json(driest) if args.json else format_driest(driest)
        elif args.rainstorm:
            rainstorm = fetch_rainstorm(timeout=args.timeout, lang=args.lang)
            if rainstorm is None:
                text = format_rainstorm_miss(as_json=args.json)
            else:
                text = format_json(rainstorm) if args.json else format_rainstorm(rainstorm)
        elif args.cyclone:
            cyclone = fetch_cyclone(timeout=args.timeout, lang=args.lang)
            if cyclone is None:
                text = format_cyclone_miss(as_json=args.json)
            else:
                text = format_json(cyclone) if args.json else format_cyclone(cyclone)
        elif args.lightning:
            lightning = fetch_lightning(timeout=args.timeout, lang=args.lang)
            text = format_json(lightning) if args.json else format_lightning(lightning)
        elif args.strikes:
            strikes = fetch_strikes(timeout=args.timeout, lang=args.lang)
            if not strikes.counts:
                text = format_strikes_miss(as_json=args.json)
            else:
                text = format_json(strikes) if args.json else format_strikes(strikes)
        elif args.humidity:
            humidity = fetch_humidity(timeout=args.timeout, lang=args.lang)
            text = format_json(humidity) if args.json else format_humidity(humidity)
        elif args.humidest:
            humidest = fetch_humidest(timeout=args.timeout, lang=args.lang)
            if humidest is None:
                text = format_humidest_miss(as_json=args.json)
            else:
                text = format_json(humidest) if args.json else format_humidest(humidest)
        elif args.least_humid:
            least_humid = fetch_least_humid(timeout=args.timeout, lang=args.lang)
            if least_humid is None:
                text = format_least_humid_miss(as_json=args.json)
            else:
                text = format_json(least_humid) if args.json else format_least_humid(least_humid)
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
        elif args.overnight:
            overnight = fetch_overnight(timeout=args.timeout, lang=args.lang)
            if overnight is None:
                text = format_overnight_miss(as_json=args.json)
            else:
                text = format_json(overnight) if args.json else format_overnight(overnight)
        elif args.noon_rain:
            noon_rain = fetch_noon_rain(timeout=args.timeout, lang=args.lang)
            if noon_rain is None:
                text = format_noon_rain_miss(as_json=args.json)
            else:
                text = format_json(noon_rain) if args.json else format_noon_rain(noon_rain)
        elif args.month_rain:
            month_rain = fetch_month_rain(timeout=args.timeout, lang=args.lang)
            if month_rain is None:
                text = format_month_rain_miss(as_json=args.json)
            else:
                text = format_json(month_rain) if args.json else format_month_rain(month_rain)
        elif args.year_rain:
            year_rain = fetch_year_rain(timeout=args.timeout, lang=args.lang)
            if year_rain is None:
                text = format_year_rain_miss(as_json=args.json)
            else:
                text = format_json(year_rain) if args.json else format_year_rain(year_rain)
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
        elif args.summary:
            summary = fetch_summary(timeout=args.timeout, lang=args.lang)
            text = format_json(summary) if args.json else format_summary(summary)
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
