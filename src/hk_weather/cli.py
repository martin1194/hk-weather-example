"""Command-line entrypoint for current Hong Kong weather."""

from __future__ import annotations

import argparse
import sys

from hk_weather.hko import (
    WeatherError,
    fetch_aqhi,
    fetch_current,
    fetch_driest,
    fetch_nowcast,
    fetch_daily_rain,
    fetch_lau_fau_rain,
    fetch_forecast,
    fetch_outlook,
    fetch_coastal,
    fetch_coast_report,
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
    fetch_sunshine,
    fetch_daily_sun,
    fetch_max_uv,
    fetch_uv_peak,
    fetch_mean_uv,
    fetch_dose,
    fetch_hourly_dose,
    fetch_accum_rain,
    fetch_avg_rain,
    fetch_radiation,
    fetch_bulletin,
    fetch_radiation_note,
    fetch_radiation_weather,
    fetch_radiation_ground,
    fetch_radiation_provisional,
    fetch_coldest,
    fetch_cyclone,
    fetch_hottest,
    fetch_humidest,
    fetch_humidity,
    fetch_humidity_time,
    fetch_minute_humidity,
    fetch_mean_humidity,
    fetch_tai_mo_humidity,
    fetch_icon_time,
    fetch_icon,
    fetch_current_updated,
    fetch_least_humid,
    fetch_lightning,
    fetch_lunar,
    fetch_moon,
    fetch_month_rain,
    fetch_nine_day,
    fetch_nine_situation,
    fetch_nine_updated,
    fetch_nine_weather,
    fetch_nine_temp,
    fetch_nine_humidity,
    fetch_sea_temp,
    fetch_soil_temp,
    fetch_year_rain,
    fetch_noon_rain,
    fetch_overnight,
    fetch_psr,
    fetch_quakes,
    fetch_rain,
    fetch_rain_period,
    fetch_rain_maint,
    fetch_rainstorm,
    fetch_stations,
    fetch_strikes,
    fetch_daily_strikes,
    fetch_cloud_strikes,
    fetch_summary,
    fetch_situation,
    fetch_sunrise,
    fetch_wettest,
    fetch_temps,
    fetch_temp_time,
    fetch_minute_temp,
    fetch_since_midnight,
    fetch_pressure,
    fetch_mean_pressure,
    fetch_minute_grass,
    fetch_daily_grass,
    fetch_obs_grass,
    fetch_temp_diff,
    fetch_heat_index,
    fetch_daily_heat,
    fetch_wbgt,
    fetch_wet_bulb,
    fetch_airport_wet,
    fetch_solar,
    fetch_global_solar,
    fetch_tc_info,
    fetch_tide,
    fetch_tide_hour,
    fetch_tide_latest,
    fetch_tips,
    fetch_lamppost,
    fetch_today,
    fetch_tomorrow,
    fetch_uv,
    fetch_fifteen_uv,
    fetch_visibility,
    fetch_reduced_vis,
    fetch_warning_info,
    fetch_warnings,
    fetch_warning_time,
    fetch_weekend,
    fetch_wind,
    fetch_gust,
    fetch_prevailing,
    fetch_cheung_prevailing,
    fetch_mean_wind,
    fetch_cheung_wind,
    fetch_forecast_icon,
    fetch_yesterday,
    fetch_mean_temp,
    fetch_tai_mo_temp,
    fetch_tai_mo_min,
    fetch_tai_mo_max,
    fetch_max_temp,
    fetch_min_temp,
    fetch_dew_point,
    fetch_park_dew,
    fetch_cloud,
    fetch_evaporation,
    fetch_evapotranspiration,
    filter_stations,
    format_aqhi,
    format_aqhi_miss,
    format_day_miss,
    format_driest,
    format_driest_miss,
    format_nowcast,
    format_nowcast_miss,
    format_daily_rain,
    format_daily_rain_miss,
    format_lau_fau_rain_miss,
    format_forecast,
    format_outlook,
    format_outlook_miss,
    format_coastal,
    format_coastal_miss,
    format_coast_report,
    format_coast_report_miss,
    format_forecast_period,
    format_forecast_period_miss,
    format_forecast_desc,
    format_forecast_desc_miss,
    format_forecast_updated,
    format_forecast_updated_miss,
    format_grass,
    format_grass_miss,
    format_sunshine,
    format_sunshine_miss,
    format_daily_sun,
    format_daily_sun_miss,
    format_max_uv,
    format_max_uv_miss,
    format_uv_peak,
    format_uv_peak_miss,
    format_mean_uv,
    format_mean_uv_miss,
    format_dose,
    format_dose_miss,
    format_hourly_dose,
    format_hourly_dose_miss,
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
    format_radiation_ground,
    format_radiation_ground_miss,
    format_radiation_provisional,
    format_radiation_provisional_miss,
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
    format_humidity_time,
    format_humidity_time_miss,
    format_minute_humidity,
    format_minute_humidity_miss,
    format_mean_humidity,
    format_mean_humidity_miss,
    format_tai_mo_humidity_miss,
    format_hour_rain,
    format_hour_rain_miss,
    format_hour_wettest,
    format_hour_driest,
    format_icon_time,
    format_icon_time_miss,
    format_icon,
    format_icon_miss,
    format_current_updated,
    format_current_updated_miss,
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
    format_nine_weather,
    format_nine_weather_miss,
    format_nine_temp,
    format_nine_temp_miss,
    format_nine_humidity,
    format_nine_humidity_miss,
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
    format_rain_maint,
    format_rain_maint_miss,
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
    format_daily_strikes,
    format_daily_strikes_miss,
    format_cloud_strikes,
    format_cloud_strikes_miss,
    format_sunrise,
    format_sunrise_miss,
    format_temps,
    format_temp_time,
    format_temp_time_miss,
    format_minute_temp,
    format_minute_temp_miss,
    format_since_midnight,
    format_since_midnight_miss,
    format_pressure,
    format_pressure_miss,
    format_mean_pressure,
    format_mean_pressure_miss,
    format_minute_grass,
    format_minute_grass_miss,
    format_daily_grass,
    format_daily_grass_miss,
    format_obs_grass_miss,
    format_temp_diff,
    format_temp_diff_miss,
    format_heat_index,
    format_heat_index_miss,
    format_daily_heat,
    format_daily_heat_miss,
    format_wbgt,
    format_wbgt_miss,
    format_wet_bulb,
    format_wet_bulb_miss,
    format_airport_wet_miss,
    format_solar,
    format_solar_miss,
    format_global_solar,
    format_global_solar_miss,
    format_tide,
    format_tide_miss,
    format_tide_hour,
    format_tide_hour_miss,
    format_tide_latest,
    format_tide_latest_miss,
    format_tc_info,
    format_tc_info_miss,
    format_tips,
    format_lamppost,
    format_lamppost_miss,
    format_today_miss,
    format_tomorrow,
    format_tomorrow_miss,
    format_uv,
    format_fifteen_uv,
    format_fifteen_uv_miss,
    format_visibility,
    format_reduced_vis,
    format_reduced_vis_miss,
    format_warning_info,
    format_wettest,
    format_wettest_miss,
    format_warnings,
    format_warning_time,
    format_warning_time_miss,
    format_weekend,
    format_weekend_miss,
    format_wind,
    format_gust,
    format_gust_miss,
    format_prevailing,
    format_prevailing_miss,
    format_cheung_prevailing_miss,
    format_mean_wind,
    format_mean_wind_miss,
    format_cheung_wind_miss,
    format_forecast_icon,
    format_forecast_icon_miss,
    format_yesterday,
    format_yesterday_miss,
    format_mean_temp,
    format_mean_temp_miss,
    format_tai_mo_temp,
    format_tai_mo_temp_miss,
    format_tai_mo_min,
    format_tai_mo_min_miss,
    format_tai_mo_max,
    format_tai_mo_max_miss,
    format_max_temp,
    format_max_temp_miss,
    format_min_temp,
    format_min_temp_miss,
    format_dew_point,
    format_dew_point_miss,
    format_park_dew_miss,
    format_cloud,
    format_cloud_miss,
    format_evaporation,
    format_evaporation_miss,
    format_evapotranspiration,
    format_evapotranspiration_miss,
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
            "--coastal prints the South China coastal waters forecast; "
            "--coast-report prints the latest coastal station reports; "
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
            "--nine-weather prints each day's weather from the 9-day forecast; "
            "--nine-temp prints each day's high and low from the 9-day forecast; "
            "--nine-humidity prints each day's humidity from the 9-day forecast; "
            "--warnings lists active warnings; "
            "--warning-time prints when active warnings were issued; "
            "--uv prints the UV index; "
            "--fifteen-uv prints the latest 15-minute mean UV index; "
            "--icon-time prints when the weather icon changed; "
            "--icon prints the current weather icon; "
            "--current-updated prints when the current weather report was updated; "
            "--tips prints special weather tips; "
            "--lamppost prints the experimental smart-lamppost reading; "
            "--stations lists each station; --list-places lists their names; "
            "--place NAME filters those stations; --rain lists district rainfall; "
            "--rain-period prints the district rainfall window; "
            "--rain-maint lists districts whose rainfall gauge is under maintenance; "
            "--hour-rain lists past-hour rainfall at automatic stations; "
            "--hour-wettest prints the wettest of those stations; "
            "--hour-driest prints the driest of those stations; "
            "--lightning lists lightning locations; --strikes lists hourly lightning counts; "
            "--daily-strikes prints the latest daily cloud-to-ground count; "
            "--cloud-strikes prints the latest daily cloud-to-cloud count; "
            "--humidity lists humidity readings; "
            "--humidity-time prints when those readings were recorded; "
            "--minute-humidity prints the latest 1-minute mean humidity; "
            "--mean-humidity prints the latest daily mean humidity; "
            "--tai-mo-humidity prints the latest daily mean humidity at Tai Mo Shan; "
            "--temps lists temperatures by place; "
            "--temp-time prints when those temperatures were recorded; "
            "--minute-temp prints the latest 1-minute mean temperature; "
            "--since-midnight prints each station's high and low since midnight; "
            "--pressure prints the latest 1-minute sea level pressure; "
            "--mean-pressure prints the latest daily mean pressure; "
            "--minute-grass prints the latest 1-minute grass temperature; "
            "--daily-grass prints the latest daily grass minimum; "
            "--obs-grass prints the latest daily grass minimum at the Observatory; "
            "--temp-diff prints the past 24-hour temperature change; "
            "--heat-index prints the latest Hong Kong Heat Index; "
            "--daily-heat prints the latest daily maximum heat index at King's Park; "
            "--wbgt prints the latest Wet Bulb Globe Temperature; "
            "--wet-bulb prints the latest daily wet-bulb temperature; "
            "--airport-wet prints the latest daily wet-bulb temperature at the airport; "
            "--solar prints the latest solar radiation; "
            "--global-solar prints the latest daily global solar radiation; "
            "--wind lists the forecast wind; "
            "--gust prints the latest 10-minute wind and gust; "
            "--prevailing prints the latest prevailing wind direction; "
            "--cheung-prevailing prints the latest prevailing wind at Cheung Chau; "
            "--mean-wind prints the latest daily mean wind speed; "
            "--cheung-wind prints the latest daily mean wind speed at Cheung Chau; "
            "--forecast-icon prints each day's weather icon; "
            "--quake lists the latest earthquake message; "
            "--felt prints the locally felt earth tremor; --today prints today; "
            "--yesterday prints yesterday's Observatory summary; "
            "--mean-temp prints the latest daily mean temperature; "
            "--tai-mo-temp prints the latest daily mean temperature at Tai Mo Shan; "
            "--max-temp prints the latest daily maximum temperature; "
            "--min-temp prints the latest daily minimum temperature; "
            "--tai-mo-min prints the latest daily minimum temperature at Tai Mo Shan; "
            "--tai-mo-max prints the latest daily maximum temperature at Tai Mo Shan; "
            "--dew-point prints the latest daily mean dew point; "
            "--park-dew prints the latest daily mean dew point at King's Park; "
            "--cloud prints the latest daily mean cloud amount; "
            "--evaporation prints the latest daily evaporation; "
            "--evapotranspiration prints the latest monthly potential evapotranspiration; "
            "--grass prints yesterday's grass minimum; "
            "--sunshine prints yesterday's sunshine duration; "
            "--daily-sun prints the latest daily bright sunshine total; "
            "--max-uv prints yesterday's maximum UV index; "
            "--uv-peak prints the latest daily maximum UV index and its period; "
            "--mean-uv prints yesterday's mean UV index; "
            "--dose prints yesterday's gamma dose rate; "
            "--hourly-dose prints the latest hourly gamma dose rate; "
            "--accum-rain prints accumulated rainfall since 1 January; "
            "--avg-rain prints the climatological rainfall normal; "
            "--radiation prints yesterday's gamma radiation report; "
            "--bulletin prints when yesterday's bulletin was issued; "
            "--radiation-note prints the normal radiation range; "
            "--radiation-weather prints how radiation varies with the weather; "
            "--radiation-ground prints how radiation varies with the ground; "
            "--radiation-provisional prints the provisional radiation note; "
            "--tomorrow prints tomorrow; "
            "--day N prints forecast day N (1 is the first entry); "
            "--psr lists the chance of significant rain; "
            "--warning-info prints detailed warning messages; "
            "--weekend prints Saturday and Sunday; "
            "--visibility lists 10-minute mean visibility; "
            "--reduced-vis prints the latest daily hours of reduced visibility; "
            "--hottest prints the warmest place; "
            "--coldest prints the coolest place; "
            "--overnight prints the midnight-to-9am minimum; "
            "--noon-rain prints the midnight-to-noon rainfall note; "
            "--month-rain prints last month's rainfall note; "
            "--year-rain prints the January-to-last-month rainfall note; "
            "--wettest prints the wettest district; "
            "--driest prints the driest district; "
            "--nowcast prints the heaviest rainfall-nowcast cell in each half-hour; "
            "--daily-rain prints the latest daily rainfall total; "
            "--lau-fau-rain prints the latest daily rainfall at Lau Fau Shan; "
            "--tide prints today's high and low tides; "
            "--tide-hour prints today's hourly tide heights; "
            "--tide-latest prints the latest observed tide height; "
            "--aqhi prints the air quality health index; "
            "--sunrise prints today's sunrise and sunset; "
            "--moon prints today's moonrise and moonset; "
            "--lunar prints today's lunar date; "
            "--rainstorm prints the rainstorm reminder; "
            "--cyclone prints the tropical cyclone message; "
            "--humidest prints the most humid place; "
            "--least-humid prints the least humid place; "
            "--mean-humidity prints the latest daily mean humidity."
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
        "--coastal",
        action="store_true",
        help="Print the South China coastal waters area forecast",
    )
    parser.add_argument(
        "--coast-report",
        action="store_true",
        help="Print the latest reports from South China coastal stations",
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
        "--nine-weather",
        action="store_true",
        help="Print each day's weather from the 9-day forecast",
    )
    parser.add_argument(
        "--nine-temp",
        action="store_true",
        help="Print each day's high and low from the 9-day forecast",
    )
    parser.add_argument(
        "--nine-humidity",
        action="store_true",
        help="Print each day's humidity range from the 9-day forecast",
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
        "--mean-temp",
        action="store_true",
        help="Print the latest daily mean temperature at the Observatory",
    )
    parser.add_argument(
        "--tai-mo-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Tai Mo Shan",
    )
    parser.add_argument(
        "--max-temp",
        action="store_true",
        help="Print the latest daily maximum temperature at the Observatory",
    )
    parser.add_argument(
        "--min-temp",
        action="store_true",
        help="Print the latest daily minimum temperature at the Observatory",
    )
    parser.add_argument(
        "--tai-mo-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Tai Mo Shan",
    )
    parser.add_argument(
        "--tai-mo-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Tai Mo Shan",
    )
    parser.add_argument(
        "--dew-point",
        action="store_true",
        help="Print the latest daily mean dew point at the Observatory",
    )
    parser.add_argument(
        "--park-dew",
        action="store_true",
        help="Print the latest daily mean dew point at King's Park",
    )
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Print the latest daily mean cloud amount at the Observatory",
    )
    parser.add_argument(
        "--evaporation",
        action="store_true",
        help="Print the latest daily total evaporation at King's Park",
    )
    parser.add_argument(
        "--evapotranspiration",
        action="store_true",
        help="Print the latest monthly potential evapotranspiration at King's Park",
    )
    parser.add_argument(
        "--grass",
        action="store_true",
        help="Print yesterday's grass minimum temperature at the Observatory",
    )
    parser.add_argument(
        "--sunshine",
        action="store_true",
        help="Print yesterday's sunshine duration at King's Park",
    )
    parser.add_argument(
        "--daily-sun",
        action="store_true",
        help="Print the latest daily bright sunshine total at King's Park",
    )
    parser.add_argument(
        "--max-uv",
        action="store_true",
        help="Print yesterday's maximum UV index at King's Park",
    )
    parser.add_argument(
        "--uv-peak",
        action="store_true",
        help="Print the latest daily maximum UV index and when it occurred",
    )
    parser.add_argument(
        "--mean-uv",
        action="store_true",
        help="Print yesterday's mean UV index at King's Park",
    )
    parser.add_argument(
        "--dose",
        action="store_true",
        help="Print yesterday's gamma dose rate at King's Park",
    )
    parser.add_argument(
        "--hourly-dose",
        action="store_true",
        help="Print the latest hourly mean ambient gamma dose rate",
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
        "--radiation-ground",
        action="store_true",
        help="Print how outdoor radiation varies with the ground",
    )
    parser.add_argument(
        "--radiation-provisional",
        action="store_true",
        help="Print the provisional-data note on the radiation report",
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
        "--gust",
        action="store_true",
        help="Print the latest 10-minute wind and gust at automatic stations",
    )
    parser.add_argument(
        "--prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Waglan Island",
    )
    parser.add_argument(
        "--cheung-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Cheung Chau",
    )
    parser.add_argument(
        "--mean-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Waglan Island",
    )
    parser.add_argument(
        "--cheung-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Cheung Chau",
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
        "--reduced-vis",
        action="store_true",
        help="Print the latest daily hours of reduced visibility at the airport",
    )
    parser.add_argument(
        "-I",
        "--tide",
        action="store_true",
        help="Print today's high and low tides at Quarry Bay",
    )
    parser.add_argument(
        "--tide-hour",
        action="store_true",
        help="Print today's hourly tide heights at Quarry Bay",
    )
    parser.add_argument(
        "--tide-latest",
        action="store_true",
        help="Print the latest observed tide height at tide stations",
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
        "--fifteen-uv",
        action="store_true",
        help="Print the latest 15-minute mean UV index at King's Park",
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
        "--current-updated",
        action="store_true",
        help="Print when the current weather report was last updated",
    )
    parser.add_argument(
        "-t",
        "--tips",
        action="store_true",
        help="Print special weather tips",
    )
    parser.add_argument(
        "--lamppost",
        action="store_true",
        help="Print the experimental reading from smart lamppost GF3637",
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
        "--rain-maint",
        action="store_true",
        help="Print districts whose rainfall gauge is under maintenance",
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
        "--nowcast",
        action="store_true",
        help="Print the heaviest cell in each half-hour of the rainfall nowcast",
    )
    parser.add_argument(
        "--daily-rain",
        action="store_true",
        help="Print the latest daily total rainfall at the Observatory",
    )
    parser.add_argument(
        "--lau-fau-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Lau Fau Shan",
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
        "--daily-strikes",
        action="store_true",
        help="Print the latest daily cloud-to-ground lightning count over Hong Kong",
    )
    parser.add_argument(
        "--cloud-strikes",
        action="store_true",
        help="Print the latest daily cloud-to-cloud lightning count over Hong Kong",
    )
    parser.add_argument(
        "--humidity",
        action="store_true",
        help="Print humidity readings from the current report",
    )
    parser.add_argument(
        "--humidity-time",
        action="store_true",
        help="Print when the current humidity readings were recorded",
    )
    parser.add_argument(
        "--minute-humidity",
        action="store_true",
        help="Print the latest 1-minute mean humidity at automatic stations",
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
        "--mean-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at the Observatory",
    )
    parser.add_argument(
        "--tai-mo-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Tai Mo Shan",
    )
    parser.add_argument(
        "--temps",
        action="store_true",
        help="Print temperatures by place from the current report",
    )
    parser.add_argument(
        "--temp-time",
        action="store_true",
        help="Print when the current temperatures were recorded",
    )
    parser.add_argument(
        "--minute-temp",
        action="store_true",
        help="Print the latest 1-minute mean temperature at automatic stations",
    )
    parser.add_argument(
        "--since-midnight",
        action="store_true",
        help="Print each station's maximum and minimum temperature since midnight",
    )
    parser.add_argument(
        "--pressure",
        action="store_true",
        help="Print the latest 1-minute mean sea level pressure at automatic stations",
    )
    parser.add_argument(
        "--mean-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at the Observatory",
    )
    parser.add_argument(
        "--minute-grass",
        action="store_true",
        help="Print the latest 1-minute mean grass temperature at automatic stations",
    )
    parser.add_argument(
        "--daily-grass",
        action="store_true",
        help="Print the latest daily grass minimum at King's Park",
    )
    parser.add_argument(
        "--obs-grass",
        action="store_true",
        help="Print the latest daily grass minimum at the Observatory",
    )
    parser.add_argument(
        "--temp-diff",
        action="store_true",
        help="Print the past 24-hour temperature change at automatic stations",
    )
    parser.add_argument(
        "--heat-index",
        action="store_true",
        help="Print the latest 10-minute mean Hong Kong Heat Index",
    )
    parser.add_argument(
        "--daily-heat",
        action="store_true",
        help="Print the latest daily maximum Hong Kong Heat Index at King's Park",
    )
    parser.add_argument(
        "--wbgt",
        action="store_true",
        help="Print the latest 60-minute mean Wet Bulb Globe Temperature",
    )
    parser.add_argument(
        "--wet-bulb",
        action="store_true",
        help="Print the latest daily mean wet-bulb temperature at the Observatory",
    )
    parser.add_argument(
        "--airport-wet",
        action="store_true",
        help="Print the latest daily mean wet-bulb temperature at the airport",
    )
    parser.add_argument(
        "--solar",
        action="store_true",
        help="Print the latest 1-minute solar radiation at automatic stations",
    )
    parser.add_argument(
        "--global-solar",
        action="store_true",
        help="Print the latest daily global solar radiation at King's Park",
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
        elif args.coastal:
            coastal = fetch_coastal(timeout=args.timeout, lang=args.lang)
            if not coastal.areas:
                text = format_coastal_miss(as_json=args.json)
            else:
                text = format_json(coastal) if args.json else format_coastal(coastal)
        elif args.coast_report:
            coast_report = fetch_coast_report(timeout=args.timeout, lang=args.lang)
            if not coast_report.stations:
                text = format_coast_report_miss(as_json=args.json)
            else:
                text = format_json(coast_report) if args.json else format_coast_report(coast_report)
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
        elif args.nine_weather:
            nine_weather = fetch_nine_weather(timeout=args.timeout, lang=args.lang)
            if not nine_weather.days:
                text = format_nine_weather_miss(as_json=args.json)
            else:
                text = format_json(nine_weather) if args.json else format_nine_weather(nine_weather)
        elif args.nine_temp:
            nine_temp = fetch_nine_temp(timeout=args.timeout, lang=args.lang)
            if not nine_temp.days:
                text = format_nine_temp_miss(as_json=args.json)
            else:
                text = format_json(nine_temp) if args.json else format_nine_temp(nine_temp)
        elif args.nine_humidity:
            nine_humidity = fetch_nine_humidity(timeout=args.timeout, lang=args.lang)
            if not nine_humidity.days:
                text = format_nine_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(nine_humidity) if args.json else format_nine_humidity(nine_humidity)
                )
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
        elif args.mean_temp:
            mean_temp = fetch_mean_temp(timeout=args.timeout, lang=args.lang)
            if mean_temp is None:
                text = format_mean_temp_miss(as_json=args.json)
            else:
                text = format_json(mean_temp) if args.json else format_mean_temp(mean_temp)
        elif args.tai_mo_temp:
            tai_mo_temp = fetch_tai_mo_temp(timeout=args.timeout, lang=args.lang)
            if tai_mo_temp is None:
                text = format_tai_mo_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mo_temp) if args.json else format_tai_mo_temp(tai_mo_temp)
                )
        elif args.max_temp:
            max_temp = fetch_max_temp(timeout=args.timeout, lang=args.lang)
            if max_temp is None:
                text = format_max_temp_miss(as_json=args.json)
            else:
                text = format_json(max_temp) if args.json else format_max_temp(max_temp)
        elif args.min_temp:
            min_temp = fetch_min_temp(timeout=args.timeout, lang=args.lang)
            if min_temp is None:
                text = format_min_temp_miss(as_json=args.json)
            else:
                text = format_json(min_temp) if args.json else format_min_temp(min_temp)
        elif args.tai_mo_min:
            tai_mo_min = fetch_tai_mo_min(timeout=args.timeout, lang=args.lang)
            if tai_mo_min is None:
                text = format_tai_mo_min_miss(as_json=args.json)
            else:
                text = format_json(tai_mo_min) if args.json else format_tai_mo_min(tai_mo_min)
        elif args.tai_mo_max:
            tai_mo_max = fetch_tai_mo_max(timeout=args.timeout, lang=args.lang)
            if tai_mo_max is None:
                text = format_tai_mo_max_miss(as_json=args.json)
            else:
                text = format_json(tai_mo_max) if args.json else format_tai_mo_max(tai_mo_max)
        elif args.dew_point:
            dew_point = fetch_dew_point(timeout=args.timeout, lang=args.lang)
            if dew_point is None:
                text = format_dew_point_miss(as_json=args.json)
            else:
                text = format_json(dew_point) if args.json else format_dew_point(dew_point)
        elif args.park_dew:
            park_dew = fetch_park_dew(timeout=args.timeout, lang=args.lang)
            if park_dew is None:
                text = format_park_dew_miss(as_json=args.json)
            else:
                text = format_json(park_dew) if args.json else format_dew_point(park_dew)
        elif args.cloud:
            cloud = fetch_cloud(timeout=args.timeout, lang=args.lang)
            if cloud is None:
                text = format_cloud_miss(as_json=args.json)
            else:
                text = format_json(cloud) if args.json else format_cloud(cloud)
        elif args.evaporation:
            evaporation = fetch_evaporation(timeout=args.timeout, lang=args.lang)
            if evaporation is None:
                text = format_evaporation_miss(as_json=args.json)
            else:
                text = format_json(evaporation) if args.json else format_evaporation(evaporation)
        elif args.evapotranspiration:
            evapotranspiration = fetch_evapotranspiration(timeout=args.timeout, lang=args.lang)
            if evapotranspiration is None:
                text = format_evapotranspiration_miss(as_json=args.json)
            else:
                text = (
                    format_json(evapotranspiration)
                    if args.json
                    else format_evapotranspiration(evapotranspiration)
                )
        elif args.grass:
            grass = fetch_grass(timeout=args.timeout, lang=args.lang)
            if grass is None:
                text = format_grass_miss(as_json=args.json)
            else:
                text = format_json(grass) if args.json else format_grass(grass)
        elif args.sunshine:
            sunshine = fetch_sunshine(timeout=args.timeout, lang=args.lang)
            if sunshine is None:
                text = format_sunshine_miss(as_json=args.json)
            else:
                text = format_json(sunshine) if args.json else format_sunshine(sunshine)
        elif args.daily_sun:
            daily_sun = fetch_daily_sun(timeout=args.timeout, lang=args.lang)
            if daily_sun is None:
                text = format_daily_sun_miss(as_json=args.json)
            else:
                text = format_json(daily_sun) if args.json else format_daily_sun(daily_sun)
        elif args.max_uv:
            max_uv = fetch_max_uv(timeout=args.timeout, lang=args.lang)
            if max_uv is None:
                text = format_max_uv_miss(as_json=args.json)
            else:
                text = format_json(max_uv) if args.json else format_max_uv(max_uv)
        elif args.uv_peak:
            uv_peak = fetch_uv_peak(timeout=args.timeout, lang=args.lang)
            if uv_peak is None:
                text = format_uv_peak_miss(as_json=args.json)
            else:
                text = format_json(uv_peak) if args.json else format_uv_peak(uv_peak)
        elif args.mean_uv:
            mean_uv = fetch_mean_uv(timeout=args.timeout, lang=args.lang)
            if mean_uv is None:
                text = format_mean_uv_miss(as_json=args.json)
            else:
                text = format_json(mean_uv) if args.json else format_mean_uv(mean_uv)
        elif args.dose:
            dose = fetch_dose(timeout=args.timeout, lang=args.lang)
            if dose is None:
                text = format_dose_miss(as_json=args.json)
            else:
                text = format_json(dose) if args.json else format_dose(dose)
        elif args.hourly_dose:
            hourly_dose = fetch_hourly_dose(timeout=args.timeout, lang=args.lang)
            if not hourly_dose.stations:
                text = format_hourly_dose_miss(as_json=args.json)
            else:
                text = format_json(hourly_dose) if args.json else format_hourly_dose(hourly_dose)
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
        elif args.radiation_ground:
            radiation_ground = fetch_radiation_ground(timeout=args.timeout, lang=args.lang)
            if radiation_ground is None:
                text = format_radiation_ground_miss(as_json=args.json)
            else:
                text = (
                    format_json(radiation_ground)
                    if args.json
                    else format_radiation_ground(radiation_ground)
                )
        elif args.radiation_provisional:
            radiation_provisional = fetch_radiation_provisional(
                timeout=args.timeout, lang=args.lang
            )
            if radiation_provisional is None:
                text = format_radiation_provisional_miss(as_json=args.json)
            else:
                text = (
                    format_json(radiation_provisional)
                    if args.json
                    else format_radiation_provisional(radiation_provisional)
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
        elif args.gust:
            gust = fetch_gust(timeout=args.timeout, lang=args.lang)
            if not gust.stations:
                text = format_gust_miss(as_json=args.json)
            else:
                text = format_json(gust) if args.json else format_gust(gust)
        elif args.prevailing:
            prevailing = fetch_prevailing(timeout=args.timeout, lang=args.lang)
            if prevailing is None:
                text = format_prevailing_miss(as_json=args.json)
            else:
                text = format_json(prevailing) if args.json else format_prevailing(prevailing)
        elif args.cheung_prevailing:
            cheung_prevailing = fetch_cheung_prevailing(timeout=args.timeout, lang=args.lang)
            if cheung_prevailing is None:
                text = format_cheung_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(cheung_prevailing)
                    if args.json
                    else format_prevailing(cheung_prevailing)
                )
        elif args.mean_wind:
            mean_wind = fetch_mean_wind(timeout=args.timeout, lang=args.lang)
            if mean_wind is None:
                text = format_mean_wind_miss(as_json=args.json)
            else:
                text = format_json(mean_wind) if args.json else format_mean_wind(mean_wind)
        elif args.cheung_wind:
            cheung_wind = fetch_cheung_wind(timeout=args.timeout, lang=args.lang)
            if cheung_wind is None:
                text = format_cheung_wind_miss(as_json=args.json)
            else:
                text = format_json(cheung_wind) if args.json else format_mean_wind(cheung_wind)
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
        elif args.reduced_vis:
            reduced_vis = fetch_reduced_vis(timeout=args.timeout, lang=args.lang)
            if reduced_vis is None:
                text = format_reduced_vis_miss(as_json=args.json)
            else:
                text = format_json(reduced_vis) if args.json else format_reduced_vis(reduced_vis)
        elif args.tide:
            tide = fetch_tide(timeout=args.timeout, lang=args.lang)
            if not tide.events:
                text = format_tide_miss(as_json=args.json)
            else:
                text = format_json(tide) if args.json else format_tide(tide)
        elif args.tide_hour:
            tide_hour = fetch_tide_hour(timeout=args.timeout, lang=args.lang)
            if not tide_hour.hours:
                text = format_tide_hour_miss(as_json=args.json)
            else:
                text = format_json(tide_hour) if args.json else format_tide_hour(tide_hour)
        elif args.tide_latest:
            tide_latest = fetch_tide_latest(timeout=args.timeout, lang=args.lang)
            if not tide_latest.stations:
                text = format_tide_latest_miss(as_json=args.json)
            else:
                text = format_json(tide_latest) if args.json else format_tide_latest(tide_latest)
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
        elif args.fifteen_uv:
            fifteen_uv = fetch_fifteen_uv(timeout=args.timeout, lang=args.lang)
            if fifteen_uv is None:
                text = format_fifteen_uv_miss(as_json=args.json)
            else:
                text = format_json(fifteen_uv) if args.json else format_fifteen_uv(fifteen_uv)
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
        elif args.current_updated:
            current_updated = fetch_current_updated(timeout=args.timeout, lang=args.lang)
            if current_updated is None:
                text = format_current_updated_miss(as_json=args.json)
            else:
                text = (
                    format_json(current_updated)
                    if args.json
                    else format_current_updated(current_updated)
                )
        elif args.tips:
            tips = fetch_tips(timeout=args.timeout, lang=args.lang)
            text = format_json(tips) if args.json else format_tips(tips)
        elif args.lamppost:
            lamppost = fetch_lamppost(timeout=args.timeout, lang=args.lang)
            if lamppost is None:
                text = format_lamppost_miss(as_json=args.json)
            else:
                text = format_json(lamppost) if args.json else format_lamppost(lamppost)
        elif args.rain:
            rain = fetch_rain(timeout=args.timeout, lang=args.lang)
            text = format_json(rain) if args.json else format_rain(rain)
        elif args.rain_period:
            rain_period = fetch_rain_period(timeout=args.timeout, lang=args.lang)
            if rain_period is None:
                text = format_rain_period_miss(as_json=args.json)
            else:
                text = format_json(rain_period) if args.json else format_rain_period(rain_period)
        elif args.rain_maint:
            rain_maint = fetch_rain_maint(timeout=args.timeout, lang=args.lang)
            if not rain_maint.places:
                text = format_rain_maint_miss(as_json=args.json)
            else:
                text = format_json(rain_maint) if args.json else format_rain_maint(rain_maint)
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
        elif args.nowcast:
            nowcast = fetch_nowcast(timeout=args.timeout, lang=args.lang)
            if not nowcast.periods:
                text = format_nowcast_miss(as_json=args.json)
            else:
                text = format_json(nowcast) if args.json else format_nowcast(nowcast)
        elif args.daily_rain:
            daily_rain = fetch_daily_rain(timeout=args.timeout, lang=args.lang)
            if daily_rain is None:
                text = format_daily_rain_miss(as_json=args.json)
            else:
                text = format_json(daily_rain) if args.json else format_daily_rain(daily_rain)
        elif args.lau_fau_rain:
            lau_fau_rain = fetch_lau_fau_rain(timeout=args.timeout, lang=args.lang)
            if lau_fau_rain is None:
                text = format_lau_fau_rain_miss(as_json=args.json)
            else:
                text = format_json(lau_fau_rain) if args.json else format_daily_rain(lau_fau_rain)
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
        elif args.daily_strikes:
            daily_strikes = fetch_daily_strikes(timeout=args.timeout, lang=args.lang)
            if daily_strikes is None:
                text = format_daily_strikes_miss(as_json=args.json)
            else:
                text = (
                    format_json(daily_strikes) if args.json else format_daily_strikes(daily_strikes)
                )
        elif args.cloud_strikes:
            cloud_strikes = fetch_cloud_strikes(timeout=args.timeout, lang=args.lang)
            if cloud_strikes is None:
                text = format_cloud_strikes_miss(as_json=args.json)
            else:
                text = (
                    format_json(cloud_strikes)
                    if args.json
                    else format_cloud_strikes(cloud_strikes)
                )
        elif args.humidity:
            humidity = fetch_humidity(timeout=args.timeout, lang=args.lang)
            text = format_json(humidity) if args.json else format_humidity(humidity)
        elif args.humidity_time:
            humidity_time = fetch_humidity_time(timeout=args.timeout, lang=args.lang)
            if humidity_time is None:
                text = format_humidity_time_miss(as_json=args.json)
            else:
                text = format_json(humidity_time) if args.json else format_humidity_time(humidity_time)
        elif args.minute_humidity:
            minute_humidity = fetch_minute_humidity(timeout=args.timeout, lang=args.lang)
            if not minute_humidity.stations:
                text = format_minute_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(minute_humidity)
                    if args.json
                    else format_minute_humidity(minute_humidity)
                )
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
        elif args.mean_humidity:
            mean_humidity = fetch_mean_humidity(timeout=args.timeout, lang=args.lang)
            if mean_humidity is None:
                text = format_mean_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(mean_humidity)
                    if args.json
                    else format_mean_humidity(mean_humidity)
                )
        elif args.tai_mo_humidity:
            tai_mo_humidity = fetch_tai_mo_humidity(timeout=args.timeout, lang=args.lang)
            if tai_mo_humidity is None:
                text = format_tai_mo_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mo_humidity)
                    if args.json
                    else format_mean_humidity(tai_mo_humidity)
                )
        elif args.temps:
            temps = fetch_temps(timeout=args.timeout, lang=args.lang)
            text = format_json(temps) if args.json else format_temps(temps)
        elif args.temp_time:
            temp_time = fetch_temp_time(timeout=args.timeout, lang=args.lang)
            if temp_time is None:
                text = format_temp_time_miss(as_json=args.json)
            else:
                text = format_json(temp_time) if args.json else format_temp_time(temp_time)
        elif args.minute_temp:
            minute_temp = fetch_minute_temp(timeout=args.timeout, lang=args.lang)
            if not minute_temp.stations:
                text = format_minute_temp_miss(as_json=args.json)
            else:
                text = format_json(minute_temp) if args.json else format_minute_temp(minute_temp)
        elif args.since_midnight:
            since_midnight = fetch_since_midnight(timeout=args.timeout, lang=args.lang)
            if not since_midnight.stations:
                text = format_since_midnight_miss(as_json=args.json)
            else:
                text = (
                    format_json(since_midnight)
                    if args.json
                    else format_since_midnight(since_midnight)
                )
        elif args.pressure:
            pressure = fetch_pressure(timeout=args.timeout, lang=args.lang)
            if not pressure.stations:
                text = format_pressure_miss(as_json=args.json)
            else:
                text = format_json(pressure) if args.json else format_pressure(pressure)
        elif args.mean_pressure:
            mean_pressure = fetch_mean_pressure(timeout=args.timeout, lang=args.lang)
            if mean_pressure is None:
                text = format_mean_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(mean_pressure)
                    if args.json
                    else format_mean_pressure(mean_pressure)
                )
        elif args.minute_grass:
            minute_grass = fetch_minute_grass(timeout=args.timeout, lang=args.lang)
            if not minute_grass.stations:
                text = format_minute_grass_miss(as_json=args.json)
            else:
                text = format_json(minute_grass) if args.json else format_minute_grass(minute_grass)
        elif args.daily_grass:
            daily_grass = fetch_daily_grass(timeout=args.timeout, lang=args.lang)
            if daily_grass is None:
                text = format_daily_grass_miss(as_json=args.json)
            else:
                text = format_json(daily_grass) if args.json else format_daily_grass(daily_grass)
        elif args.obs_grass:
            obs_grass = fetch_obs_grass(timeout=args.timeout, lang=args.lang)
            if obs_grass is None:
                text = format_obs_grass_miss(as_json=args.json)
            else:
                text = format_json(obs_grass) if args.json else format_daily_grass(obs_grass)
        elif args.temp_diff:
            temp_diff = fetch_temp_diff(timeout=args.timeout, lang=args.lang)
            if not temp_diff.stations:
                text = format_temp_diff_miss(as_json=args.json)
            else:
                text = format_json(temp_diff) if args.json else format_temp_diff(temp_diff)
        elif args.heat_index:
            heat_index = fetch_heat_index(timeout=args.timeout, lang=args.lang)
            if not heat_index.stations:
                text = format_heat_index_miss(as_json=args.json)
            else:
                text = format_json(heat_index) if args.json else format_heat_index(heat_index)
        elif args.daily_heat:
            daily_heat = fetch_daily_heat(timeout=args.timeout, lang=args.lang)
            if daily_heat is None:
                text = format_daily_heat_miss(as_json=args.json)
            else:
                text = format_json(daily_heat) if args.json else format_daily_heat(daily_heat)
        elif args.wbgt:
            wbgt = fetch_wbgt(timeout=args.timeout, lang=args.lang)
            if not wbgt.stations:
                text = format_wbgt_miss(as_json=args.json)
            else:
                text = format_json(wbgt) if args.json else format_wbgt(wbgt)
        elif args.wet_bulb:
            wet_bulb = fetch_wet_bulb(timeout=args.timeout, lang=args.lang)
            if wet_bulb is None:
                text = format_wet_bulb_miss(as_json=args.json)
            else:
                text = format_json(wet_bulb) if args.json else format_wet_bulb(wet_bulb)
        elif args.airport_wet:
            airport_wet = fetch_airport_wet(timeout=args.timeout, lang=args.lang)
            if airport_wet is None:
                text = format_airport_wet_miss(as_json=args.json)
            else:
                text = format_json(airport_wet) if args.json else format_wet_bulb(airport_wet)
        elif args.solar:
            solar = fetch_solar(timeout=args.timeout, lang=args.lang)
            if not solar.stations:
                text = format_solar_miss(as_json=args.json)
            else:
                text = format_json(solar) if args.json else format_solar(solar)
        elif args.global_solar:
            global_solar = fetch_global_solar(timeout=args.timeout, lang=args.lang)
            if global_solar is None:
                text = format_global_solar_miss(as_json=args.json)
            else:
                text = format_json(global_solar) if args.json else format_global_solar(global_solar)
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
