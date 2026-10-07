"""Fetch and format Hong Kong Observatory current weather and the local forecast."""

from __future__ import annotations

import csv
import io
import json
import math
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

from hk_weather.icons import conditions_with_emoji, icon_label

# Hong Kong Observatory open data. No API key.
# rhrread: current weather (and its uvindex field). flw: local forecast.
# fnd: 9-day. warnsum: warnings. swt: special weather tips. UV has no separate dataType; HKO
# returns uvindex as "" when the reading is unavailable.
_API = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
DEFAULT_URL = f"{_API}?dataType=rhrread&lang=en"
# Past-hour rainfall at automatic weather stations. lang is accepted.
HOURLY_RAIN_URL = "https://data.weather.gov.hk/weatherAPI/opendata/hourlyRainfall.php?lang=en"
FORECAST_URL = f"{_API}?dataType=flw&lang=en"
NINE_DAY_URL = f"{_API}?dataType=fnd&lang=en"
WARNINGS_URL = f"{_API}?dataType=warnsum&lang=en"
WARNING_INFO_URL = f"{_API}?dataType=warningInfo&lang=en"
TIPS_URL = f"{_API}?dataType=swt&lang=en"
# Quick earthquake messages live on earthquake.php. dataType=qem is the latest
# magnitude 6+ event; dataType=eeq is not a valid Observatory parameter.
QUAKE_URL = "https://data.weather.gov.hk/weatherAPI/opendata/earthquake.php?dataType=qem&lang=en"
# Locally felt earth tremor report. An empty object means none is reported.
FELT_URL = (
    "https://data.weather.gov.hk/weatherAPI/opendata/earthquake.php"
    "?dataType=feltearthquake&lang=en"
)
# Latest 10-minute mean visibility. weather.php rejects dataType=LTMV; this feed
# is the open-data endpoint and needs rformat=json plus lang.
VISIBILITY_URL = (
    "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
    "?dataType=LTMV&rformat=json&lang=en"
)
# Latest 10-minute mean wind and gust. These regional files are CSV, one per language.
GUST_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_10min_wind.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_10min_wind_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_10min_wind_sc.csv"
    ),
}
# Latest 1-minute mean air temperature. These regional files are CSV, one per language.
MINUTE_TEMP_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_temperature.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_temperature_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_temperature_sc.csv"
    ),
}
# Latest 1-minute mean relative humidity. These regional files are CSV, one per language.
MINUTE_HUMIDITY_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_humidity.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_humidity_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_humidity_sc.csv"
    ),
}
# Maximum and minimum air temperature since midnight. CSV, one file per language.
SINCE_MIDNIGHT_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_since_midnight_maxmin.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_since_midnight_maxmin_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_since_midnight_maxmin_sc.csv"
    ),
}
# Latest 1-minute mean sea level pressure. CSV, one file per language.
PRESSURE_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_pressure.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_pressure_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_pressure_sc.csv"
    ),
}
# Latest 1-minute mean grass temperature. CSV, one file per language.
MINUTE_GRASS_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_grass.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_grass_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_grass_sc.csv"
    ),
}
# Past 24-hour air-temperature difference. CSV, one file per language.
TEMP_DIFF_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_past24_temperature_diff.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_past24_temperature_diff_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_past24_temperature_diff_sc.csv"
    ),
}
# Latest 10-minute mean Hong Kong Heat Index. CSV, one file per language.
HEAT_INDEX_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "recent10_10min_hkhi.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "recent10_10min_hkhi_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "recent10_10min_hkhi_sc.csv"
    ),
}
# Latest 60-minute mean Wet Bulb Globe Temperature. CSV, one file per language.
WBGT_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "recent10_60min_wbgt.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "recent10_60min_wbgt_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "recent10_60min_wbgt_sc.csv"
    ),
}
# Latest 1-minute solar radiation. CSV, one file per language.
SOLAR_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_solar.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_solar_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_1min_solar_sc.csv"
    ),
}
# Latest hourly mean ambient gamma dose rate. CSV, one file per language.
HOURLY_DOSE_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_hourly_rmn.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_hourly_rmn_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_hourly_rmn_sc.csv"
    ),
}
# South China Coastal Waters bulletin. JSON, one file per language.
COASTAL_URLS = {
    "en": "https://data.weather.gov.hk/openData/json/sccw_json_datagov.json",
    "tc": "https://data.weather.gov.hk/openData/json/sccw_json_datagov_uc.json",
    "sc": "https://data.weather.gov.hk/openData/json/gb/sccw_json_datagov_uc.json",
}
# Gridded half-hourly rainfall nowcast. CSV, one file per language.
NOWCAST_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/F3/"
        "Gridded_rainfall_nowcast.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/F3/"
        "Gridded_rainfall_nowcast_tc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/F3/"
        "Gridded_rainfall_nowcast_sc.csv"
    ),
}
# Experimental smart-lamppost reading. The Observatory's documented example post.
LAMPPOST_URL = (
    "https://data.weather.gov.hk/weatherAPI/smart-lamppost/"
    "smart-lamppost.php?pi=GF3637&di=01"
)
# Latest observed tide height. CSV, one file per language.
LATEST_TIDE_URLS = {
    "en": "https://data.weather.gov.hk/weatherAPI/hko_data/tide/ALL_en.csv",
    "tc": "https://data.weather.gov.hk/weatherAPI/hko_data/tide/ALL_tc.csv",
    "sc": "https://data.weather.gov.hk/weatherAPI/hko_data/tide/ALL_sc.csv",
}
# Hourly cloud-to-ground and cloud-to-cloud lightning counts. lang is accepted.
STRIKES_URL = (
    "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
    "?dataType=LHL&rformat=json&lang=en"
)
# Astronomical high and low tides. opendata.php requires a station plus year,
# month, and day; Quarry Bay is the default station. lang is accepted.
TIDE_STATION = "QUB"
TIDE_STATION_NAME = "Quarry Bay"
# Yesterday's sunshine duration is recorded at King's Park.
SUNSHINE_STATION = "KP"
SUNSHINE_STATION_NAME = "King's Park"
# Current AQHI by station. weather.php has no AQHI dataType; these are the
# Environmental Protection Department RSS feeds, one file per language.
AQHI_URLS = {
    "en": "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_ind_rss_Eng.xml",
    "tc": "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_ind_rss_ChT.xml",
    "sc": "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_ind_rss_ChS.xml",
}
UV_URL = DEFAULT_URL
# Latest 15-minute mean UV index at King's Park. CSV, one file per language.
FIFTEEN_UV_URLS = {
    "en": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_15min_uvindex.csv"
    ),
    "tc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_15min_uvindex_uc.csv"
    ),
    "sc": (
        "https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/"
        "latest_15min_uvindex_sc.csv"
    ),
}
_CANCELLED = {"CANCEL", "CANCELLED"}
HKO_STATION = "Hong Kong Observatory"
USER_AGENT = "hk-weather-demo/0.1 (+https://github.com)"


class WeatherError(Exception):
    """The current report could not be fetched or parsed."""


@dataclass(frozen=True)
class CurrentWeather:
    update_time: str
    conditions: str
    place: str
    temperature_c: float
    humidity_percent: float | None
    rainfall_mm: float | None
    rainfall_place: str | None
    lightning_places: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class LocalForecast:
    update_time: str
    period: str
    forecast: str
    outlook: str


@dataclass(frozen=True)
class ForecastOutlook:
    outlook: str


@dataclass(frozen=True)
class CoastalArea:
    place: str
    wind: str
    weather: str
    sea: str


@dataclass(frozen=True)
class CoastalForecast:
    update_time: str
    areas: tuple[CoastalArea, ...]


@dataclass(frozen=True)
class CoastStation:
    place: str
    wind: str
    weather: str
    visibility: float | None
    visibility_unit: str


@dataclass(frozen=True)
class CoastReport:
    update_time: str
    stations: tuple[CoastStation, ...]


@dataclass(frozen=True)
class ForecastPeriod:
    period: str


@dataclass(frozen=True)
class ForecastDesc:
    description: str


@dataclass(frozen=True)
class ForecastUpdated:
    updated: str


@dataclass(frozen=True)
class GeneralSituation:
    situation: str


@dataclass(frozen=True)
class FireDanger:
    warning: str


@dataclass(frozen=True)
class TcInfo:
    info: str


@dataclass(frozen=True)
class WeatherWarning:
    code: str
    description: str


@dataclass(frozen=True)
class WarningTime:
    code: str
    description: str
    issue_time: str
    update_time: str
    expire_time: str


@dataclass(frozen=True)
class WarningLevel:
    code: str
    description: str
    level: str


@dataclass(frozen=True)
class WarningTimeReport:
    warnings: tuple[WarningTime, ...]


@dataclass(frozen=True)
class WarningDetail:
    code: str
    subtype: str
    update_time: str
    contents: tuple[str, ...]


@dataclass(frozen=True)
class ForecastDay:
    date: str
    week: str
    weather: str
    temp_high_c: float | None
    temp_low_c: float | None
    humidity_high_percent: float | None
    humidity_low_percent: float | None
    rain_chance: str | None


@dataclass(frozen=True)
class NineDayForecast:
    update_time: str
    days: tuple[ForecastDay, ...]


@dataclass(frozen=True)
class NineUpdated:
    updated: str


@dataclass(frozen=True)
class NineWeatherDay:
    date: str
    week: str
    weather: str


@dataclass(frozen=True)
class NineWeather:
    update_time: str
    days: tuple[NineWeatherDay, ...]


@dataclass(frozen=True)
class NineTempDay:
    date: str
    week: str
    temp_high_c: float | None
    temp_low_c: float | None


@dataclass(frozen=True)
class NineTemp:
    update_time: str
    days: tuple[NineTempDay, ...]


@dataclass(frozen=True)
class NineHumidityDay:
    date: str
    week: str
    humidity_high_percent: float | None
    humidity_low_percent: float | None


@dataclass(frozen=True)
class NineHumidity:
    update_time: str
    days: tuple[NineHumidityDay, ...]


@dataclass(frozen=True)
class SeaTemperature:
    place: str
    temperature_c: float
    recorded: str


@dataclass(frozen=True)
class MorningSea:
    station: str
    date: str
    sea_temperature_c: float


@dataclass(frozen=True)
class AfternoonSea:
    station: str
    date: str
    sea_temperature_c: float


@dataclass(frozen=True)
class SoilReading:
    place: str
    depth_m: float
    temperature_c: float
    recorded: str


@dataclass(frozen=True)
class SoilReport:
    readings: tuple[SoilReading, ...]


@dataclass(frozen=True)
class PsrDay:
    date: str
    week: str
    psr: str | None


@dataclass(frozen=True)
class PsrForecast:
    update_time: str
    days: tuple[PsrDay, ...]


@dataclass(frozen=True)
class TomorrowForecast:
    update_time: str
    date: str
    week: str
    weather: str
    temp_high_c: float | None
    temp_low_c: float | None
    humidity_high_percent: float | None
    humidity_low_percent: float | None
    rain_chance: str | None
    wind: str | None


@dataclass(frozen=True)
class WeekendDay:
    date: str
    week: str
    weather: str
    temp_high_c: float | None
    temp_low_c: float | None
    humidity_high_percent: float | None
    humidity_low_percent: float | None
    rain_chance: str | None
    wind: str | None


@dataclass(frozen=True)
class WeekendForecast:
    update_time: str
    days: tuple[WeekendDay, ...]


@dataclass(frozen=True)
class WindDay:
    date: str
    week: str
    wind: str


@dataclass(frozen=True)
class GustReading:
    place: str
    direction: str
    speed_kmh: float | None
    gust_kmh: float | None


@dataclass(frozen=True)
class GustReport:
    obs_time: str
    stations: tuple[GustReading, ...]


@dataclass(frozen=True)
class PrevailingWind:
    station: str
    date: str
    direction_deg: float


@dataclass(frozen=True)
class MeanWind:
    station: str
    date: str
    wind_km_h: float


@dataclass(frozen=True)
class WindForecast:
    update_time: str
    days: tuple[WindDay, ...]


@dataclass(frozen=True)
class ForecastIconDay:
    date: str
    week: str
    icon: int
    label: str


@dataclass(frozen=True)
class ForecastIcons:
    update_time: str
    days: tuple[ForecastIconDay, ...]


@dataclass(frozen=True)
class Earthquake:
    time: str
    region: str
    magnitude: float | None
    latitude: float | None
    longitude: float | None
    update_time: str


@dataclass(frozen=True)
class QuakeReport:
    quakes: tuple[Earthquake, ...]


@dataclass(frozen=True)
class FeltTremor:
    time: str
    update_time: str
    region: str
    magnitude: float | None
    intensity: str
    latitude: float | None
    longitude: float | None
    details: str


@dataclass(frozen=True)
class VisibilityReading:
    time: str
    place: str
    visibility: str


@dataclass(frozen=True)
class VisibilityReport:
    readings: tuple[VisibilityReading, ...]


@dataclass(frozen=True)
class ReducedVisibility:
    station: str
    date: str
    hours: float


@dataclass(frozen=True)
class TideEvent:
    date: str
    time: str
    height_m: float


@dataclass(frozen=True)
class TideReport:
    station: str
    events: tuple[TideEvent, ...]


@dataclass(frozen=True)
class HourlyTideReading:
    hour: str
    height_m: float


@dataclass(frozen=True)
class HourlyTideReport:
    station: str
    date: str
    hours: tuple[HourlyTideReading, ...]


@dataclass(frozen=True)
class LatestTideReading:
    place: str
    height_m: float


@dataclass(frozen=True)
class LatestTideReport:
    obs_time: str
    stations: tuple[LatestTideReading, ...]


@dataclass(frozen=True)
class AqhiReading:
    station: str
    area: str
    aqhi: str
    health_risk: str


@dataclass(frozen=True)
class AqhiReport:
    updated: str
    readings: tuple[AqhiReading, ...]


@dataclass(frozen=True)
class Sunrise:
    date: str
    rise: str
    transit: str
    set: str


@dataclass(frozen=True)
class Moon:
    date: str
    rise: str
    transit: str
    set: str


@dataclass(frozen=True)
class LunarDate:
    date: str
    lunar_year: str
    lunar_date: str


@dataclass(frozen=True)
class SpecialTips:
    tips: tuple[str, ...]


@dataclass(frozen=True)
class LamppostReading:
    lamppost: str
    time: str
    temperature_c: float | None
    humidity_percent: float | None
    wind_km_h: float | None
    direction_deg: float | None


@dataclass(frozen=True)
class StationReading:
    place: str
    temperature_c: float | None
    humidity_percent: float | None


@dataclass(frozen=True)
class StationReport:
    update_time: str
    stations: tuple[StationReading, ...]


@dataclass(frozen=True)
class RainReading:
    place: str
    rainfall_mm: float


@dataclass(frozen=True)
class RainReport:
    readings: tuple[RainReading, ...]


@dataclass(frozen=True)
class RainPeriod:
    start: str
    end: str


@dataclass(frozen=True)
class RainMaintenance:
    places: tuple[str, ...]


@dataclass(frozen=True)
class HourRainReading:
    place: str
    station_id: str
    rainfall_mm: float


@dataclass(frozen=True)
class HourRainReport:
    obs_time: str
    readings: tuple[HourRainReading, ...]


@dataclass(frozen=True)
class HourWettest:
    obs_time: str
    place: str
    station_id: str
    rainfall_mm: float


@dataclass(frozen=True)
class HourDriest:
    obs_time: str
    place: str
    station_id: str
    rainfall_mm: float


@dataclass(frozen=True)
class YesterdayReport:
    date: str
    temp_high_c: float | None
    temp_low_c: float | None
    rainfall_mm: float | None
    humidity_high_percent: float | None
    humidity_low_percent: float | None


@dataclass(frozen=True)
class DailyMean:
    date: str
    temperature_c: float


@dataclass(frozen=True)
class TaiMoTemp:
    station: str
    date: str
    temperature_c: float


@dataclass(frozen=True)
class DailyMax:
    date: str
    temperature_c: float


@dataclass(frozen=True)
class DailyMin:
    date: str
    temperature_c: float


@dataclass(frozen=True)
class DewPoint:
    station: str
    date: str
    dew_point_c: float


@dataclass(frozen=True)
class CloudAmount:
    station: str
    date: str
    cloud_percent: float


@dataclass(frozen=True)
class Evaporation:
    station: str
    date: str
    evaporation_mm: float


@dataclass(frozen=True)
class Evapotranspiration:
    station: str
    month: str
    evapotranspiration_mm: float


@dataclass(frozen=True)
class GrassMinimum:
    date: str
    grass_min_c: float


@dataclass(frozen=True)
class Sunshine:
    station: str
    date: str
    hours: float


@dataclass(frozen=True)
class DailySun:
    station: str
    date: str
    hours: float


@dataclass(frozen=True)
class MaxUv:
    station: str
    date: str
    uv_index: float


@dataclass(frozen=True)
class UvPeak:
    station: str
    date: str
    uv_index: float
    period: str


@dataclass(frozen=True)
class MeanUv:
    station: str
    date: str
    uv_index: float


@dataclass(frozen=True)
class GammaDose:
    station: str
    date: str
    dose_usv_h: float


@dataclass(frozen=True)
class HourlyDoseReading:
    place: str
    dose_usv_h: float


@dataclass(frozen=True)
class HourlyDoseReport:
    obs_time: str
    stations: tuple[HourlyDoseReading, ...]


@dataclass(frozen=True)
class AccumulatedRainfall:
    date: str
    rainfall_mm: float


@dataclass(frozen=True)
class AverageRainfall:
    date: str
    rainfall_mm: float


@dataclass(frozen=True)
class RainComparison:
    date: str
    accumulated_mm: float
    normal_mm: float


@dataclass(frozen=True)
class RadiationReport:
    date: str
    report: str


@dataclass(frozen=True)
class WeatherBulletin:
    date: str
    time: str


@dataclass(frozen=True)
class RadiationNote:
    note: str


@dataclass(frozen=True)
class RadiationWeather:
    note: str


@dataclass(frozen=True)
class RadiationGround:
    note: str


@dataclass(frozen=True)
class RadiationProvisional:
    note: str


@dataclass(frozen=True)
class RainstormReminder:
    reminder: str


@dataclass(frozen=True)
class CycloneMessage:
    messages: tuple[str, ...]


@dataclass(frozen=True)
class WettestReading:
    place: str
    rainfall_mm: float


@dataclass(frozen=True)
class DriestReading:
    place: str
    rainfall_mm: float


@dataclass(frozen=True)
class NowcastPeak:
    ending: str
    latitude: float
    longitude: float
    rainfall_mm: float


@dataclass(frozen=True)
class NowcastReport:
    updated: str
    periods: tuple[NowcastPeak, ...]


@dataclass(frozen=True)
class DailyRain:
    station: str
    date: str
    rainfall_mm: float


@dataclass(frozen=True)
class LightningReport:
    places: tuple[str, ...]


@dataclass(frozen=True)
class LightningCount:
    start: str
    end: str
    kind: str
    region: str
    count: int


@dataclass(frozen=True)
class LightningCountReport:
    counts: tuple[LightningCount, ...]


@dataclass(frozen=True)
class DailyStrikes:
    date: str
    count: float


@dataclass(frozen=True)
class CloudStrikes:
    date: str
    count: float


@dataclass(frozen=True)
class HumidityReading:
    place: str
    humidity_percent: float


@dataclass(frozen=True)
class HumidityReport:
    record_time: str
    readings: tuple[HumidityReading, ...]


@dataclass(frozen=True)
class HumidityTime:
    recorded: str


@dataclass(frozen=True)
class HumidestReading:
    record_time: str
    place: str
    humidity_percent: float


@dataclass(frozen=True)
class LeastHumidReading:
    record_time: str
    place: str
    humidity_percent: float


@dataclass(frozen=True)
class MeanHumidity:
    station: str
    date: str
    humidity_percent: float


@dataclass(frozen=True)
class TempReading:
    place: str
    temperature_c: float


@dataclass(frozen=True)
class TempReport:
    record_time: str
    readings: tuple[TempReading, ...]


@dataclass(frozen=True)
class TempTime:
    recorded: str


@dataclass(frozen=True)
class MinuteTempReading:
    place: str
    temperature_c: float


@dataclass(frozen=True)
class MinuteTempReport:
    obs_time: str
    stations: tuple[MinuteTempReading, ...]


@dataclass(frozen=True)
class MinuteHumidityReading:
    place: str
    humidity_percent: float


@dataclass(frozen=True)
class MinuteHumidityReport:
    obs_time: str
    stations: tuple[MinuteHumidityReading, ...]


@dataclass(frozen=True)
class SinceMidnightReading:
    place: str
    temp_high_c: float | None
    temp_low_c: float | None


@dataclass(frozen=True)
class SinceMidnightReport:
    obs_time: str
    stations: tuple[SinceMidnightReading, ...]


@dataclass(frozen=True)
class PressureReading:
    place: str
    pressure_hpa: float


@dataclass(frozen=True)
class PressureReport:
    obs_time: str
    stations: tuple[PressureReading, ...]


@dataclass(frozen=True)
class MeanPressure:
    station: str
    date: str
    pressure_hpa: float


@dataclass(frozen=True)
class MinuteGrassReading:
    place: str
    grass_c: float


@dataclass(frozen=True)
class MinuteGrassReport:
    obs_time: str
    stations: tuple[MinuteGrassReading, ...]


@dataclass(frozen=True)
class DailyGrass:
    station: str
    date: str
    grass_c: float


@dataclass(frozen=True)
class TempDiffReading:
    place: str
    change_c: float


@dataclass(frozen=True)
class TempDiffReport:
    obs_time: str
    stations: tuple[TempDiffReading, ...]


@dataclass(frozen=True)
class HeatIndexReading:
    place: str
    heat_index: float


@dataclass(frozen=True)
class HeatIndexReport:
    obs_time: str
    stations: tuple[HeatIndexReading, ...]


@dataclass(frozen=True)
class DailyHeat:
    station: str
    date: str
    heat_index: float


@dataclass(frozen=True)
class WbgtReading:
    place: str
    wbgt_c: float


@dataclass(frozen=True)
class WbgtReport:
    obs_time: str
    stations: tuple[WbgtReading, ...]


@dataclass(frozen=True)
class WetBulb:
    station: str
    date: str
    wet_bulb_c: float


@dataclass(frozen=True)
class SolarReading:
    place: str
    global_w_m2: float
    direct_w_m2: float
    diffuse_w_m2: float


@dataclass(frozen=True)
class SolarReport:
    obs_time: str
    stations: tuple[SolarReading, ...]


@dataclass(frozen=True)
class GlobalSolar:
    station: str
    date: str
    global_solar_mj_m2: float


@dataclass(frozen=True)
class HottestReading:
    record_time: str
    place: str
    temperature_c: float


@dataclass(frozen=True)
class ColdestReading:
    record_time: str
    place: str
    temperature_c: float


@dataclass(frozen=True)
class OvernightMinimum:
    report: str


@dataclass(frozen=True)
class NoonRainfall:
    report: str


@dataclass(frozen=True)
class MonthRainfall:
    report: str


@dataclass(frozen=True)
class YearRainfall:
    report: str


@dataclass(frozen=True)
class SummaryToday:
    date: str
    high_c: float | None
    low_c: float | None
    rain_chance: str | None


@dataclass(frozen=True)
class WeatherSummary:
    conditions: str
    warnings: tuple[WeatherWarning, ...]
    today: SummaryToday | None


@dataclass(frozen=True)
class UvIndex:
    update_time: str
    place: str | None
    value: float | None
    description: str | None
    record: str | None


@dataclass(frozen=True)
class FifteenUv:
    station: str
    time: str
    uv_index: float


@dataclass(frozen=True)
class IconUpdate:
    updated: str


@dataclass(frozen=True)
class IconReading:
    code: int
    label: str


@dataclass(frozen=True)
class IconReport:
    icons: tuple[IconReading, ...]


@dataclass(frozen=True)
class CurrentUpdated:
    updated: str


def fetch_current(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> CurrentWeather:
    """Download the current weather report and return a summary."""
    return parse_current_report(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_forecast(url: str = FORECAST_URL, timeout: float = 10, lang: str = "en") -> LocalForecast:
    """Download the local weather forecast (`dataType=flw`)."""
    return parse_forecast(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_outlook(
    url: str = FORECAST_URL, timeout: float = 10, lang: str = "en"
) -> ForecastOutlook | None:
    """Download the outlook from the local forecast (`dataType=flw`)."""
    return parse_outlook(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_coastal(timeout: float = 10, lang: str = "en") -> CoastalForecast:
    """Download the South China Coastal Waters area forecast."""
    url = COASTAL_URLS.get(lang, COASTAL_URLS["en"])
    return parse_coastal(_fetch_json(url, timeout))


def fetch_coast_report(timeout: float = 10, lang: str = "en") -> CoastReport:
    """Download the latest South China coastal station reports."""
    url = COASTAL_URLS.get(lang, COASTAL_URLS["en"])
    return parse_coast_report(_fetch_json(url, timeout))


def fetch_forecast_period(
    url: str = FORECAST_URL, timeout: float = 10, lang: str = "en"
) -> ForecastPeriod | None:
    """Download the forecast period from the local forecast (`dataType=flw`)."""
    return parse_forecast_period(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_forecast_desc(
    url: str = FORECAST_URL, timeout: float = 10, lang: str = "en"
) -> ForecastDesc | None:
    """Download the forecast description from the local forecast (`dataType=flw`)."""
    return parse_forecast_desc(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_forecast_updated(
    url: str = FORECAST_URL, timeout: float = 10, lang: str = "en"
) -> ForecastUpdated | None:
    """Download when the local forecast was updated (`dataType=flw`)."""
    return parse_forecast_updated(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_situation(
    url: str = FORECAST_URL, timeout: float = 10, lang: str = "en"
) -> GeneralSituation | None:
    """Download the general situation from the local forecast (`dataType=flw`)."""
    return parse_situation(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_fire_danger(
    url: str = FORECAST_URL, timeout: float = 10, lang: str = "en"
) -> FireDanger | None:
    """Download the fire danger warning from the local forecast (`dataType=flw`)."""
    return parse_fire_danger(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_tc_info(
    url: str = FORECAST_URL, timeout: float = 10, lang: str = "en"
) -> TcInfo | None:
    """Download tropical cyclone information from the local forecast (`dataType=flw`)."""
    return parse_tc_info(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_warnings(
    url: str = WARNINGS_URL, timeout: float = 10, lang: str = "en"
) -> tuple[WeatherWarning, ...]:
    """Download active weather warnings (`dataType=warnsum`)."""
    return parse_warnings(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_warning_time(
    url: str = WARNINGS_URL, timeout: float = 10, lang: str = "en"
) -> WarningTimeReport:
    """Download issue and expiry times for active warnings (`dataType=warnsum`)."""
    return parse_warning_time(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_warning_level(
    url: str = WARNINGS_URL, timeout: float = 10, lang: str = "en"
) -> tuple[WarningLevel, ...]:
    """Download the level of each active warning (`dataType=warnsum`)."""
    return parse_warning_level(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_warning_info(
    url: str = WARNING_INFO_URL, timeout: float = 10, lang: str = "en"
) -> tuple[WarningDetail, ...]:
    """Download detailed warning messages (`dataType=warningInfo`)."""
    return parse_warning_info(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_nine_day(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> NineDayForecast:
    """Download the 9-day forecast (`dataType=fnd`)."""
    return parse_nine_day(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_sea_temp(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> SeaTemperature | None:
    """Download the sea temperature from the 9-day forecast (`dataType=fnd`)."""
    return parse_sea_temp(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_north_point_am_sea(timeout: float = 10, lang: str = "en") -> MorningSea | None:
    """Download the latest daily morning sea temperature at North Point."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NPF/"
        f"{year}/daily_NPF_SSTA_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_north_point_am_sea(text, lang)


def fetch_north_point_pm_sea(timeout: float = 10, lang: str = "en") -> AfternoonSea | None:
    """Download the latest daily afternoon sea temperature at North Point."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NPF/"
        f"{year}/daily_NPF_SSTP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_north_point_pm_sea(text, lang)


def fetch_soil_temp(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> SoilReport | None:
    """Download soil temperatures from the 9-day forecast (`dataType=fnd`)."""
    return parse_soil_temp(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_nine_situation(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> GeneralSituation | None:
    """Download the general situation from the 9-day forecast (`dataType=fnd`)."""
    return parse_situation(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_nine_updated(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> NineUpdated | None:
    """Download when the 9-day forecast was updated (`dataType=fnd`)."""
    return parse_nine_updated(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_nine_weather(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> NineWeather:
    """Download each day's weather from the 9-day forecast (`dataType=fnd`)."""
    return parse_nine_weather(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_nine_temp(url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en") -> NineTemp:
    """Download each day's high and low from the 9-day forecast (`dataType=fnd`)."""
    return parse_nine_temp(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_nine_humidity(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> NineHumidity:
    """Download each day's humidity range from the 9-day forecast (`dataType=fnd`)."""
    return parse_nine_humidity(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_psr(url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en") -> PsrForecast:
    """Download the chance of significant rain from the 9-day forecast."""
    forecast = fetch_nine_day(url, timeout, lang)
    return PsrForecast(
        update_time=forecast.update_time,
        days=tuple(PsrDay(day.date, day.week, day.rain_chance) for day in forecast.days),
    )


def fetch_tomorrow(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> TomorrowForecast | None:
    """Download tomorrow's day from the 9-day forecast (`dataType=fnd`)."""
    return parse_tomorrow(
        _fetch_json(_apply_lang(url, lang), timeout),
        _hong_kong_tomorrow(),
    )


def fetch_today(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> TomorrowForecast | None:
    """Download today's day from the 9-day forecast (`dataType=fnd`)."""
    return parse_tomorrow(
        _fetch_json(_apply_lang(url, lang), timeout),
        _hong_kong_today(),
    )


def fetch_yesterday(timeout: float = 10, lang: str = "en") -> YesterdayReport | None:
    """Download yesterday's Observatory summary (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_yesterday(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_mean_temp(timeout: float = 10, lang: str = "en") -> DailyMean | None:
    """Download the latest daily mean temperature (`dataType=CLMTEMP`, station HKO)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=CLMTEMP&rformat=json&station=HKO&year={year}&lang=en"
    )
    return parse_mean_temp(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_tai_mo_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Tai Mo Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMS/"
        f"{year}/daily_TMS_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_temp(text, lang)


def fetch_tate_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Tate's Cairn."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TC/"
        f"{year}/daily_TC_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tate_temp(text, lang)


def fetch_sai_kung_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Sai Kung."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKG/"
        f"{year}/daily_SKG_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sai_kung_temp(text, lang)


def fetch_sha_tin_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Sha Tin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SHA/"
        f"{year}/daily_SHA_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_tin_temp(text, lang)


def fetch_sheung_shui_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Sheung Shui."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSH/"
        f"{year}/daily_SSH_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sheung_shui_temp(text, lang)


def fetch_wong_chuk_hang_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Wong Chuk Hang."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKS/"
        f"{year}/daily_HKS_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_chuk_hang_temp(text, lang)


def fetch_lau_fau_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Lau Fau Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LFS/"
        f"{year}/daily_LFS_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lau_fau_temp(text, lang)


def fetch_tseung_kwan_o_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Tseung Kwan O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/JKB/"
        f"{year}/daily_JKB_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tseung_kwan_o_temp(text, lang)


def fetch_sham_shui_po_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Sham Shui Po."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSP/"
        f"{year}/daily_SSP_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sham_shui_po_temp(text, lang)


def fetch_shek_kong_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Shek Kong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SEK/"
        f"{year}/daily_SEK_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shek_kong_temp(text, lang)


def fetch_wetland_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Wetland Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WLP/"
        f"{year}/daily_WLP_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wetland_temp(text, lang)


def fetch_ta_kwu_ling_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Ta Kwu Ling."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TKL/"
        f"{year}/daily_TKL_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ta_kwu_ling_temp(text, lang)


def fetch_peng_chau_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Peng Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PEN/"
        f"{year}/daily_PEN_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_peng_chau_temp(text, lang)


def fetch_park_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_park_temp(text, lang)


def fetch_cheung_chau_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Cheung Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCH/"
        f"{year}/daily_CCH_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_chau_temp(text, lang)


def fetch_waglan_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Waglan Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WGL/"
        f"{year}/daily_WGL_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_waglan_temp(text, lang)


def fetch_ping_chau_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Ping Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/EPC/"
        f"{year}/daily_EPC_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ping_chau_temp(text, lang)


def fetch_sha_lo_wan_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Sha Lo Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SLW/"
        f"{year}/daily_SLW_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_lo_wan_temp(text, lang)


def fetch_airport_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_airport_temp(text, lang)


def fetch_clear_water_bay_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Clear Water Bay."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CWB/"
        f"{year}/daily_CWB_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_clear_water_bay_temp(text, lang)


def fetch_hong_kong_park_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Hong Kong Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKP/"
        f"{year}/daily_HKP_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_hong_kong_park_temp(text, lang)


def fetch_ngong_ping_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Ngong Ping."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NGP/"
        f"{year}/daily_NGP_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ngong_ping_temp(text, lang)


def fetch_kwun_tong_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Kwun Tong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KTG/"
        f"{year}/daily_KTG_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kwun_tong_temp(text, lang)


def fetch_wong_tai_sin_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Wong Tai Sin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WTS/"
        f"{year}/daily_WTS_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_tai_sin_temp(text, lang)


def fetch_tsuen_wan_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Tsuen Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TWN/"
        f"{year}/daily_TWN_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tsuen_wan_temp(text, lang)


def fetch_yuen_long_park_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Yuen Long Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/YLP/"
        f"{year}/daily_YLP_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_yuen_long_park_temp(text, lang)


def fetch_tap_mun_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Tap Mun."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TAP/"
        f"{year}/daily_TAP_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tap_mun_temp(text, lang)


def fetch_shau_kei_wan_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Shau Kei Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKW/"
        f"{year}/daily_SKW_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shau_kei_wan_temp(text, lang)


def fetch_happy_valley_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Happy Valley."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HPV/"
        f"{year}/daily_HPV_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_happy_valley_temp(text, lang)


def fetch_tai_mei_tuk_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Tai Mei Tuk."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PLC/"
        f"{year}/daily_PLC_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mei_tuk_temp(text, lang)


def fetch_kau_sai_chau_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Kau Sai Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KSC/"
        f"{year}/daily_KSC_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kau_sai_chau_temp(text, lang)


def fetch_kadoorie_farm_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Kadoorie Farm and Botanic Garden."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KFB/"
        f"{year}/daily_KFB_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kadoorie_farm_temp(text, lang)


def fetch_the_peak_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at The Peak."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/VP1/"
        f"{year}/daily_VP1_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_the_peak_temp(text, lang)


def fetch_kat_o_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Kat O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KAT/"
        f"{year}/daily_KAT_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kat_o_temp(text, lang)


def fetch_pak_tam_chung_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Pak Tam Chung (Tsak Yue Wu)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TYW/"
        f"{year}/daily_TYW_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_pak_tam_chung_temp(text, lang)


def fetch_beas_river_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Beas River."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/BR1/"
        f"{year}/daily_BR1_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_beas_river_temp(text, lang)


def fetch_bluff_head_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Bluff Head."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/BHD/"
        f"{year}/daily_BHD_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_bluff_head_temp(text, lang)


def fetch_runway_park_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Kai Tak Runway Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SE1/"
        f"{year}/daily_SE1_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_runway_park_temp(text, lang)


def fetch_kowloon_city_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Kowloon City."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KLT/"
        f"{year}/daily_KLT_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kowloon_city_temp(text, lang)


def fetch_nei_lak_shan_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Nei Lak Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NLS/"
        f"{year}/daily_NLS_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_nei_lak_shan_temp(text, lang)


def fetch_new_tsing_yi_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at New Tsing Yi Station."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TY1/"
        f"{year}/daily_TY1_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_new_tsing_yi_temp(text, lang)


def fetch_stanley_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Stanley."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/STY/"
        f"{year}/daily_STY_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_stanley_temp(text, lang)


def fetch_shing_mun_valley_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Tsuen Wan Shing Mun Valley."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TW/"
        f"{year}/daily_TW_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shing_mun_valley_temp(text, lang)


def fetch_tuen_mun_home_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at Tuen Mun Children and Juvenile Home."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TU1/"
        f"{year}/daily_TU1_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tuen_mun_home_temp(text, lang)


def fetch_buoy_2_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at weather buoy No.2."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB2/"
        f"{year}/daily_WB2_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_2_temp(text, lang)


def fetch_buoy_8_temp(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily mean temperature at weather buoy No.8."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB8/"
        f"{year}/daily_WB8_TEMP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_8_temp(text, lang)


def fetch_tai_mo_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Tai Mo Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMS/"
        f"{year}/daily_TMS_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_min(text, lang)


def fetch_tate_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Tate's Cairn."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TC/"
        f"{year}/daily_TC_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tate_min(text, lang)


def fetch_sai_kung_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Sai Kung."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKG/"
        f"{year}/daily_SKG_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sai_kung_min(text, lang)


def fetch_wong_chuk_hang_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Wong Chuk Hang."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKS/"
        f"{year}/daily_HKS_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_chuk_hang_min(text, lang)


def fetch_waglan_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Waglan Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WGL/"
        f"{year}/daily_WGL_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_waglan_min(text, lang)


def fetch_sha_tin_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Sha Tin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SHA/"
        f"{year}/daily_SHA_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_tin_min(text, lang)


def fetch_cheung_chau_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Cheung Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCH/"
        f"{year}/daily_CCH_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_chau_min(text, lang)


def fetch_park_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_park_min(text, lang)


def fetch_lau_fau_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Lau Fau Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LFS/"
        f"{year}/daily_LFS_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lau_fau_min(text, lang)


def fetch_sheung_shui_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Sheung Shui."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSH/"
        f"{year}/daily_SSH_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sheung_shui_min(text, lang)


def fetch_tseung_kwan_o_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Tseung Kwan O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/JKB/"
        f"{year}/daily_JKB_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tseung_kwan_o_min(text, lang)


def fetch_sham_shui_po_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Sham Shui Po."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSP/"
        f"{year}/daily_SSP_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sham_shui_po_min(text, lang)


def fetch_shek_kong_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Shek Kong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SEK/"
        f"{year}/daily_SEK_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shek_kong_min(text, lang)


def fetch_wetland_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Wetland Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WLP/"
        f"{year}/daily_WLP_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wetland_min(text, lang)


def fetch_ta_kwu_ling_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Ta Kwu Ling."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TKL/"
        f"{year}/daily_TKL_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ta_kwu_ling_min(text, lang)


def fetch_sha_lo_wan_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Sha Lo Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SLW/"
        f"{year}/daily_SLW_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_lo_wan_min(text, lang)


def fetch_airport_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_airport_min(text, lang)


def fetch_yuen_long_park_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Yuen Long Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/YLP/"
        f"{year}/daily_YLP_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_yuen_long_park_min(text, lang)


def fetch_clear_water_bay_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Clear Water Bay."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CWB/"
        f"{year}/daily_CWB_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_clear_water_bay_min(text, lang)


def fetch_tap_mun_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Tap Mun."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TAP/"
        f"{year}/daily_TAP_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tap_mun_min(text, lang)


def fetch_hong_kong_park_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Hong Kong Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKP/"
        f"{year}/daily_HKP_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_hong_kong_park_min(text, lang)


def fetch_ngong_ping_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Ngong Ping."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NGP/"
        f"{year}/daily_NGP_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ngong_ping_min(text, lang)


def fetch_kwun_tong_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Kwun Tong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KTG/"
        f"{year}/daily_KTG_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kwun_tong_min(text, lang)


def fetch_wong_tai_sin_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Wong Tai Sin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WTS/"
        f"{year}/daily_WTS_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_tai_sin_min(text, lang)


def fetch_tsuen_wan_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Tsuen Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TWN/"
        f"{year}/daily_TWN_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tsuen_wan_min(text, lang)


def fetch_kau_sai_chau_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Kau Sai Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KSC/"
        f"{year}/daily_KSC_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kau_sai_chau_min(text, lang)


def fetch_kadoorie_farm_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Kadoorie Farm and Botanic Garden."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KFB/"
        f"{year}/daily_KFB_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kadoorie_farm_min(text, lang)


def fetch_the_peak_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at The Peak."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/VP1/"
        f"{year}/daily_VP1_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_the_peak_min(text, lang)


def fetch_kat_o_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Kat O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KAT/"
        f"{year}/daily_KAT_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kat_o_min(text, lang)


def fetch_pak_tam_chung_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Pak Tam Chung."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TYW/"
        f"{year}/daily_TYW_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_pak_tam_chung_min(text, lang)


def fetch_beas_river_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Beas River."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/BR1/"
        f"{year}/daily_BR1_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_beas_river_min(text, lang)


def fetch_kowloon_city_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Kowloon City."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KLT/"
        f"{year}/daily_KLT_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kowloon_city_min(text, lang)


def fetch_new_tsing_yi_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at New Tsing Yi Station."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TY1/"
        f"{year}/daily_TY1_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_new_tsing_yi_min(text, lang)


def fetch_stanley_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Stanley."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/STY/"
        f"{year}/daily_STY_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_stanley_min(text, lang)


def fetch_shing_mun_valley_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Tsuen Wan Shing Mun Valley."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TW/"
        f"{year}/daily_TW_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shing_mun_valley_min(text, lang)


def fetch_tuen_mun_home_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at Tuen Mun Children and Juvenile Home."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TU1/"
        f"{year}/daily_TU1_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tuen_mun_home_min(text, lang)


def fetch_buoy_2_min(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily minimum temperature at weather buoy No.2."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB2/"
        f"{year}/daily_WB2_MINT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_2_min(text, lang)


def fetch_tai_mo_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Tai Mo Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMS/"
        f"{year}/daily_TMS_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_max(text, lang)


def fetch_tseung_kwan_o_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Tseung Kwan O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/JKB/"
        f"{year}/daily_JKB_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tseung_kwan_o_max(text, lang)


def fetch_sheung_shui_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Sheung Shui."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSH/"
        f"{year}/daily_SSH_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sheung_shui_max(text, lang)


def fetch_waglan_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Waglan Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WGL/"
        f"{year}/daily_WGL_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_waglan_max(text, lang)


def fetch_shek_kong_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Shek Kong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SEK/"
        f"{year}/daily_SEK_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shek_kong_max(text, lang)


def fetch_cheung_chau_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Cheung Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCH/"
        f"{year}/daily_CCH_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_chau_max(text, lang)


def fetch_park_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_park_max(text, lang)


def fetch_lau_fau_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Lau Fau Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LFS/"
        f"{year}/daily_LFS_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lau_fau_max(text, lang)


def fetch_sai_kung_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Sai Kung."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKG/"
        f"{year}/daily_SKG_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sai_kung_max(text, lang)


def fetch_sha_tin_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Sha Tin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SHA/"
        f"{year}/daily_SHA_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_tin_max(text, lang)


def fetch_tate_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Tate's Cairn."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TC/"
        f"{year}/daily_TC_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tate_max(text, lang)


def fetch_wong_chuk_hang_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Wong Chuk Hang."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKS/"
        f"{year}/daily_HKS_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_chuk_hang_max(text, lang)


def fetch_sham_shui_po_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Sham Shui Po."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSP/"
        f"{year}/daily_SSP_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sham_shui_po_max(text, lang)


def fetch_wetland_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Wetland Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WLP/"
        f"{year}/daily_WLP_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wetland_max(text, lang)


def fetch_ta_kwu_ling_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Ta Kwu Ling."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TKL/"
        f"{year}/daily_TKL_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ta_kwu_ling_max(text, lang)


def fetch_sha_lo_wan_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Sha Lo Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SLW/"
        f"{year}/daily_SLW_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_lo_wan_max(text, lang)


def fetch_airport_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_airport_max(text, lang)


def fetch_yuen_long_park_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Yuen Long Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/YLP/"
        f"{year}/daily_YLP_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_yuen_long_park_max(text, lang)


def fetch_clear_water_bay_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Clear Water Bay."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CWB/"
        f"{year}/daily_CWB_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_clear_water_bay_max(text, lang)


def fetch_tap_mun_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Tap Mun."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TAP/"
        f"{year}/daily_TAP_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tap_mun_max(text, lang)


def fetch_hong_kong_park_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Hong Kong Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKP/"
        f"{year}/daily_HKP_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_hong_kong_park_max(text, lang)


def fetch_ngong_ping_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Ngong Ping."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NGP/"
        f"{year}/daily_NGP_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ngong_ping_max(text, lang)


def fetch_kwun_tong_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Kwun Tong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KTG/"
        f"{year}/daily_KTG_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kwun_tong_max(text, lang)


def fetch_wong_tai_sin_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Wong Tai Sin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WTS/"
        f"{year}/daily_WTS_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_tai_sin_max(text, lang)


def fetch_tsuen_wan_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Tsuen Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TWN/"
        f"{year}/daily_TWN_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tsuen_wan_max(text, lang)


def fetch_kau_sai_chau_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Kau Sai Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KSC/"
        f"{year}/daily_KSC_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kau_sai_chau_max(text, lang)


def fetch_kadoorie_farm_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Kadoorie Farm and Botanic Garden."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KFB/"
        f"{year}/daily_KFB_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kadoorie_farm_max(text, lang)


def fetch_the_peak_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at The Peak."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/VP1/"
        f"{year}/daily_VP1_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_the_peak_max(text, lang)


def fetch_kat_o_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Kat O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KAT/"
        f"{year}/daily_KAT_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kat_o_max(text, lang)


def fetch_pak_tam_chung_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Pak Tam Chung (Tsak Yue Wu)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TYW/"
        f"{year}/daily_TYW_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_pak_tam_chung_max(text, lang)


def fetch_beas_river_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Beas River."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/BR1/"
        f"{year}/daily_BR1_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_beas_river_max(text, lang)


def fetch_kowloon_city_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Kowloon City."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KLT/"
        f"{year}/daily_KLT_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kowloon_city_max(text, lang)


def fetch_new_tsing_yi_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at New Tsing Yi Station."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TY1/"
        f"{year}/daily_TY1_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_new_tsing_yi_max(text, lang)


def fetch_stanley_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Stanley."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/STY/"
        f"{year}/daily_STY_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_stanley_max(text, lang)


def fetch_shing_mun_valley_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Tsuen Wan Shing Mun Valley."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TW/"
        f"{year}/daily_TW_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shing_mun_valley_max(text, lang)


def fetch_tuen_mun_home_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at Tuen Mun Children and Juvenile Home."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TU1/"
        f"{year}/daily_TU1_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tuen_mun_home_max(text, lang)


def fetch_buoy_2_max(timeout: float = 10, lang: str = "en") -> TaiMoTemp | None:
    """Download the latest daily maximum temperature at weather buoy No.2."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB2/"
        f"{year}/daily_WB2_MAXT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_2_max(text, lang)


def fetch_max_temp(timeout: float = 10, lang: str = "en") -> DailyMax | None:
    """Download the latest daily maximum temperature (`dataType=CLMMAXT`, station HKO)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=CLMMAXT&rformat=json&station=HKO&year={year}&lang=en"
    )
    return parse_max_temp(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_min_temp(timeout: float = 10, lang: str = "en") -> DailyMin | None:
    """Download the latest daily minimum temperature (`dataType=CLMMINT`, station HKO)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=CLMMINT&rformat=json&station=HKO&year={year}&lang=en"
    )
    return parse_min_temp(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_dew_point(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at the Observatory."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKO/"
        f"{year}/daily_HKO_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_dew_point(text, lang)


def fetch_park_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_park_dew(text, lang)


def fetch_cheung_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Cheung Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCH/"
        f"{year}/daily_CCH_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_dew(text, lang)


def fetch_wong_chuk_hang_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Wong Chuk Hang."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKS/"
        f"{year}/daily_HKS_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_chuk_hang_dew(text, lang)


def fetch_sai_kung_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Sai Kung."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKG/"
        f"{year}/daily_SKG_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sai_kung_dew(text, lang)


def fetch_sha_tin_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Sha Tin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SHA/"
        f"{year}/daily_SHA_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_tin_dew(text, lang)


def fetch_sheung_shui_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Sheung Shui."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSH/"
        f"{year}/daily_SSH_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sheung_shui_dew(text, lang)


def fetch_waglan_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Waglan Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WGL/"
        f"{year}/daily_WGL_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_waglan_dew(text, lang)


def fetch_lau_fau_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Lau Fau Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LFS/"
        f"{year}/daily_LFS_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lau_fau_dew(text, lang)


def fetch_wetland_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Wetland Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WLP/"
        f"{year}/daily_WLP_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wetland_dew(text, lang)


def fetch_ta_kwu_ling_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Ta Kwu Ling."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TKL/"
        f"{year}/daily_TKL_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ta_kwu_ling_dew(text, lang)


def fetch_shek_kong_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Shek Kong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SEK/"
        f"{year}/daily_SEK_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shek_kong_dew(text, lang)


def fetch_tseung_kwan_o_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Tseung Kwan O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/JKB/"
        f"{year}/daily_JKB_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tseung_kwan_o_dew(text, lang)


def fetch_tai_mo_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Tai Mo Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMS/"
        f"{year}/daily_TMS_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_dew(text, lang)


def fetch_peng_chau_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Peng Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PEN/"
        f"{year}/daily_PEN_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_peng_chau_dew(text, lang)


def fetch_sha_lo_wan_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Sha Lo Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SLW/"
        f"{year}/daily_SLW_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_lo_wan_dew(text, lang)


def fetch_airport_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_airport_dew(text, lang)


def fetch_clear_water_bay_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Clear Water Bay."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CWB/"
        f"{year}/daily_CWB_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_clear_water_bay_dew(text, lang)


def fetch_hong_kong_park_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Hong Kong Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKP/"
        f"{year}/daily_HKP_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_hong_kong_park_dew(text, lang)


def fetch_tsuen_wan_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Tsuen Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TWN/"
        f"{year}/daily_TWN_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tsuen_wan_dew(text, lang)


def fetch_shau_kei_wan_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Shau Kei Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKW/"
        f"{year}/daily_SKW_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shau_kei_wan_dew(text, lang)


def fetch_kau_sai_chau_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Kau Sai Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KSC/"
        f"{year}/daily_KSC_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kau_sai_chau_dew(text, lang)


def fetch_pak_tam_chung_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Pak Tam Chung."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TYW/"
        f"{year}/daily_TYW_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_pak_tam_chung_dew(text, lang)


def fetch_beas_river_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Beas River."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/BR1/"
        f"{year}/daily_BR1_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_beas_river_dew(text, lang)


def fetch_runway_park_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Kai Tak Runway Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SE1/"
        f"{year}/daily_SE1_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_runway_park_dew(text, lang)


def fetch_kowloon_city_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Kowloon City."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KLT/"
        f"{year}/daily_KLT_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kowloon_city_dew(text, lang)


def fetch_nei_lak_shan_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Nei Lak Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NLS/"
        f"{year}/daily_NLS_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_nei_lak_shan_dew(text, lang)


def fetch_new_tsing_yi_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at New Tsing Yi Station."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TY1/"
        f"{year}/daily_TY1_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_new_tsing_yi_dew(text, lang)


def fetch_tate_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Tate's Cairn."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TC/"
        f"{year}/daily_TC_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tate_dew(text, lang)


def fetch_shing_mun_valley_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Tsuen Wan Shing Mun Valley."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TW/"
        f"{year}/daily_TW_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shing_mun_valley_dew(text, lang)


def fetch_tuen_mun_home_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at Tuen Mun Children and Juvenile Home."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TU1/"
        f"{year}/daily_TU1_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tuen_mun_home_dew(text, lang)


def fetch_buoy_2_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at weather buoy No.2."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB2/"
        f"{year}/daily_WB2_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_2_dew(text, lang)


def fetch_buoy_8_dew(timeout: float = 10, lang: str = "en") -> DewPoint | None:
    """Download the latest daily mean dew point at weather buoy No.8."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB8/"
        f"{year}/daily_WB8_DEW_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_8_dew(text, lang)


def fetch_cloud(timeout: float = 10, lang: str = "en") -> CloudAmount | None:
    """Download the latest daily mean cloud amount at the Observatory."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKO/"
        f"{year}/daily_HKO_CLD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cloud(text, lang)


def fetch_evaporation(timeout: float = 10, lang: str = "en") -> Evaporation | None:
    """Download the latest daily total evaporation at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_EVAP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_evaporation(text, lang)


def fetch_evapotranspiration(
    timeout: float = 10, lang: str = "en"
) -> Evapotranspiration | None:
    """Download the latest monthly potential evapotranspiration at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/monthly_KP_EVAPTRAN_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_evapotranspiration(text, lang)


def fetch_grass(timeout: float = 10, lang: str = "en") -> GrassMinimum | None:
    """Download yesterday's grass minimum (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_grass(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_sunshine(timeout: float = 10, lang: str = "en") -> Sunshine | None:
    """Download yesterday's sunshine duration (`dataType=RYES`, station KP)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}"
        f"&station={SUNSHINE_STATION}&lang=en"
    )
    return parse_sunshine(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_daily_sun(timeout: float = 10, lang: str = "en") -> DailySun | None:
    """Download the latest daily bright sunshine total at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_SUN_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_daily_sun(text, lang)


def fetch_max_uv(timeout: float = 10, lang: str = "en") -> MaxUv | None:
    """Download yesterday's maximum UV index (`dataType=RYES`, station KP)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}"
        f"&station={SUNSHINE_STATION}&lang=en"
    )
    return parse_max_uv(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_uv_peak(timeout: float = 10, lang: str = "en") -> UvPeak | None:
    """Download the latest daily maximum UV index and its 15-minute period."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_MAXUV_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_uv_peak(text, lang)


def fetch_mean_uv(timeout: float = 10, lang: str = "en") -> MeanUv | None:
    """Download yesterday's mean UV index (`dataType=RYES`, station KP)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}"
        f"&station={SUNSHINE_STATION}&lang=en"
    )
    return parse_mean_uv(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_daily_uv(timeout: float = 10, lang: str = "en") -> MeanUv | None:
    """Download the latest daily mean UV index at King's Park (7 a.m. to 6 p.m.)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_UV_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_daily_uv(text, lang)


def fetch_dose(timeout: float = 10, lang: str = "en") -> GammaDose | None:
    """Download yesterday's gamma dose rate (`dataType=RYES`, station KP)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}"
        f"&station={SUNSHINE_STATION}&lang=en"
    )
    return parse_dose(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_hourly_dose(timeout: float = 10, lang: str = "en") -> HourlyDoseReport:
    """Download the latest hourly mean ambient gamma dose rate."""
    url = HOURLY_DOSE_URLS.get(lang, HOURLY_DOSE_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_hourly_dose(text)


def fetch_accum_rain(timeout: float = 10, lang: str = "en") -> AccumulatedRainfall | None:
    """Download accumulated rainfall since 1 January (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_accum_rain(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_avg_rain(timeout: float = 10, lang: str = "en") -> AverageRainfall | None:
    """Download the climatological rainfall normal (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_avg_rain(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_rain_vs_normal(timeout: float = 10, lang: str = "en") -> RainComparison | None:
    """Download accumulated rainfall and its normal (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_rain_vs_normal(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_radiation(timeout: float = 10, lang: str = "en") -> RadiationReport | None:
    """Download yesterday's gamma radiation report (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_radiation(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_bulletin(timeout: float = 10, lang: str = "en") -> WeatherBulletin | None:
    """Download the issue time of yesterday's bulletin (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_bulletin(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_radiation_note(timeout: float = 10, lang: str = "en") -> RadiationNote | None:
    """Download the radiation range note (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_radiation_note(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_radiation_weather(timeout: float = 10, lang: str = "en") -> RadiationWeather | None:
    """Download the weather-variation radiation note (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_radiation_weather(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_radiation_ground(timeout: float = 10, lang: str = "en") -> RadiationGround | None:
    """Download the ground-variation radiation note (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_radiation_ground(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_radiation_provisional(
    timeout: float = 10, lang: str = "en"
) -> RadiationProvisional | None:
    """Download the provisional radiation note (`dataType=RYES`, station HKO)."""
    day = _hong_kong_yesterday()
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=RYES&rformat=json&date={day.replace('-', '')}&station=HKO&lang=en"
    )
    return parse_radiation_provisional(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_summary(timeout: float = 10, lang: str = "en") -> WeatherSummary:
    """Briefing from current conditions, active warnings, and today's forecast."""
    weather = fetch_current(timeout=timeout, lang=lang)
    warnings = fetch_warnings(timeout=timeout, lang=lang)
    today = fetch_today(timeout=timeout, lang=lang)
    humidity = (
        f"{_number(weather.humidity_percent)}%"
        if weather.humidity_percent is not None
        else "n/a"
    )
    conditions = f"{weather.conditions}, {_number(weather.temperature_c)}°C, humidity {humidity}"
    summary_today = None
    if today is not None:
        summary_today = SummaryToday(
            date=today.date,
            high_c=today.temp_high_c,
            low_c=today.temp_low_c,
            rain_chance=today.rain_chance,
        )
    return WeatherSummary(conditions, warnings, summary_today)


def fetch_forecast_day(
    day: int, url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> TomorrowForecast | None:
    """Download forecast day N, where 1 is the first `weatherForecast` entry."""
    return parse_forecast_day(_fetch_json(_apply_lang(url, lang), timeout), day)


def fetch_weekend(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> WeekendForecast:
    """Download Saturday and Sunday from the 9-day forecast (`dataType=fnd`)."""
    return parse_weekend(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_wind(url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en") -> WindForecast:
    """Download forecast wind from the 9-day forecast (`dataType=fnd`)."""
    return parse_wind(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_gust(timeout: float = 10, lang: str = "en") -> GustReport:
    """Download the latest 10-minute wind and gust at automatic stations."""
    url = GUST_URLS.get(lang, GUST_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_gust(text)


def fetch_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Waglan Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WGL/"
        f"{year}/daily_WGL_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_prevailing(text, lang)


def fetch_cheung_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Cheung Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCH/"
        f"{year}/daily_CCH_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_prevailing(text, lang)


def fetch_ping_chau_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Ping Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/EPC/"
        f"{year}/daily_EPC_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ping_chau_prevailing(text, lang)


def fetch_tai_mo_to_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Tai Mo To."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMT/"
        f"{year}/daily_TMT_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_to_prevailing(text, lang)


def fetch_tai_po_kau_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Tai Po Kau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TPK/"
        f"{year}/daily_TPK_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_po_kau_prevailing(text, lang)


def fetch_park_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_park_prevailing(text, lang)


def fetch_lau_fau_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Lau Fau Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LFS/"
        f"{year}/daily_LFS_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lau_fau_prevailing(text, lang)


def fetch_sha_lo_wan_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Sha Lo Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SLW/"
        f"{year}/daily_SLW_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_lo_wan_prevailing(text, lang)


def fetch_wong_chuk_hang_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Wong Chuk Hang."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKS/"
        f"{year}/daily_HKS_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_chuk_hang_prevailing(text, lang)


def fetch_sai_kung_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Sai Kung."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKG/"
        f"{year}/daily_SKG_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sai_kung_prevailing(text, lang)


def fetch_tseung_kwan_o_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Tseung Kwan O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/JKB/"
        f"{year}/daily_JKB_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tseung_kwan_o_prevailing(text, lang)


def fetch_shek_kong_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Shek Kong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SEK/"
        f"{year}/daily_SEK_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shek_kong_prevailing(text, lang)


def fetch_sha_tin_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Sha Tin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SHA/"
        f"{year}/daily_SHA_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_tin_prevailing(text, lang)


def fetch_ta_kwu_ling_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Ta Kwu Ling."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TKL/"
        f"{year}/daily_TKL_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ta_kwu_ling_prevailing(text, lang)


def fetch_wetland_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Wetland Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WLP/"
        f"{year}/daily_WLP_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wetland_prevailing(text, lang)


def fetch_tai_mo_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Tai Mo Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMS/"
        f"{year}/daily_TMS_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_prevailing(text, lang)


def fetch_airport_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_airport_prevailing(text, lang)


def fetch_kai_tak_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Kai Tak."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SE/"
        f"{year}/daily_SE_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kai_tak_prevailing(text, lang)


def fetch_green_island_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Green Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/GI/"
        f"{year}/daily_GI_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_green_island_prevailing(text, lang)


def fetch_ngong_ping_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Ngong Ping."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NGP/"
        f"{year}/daily_NGP_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ngong_ping_prevailing(text, lang)


def fetch_tai_mei_tuk_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Tai Mei Tuk."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PLC/"
        f"{year}/daily_PLC_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mei_tuk_prevailing(text, lang)


def fetch_central_pier_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Central Pier."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CP1/"
        f"{year}/daily_CP1_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_central_pier_prevailing(text, lang)


def fetch_nei_lak_shan_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Nei Lak Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NLS/"
        f"{year}/daily_NLS_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_nei_lak_shan_prevailing(text, lang)


def fetch_buoy_2_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at weather buoy No.2."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB2/"
        f"{year}/daily_WB2_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_2_prevailing(text, lang)


def fetch_buoy_8_prevailing(timeout: float = 10, lang: str = "en") -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at weather buoy No.8."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB8/"
        f"{year}/daily_WB8_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_8_prevailing(text, lang)


def fetch_cheung_chau_beach_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Cheung Chau Beach."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCB/"
        f"{year}/daily_CCB_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_chau_beach_prevailing(text, lang)


def fetch_north_point_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at North Point."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NP/"
        f"{year}/daily_NP_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_north_point_prevailing(text, lang)


def fetch_sha_chau_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Sha Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SC/"
        f"{year}/daily_SC_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_chau_prevailing(text, lang)


def fetch_star_ferry_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Star Ferry(Kowloon)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SF/"
        f"{year}/daily_SF_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_star_ferry_prevailing(text, lang)


def fetch_tuen_mun_government_offices_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Tuen Mun Government Offices."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TUN/"
        f"{year}/daily_TUN_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tuen_mun_government_offices_prevailing(text, lang)


def fetch_yi_tung_shan_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Yi Tung Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/YTS/"
        f"{year}/daily_YTS_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_yi_tung_shan_prevailing(text, lang)


def fetch_tap_mun_east_prevailing(
    timeout: float = 10, lang: str = "en"
) -> PrevailingWind | None:
    """Download the latest daily prevailing wind direction at Tap Mun East."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TME/"
        f"{year}/daily_TME_PDIR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tap_mun_east_prevailing(text, lang)


def fetch_mean_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Waglan Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WGL/"
        f"{year}/daily_WGL_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_mean_wind(text, lang)


def fetch_cheung_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Cheung Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCH/"
        f"{year}/daily_CCH_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_wind(text, lang)


def fetch_lau_fau_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Lau Fau Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LFS/"
        f"{year}/daily_LFS_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lau_fau_wind(text, lang)


def fetch_peng_chau_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Peng Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PEN/"
        f"{year}/daily_PEN_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_peng_chau_wind(text, lang)


def fetch_tai_po_kau_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Tai Po Kau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TPK/"
        f"{year}/daily_TPK_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_po_kau_wind(text, lang)


def fetch_tai_mo_to_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Tai Mo To."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMT/"
        f"{year}/daily_TMT_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_to_wind(text, lang)


def fetch_tai_mo_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Tai Mo Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMS/"
        f"{year}/daily_TMS_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_wind(text, lang)


def fetch_tate_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Tate's Cairn."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TC/"
        f"{year}/daily_TC_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tate_wind(text, lang)


def fetch_shek_kong_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Shek Kong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SEK/"
        f"{year}/daily_SEK_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shek_kong_wind(text, lang)


def fetch_sai_kung_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Sai Kung."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKG/"
        f"{year}/daily_SKG_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sai_kung_wind(text, lang)


def fetch_sha_tin_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Sha Tin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SHA/"
        f"{year}/daily_SHA_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_tin_wind(text, lang)


def fetch_wong_chuk_hang_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Wong Chuk Hang."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKS/"
        f"{year}/daily_HKS_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_chuk_hang_wind(text, lang)


def fetch_park_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_park_wind(text, lang)


def fetch_wetland_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Wetland Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WLP/"
        f"{year}/daily_WLP_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wetland_wind(text, lang)


def fetch_tseung_kwan_o_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Tseung Kwan O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/JKB/"
        f"{year}/daily_JKB_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tseung_kwan_o_wind(text, lang)


def fetch_ta_kwu_ling_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Ta Kwu Ling."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TKL/"
        f"{year}/daily_TKL_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ta_kwu_ling_wind(text, lang)


def fetch_sha_lo_wan_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Sha Lo Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SLW/"
        f"{year}/daily_SLW_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_lo_wan_wind(text, lang)


def fetch_ping_chau_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Ping Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/EPC/"
        f"{year}/daily_EPC_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ping_chau_wind(text, lang)


def fetch_airport_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_airport_wind(text, lang)


def fetch_green_island_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Green Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/GI/"
        f"{year}/daily_GI_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_green_island_wind(text, lang)


def fetch_ngong_ping_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Ngong Ping."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NGP/"
        f"{year}/daily_NGP_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ngong_ping_wind(text, lang)


def fetch_tai_mei_tuk_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Tai Mei Tuk."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PLC/"
        f"{year}/daily_PLC_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mei_tuk_wind(text, lang)


def fetch_lamma_island_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Lamma Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LAM/"
        f"{year}/daily_LAM_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lamma_island_wind(text, lang)


def fetch_kai_tak_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Kai Tak."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SE/"
        f"{year}/daily_SE_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kai_tak_wind(text, lang)


def fetch_central_pier_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Central Pier."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CP1/"
        f"{year}/daily_CP1_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_central_pier_wind(text, lang)


def fetch_nei_lak_shan_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Nei Lak Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NLS/"
        f"{year}/daily_NLS_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_nei_lak_shan_wind(text, lang)


def fetch_buoy_2_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at weather buoy No.2."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB2/"
        f"{year}/daily_WB2_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_2_wind(text, lang)


def fetch_buoy_8_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at weather buoy No.8."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB8/"
        f"{year}/daily_WB8_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_8_wind(text, lang)


def fetch_cheung_chau_beach_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Cheung Chau Beach."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCB/"
        f"{year}/daily_CCB_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_chau_beach_wind(text, lang)


def fetch_north_point_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at North Point."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NP/"
        f"{year}/daily_NP_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_north_point_wind(text, lang)


def fetch_sha_chau_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Sha Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SC/"
        f"{year}/daily_SC_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_chau_wind(text, lang)


def fetch_star_ferry_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Star Ferry(Kowloon)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SF/"
        f"{year}/daily_SF_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_star_ferry_wind(text, lang)


def fetch_tuen_mun_government_offices_wind(
    timeout: float = 10, lang: str = "en"
) -> MeanWind | None:
    """Download the latest daily mean wind speed at Tuen Mun Government Offices."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TUN/"
        f"{year}/daily_TUN_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tuen_mun_government_offices_wind(text, lang)


def fetch_yi_tung_shan_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Yi Tung Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/YTS/"
        f"{year}/daily_YTS_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_yi_tung_shan_wind(text, lang)


def fetch_tap_mun_east_wind(timeout: float = 10, lang: str = "en") -> MeanWind | None:
    """Download the latest daily mean wind speed at Tap Mun East."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TME/"
        f"{year}/daily_TME_WSPD_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tap_mun_east_wind(text, lang)


def fetch_minute_temp(timeout: float = 10, lang: str = "en") -> MinuteTempReport:
    """Download the latest 1-minute mean air temperature at automatic stations."""
    url = MINUTE_TEMP_URLS.get(lang, MINUTE_TEMP_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_minute_temp(text)


def fetch_minute_humidity(timeout: float = 10, lang: str = "en") -> MinuteHumidityReport:
    """Download the latest 1-minute mean relative humidity at automatic stations."""
    url = MINUTE_HUMIDITY_URLS.get(lang, MINUTE_HUMIDITY_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_minute_humidity(text)


def fetch_mean_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at the Observatory."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKO/"
        f"{year}/daily_HKO_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_mean_humidity(text, lang)


def fetch_tai_mo_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Tai Mo Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMS/"
        f"{year}/daily_TMS_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_humidity(text, lang)


def fetch_waglan_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Waglan Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WGL/"
        f"{year}/daily_WGL_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_waglan_humidity(text, lang)


def fetch_tate_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Tate's Cairn."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TC/"
        f"{year}/daily_TC_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tate_humidity(text, lang)


def fetch_ta_kwu_ling_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Ta Kwu Ling."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TKL/"
        f"{year}/daily_TKL_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ta_kwu_ling_humidity(text, lang)


def fetch_wetland_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Wetland Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WLP/"
        f"{year}/daily_WLP_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wetland_humidity(text, lang)


def fetch_shek_kong_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Shek Kong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SEK/"
        f"{year}/daily_SEK_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shek_kong_humidity(text, lang)


def fetch_lau_fau_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Lau Fau Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LFS/"
        f"{year}/daily_LFS_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lau_fau_humidity(text, lang)


def fetch_park_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_park_humidity(text, lang)


def fetch_sai_kung_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Sai Kung."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKG/"
        f"{year}/daily_SKG_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sai_kung_humidity(text, lang)


def fetch_cheung_chau_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Cheung Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCH/"
        f"{year}/daily_CCH_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_chau_humidity(text, lang)


def fetch_sha_tin_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Sha Tin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SHA/"
        f"{year}/daily_SHA_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_tin_humidity(text, lang)


def fetch_sheung_shui_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Sheung Shui."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSH/"
        f"{year}/daily_SSH_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sheung_shui_humidity(text, lang)


def fetch_wong_chuk_hang_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Wong Chuk Hang."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKS/"
        f"{year}/daily_HKS_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_chuk_hang_humidity(text, lang)


def fetch_tseung_kwan_o_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Tseung Kwan O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/JKB/"
        f"{year}/daily_JKB_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tseung_kwan_o_humidity(text, lang)


def fetch_peng_chau_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Peng Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PEN/"
        f"{year}/daily_PEN_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_peng_chau_humidity(text, lang)


def fetch_sha_lo_wan_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Sha Lo Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SLW/"
        f"{year}/daily_SLW_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_lo_wan_humidity(text, lang)


def fetch_airport_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_airport_humidity(text, lang)


def fetch_tsuen_wan_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Tsuen Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TWN/"
        f"{year}/daily_TWN_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tsuen_wan_humidity(text, lang)


def fetch_hong_kong_park_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Hong Kong Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKP/"
        f"{year}/daily_HKP_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_hong_kong_park_humidity(text, lang)


def fetch_clear_water_bay_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Clear Water Bay."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CWB/"
        f"{year}/daily_CWB_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_clear_water_bay_humidity(text, lang)


def fetch_shau_kei_wan_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Shau Kei Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKW/"
        f"{year}/daily_SKW_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shau_kei_wan_humidity(text, lang)


def fetch_kau_sai_chau_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Kau Sai Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KSC/"
        f"{year}/daily_KSC_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kau_sai_chau_humidity(text, lang)


def fetch_pak_tam_chung_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Pak Tam Chung."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TYW/"
        f"{year}/daily_TYW_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_pak_tam_chung_humidity(text, lang)


def fetch_beas_river_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Beas River."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/BR1/"
        f"{year}/daily_BR1_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_beas_river_humidity(text, lang)


def fetch_runway_park_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Kai Tak Runway Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SE1/"
        f"{year}/daily_SE1_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_runway_park_humidity(text, lang)


def fetch_kowloon_city_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Kowloon City."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KLT/"
        f"{year}/daily_KLT_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kowloon_city_humidity(text, lang)


def fetch_nei_lak_shan_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Nei Lak Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NLS/"
        f"{year}/daily_NLS_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_nei_lak_shan_humidity(text, lang)


def fetch_new_tsing_yi_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at New Tsing Yi Station."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TY1/"
        f"{year}/daily_TY1_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_new_tsing_yi_humidity(text, lang)


def fetch_shing_mun_valley_humidity(
    timeout: float = 10, lang: str = "en"
) -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Tsuen Wan Shing Mun Valley."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TW/"
        f"{year}/daily_TW_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shing_mun_valley_humidity(text, lang)


def fetch_tuen_mun_home_humidity(
    timeout: float = 10, lang: str = "en"
) -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at Tuen Mun Children and Juvenile Home."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TU1/"
        f"{year}/daily_TU1_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tuen_mun_home_humidity(text, lang)


def fetch_buoy_2_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at weather buoy No.2."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB2/"
        f"{year}/daily_WB2_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_2_humidity(text, lang)


def fetch_buoy_8_humidity(timeout: float = 10, lang: str = "en") -> MeanHumidity | None:
    """Download the latest daily mean relative humidity at weather buoy No.8."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WB8/"
        f"{year}/daily_WB8_RH_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_buoy_8_humidity(text, lang)


def fetch_since_midnight(timeout: float = 10, lang: str = "en") -> SinceMidnightReport:
    """Download each station's maximum and minimum temperature since midnight."""
    url = SINCE_MIDNIGHT_URLS.get(lang, SINCE_MIDNIGHT_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_since_midnight(text)


def fetch_pressure(timeout: float = 10, lang: str = "en") -> PressureReport:
    """Download the latest 1-minute mean sea level pressure at automatic stations."""
    url = PRESSURE_URLS.get(lang, PRESSURE_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_pressure(text)


def fetch_mean_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at the Observatory."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKO/"
        f"{year}/daily_HKO_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_mean_pressure(text, lang)


def fetch_park_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_park_pressure(text, lang)


def fetch_sha_tin_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Sha Tin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SHA/"
        f"{year}/daily_SHA_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_tin_pressure(text, lang)


def fetch_sheung_shui_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Sheung Shui."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSH/"
        f"{year}/daily_SSH_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sheung_shui_pressure(text, lang)


def fetch_waglan_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Waglan Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WGL/"
        f"{year}/daily_WGL_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_waglan_pressure(text, lang)


def fetch_cheung_chau_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Cheung Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCH/"
        f"{year}/daily_CCH_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_chau_pressure(text, lang)


def fetch_lau_fau_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Lau Fau Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LFS/"
        f"{year}/daily_LFS_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lau_fau_pressure(text, lang)


def fetch_tate_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Tate's Cairn."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TC/"
        f"{year}/daily_TC_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tate_pressure(text, lang)


def fetch_wetland_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Wetland Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WLP/"
        f"{year}/daily_WLP_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wetland_pressure(text, lang)


def fetch_peng_chau_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Peng Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PEN/"
        f"{year}/daily_PEN_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_peng_chau_pressure(text, lang)


def fetch_tai_mo_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Tai Mo Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMS/"
        f"{year}/daily_TMS_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_pressure(text, lang)


def fetch_sha_lo_wan_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Sha Lo Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SLW/"
        f"{year}/daily_SLW_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_lo_wan_pressure(text, lang)


def fetch_shek_kong_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Shek Kong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SEK/"
        f"{year}/daily_SEK_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shek_kong_pressure(text, lang)


def fetch_ta_kwu_ling_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Ta Kwu Ling."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TKL/"
        f"{year}/daily_TKL_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ta_kwu_ling_pressure(text, lang)


def fetch_airport_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_airport_pressure(text, lang)


def fetch_nei_lak_shan_pressure(timeout: float = 10, lang: str = "en") -> MeanPressure | None:
    """Download the latest daily mean pressure at Nei Lak Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NLS/"
        f"{year}/daily_NLS_MSLP_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_nei_lak_shan_pressure(text, lang)


def fetch_minute_grass(timeout: float = 10, lang: str = "en") -> MinuteGrassReport:
    """Download the latest 1-minute mean grass temperature at automatic stations."""
    url = MINUTE_GRASS_URLS.get(lang, MINUTE_GRASS_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_minute_grass(text)


def fetch_daily_grass(timeout: float = 10, lang: str = "en") -> DailyGrass | None:
    """Download the latest daily grass minimum at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_GMT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_daily_grass(text, lang)


def fetch_obs_grass(timeout: float = 10, lang: str = "en") -> DailyGrass | None:
    """Download the latest daily grass minimum at the Observatory."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKO/"
        f"{year}/daily_HKO_GMT_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_obs_grass(text, lang)


def fetch_temp_diff(timeout: float = 10, lang: str = "en") -> TempDiffReport:
    """Download the past 24-hour temperature change at automatic stations."""
    url = TEMP_DIFF_URLS.get(lang, TEMP_DIFF_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_temp_diff(text)


def fetch_heat_index(timeout: float = 10, lang: str = "en") -> HeatIndexReport:
    """Download the latest 10-minute mean Hong Kong Heat Index."""
    url = HEAT_INDEX_URLS.get(lang, HEAT_INDEX_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_heat_index(text)


def fetch_daily_heat(timeout: float = 10, lang: str = "en") -> DailyHeat | None:
    """Download the latest daily maximum Hong Kong Heat Index at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_MAXHKHI_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_daily_heat(text, lang)


def fetch_mean_heat(timeout: float = 10, lang: str = "en") -> DailyHeat | None:
    """Download the latest daily mean Hong Kong Heat Index at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_MEANHKHI_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_mean_heat(text, lang)


def fetch_wbgt(timeout: float = 10, lang: str = "en") -> WbgtReport:
    """Download the latest 60-minute mean Wet Bulb Globe Temperature."""
    url = WBGT_URLS.get(lang, WBGT_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wbgt(text)


def fetch_wet_bulb(timeout: float = 10, lang: str = "en") -> WetBulb | None:
    """Download the latest daily mean wet-bulb temperature at the Observatory."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKO/"
        f"{year}/daily_HKO_WET_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wet_bulb(text, lang)


def fetch_airport_wet(timeout: float = 10, lang: str = "en") -> WetBulb | None:
    """Download the latest daily mean wet-bulb temperature at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_WET_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_airport_wet(text, lang)


def fetch_park_wet(timeout: float = 10, lang: str = "en") -> WetBulb | None:
    """Download the latest daily mean wet-bulb temperature at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_WET_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_park_wet(text, lang)


def fetch_sha_lo_wan_wet(timeout: float = 10, lang: str = "en") -> WetBulb | None:
    """Download the latest daily mean wet-bulb temperature at Sha Lo Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SLW/"
        f"{year}/daily_SLW_WET_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_lo_wan_wet(text, lang)


def fetch_nei_lak_shan_wet(timeout: float = 10, lang: str = "en") -> WetBulb | None:
    """Download the latest daily mean wet-bulb temperature at Nei Lak Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/NLS/"
        f"{year}/daily_NLS_WET_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_nei_lak_shan_wet(text, lang)


def fetch_solar(timeout: float = 10, lang: str = "en") -> SolarReport:
    """Download the latest 1-minute solar radiation at automatic stations."""
    url = SOLAR_URLS.get(lang, SOLAR_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_solar(text)


def fetch_global_solar(timeout: float = 10, lang: str = "en") -> GlobalSolar | None:
    """Download the latest daily global solar radiation at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_GSR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_global_solar(text, lang)


def fetch_kau_sai_chau_solar(timeout: float = 10, lang: str = "en") -> GlobalSolar | None:
    """Download the latest daily global solar radiation at Kau Sai Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KSC/"
        f"{year}/daily_KSC_GSR_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kau_sai_chau_solar(text, lang)


def fetch_forecast_icon(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> ForecastIcons:
    """Download each day's weather icon from the 9-day forecast (`dataType=fnd`)."""
    return parse_forecast_icon(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_quakes(url: str = QUAKE_URL, timeout: float = 10, lang: str = "en") -> QuakeReport:
    """Download the latest quick earthquake message (`dataType=qem`)."""
    return parse_quakes(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_felt(url: str = FELT_URL, timeout: float = 10, lang: str = "en") -> FeltTremor | None:
    """Download the locally felt earth tremor report (`dataType=feltearthquake`)."""
    return parse_felt(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_visibility(
    url: str = VISIBILITY_URL, timeout: float = 10, lang: str = "en"
) -> VisibilityReport:
    """Download the latest 10-minute mean visibility (`dataType=LTMV`)."""
    return parse_visibility(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_reduced_vis(timeout: float = 10, lang: str = "en") -> ReducedVisibility | None:
    """Download the latest daily hours of reduced visibility at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_RVIS_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_reduced_vis(text, lang)


def fetch_tide(timeout: float = 10, lang: str = "en") -> TideReport:
    """Download today's high and low tides at Quarry Bay (`dataType=HLT`)."""
    today = _hong_kong_today()
    year = int(today[:4])
    month = int(today[5:7])
    day = int(today[8:10])
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=HLT&rformat=json&station={TIDE_STATION}"
        f"&year={year}&month={month}&day={day}&lang=en"
    )
    return parse_tide(_fetch_json(_apply_lang(url, lang), timeout), year)


def fetch_tide_hour(timeout: float = 10, lang: str = "en") -> HourlyTideReport:
    """Download today's hourly tide heights at Quarry Bay (`dataType=HHOT`)."""
    today = _hong_kong_today()
    year = int(today[:4])
    month = int(today[5:7])
    day = int(today[8:10])
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=HHOT&rformat=json&station={TIDE_STATION}"
        f"&year={year}&month={month}&day={day}&lang=en"
    )
    return parse_tide_hour(_fetch_json(_apply_lang(url, lang), timeout), year)


def fetch_tide_latest(timeout: float = 10, lang: str = "en") -> LatestTideReport:
    """Download the latest observed tide height at each tide station."""
    url = LATEST_TIDE_URLS.get(lang, LATEST_TIDE_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tide_latest(text)


def fetch_aqhi(timeout: float = 10, lang: str = "en") -> AqhiReport:
    """Download the current Air Quality Health Index (EPD station RSS)."""
    url = AQHI_URLS.get(lang, AQHI_URLS["en"])
    return parse_aqhi(_fetch_text(url, timeout))


def fetch_sunrise(timeout: float = 10, lang: str = "en") -> Sunrise | None:
    """Download today's sunrise, sun transit, and sunset (`dataType=SRS`)."""
    today = _hong_kong_today()
    year = int(today[:4])
    month = int(today[5:7])
    day = int(today[8:10])
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=SRS&rformat=json&year={year}&month={month}&day={day}&lang=en"
    )
    return parse_sunrise(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_moon(timeout: float = 10, lang: str = "en") -> Moon | None:
    """Download today's moonrise, moon transit, and moonset (`dataType=MRS`)."""
    today = _hong_kong_today()
    year = int(today[:4])
    month = int(today[5:7])
    day = int(today[8:10])
    url = (
        "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
        f"?dataType=MRS&rformat=json&year={year}&month={month}&day={day}&lang=en"
    )
    return parse_moon(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_lunar(timeout: float = 10, lang: str = "en") -> LunarDate | None:
    """Download today's lunar date (`lunardate.php`)."""
    today = _hong_kong_today()
    url = f"https://data.weather.gov.hk/weatherAPI/opendata/lunardate.php?date={today}&lang=en"
    return parse_lunar(_fetch_json(_apply_lang(url, lang), timeout), today)


def fetch_uv(url: str = UV_URL, timeout: float = 10, lang: str = "en") -> UvIndex:
    """Download the UV index from the current weather report (`dataType=rhrread`)."""
    return parse_uv(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_fifteen_uv(timeout: float = 10, lang: str = "en") -> FifteenUv | None:
    """Download the latest 15-minute mean UV index at King's Park."""
    url = FIFTEEN_UV_URLS.get(lang, FIFTEEN_UV_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_fifteen_uv(text, lang)


def fetch_icon_time(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> IconUpdate | None:
    """Download the weather-icon update time from the current report (`iconUpdateTime`)."""
    return parse_icon_time(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_icon(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> IconReport | None:
    """Download the current weather icon from the current report (`dataType=rhrread`)."""
    return parse_icon(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_current_updated(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> CurrentUpdated | None:
    """Download when the current weather report was updated (`dataType=rhrread`)."""
    return parse_current_updated(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_tips(url: str = TIPS_URL, timeout: float = 10, lang: str = "en") -> SpecialTips:
    """Download special weather tips (`dataType=swt`)."""
    return parse_tips(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_lamppost(timeout: float = 10, lang: str = "en") -> LamppostReading | None:
    """Download the latest experimental reading from lamppost GF3637."""
    del lang
    return parse_lamppost(_fetch_json(LAMPPOST_URL, timeout))


def fetch_stations(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> StationReport:
    """Download per-station temperature and humidity from the current report."""
    return parse_stations(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_rain(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> RainReport:
    """Download district rainfall from the current report (`dataType=rhrread`)."""
    return parse_rain(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_rain_period(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> RainPeriod | None:
    """Download the district rainfall window from the current report (`dataType=rhrread`)."""
    return parse_rain_period(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_rain_maint(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> RainMaintenance:
    """Download districts whose rainfall gauge is under maintenance (`dataType=rhrread`)."""
    return parse_rain_maint(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_hour_rain(
    url: str = HOURLY_RAIN_URL, timeout: float = 10, lang: str = "en"
) -> HourRainReport:
    """Download past-hour rainfall from automatic stations (`hourlyRainfall.php`)."""
    return parse_hour_rain(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_hour_wettest(
    url: str = HOURLY_RAIN_URL, timeout: float = 10, lang: str = "en"
) -> HourWettest | None:
    """Download the wettest automatic station from the past hour."""
    report = fetch_hour_rain(url, timeout, lang)
    if not report.readings:
        return None
    wettest = report.readings[0]
    return HourWettest(report.obs_time, wettest.place, wettest.station_id, wettest.rainfall_mm)


def fetch_hour_driest(
    url: str = HOURLY_RAIN_URL, timeout: float = 10, lang: str = "en"
) -> HourDriest | None:
    """Download the driest automatic station from the past hour."""
    report = fetch_hour_rain(url, timeout, lang)
    if not report.readings:
        return None
    driest = min(report.readings, key=lambda reading: reading.rainfall_mm)
    return HourDriest(report.obs_time, driest.place, driest.station_id, driest.rainfall_mm)


def fetch_wettest(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> WettestReading | None:
    """Download the wettest district from the current report (`dataType=rhrread`)."""
    report = fetch_rain(url, timeout, lang)
    if not report.readings:
        return None
    wettest = report.readings[0]
    return WettestReading(wettest.place, wettest.rainfall_mm)


def fetch_driest(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> DriestReading | None:
    """Download the driest district from the current report (`dataType=rhrread`)."""
    report = fetch_rain(url, timeout, lang)
    if not report.readings:
        return None
    driest = min(report.readings, key=lambda reading: reading.rainfall_mm)
    return DriestReading(driest.place, driest.rainfall_mm)


def fetch_nowcast(timeout: float = 10, lang: str = "en") -> NowcastReport:
    """Download the gridded half-hourly rainfall nowcast."""
    url = NOWCAST_URLS.get(lang, NOWCAST_URLS["en"])
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_nowcast(text)


def fetch_daily_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at the Observatory."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKO/"
        f"{year}/daily_HKO_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_daily_rain(text, lang)


def fetch_lau_fau_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Lau Fau Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LFS/"
        f"{year}/daily_LFS_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lau_fau_rain(text, lang)


def fetch_shek_kong_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Shek Kong."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SEK/"
        f"{year}/daily_SEK_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shek_kong_rain(text, lang)


def fetch_wetland_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Wetland Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WLP/"
        f"{year}/daily_WLP_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wetland_rain(text, lang)


def fetch_sham_shui_po_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Sham Shui Po."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSP/"
        f"{year}/daily_SSP_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sham_shui_po_rain(text, lang)


def fetch_park_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at King's Park."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KP/"
        f"{year}/daily_KP_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_park_rain(text, lang)


def fetch_tseung_kwan_o_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tseung Kwan O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/JKB/"
        f"{year}/daily_JKB_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tseung_kwan_o_rain(text, lang)


def fetch_sheung_shui_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Sheung Shui."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SSH/"
        f"{year}/daily_SSH_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sheung_shui_rain(text, lang)


def fetch_sha_tin_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Sha Tin."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SHA/"
        f"{year}/daily_SHA_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_tin_rain(text, lang)


def fetch_ta_kwu_ling_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Ta Kwu Ling."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TKL/"
        f"{year}/daily_TKL_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ta_kwu_ling_rain(text, lang)


def fetch_cheung_chau_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Cheung Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CCH/"
        f"{year}/daily_CCH_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cheung_chau_rain(text, lang)


def fetch_waglan_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Waglan Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/WGL/"
        f"{year}/daily_WGL_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_waglan_rain(text, lang)


def fetch_tate_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tate's Cairn."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TC/"
        f"{year}/daily_TC_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tate_rain(text, lang)


def fetch_peng_chau_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Peng Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PEN/"
        f"{year}/daily_PEN_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_peng_chau_rain(text, lang)


def fetch_ping_chau_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Ping Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/EPC/"
        f"{year}/daily_EPC_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ping_chau_rain(text, lang)


def fetch_tai_mo_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tai Mo Shan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMS/"
        f"{year}/daily_TMS_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mo_rain(text, lang)


def fetch_sha_lo_wan_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Sha Lo Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SLW/"
        f"{year}/daily_SLW_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_lo_wan_rain(text, lang)


def fetch_airport_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at the airport."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HKA/"
        f"{year}/daily_HKA_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_airport_rain(text, lang)


def fetch_green_island_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Green Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/GI/"
        f"{year}/daily_GI_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_green_island_rain(text, lang)


def fetch_tsuen_wan_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tsuen Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TWN/"
        f"{year}/daily_TWN_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tsuen_wan_rain(text, lang)


def fetch_tap_mun_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tap Mun."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TAP/"
        f"{year}/daily_TAP_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tap_mun_rain(text, lang)


def fetch_clear_water_bay_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Clear Water Bay."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CWB/"
        f"{year}/daily_CWB_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_clear_water_bay_rain(text, lang)


def fetch_shau_kei_wan_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Shau Kei Wan."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SKW/"
        f"{year}/daily_SKW_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_shau_kei_wan_rain(text, lang)


def fetch_happy_valley_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Happy Valley."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HPV/"
        f"{year}/daily_HPV_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_happy_valley_rain(text, lang)


def fetch_tai_mei_tuk_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tai Mei Tuk."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PLC/"
        f"{year}/daily_PLC_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mei_tuk_rain(text, lang)


def fetch_kadoorie_farm_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Kadoorie Farm and Botanic Garden."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KFB/"
        f"{year}/daily_KFB_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kadoorie_farm_rain(text, lang)


def fetch_the_peak_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at The Peak."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/VP1/"
        f"{year}/daily_VP1_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_the_peak_rain(text, lang)


def fetch_pak_tam_chung_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Pak Tam Chung (Tsak Yue Wu)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TYW/"
        f"{year}/daily_TYW_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_pak_tam_chung_rain(text, lang)


def fetch_ching_pak_house_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Ching Pak House(Tsing Yi)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/CPH/"
        f"{year}/daily_CPH_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ching_pak_house_rain(text, lang)


def fetch_kau_sai_chau_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Kau Sai Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KSC/"
        f"{year}/daily_KSC_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kau_sai_chau_rain(text, lang)


def fetch_kai_tak_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Kai Tak."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/SE/"
        f"{year}/daily_SE_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kai_tak_rain(text, lang)


def fetch_sha_tau_kok_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Sha Tau Kok."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/R24/"
        f"{year}/daily_R24_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_sha_tau_kok_rain(text, lang)


def fetch_beas_river_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Beas River."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/BR1/"
        f"{year}/daily_BR1_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_beas_river_rain(text, lang)


def fetch_kat_o_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Kat O."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/KAT/"
        f"{year}/daily_KAT_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_kat_o_rain(text, lang)


def fetch_tap_shek_kok_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tap Shek Kok."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/R21/"
        f"{year}/daily_R21_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tap_shek_kok_rain(text, lang)


def fetch_tsim_bei_tsui_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tsim Bei Tsui."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/R22/"
        f"{year}/daily_R22_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tsim_bei_tsui_rain(text, lang)


def fetch_tai_mei_tuk_pump_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tai Mei Tuk Pumping Station."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/R31/"
        f"{year}/daily_R31_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_mei_tuk_pump_rain(text, lang)


def fetch_ngong_ping_reservoir_rain(
    timeout: float = 10, lang: str = "en"
) -> DailyRain | None:
    """Download the latest daily total rainfall at Ngong Ping Fresh Water Reservoir."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/R11/"
        f"{year}/daily_R11_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_ngong_ping_reservoir_rain(text, lang)


def fetch_discovery_bay_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Discovery Bay."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/R12/"
        f"{year}/daily_R12_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_discovery_bay_rain(text, lang)


def fetch_adventist_college_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Hong Kong Adventist College(Sai Kung)."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/R18/"
        f"{year}/daily_R18_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_adventist_college_rain(text, lang)


def fetch_wong_shiu_chi_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tai Po Wong Shiu Chi Secondary School."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/R23/"
        f"{year}/daily_R23_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_wong_shiu_chi_rain(text, lang)


def fetch_au_tau_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Au Tau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/R28/"
        f"{year}/daily_R28_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_au_tau_rain(text, lang)


def fetch_lok_ma_chau_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Lok Ma Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/R29/"
        f"{year}/daily_R29_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lok_ma_chau_rain(text, lang)


def fetch_po_pin_chau_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Po Pin Chau."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/PPC/"
        f"{year}/daily_PPC_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_po_pin_chau_rain(text, lang)


def fetch_tuen_mun_reservior_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tuen Mun Reservior."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TMR/"
        f"{year}/daily_TMR_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tuen_mun_reservior_rain(text, lang)


def fetch_tai_tan_camp_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tai Tan Camp."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TTC/"
        f"{year}/daily_TTC_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tai_tan_camp_rain(text, lang)


def fetch_lamma_island_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Lamma Island."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/LAM/"
        f"{year}/daily_LAM_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_lamma_island_rain(text, lang)


def fetch_tuen_mun_home_rain(timeout: float = 10, lang: str = "en") -> DailyRain | None:
    """Download the latest daily total rainfall at Tuen Mun Children and Juvenile Home."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/TU1/"
        f"{year}/daily_TU1_RF_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_tuen_mun_home_rain(text, lang)


def fetch_rainstorm(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> RainstormReminder | None:
    """Download the rainstorm reminder from the current report (`dataType=rhrread`)."""
    return parse_rainstorm(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_cyclone(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> CycloneMessage | None:
    """Download the tropical cyclone message from the current report (`dataType=rhrread`)."""
    return parse_cyclone(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_lightning(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> LightningReport:
    """Download lightning locations from the current report (`dataType=rhrread`)."""
    return parse_lightning(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_strikes(
    url: str = STRIKES_URL, timeout: float = 10, lang: str = "en"
) -> LightningCountReport:
    """Download hourly lightning counts (`dataType=LHL`)."""
    return parse_strikes(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_daily_strikes(timeout: float = 10, lang: str = "en") -> DailyStrikes | None:
    """Download the latest daily cloud-to-ground lightning count."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HK/"
        f"{year}/daily_HK_LGTG_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_daily_strikes(text, lang)


def fetch_cloud_strikes(timeout: float = 10, lang: str = "en") -> CloudStrikes | None:
    """Download the latest daily cloud-to-cloud lightning count."""
    year = _hong_kong_today()[:4]
    url = (
        "https://data.weather.gov.hk/weatherAPI/cis/csvfile/HK/"
        f"{year}/daily_HK_LGTC_{year}.csv"
    )
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("Hong Kong Observatory returned invalid text") from exc
    return parse_cloud_strikes(text, lang)


def fetch_humidity(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> HumidityReport:
    """Download humidity readings from the current report (`dataType=rhrread`)."""
    return parse_humidity(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_humidity_time(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> HumidityTime | None:
    """Download when the current humidity readings were recorded (`dataType=rhrread`)."""
    return parse_humidity_time(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_humidest(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> HumidestReading | None:
    """Download the most humid place from the current report (`dataType=rhrread`)."""
    report = fetch_humidity(url, timeout, lang)
    if not report.readings:
        return None
    dampest = max(report.readings, key=lambda reading: reading.humidity_percent)
    return HumidestReading(report.record_time, dampest.place, dampest.humidity_percent)


def fetch_least_humid(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> LeastHumidReading | None:
    """Download the least humid place from the current report (`dataType=rhrread`)."""
    report = fetch_humidity(url, timeout, lang)
    if not report.readings:
        return None
    driest = min(report.readings, key=lambda reading: reading.humidity_percent)
    return LeastHumidReading(report.record_time, driest.place, driest.humidity_percent)


def fetch_temps(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> TempReport:
    """Download temperature readings from the current report (`dataType=rhrread`)."""
    return parse_temps(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_temp_time(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> TempTime | None:
    """Download when the current temperatures were recorded (`dataType=rhrread`)."""
    return parse_temp_time(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_hottest(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> HottestReading | None:
    """Download the warmest place from the current report (`dataType=rhrread`)."""
    report = fetch_temps(url, timeout, lang)
    if not report.readings:
        return None
    warmest = max(report.readings, key=lambda reading: reading.temperature_c)
    return HottestReading(report.record_time, warmest.place, warmest.temperature_c)


def fetch_coldest(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> ColdestReading | None:
    """Download the coolest place from the current report (`dataType=rhrread`)."""
    report = fetch_temps(url, timeout, lang)
    if not report.readings:
        return None
    coolest = min(report.readings, key=lambda reading: reading.temperature_c)
    return ColdestReading(report.record_time, coolest.place, coolest.temperature_c)


def fetch_overnight(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> OvernightMinimum | None:
    """Download the midnight-to-9am minimum (`mintempFrom00To09` on `rhrread`)."""
    return parse_overnight(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_noon_rain(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> NoonRainfall | None:
    """Download the midnight-to-noon rainfall note (`rainfallFrom00To12` on `rhrread`)."""
    return parse_noon_rain(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_month_rain(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> MonthRainfall | None:
    """Download last month's rainfall note (`rainfallLastMonth` on `rhrread`)."""
    return parse_month_rain(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_year_rain(
    url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en"
) -> YearRainfall | None:
    """Download the January-to-last-month rainfall note (`rainfallJanuaryToLastMonth`)."""
    return parse_year_rain(_fetch_json(_apply_lang(url, lang), timeout))


def _apply_lang(url: str, lang: str) -> str:
    """Set the Observatory `lang` query parameter. Default URLs already use `en`."""
    if lang == "en" and "lang=en" in url:
        return url
    prefix, sep, rest = url.partition("lang=")
    if not sep:
        joiner = "&" if "?" in url else "?"
        return f"{url}{joiner}lang={lang}"
    amp = rest.find("&")
    tail = rest[amp:] if amp != -1 else ""
    return f"{prefix}lang={lang}{tail}"


def _fetch_json(url: str, timeout: float) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach Hong Kong Observatory: {exc}") from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WeatherError("Hong Kong Observatory returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise WeatherError("Hong Kong Observatory returned an unexpected payload")
    return payload


def _fetch_text(url: str, timeout: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WeatherError(f"could not reach the AQHI feed: {exc}") from exc
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeatherError("the AQHI feed returned invalid text") from exc


def parse_current_report(payload: dict) -> CurrentWeather:
    """Turn an `rhrread` JSON document into current conditions."""
    place, temperature = _temperature(payload)
    rainfall_mm, rainfall_place = _peak_rainfall(payload)
    return CurrentWeather(
        update_time=_text(payload.get("updateTime")) or "unknown",
        conditions=_conditions(payload.get("icon")),
        place=place,
        temperature_c=temperature,
        humidity_percent=_humidity(payload),
        rainfall_mm=rainfall_mm,
        rainfall_place=rainfall_place,
        lightning_places=_lightning(payload),
        warnings=_warnings(payload.get("warningMessage")),
    )


def _clock() -> datetime:
    """Current time. Tests replace this so relative ages stay fixed."""
    return datetime.now(timezone.utc)


def _ago_phrase(update_time: str) -> str | None:
    """Describe how long ago an Observatory timestamp was, or None if it cannot be read."""
    try:
        updated = datetime.fromisoformat(update_time)
    except ValueError:
        return None
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone(timedelta(hours=8)))
    seconds = int((_clock() - updated).total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return "1 min ago" if minutes == 1 else f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return "1 hour ago" if hours == 1 else f"{hours} hours ago"
    days = hours // 24
    return "1 day ago" if days == 1 else f"{days} days ago"


def _clock_phrase(update_time: str) -> str | None:
    """Return the observation clock time, labeled HKT when the offset is +08:00."""
    try:
        updated = datetime.fromisoformat(update_time)
    except ValueError:
        return None
    clock = updated.strftime("%H:%M")
    if updated.utcoffset() == timedelta(hours=8):
        return f"{clock} HKT"
    return clock


def _live_dew_c(temperature_c: float, humidity_percent: float) -> float:
    """Magnus dew point over water from air temperature and relative humidity."""
    a = 17.625
    b = 243.04
    gamma = math.log(humidity_percent / 100) + (a * temperature_c) / (b + temperature_c)
    return (b * gamma) / (a - gamma)


def _live_dew_text(
    temperature_c: float, humidity_percent: float | None, *, fahrenheit: bool
) -> str | None:
    """Format an estimated dew point, or None when humidity cannot support one."""
    if humidity_percent is None or not 0 < humidity_percent <= 100:
        return None
    dew = round(_live_dew_c(temperature_c, humidity_percent), 1)
    return _celsius_text(dew, fahrenheit=fahrenheit)


def _celsius_text(celsius: float, *, fahrenheit: bool) -> str:
    """Format a Celsius reading, optionally with Fahrenheit beside it."""
    text = f"{_number(celsius)}°C"
    if not fahrenheit:
        return text
    converted = round(celsius * 9 / 5 + 32)
    return f"{text} ({converted}°F)"


def format_report(
    weather: CurrentWeather,
    *,
    plain: bool = False,
    fahrenheit: bool = False,
    ago: bool = False,
    live_dew: bool = False,
    when: bool = False,
) -> str:
    """Render current conditions as plain text."""
    conditions = weather.conditions if plain else conditions_with_emoji(weather.conditions)
    updated = f"Updated: {weather.update_time}"
    notes: list[str] = []
    if when:
        clock = _clock_phrase(weather.update_time)
        if clock is not None:
            notes.append(clock)
    if ago:
        phrase = _ago_phrase(weather.update_time)
        if phrase is not None:
            notes.append(phrase)
    if notes:
        updated = f"{updated} ({', '.join(notes)})"
    lines = [
        "Hong Kong weather",
        "Source: Hong Kong Observatory open data",
        updated,
        f"Conditions: {conditions}",
        f"Temperature: {_celsius_text(weather.temperature_c, fahrenheit=fahrenheit)} ({weather.place})",
        "Humidity: "
        + (
            f"{_number(weather.humidity_percent)}%"
            if weather.humidity_percent is not None
            else "n/a"
        ),
    ]
    if live_dew:
        dew = _live_dew_text(
            weather.temperature_c, weather.humidity_percent, fahrenheit=fahrenheit
        )
        if dew is not None:
            lines.append(f"Dew point: {dew}")
    if weather.rainfall_mm is not None and weather.rainfall_place:
        lines.append(
            "Rainfall (past hour, highest district): "
            f"{_number(weather.rainfall_mm)} mm ({weather.rainfall_place})"
        )
    if weather.lightning_places:
        lines.append("Lightning: " + ", ".join(weather.lightning_places))
    if weather.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {message}" for message in weather.warnings)
    return "\n".join(lines) + "\n"


def format_summary(report: WeatherSummary, *, plain: bool = False, fahrenheit: bool = False) -> str:
    """Render a short briefing: conditions, warnings, and today's high and low."""
    conditions = report.conditions if plain else conditions_with_emoji(report.conditions)
    lines = ["Hong Kong summary", conditions]
    if report.warnings:
        lines.append("Warnings:")
        lines.extend(f"{warning.code}  {warning.description}" for warning in report.warnings)
    else:
        lines.append("Warnings: none")
    if report.today is None:
        lines.append("Today: not available")
    else:
        parts = [report.today.date] if report.today.date else []
        if report.today.high_c is not None:
            parts.append(f"high {_celsius_text(report.today.high_c, fahrenheit=fahrenheit)}")
        if report.today.low_c is not None:
            parts.append(f"low {_celsius_text(report.today.low_c, fahrenheit=fahrenheit)}")
        if report.today.rain_chance:
            parts.append(f"rain {report.today.rain_chance}")
        lines.append("Today: " + "  ".join(parts))
    return "\n".join(lines) + "\n"


def format_short(
    weather: CurrentWeather,
    *,
    plain: bool = False,
    fahrenheit: bool = False,
    ago: bool = False,
    where: bool = False,
    live_dew: bool = False,
    when: bool = False,
) -> str:
    """Render current conditions as one compact line."""
    humidity = (
        f"{_number(weather.humidity_percent)}%"
        if weather.humidity_percent is not None
        else "n/a"
    )
    conditions = weather.conditions if plain else conditions_with_emoji(weather.conditions)
    temperature = _celsius_text(weather.temperature_c, fahrenheit=fahrenheit)
    place = weather.place.strip()
    if where and place:
        temperature = f"{temperature} at {place}"
    line = f"{conditions}, {temperature}, humidity {humidity}"
    if live_dew:
        dew = _live_dew_text(
            weather.temperature_c, weather.humidity_percent, fahrenheit=fahrenheit
        )
        if dew is not None:
            line = f"{line}, dew point {dew}"
    if when:
        clock = _clock_phrase(weather.update_time)
        if clock is not None:
            line = f"{line} at {clock}"
    if weather.warnings:
        note = _brief_warning(weather.warnings[0])
        extra = len(weather.warnings) - 1
        if extra:
            note = f"{note} (+{extra} more)"
        line = f"{line} — {note}"
    if ago:
        phrase = _ago_phrase(weather.update_time)
        if phrase is not None:
            line = f"{line} ({phrase})"
    return line + "\n"


_RAIN_WORDS = frozenset(
    {"rain", "shower", "showers", "drizzle", "thunderstorm", "thunderstorms"}
)


def _condition_words(conditions: str) -> set[str]:
    """Split a condition label into lowercase words."""
    words: set[str] = set()
    token: list[str] = []
    for char in conditions.casefold():
        if char.isalpha():
            token.append(char)
            continue
        if token:
            words.add("".join(token))
            token = []
    if token:
        words.add("".join(token))
    return words


def _is_raining(weather: CurrentWeather) -> bool:
    """True when conditions mention rain or a district recorded rainfall."""
    if weather.rainfall_mm is not None and weather.rainfall_mm > 0:
        return True
    return bool(_condition_words(weather.conditions) & _RAIN_WORDS)


def format_raining(weather: CurrentWeather, *, as_json: bool) -> str:
    """Print yes or no for rain in the current report."""
    raining = _is_raining(weather)
    if as_json:
        return json.dumps({"raining": raining}, indent=2) + "\n"
    return "yes\n" if raining else "no\n"


def format_hotter(weather: CurrentWeather, threshold_c: float, *, as_json: bool) -> str:
    """Print yes or no if the current temperature is above threshold_c."""
    hotter = weather.temperature_c > threshold_c
    if as_json:
        return (
            json.dumps(
                {
                    "hotter": hotter,
                    "threshold_c": threshold_c,
                    "temperature_c": weather.temperature_c,
                },
                indent=2,
            )
            + "\n"
        )
    return "yes\n" if hotter else "no\n"


def _humidex_c(temperature_c: float, humidity_percent: float) -> float:
    """Canadian humidex from air temperature and relative humidity."""
    dew = _live_dew_c(temperature_c, humidity_percent)
    vapour = 6.11 * math.exp(5417.7530 * (1 / 273.16 - 1 / (273.15 + dew)))
    return temperature_c + 0.5555 * (vapour - 10)


def format_feels_like(
    weather: CurrentWeather, *, as_json: bool, fahrenheit: bool = False
) -> str:
    """Estimate how warm it feels from the current temperature and humidity."""
    humidity = weather.humidity_percent
    if humidity is None or not 0 < humidity <= 100:
        return _unavailable("No feels-like temperature is available.", as_json=as_json)
    feels = round(_humidex_c(weather.temperature_c, humidity), 1)
    if as_json:
        return (
            json.dumps(
                {
                    "feels_like_c": feels,
                    "temperature_c": weather.temperature_c,
                    "humidity_percent": humidity,
                },
                indent=2,
            )
            + "\n"
        )
    return f"Feels like {_celsius_text(feels, fahrenheit=fahrenheit)}\n"


def format_dew_gap(weather: CurrentWeather, *, as_json: bool) -> str:
    """Say how far the current temperature is above the estimated dew point."""
    humidity = weather.humidity_percent
    if humidity is None or not 0 < humidity <= 100:
        return _unavailable("No dew point is available.", as_json=as_json)
    dew = round(_live_dew_c(weather.temperature_c, humidity), 1)
    gap = round(weather.temperature_c - dew, 1)
    dew_text = _number(dew)
    if gap > 0:
        phrase = f"{_number(gap)}°C above the dew point of {dew_text}°C"
    elif gap < 0:
        phrase = f"{_number(abs(gap))}°C below the dew point of {dew_text}°C"
    else:
        phrase = f"At the dew point of {dew_text}°C"
    if as_json:
        return (
            json.dumps(
                {
                    "temperature_c": weather.temperature_c,
                    "humidity_percent": humidity,
                    "dew_c": dew,
                    "gap_c": gap,
                    "phrase": phrase,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
    return phrase + "\n"


def _brief_warning(message: str) -> str:
    sentence = message.strip().split(". ", 1)[0].rstrip(".")
    if len(sentence) > 80:
        return sentence[:77].rstrip() + "..."
    return sentence


def parse_forecast(payload: dict) -> LocalForecast:
    """Turn an `flw` JSON document into a short local forecast."""
    forecast = _text(payload.get("forecastDesc"))
    if not forecast:
        raise WeatherError("local forecast is missing from the report")
    return LocalForecast(
        update_time=_text(payload.get("updateTime")) or "unknown",
        period=_text(payload.get("forecastPeriod")) or "Hong Kong",
        forecast=forecast,
        outlook=_text(payload.get("outlook")),
    )


def format_forecast(forecast: LocalForecast) -> str:
    """Render the local forecast as plain text."""
    lines = [
        "Hong Kong forecast",
        "Source: Hong Kong Observatory open data",
        f"Updated: {forecast.update_time}",
        f"Period: {forecast.period}",
        forecast.forecast,
    ]
    if forecast.outlook:
        lines.append(f"Outlook: {forecast.outlook}")
    return "\n".join(lines) + "\n"


def parse_outlook(payload: dict) -> ForecastOutlook | None:
    """Turn the `flw` outlook into one paragraph."""
    text = _text(payload.get("outlook"))
    if not text:
        return None
    return ForecastOutlook(text)


def format_outlook(report: ForecastOutlook) -> str:
    """Render the local-forecast outlook."""
    return f"Hong Kong outlook\n{report.outlook}\n"


def format_outlook_miss(*, as_json: bool = False) -> str:
    """Say that the local forecast has no outlook."""
    return _unavailable("No outlook is available.", as_json=as_json)


def parse_coastal(payload: dict) -> CoastalForecast:
    """Turn the coastal-waters bulletin into one forecast line per area."""
    forecast = payload.get("weatherForecast")
    rows = forecast.get("data") if isinstance(forecast, dict) else None
    areas: list[CoastalArea] = []
    if isinstance(rows, list):
        for item in rows:
            if not isinstance(item, dict):
                continue
            place = _text(item.get("locationName"))
            wind = _text(item.get("windInfo"))
            weather = _text(item.get("weatherDescription"))
            sea = _text(item.get("seaSituation"))
            if not place or not (wind or weather or sea):
                continue
            areas.append(CoastalArea(place, wind, weather, sea))
    return CoastalForecast(_text(payload.get("updateTime")), tuple(areas))


def format_coastal(report: CoastalForecast) -> str:
    """Render the South China Coastal Waters area forecast."""
    lines = ["Hong Kong coastal waters"]
    if report.update_time:
        lines.append(f"Updated: {report.update_time}")
    for area in report.areas:
        detail = "  ".join(part for part in (area.wind, area.weather, area.sea) if part)
        lines.append(f"{area.place}  {detail}")
    return "\n".join(lines) + "\n"


def format_coastal_miss(*, as_json: bool = False) -> str:
    """Say that no coastal waters forecast is available."""
    return _unavailable("No coastal waters forecast is available.", as_json=as_json)


def _visibility_unit(unit: str) -> str:
    if unit.lower() in {"kilometre", "kilometer", "km"}:
        return "km"
    return unit


def parse_coast_report(payload: dict) -> CoastReport:
    """Turn the coastal bulletin into the latest station reports."""
    report = payload.get("weatherReport")
    rows = report.get("data") if isinstance(report, dict) else None
    stations: list[CoastStation] = []
    if isinstance(rows, list):
        for item in rows:
            if not isinstance(item, dict):
                continue
            place = _text(item.get("locationName"))
            wind = _text(item.get("windInfo"))
            weather = _text(item.get("weatherDescription"))
            info = item.get("visibilityInfo")
            visibility = None
            unit = ""
            if isinstance(info, dict):
                visibility = _hour_mm(info.get("value"))
                unit = _visibility_unit(_text(info.get("unit"))) if visibility is not None else ""
            if not place or not (wind or weather or visibility is not None):
                continue
            stations.append(CoastStation(place, wind, weather, visibility, unit))
    return CoastReport(_text(payload.get("updateTime")), tuple(stations))


def format_coast_report(report: CoastReport) -> str:
    """Render the latest coastal station reports."""
    lines = ["Hong Kong coastal reports"]
    if report.update_time:
        lines.append(f"Updated: {report.update_time}")
    for station in report.stations:
        parts = [part for part in (station.wind, station.weather) if part]
        if station.visibility is not None:
            visibility = f"visibility {_number(station.visibility)}"
            if station.visibility_unit:
                visibility = f"{visibility} {station.visibility_unit}"
            parts.append(visibility)
        lines.append(f"{station.place}  {'  '.join(parts)}")
    return "\n".join(lines) + "\n"


def format_coast_report_miss(*, as_json: bool = False) -> str:
    """Say that no coastal station reports are available."""
    return _unavailable("No coastal station reports are available.", as_json=as_json)


def parse_forecast_period(payload: dict) -> ForecastPeriod | None:
    """Turn the `flw` forecast period into one line."""
    text = _text(payload.get("forecastPeriod"))
    if not text:
        return None
    return ForecastPeriod(text)


def format_forecast_period(report: ForecastPeriod) -> str:
    """Render the local-forecast period."""
    return f"Hong Kong forecast period\n{report.period}\n"


def format_forecast_period_miss(*, as_json: bool = False) -> str:
    """Say that the local forecast has no period."""
    return _unavailable("No forecast period is available.", as_json=as_json)


def parse_forecast_desc(payload: dict) -> ForecastDesc | None:
    """Turn the `flw` forecast description into one paragraph."""
    text = _text(payload.get("forecastDesc"))
    if not text:
        return None
    return ForecastDesc(text)


def format_forecast_desc(report: ForecastDesc) -> str:
    """Render the local-forecast description."""
    return f"Hong Kong forecast description\n{report.description}\n"


def _first_sentence(text: str) -> str:
    """Return the first sentence, keeping its closing punctuation."""
    stripped = text.strip()
    cuts: list[int] = []
    for mark in (". ", "? ", "! "):
        index = stripped.find(mark)
        if index != -1:
            cuts.append(index)
    for mark in ("。", "？", "！"):
        index = stripped.find(mark)
        if index != -1:
            cuts.append(index)
    if not cuts:
        return stripped
    return stripped[: min(cuts) + 1]


def format_forecast_line(report: ForecastDesc | None, *, as_json: bool) -> str:
    """Print the first sentence of the local forecast."""
    if report is None or not report.description.strip():
        return _unavailable("No forecast description is available.", as_json=as_json)
    line = _first_sentence(report.description)
    if as_json:
        return json.dumps({"forecast": line}, indent=2, ensure_ascii=False) + "\n"
    return line + "\n"


def format_forecast_desc_miss(*, as_json: bool = False) -> str:
    """Say that the local forecast has no description."""
    return _unavailable("No forecast description is available.", as_json=as_json)


def parse_forecast_updated(payload: dict) -> ForecastUpdated | None:
    """Turn the `flw` update time into one timestamp."""
    text = _text(payload.get("updateTime"))
    if not text:
        return None
    return ForecastUpdated(text)


def format_forecast_updated(report: ForecastUpdated) -> str:
    """Render when the local forecast was updated."""
    return f"Hong Kong forecast update\n{report.updated}\n"


def format_forecast_updated_miss(*, as_json: bool = False) -> str:
    """Say that the local forecast has no update time."""
    return _unavailable("No forecast update time is available.", as_json=as_json)


def parse_situation(payload: dict) -> GeneralSituation | None:
    """Turn the `flw` general situation into one paragraph."""
    text = _text(payload.get("generalSituation"))
    if not text:
        return None
    return GeneralSituation(text)


def format_situation(report: GeneralSituation) -> str:
    """Render the general situation."""
    return f"Hong Kong general situation\n{report.situation}\n"


def format_situation_miss(*, as_json: bool = False) -> str:
    """Say that the local forecast has no general situation."""
    return _unavailable("No general situation is available.", as_json=as_json)


def parse_fire_danger(payload: dict) -> FireDanger | None:
    """Turn the `flw` fire danger warning into one sentence."""
    text = _text(payload.get("fireDangerWarning"))
    if not text:
        return None
    return FireDanger(text)


def format_fire_danger(report: FireDanger) -> str:
    """Render the fire danger warning."""
    return f"Hong Kong fire danger\n{report.warning}\n"


def format_fire_danger_miss(*, as_json: bool = False) -> str:
    """Say that the local forecast has no fire danger warning."""
    return _unavailable("No fire danger warning is available.", as_json=as_json)


def parse_tc_info(payload: dict) -> TcInfo | None:
    """Turn the `flw` tropical cyclone information into one paragraph."""
    text = _text(payload.get("tcInfo"))
    if not text:
        return None
    return TcInfo(text)


def format_tc_info(report: TcInfo) -> str:
    """Render the local-forecast tropical cyclone information."""
    return f"Hong Kong tropical cyclone information\n{report.info}\n"


def format_tc_info_miss(*, as_json: bool = False) -> str:
    """Say that the local forecast has no tropical cyclone information."""
    return _unavailable("No tropical cyclone information is available.", as_json=as_json)


def parse_warnings(payload: dict) -> tuple[WeatherWarning, ...]:
    """Turn a `warnsum` document into active warnings (code and name)."""
    warnings: list[WeatherWarning] = []
    for key, item in payload.items():
        if not isinstance(item, dict):
            continue
        action = _text(item.get("actionCode")).upper()
        if action in _CANCELLED:
            continue
        code = _text(item.get("code")) or _text(key)
        description = _text(item.get("name"))
        if not code or not description:
            continue
        warnings.append(WeatherWarning(code=code, description=description))
    return tuple(warnings)


def format_warnings(warnings: tuple[WeatherWarning, ...], *, as_json: bool = False) -> str:
    """Render active warnings as a short list, or one JSON object."""
    if as_json:
        payload = {"warnings": [asdict(warning) for warning in warnings]}
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if not warnings:
        return "No weather warnings are in force.\n"
    lines = ["Hong Kong weather warnings"]
    lines.extend(f"{warning.code}  {warning.description}" for warning in warnings)
    return "\n".join(lines) + "\n"


def format_warning_count(warnings: tuple[WeatherWarning, ...], *, as_json: bool) -> str:
    """Print how many weather warnings are in force."""
    count = len(warnings)
    if as_json:
        return json.dumps({"count": count}, indent=2) + "\n"
    if count == 0:
        return "No weather warnings are in force.\n"
    if count == 1:
        return "1 warning in force\n"
    return f"{count} warnings in force\n"


def parse_warning_time(payload: dict) -> WarningTimeReport:
    """Turn a `warnsum` document into issue and expiry times for active warnings."""
    warnings: list[WarningTime] = []
    for key, item in payload.items():
        if not isinstance(item, dict):
            continue
        action = _text(item.get("actionCode")).upper()
        if action in _CANCELLED:
            continue
        code = _text(item.get("code")) or _text(key)
        description = _text(item.get("name"))
        if not code or not description:
            continue
        warnings.append(
            WarningTime(
                code=code,
                description=description,
                issue_time=_text(item.get("issueTime")),
                update_time=_text(item.get("updateTime")),
                expire_time=_text(item.get("expireTime")),
            )
        )
    return WarningTimeReport(tuple(warnings))


def format_warning_time(report: WarningTimeReport) -> str:
    """Render issue and expiry times for active warnings."""
    lines = ["Hong Kong warning times"]
    for warning in report.warnings:
        lines.append(f"{warning.code}  {warning.description}")
        if warning.issue_time:
            lines.append(f"Issued: {warning.issue_time}")
        if warning.update_time and warning.update_time != warning.issue_time:
            lines.append(f"Updated: {warning.update_time}")
        if warning.expire_time:
            lines.append(f"Expires: {warning.expire_time}")
    return "\n".join(lines) + "\n"


def format_warning_time_miss(*, as_json: bool = False) -> str:
    """Say that no weather warnings are in force."""
    return _unavailable("No weather warnings are in force.", as_json=as_json)


def parse_warning_level(payload: dict) -> tuple[WarningLevel, ...]:
    """Turn a `warnsum` document into the level of each active warning."""
    warnings: list[WarningLevel] = []
    for key, item in payload.items():
        if not isinstance(item, dict):
            continue
        action = _text(item.get("actionCode")).upper()
        if action in _CANCELLED:
            continue
        code = _text(item.get("code")) or _text(key)
        description = _text(item.get("name"))
        if not code or not description:
            continue
        warnings.append(WarningLevel(code, description, _text(item.get("type"))))
    return tuple(warnings)


def _warning_level_phrase(warning: WarningLevel) -> str:
    """One sentence for a warning level, or that it is simply in force."""
    if warning.level:
        return f"{warning.description} is {warning.level}"
    return f"{warning.description} is in force"


def format_warning_level(warnings: tuple[WarningLevel, ...], *, as_json: bool) -> str:
    """Print the level of each active weather warning."""
    if not warnings:
        return _unavailable("No weather warnings are in force.", as_json=as_json)
    phrases = [_warning_level_phrase(warning) for warning in warnings]
    if as_json:
        payload = {
            "warnings": [
                {
                    "code": warning.code,
                    "description": warning.description,
                    "level": warning.level,
                    "phrase": phrase,
                }
                for warning, phrase in zip(warnings, phrases)
            ]
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return "".join(phrase + "\n" for phrase in phrases)


def _warning_ago(issue_time: str, now: datetime) -> str | None:
    """How long a warning has been in force, or None if the issue time cannot be used."""
    text = issue_time.strip()
    if not text:
        return None
    try:
        issued = datetime.fromisoformat(text)
    except ValueError:
        return None
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=_HKT)
    seconds = int((now - issued).total_seconds())
    if seconds < 0:
        return None
    if seconds < 60:
        return "just now"
    return _span_phrase(seconds // 60)


def format_warning_ago(report: WarningTimeReport, *, as_json: bool) -> str:
    """Print how long each active warning has been in force."""
    if not report.warnings:
        return _unavailable("No weather warnings are in force.", as_json=as_json)
    now = _clock()
    rows = []
    for warning in report.warnings:
        ago = _warning_ago(warning.issue_time, now)
        if ago is None:
            continue
        name = warning.description or warning.code
        phrase = (
            f"{name}, issued just now" if ago == "just now" else f"{name} for {ago}"
        )
        rows.append((warning, ago, phrase))
    if not rows:
        return _unavailable("No warning issue time is available.", as_json=as_json)
    if as_json:
        payload = {
            "warnings": [
                {
                    "code": warning.code,
                    "description": warning.description,
                    "issued": warning.issue_time,
                    "ago": ago,
                }
                for warning, ago, _phrase in rows
            ]
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return "".join(phrase + "\n" for _warning, _ago, phrase in rows)


def parse_warning_info(payload: dict) -> tuple[WarningDetail, ...]:
    """Turn a `warningInfo` document into detailed warning messages."""
    raw = payload.get("details")
    if not isinstance(raw, list):
        return ()
    details: list[WarningDetail] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        raw_contents = item.get("contents")
        if not isinstance(raw_contents, list):
            continue
        contents = tuple(
            text
            for part in raw_contents
            if isinstance(part, str) and (text := part.strip())
        )
        if not contents:
            continue
        details.append(
            WarningDetail(
                code=_text(item.get("warningStatementCode")),
                subtype=_text(item.get("subtype")),
                update_time=_text(item.get("updateTime")),
                contents=contents,
            )
        )
    return tuple(details)


def format_warning_info(details: tuple[WarningDetail, ...], *, as_json: bool = False) -> str:
    """Render detailed warning messages, or one JSON object."""
    if as_json:
        payload = {
            "warnings": [
                {
                    "code": item.code,
                    "subtype": item.subtype,
                    "update_time": item.update_time,
                    "contents": list(item.contents),
                }
                for item in details
            ]
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if not details:
        return "No detailed warning information is available.\n"
    lines = ["Hong Kong warning information"]
    for item in details:
        label = f"{item.code}  {item.subtype}".strip() or "Warning"
        lines.append("")
        lines.append(label)
        if item.update_time:
            lines.append(f"Updated: {item.update_time}")
        lines.extend(f"- {paragraph}" for paragraph in item.contents)
    return "\n".join(lines) + "\n"


def parse_nine_day(payload: dict) -> NineDayForecast:
    """Turn an `fnd` document into a compact day-by-day forecast."""
    raw_days = payload.get("weatherForecast")
    if not isinstance(raw_days, list):
        raise WeatherError("9-day forecast is missing from the report")
    days = tuple(
        day for item in raw_days if (day := _forecast_day(item)) is not None
    )
    if not days:
        raise WeatherError("9-day forecast is missing from the report")
    return NineDayForecast(
        update_time=_text(payload.get("updateTime")) or "unknown",
        days=days,
    )


def format_nine_day(forecast: NineDayForecast) -> str:
    """Render the 9-day forecast as a short day-by-day list."""
    lines = [
        "Hong Kong 9-day forecast",
        "Source: Hong Kong Observatory open data",
        f"Updated: {forecast.update_time}",
    ]
    for day in forecast.days:
        heading = " ".join(part for part in (day.date, day.week) if part)
        details: list[str] = []
        if day.temp_high_c is not None:
            details.append(f"high {_number(day.temp_high_c)}°C")
        if day.temp_low_c is not None:
            details.append(f"low {_number(day.temp_low_c)}°C")
        humidity = _humidity_span(day.humidity_low_percent, day.humidity_high_percent)
        if humidity:
            details.append(humidity)
        if day.rain_chance:
            details.append(f"rain {day.rain_chance}")
        lines.append("")
        lines.append(f"{heading}  {'  '.join(details)}".rstrip())
        if day.weather:
            lines.append(day.weather)
    return "\n".join(lines) + "\n"


def parse_sea_temp(payload: dict) -> SeaTemperature | None:
    """Turn the `fnd` sea temperature into one reading."""
    raw = payload.get("seaTemp")
    value = _temp_value(raw)
    if value is None or not isinstance(raw, dict):
        return None
    return SeaTemperature(
        place=_text(raw.get("place")) or "Hong Kong",
        temperature_c=value,
        recorded=_text(raw.get("recordTime")),
    )


def format_sea_temp(reading: SeaTemperature) -> str:
    """Render the sea temperature from the 9-day forecast."""
    lines = [
        "Hong Kong sea temperature",
        f"{reading.place}  {_number(reading.temperature_c)}°C",
    ]
    if reading.recorded:
        lines.append(f"Recorded: {reading.recorded}")
    return "\n".join(lines) + "\n"


def format_sea_temp_miss(*, as_json: bool = False) -> str:
    """Say that the 9-day forecast has no sea temperature."""
    return _unavailable("No sea temperature is available.", as_json=as_json)


_NORTH_POINT_AM_SEA_STATIONS = {
    "en": "North Point",
    "tc": "北角",
    "sc": "北角",
}


def parse_north_point_am_sea(text: str, lang: str = "en") -> MorningSea | None:
    """Turn the North Point morning sea-temperature CSV into the latest numeric day."""
    station = _NORTH_POINT_AM_SEA_STATIONS.get(lang, _NORTH_POINT_AM_SEA_STATIONS["en"])
    latest: MorningSea | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MorningSea(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_morning_sea(reading: MorningSea) -> str:
    """Render the latest daily morning sea temperature at North Point."""
    return (
        "Hong Kong morning sea temperature\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.sea_temperature_c)}°C\n"
    )


def format_north_point_am_sea_miss(*, as_json: bool = False) -> str:
    """Say that no North Point morning sea temperature is available."""
    return _unavailable(
        "No North Point morning sea temperature is available.",
        as_json=as_json,
    )


_NORTH_POINT_PM_SEA_STATIONS = {
    "en": "North Point",
    "tc": "北角",
    "sc": "北角",
}


def parse_north_point_pm_sea(text: str, lang: str = "en") -> AfternoonSea | None:
    """Turn the North Point afternoon sea-temperature CSV into the latest numeric day."""
    station = _NORTH_POINT_PM_SEA_STATIONS.get(lang, _NORTH_POINT_PM_SEA_STATIONS["en"])
    latest: AfternoonSea | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = AfternoonSea(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_afternoon_sea(reading: AfternoonSea) -> str:
    """Render the latest daily afternoon sea temperature at North Point."""
    return (
        "Hong Kong afternoon sea temperature\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.sea_temperature_c)}°C\n"
    )


def format_north_point_pm_sea_miss(*, as_json: bool = False) -> str:
    """Say that no North Point afternoon sea temperature is available."""
    return _unavailable(
        "No North Point afternoon sea temperature is available.",
        as_json=as_json,
    )


def parse_soil_temp(payload: dict) -> SoilReport | None:
    """Turn the `fnd` soil temperatures into one reading per depth."""
    raw = payload.get("soilTemp")
    if not isinstance(raw, list):
        return None
    readings: list[SoilReading] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        temperature = _temp_value(item)
        depth = _temp_value(item.get("depth"))
        if temperature is None or depth is None:
            continue
        readings.append(
            SoilReading(
                place=_text(item.get("place")) or "Hong Kong",
                depth_m=depth,
                temperature_c=temperature,
                recorded=_text(item.get("recordTime")),
            )
        )
    if not readings:
        return None
    return SoilReport(tuple(readings))


def format_soil_temp(report: SoilReport) -> str:
    """Render soil temperatures from the 9-day forecast."""
    lines = ["Hong Kong soil temperature"]
    recorded = {reading.recorded for reading in report.readings}
    shared = next(iter(recorded)) if len(recorded) == 1 else ""
    for reading in report.readings:
        line = (
            f"{reading.place}  {_number(reading.depth_m)} m  "
            f"{_number(reading.temperature_c)}°C"
        )
        if reading.recorded and not shared:
            line += f"  {reading.recorded}"
        lines.append(line)
    if shared:
        lines.append(f"Recorded: {shared}")
    return "\n".join(lines) + "\n"


def format_soil_temp_miss(*, as_json: bool = False) -> str:
    """Say that the 9-day forecast has no soil temperature."""
    return _unavailable("No soil temperature is available.", as_json=as_json)


def _soil_spot(reading: SoilReading) -> str:
    return f"{reading.place} {_number(reading.depth_m)} m"


def format_warm_soil(report: SoilReport | None, *, as_json: bool) -> str:
    """Print the soil depth or depths with the highest temperature."""
    if report is None or not report.readings:
        return _unavailable("No soil temperature is available.", as_json=as_json)
    peak = max(reading.temperature_c for reading in report.readings)
    warmest = tuple(reading for reading in report.readings if reading.temperature_c == peak)
    spots = [_soil_spot(reading) for reading in warmest]
    if len(spots) == 1:
        listed = spots[0]
    elif len(spots) == 2:
        listed = f"{spots[0]} and {spots[1]}"
    else:
        listed = ", ".join(spots[:-1]) + f", and {spots[-1]}"
    phrase = f"Warmer soil: {listed}, {_number(peak)}°C"
    recorded = {reading.recorded for reading in warmest}
    stamp = next(iter(recorded)) if len(recorded) == 1 else ""
    if as_json:
        payload = {
            "recorded": stamp,
            "temperature_c": peak,
            "readings": [
                {
                    "place": reading.place,
                    "depth_m": reading.depth_m,
                    "temperature_c": reading.temperature_c,
                }
                for reading in warmest
            ],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def _soil_gap_spot(readings: tuple[SoilReading, ...]) -> str:
    depth = _number(readings[0].depth_m)
    places = [reading.place for reading in readings]
    if len(places) == 1:
        return f"{places[0]} {depth} m"
    if len(places) == 2:
        listed = f"{places[0]} and {places[1]}"
    else:
        listed = ", ".join(places[:-1]) + f", and {places[-1]}"
    return f"{listed} {depth} m"


def format_soil_gap(
    report: SoilReport | None, air_c: float, *, as_json: bool
) -> str:
    """Compare the shallowest soil temperature with the current air temperature."""
    if report is None or not report.readings:
        return _unavailable("No soil temperature is available.", as_json=as_json)
    shallow = min(reading.depth_m for reading in report.readings)
    chosen = tuple(reading for reading in report.readings if reading.depth_m == shallow)
    temperature = chosen[0].temperature_c
    same = tuple(reading for reading in chosen if reading.temperature_c == temperature)
    gap = round(temperature - air_c, 1)
    spot = _soil_gap_spot(same)
    air = _number(air_c)
    verb = "is" if len(same) == 1 else "are"
    if gap > 0:
        phrase = f"Soil at {spot} {verb} {_number(gap)}°C warmer than the {air}°C air."
    elif gap < 0:
        phrase = (
            f"Soil at {spot} {verb} {_number(abs(gap))}°C cooler than the {air}°C air."
        )
    else:
        phrase = f"Soil at {spot} matches the {air}°C air."
    if as_json:
        payload = {
            "depth_m": shallow,
            "soil_c": temperature,
            "air_c": air_c,
            "gap_c": gap,
            "places": [reading.place for reading in same],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def format_nine_situation(report: GeneralSituation) -> str:
    """Render the general situation from the 9-day forecast."""
    return f"Hong Kong 9-day situation\n{report.situation}\n"


def format_nine_situation_miss(*, as_json: bool = False) -> str:
    """Say that the 9-day forecast has no general situation."""
    return _unavailable("No 9-day situation is available.", as_json=as_json)


def parse_nine_updated(payload: dict) -> NineUpdated | None:
    """Turn the `fnd` update time into one timestamp."""
    text = _text(payload.get("updateTime"))
    if not text:
        return None
    return NineUpdated(text)


def format_nine_updated(report: NineUpdated) -> str:
    """Render when the 9-day forecast was updated."""
    return f"Hong Kong 9-day update\n{report.updated}\n"


def format_nine_updated_miss(*, as_json: bool = False) -> str:
    """Say that the 9-day forecast has no update time."""
    return _unavailable("No 9-day update time is available.", as_json=as_json)


def parse_nine_weather(payload: dict) -> NineWeather:
    """Turn `fnd` forecastWeather fields into one line per day."""
    raw_days = payload.get("weatherForecast")
    days: list[NineWeatherDay] = []
    if isinstance(raw_days, list):
        for item in raw_days:
            if not isinstance(item, dict):
                continue
            weather = _text(item.get("forecastWeather"))
            if not weather:
                continue
            days.append(
                NineWeatherDay(
                    date=_forecast_date(item.get("forecastDate")) or "unknown",
                    week=_text(item.get("week")),
                    weather=weather,
                )
            )
    return NineWeather(
        update_time=_text(payload.get("updateTime")),
        days=tuple(days),
    )


def format_nine_weather(report: NineWeather) -> str:
    """Render each day's weather from the 9-day forecast."""
    lines = ["Hong Kong 9-day weather"]
    if report.update_time:
        lines.append(f"Updated: {report.update_time}")
    for day in report.days:
        heading = " ".join(part for part in (day.date, day.week) if part)
        lines.append(f"{heading}  {day.weather}".strip())
    return "\n".join(lines) + "\n"


def format_nine_weather_miss(*, as_json: bool = False) -> str:
    """Say that the 9-day forecast has no daily weather text."""
    return _unavailable("No 9-day weather is available.", as_json=as_json)


_CLOUD_MARKS = (
    "cloud",
    "shower",
    "rain",
    "thunder",
    "drizzle",
    "squall",
    "mist",
    "fog",
    "雲",
    "云",
    "雨",
    "雷",
    "霧",
    "雾",
    "驟",
    "骤",
)


def _mentions_cloud_or_rain(weather: str) -> bool:
    folded = weather.casefold()
    return any(mark.casefold() in folded for mark in _CLOUD_MARKS)


def format_cloud_day(report: NineWeather, *, as_json: bool) -> str:
    """Print the first forecast day that mentions cloud or rain."""
    match = next((day for day in report.days if _mentions_cloud_or_rain(day.weather)), None)
    if match is None:
        return _unavailable("No cloudier day in the 9-day forecast.", as_json=as_json)
    heading = " ".join(part for part in (match.date, match.week) if part)
    if heading:
        phrase = f"First cloudier day: {heading}  {match.weather}"
    else:
        phrase = f"First cloudier day: {match.weather}"
    if as_json:
        payload = {
            "date": match.date,
            "week": match.week,
            "weather": match.weather,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def _mentions_hot(weather: str) -> bool:
    """True when the forecast sentence says hot, including 炎熱 and 热."""
    if "熱" in weather or "热" in weather:
        return True
    folded = weather.casefold()
    start = 0
    while True:
        index = folded.find("hot", start)
        if index < 0:
            return False
        before = folded[index - 1] if index else ""
        if not before.isalpha():
            return True
        start = index + 1


def format_hot_day(report: NineWeather, *, as_json: bool) -> str:
    """Print the first forecast day whose weather sentence says hot."""
    match = next((day for day in report.days if _mentions_hot(day.weather)), None)
    if match is None:
        return _unavailable("No hot day is in the forecast.", as_json=as_json)
    heading = " ".join(part for part in (match.date, match.week) if part)
    if heading:
        phrase = f"First hot day: {heading}  {match.weather}"
    else:
        phrase = f"First hot day: {match.weather}"
    if as_json:
        payload = {
            "date": match.date,
            "week": match.week,
            "weather": match.weather,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_nine_temp(payload: dict) -> NineTemp:
    """Turn `fnd` forecast high and low fields into one line per day."""
    raw_days = payload.get("weatherForecast")
    days: list[NineTempDay] = []
    if isinstance(raw_days, list):
        for item in raw_days:
            if not isinstance(item, dict):
                continue
            high = _temp_value(item.get("forecastMaxtemp"))
            low = _temp_value(item.get("forecastMintemp"))
            if high is None and low is None:
                continue
            days.append(
                NineTempDay(
                    date=_forecast_date(item.get("forecastDate")) or "unknown",
                    week=_text(item.get("week")),
                    temp_high_c=high,
                    temp_low_c=low,
                )
            )
    return NineTemp(
        update_time=_text(payload.get("updateTime")),
        days=tuple(days),
    )


def format_nine_temp(report: NineTemp) -> str:
    """Render each day's high and low from the 9-day forecast."""
    lines = ["Hong Kong 9-day temperatures"]
    if report.update_time:
        lines.append(f"Updated: {report.update_time}")
    for day in report.days:
        heading = " ".join(part for part in (day.date, day.week) if part)
        details: list[str] = []
        if day.temp_high_c is not None:
            details.append(f"high {_number(day.temp_high_c)}°C")
        if day.temp_low_c is not None:
            details.append(f"low {_number(day.temp_low_c)}°C")
        lines.append(f"{heading}  {'  '.join(details)}".strip())
    return "\n".join(lines) + "\n"


def format_nine_temp_miss(*, as_json: bool = False) -> str:
    """Say that the 9-day forecast has no daily temperatures."""
    return _unavailable("No 9-day temperatures are available.", as_json=as_json)


def _forecast_day_label(day: NineTempDay) -> str:
    """Date and weekday for one 9-day forecast row."""
    return " ".join(part for part in (day.date, day.week) if part) or "unknown"


def format_hottest_day(report: NineTemp, *, as_json: bool) -> str:
    """Print the day or days with the highest forecast high."""
    ranked = [day for day in report.days if day.temp_high_c is not None]
    if not ranked:
        return _unavailable("No forecast high is available.", as_json=as_json)
    high = max(day.temp_high_c for day in ranked)
    hottest = tuple(day for day in ranked if day.temp_high_c == high)
    labels = [_forecast_day_label(day) for day in hottest]
    if len(labels) == 1:
        listed = labels[0]
        word = "day"
    elif len(labels) == 2:
        listed = f"{labels[0]} and {labels[1]}"
        word = "days"
    else:
        listed = ", ".join(labels[:-1]) + f", and {labels[-1]}"
        word = "days"
    phrase = f"Hottest {word}: {listed}, {_number(high)}°C"
    if as_json:
        payload = {
            "high_c": high,
            "days": [{"date": day.date, "week": day.week} for day in hottest],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def format_high_step(report: NineTemp, *, as_json: bool) -> str:
    """Compare the first forecast high with the next high after it."""
    ranked = [day for day in report.days if day.temp_high_c is not None]
    if len(ranked) < 2:
        return _unavailable("No following forecast high is available.", as_json=as_json)
    earlier, later = ranked[0], ranked[1]
    gap = round(later.temp_high_c - earlier.temp_high_c, 1)
    earlier_label = _forecast_day_label(earlier)
    later_label = _forecast_day_label(later)
    earlier_high = _number(earlier.temp_high_c)
    later_high = _number(later.temp_high_c)
    if gap > 0:
        phrase = (
            f"{later_label}'s high of {later_high}°C is {_number(gap)}°C warmer than "
            f"{earlier_label}'s {earlier_high}°C."
        )
    elif gap < 0:
        phrase = (
            f"{later_label}'s high of {later_high}°C is {_number(abs(gap))}°C cooler than "
            f"{earlier_label}'s {earlier_high}°C."
        )
    else:
        phrase = f"{later_label}'s high matches {earlier_label}'s {earlier_high}°C."
    if as_json:
        payload = {
            "from_date": earlier.date,
            "from_week": earlier.week,
            "from_high_c": earlier.temp_high_c,
            "to_date": later.date,
            "to_week": later.week,
            "to_high_c": later.temp_high_c,
            "gap_c": gap,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_nine_humidity(payload: dict) -> NineHumidity:
    """Turn `fnd` forecast humidity fields into one line per day."""
    raw_days = payload.get("weatherForecast")
    days: list[NineHumidityDay] = []
    if isinstance(raw_days, list):
        for item in raw_days:
            if not isinstance(item, dict):
                continue
            high = _temp_value(item.get("forecastMaxrh"))
            low = _temp_value(item.get("forecastMinrh"))
            if high is None and low is None:
                continue
            days.append(
                NineHumidityDay(
                    date=_forecast_date(item.get("forecastDate")) or "unknown",
                    week=_text(item.get("week")),
                    humidity_high_percent=high,
                    humidity_low_percent=low,
                )
            )
    return NineHumidity(
        update_time=_text(payload.get("updateTime")),
        days=tuple(days),
    )


def format_nine_humidity(report: NineHumidity) -> str:
    """Render each day's humidity range from the 9-day forecast."""
    lines = ["Hong Kong 9-day humidity"]
    if report.update_time:
        lines.append(f"Updated: {report.update_time}")
    for day in report.days:
        heading = " ".join(part for part in (day.date, day.week) if part)
        span = _humidity_span(day.humidity_low_percent, day.humidity_high_percent)
        lines.append(f"{heading}  {span}".strip())
    return "\n".join(lines) + "\n"


def format_nine_humidity_miss(*, as_json: bool = False) -> str:
    """Say that the 9-day forecast has no daily humidity."""
    return _unavailable("No 9-day humidity is available.", as_json=as_json)


def _next_humidity_day(report: NineHumidity | None) -> NineHumidityDay | None:
    """Return the first forecast day with a low and a high humidity."""
    if report is None:
        return None
    for day in report.days:
        low = day.humidity_low_percent
        high = day.humidity_high_percent
        if low is None or high is None or high < low:
            continue
        return day
    return None


def format_in_humidity(
    report: NineHumidity | None,
    humidity_percent: float | None,
    *,
    as_json: bool,
) -> str:
    """Say whether the current humidity is inside the next forecast range."""
    day = _next_humidity_day(report)
    if day is None:
        return _unavailable("No forecast humidity range is available.", as_json=as_json)
    if humidity_percent is None:
        return _unavailable("No humidity reading is available.", as_json=as_json)
    low = day.humidity_low_percent
    high = day.humidity_high_percent
    span = f"{_number(low)}-{_number(high)}%"
    label = _forecast_day_label(day)
    reading = _number(humidity_percent)
    if humidity_percent < low:
        phrase = f"Humidity {reading}% is below {label}'s range of {span}."
        inside = False
    elif humidity_percent > high:
        phrase = f"Humidity {reading}% is above {label}'s range of {span}."
        inside = False
    else:
        phrase = f"Humidity {reading}% is inside {label}'s range of {span}."
        inside = True
    if as_json:
        payload = {
            "humidity_percent": humidity_percent,
            "date": day.date,
            "week": day.week,
            "low_percent": low,
            "high_percent": high,
            "inside": inside,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def format_psr(report: PsrForecast) -> str:
    """Render the chance of significant rain, one day per line."""
    lines = ["Hong Kong chance of significant rain"]
    if report.update_time:
        lines.append(f"Updated: {report.update_time}")
    for day in report.days:
        heading = " ".join(part for part in (day.date, day.week) if part)
        lines.append(f"{heading}  {day.psr or 'n/a'}".strip())
    return "\n".join(lines) + "\n"


def parse_tomorrow(payload: dict, tomorrow: str) -> TomorrowForecast | None:
    """Pick the 9-day entry whose date is tomorrow in Hong Kong."""
    raw_days = payload.get("weatherForecast")
    if not isinstance(raw_days, list):
        return None
    for item in raw_days:
        if not isinstance(item, dict):
            continue
        if _forecast_date(item.get("forecastDate")) != tomorrow:
            continue
        return _forecast_entry(payload, item)
    return None


def parse_forecast_day(payload: dict, day: int) -> TomorrowForecast | None:
    """Pick `weatherForecast[day - 1]`. Day 1 is the first entry, not tomorrow."""
    raw_days = payload.get("weatherForecast")
    index = day - 1
    if not isinstance(raw_days, list) or index < 0 or index >= len(raw_days):
        return None
    item = raw_days[index]
    if not isinstance(item, dict):
        return None
    return _forecast_entry(payload, item)


def _forecast_entry(payload: dict, item: dict) -> TomorrowForecast | None:
    day = _forecast_day(item)
    if day is None:
        return None
    return TomorrowForecast(
        update_time=_text(payload.get("updateTime")) or "unknown",
        date=day.date,
        week=day.week,
        weather=day.weather,
        temp_high_c=day.temp_high_c,
        temp_low_c=day.temp_low_c,
        humidity_high_percent=day.humidity_high_percent,
        humidity_low_percent=day.humidity_low_percent,
        rain_chance=day.rain_chance,
        wind=_text(item.get("forecastWind")) or None,
    )


def format_tomorrow(forecast: TomorrowForecast, *, title: str = "Hong Kong forecast for tomorrow") -> str:
    """Render one forecast day. The default title is tomorrow's."""
    lines = [
        title,
        "Source: Hong Kong Observatory open data",
        f"Updated: {forecast.update_time}",
        "",
        *_day_lines(forecast),
    ]
    return "\n".join(lines) + "\n"


def parse_weekend(payload: dict) -> WeekendForecast:
    """Keep Saturday and Sunday entries from an `fnd` document."""
    raw_days = payload.get("weatherForecast")
    days: list[WeekendDay] = []
    if isinstance(raw_days, list):
        for item in raw_days:
            if not isinstance(item, dict):
                continue
            entry = _forecast_entry(payload, item)
            if entry is None or not _is_weekend(entry.date, entry.week):
                continue
            days.append(
                WeekendDay(
                    date=entry.date,
                    week=entry.week,
                    weather=entry.weather,
                    temp_high_c=entry.temp_high_c,
                    temp_low_c=entry.temp_low_c,
                    humidity_high_percent=entry.humidity_high_percent,
                    humidity_low_percent=entry.humidity_low_percent,
                    rain_chance=entry.rain_chance,
                    wind=entry.wind,
                )
            )
    return WeekendForecast(
        update_time=_text(payload.get("updateTime")) or "unknown",
        days=tuple(days),
    )


def format_weekend(report: WeekendForecast) -> str:
    """Render Saturday and Sunday from the 9-day forecast."""
    lines = [
        "Hong Kong weekend forecast",
        "Source: Hong Kong Observatory open data",
        f"Updated: {report.update_time}",
    ]
    for day in report.days:
        lines.append("")
        lines.extend(_day_lines(day))
    return "\n".join(lines) + "\n"


def format_weekend_miss(*, as_json: bool = False) -> str:
    """Say that the 9-day window has no Saturday or Sunday."""
    return _unavailable("No weekend days are in the 9-day forecast.", as_json=as_json)


def _day_lines(day: TomorrowForecast | WeekendDay) -> list[str]:
    heading = " ".join(part for part in (day.date, day.week) if part)
    details: list[str] = []
    if day.temp_high_c is not None:
        details.append(f"high {_number(day.temp_high_c)}°C")
    if day.temp_low_c is not None:
        details.append(f"low {_number(day.temp_low_c)}°C")
    humidity = _humidity_span(day.humidity_low_percent, day.humidity_high_percent)
    if humidity:
        details.append(humidity)
    if day.rain_chance:
        details.append(f"rain {day.rain_chance}")
    lines = [f"{heading}  {'  '.join(details)}".rstrip()]
    if day.weather:
        lines.append(day.weather)
    if day.wind:
        lines.append(f"Wind: {day.wind}")
    return lines


def _is_weekend(date_text: str, week: str) -> bool:
    """True for Saturday or Sunday, using the forecast date when it parses."""
    try:
        found = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        found = None
    if found is not None:
        return found.weekday() >= 5
    name = week.casefold()
    return name in {"saturday", "sunday"} or week in {"星期六", "星期日", "星期天", "周六", "周日"}


def format_tomorrow_miss(*, as_json: bool = False) -> str:
    """Say that tomorrow is not in the 9-day forecast."""
    return _unavailable("Tomorrow's forecast is not available.", as_json=as_json)


def format_today_miss(*, as_json: bool = False) -> str:
    """Say that today is not in the 9-day forecast."""
    return _unavailable("Today's forecast is not available.", as_json=as_json)


def format_high_gap(temperature_c: float, high_c: float | None, *, as_json: bool) -> str:
    """Say how far the current temperature is from today's forecast high."""
    if high_c is None:
        return _unavailable("No forecast high is available.", as_json=as_json)
    gap = round(high_c - temperature_c, 1)
    high_text = _number(high_c)
    if gap == 0:
        phrase = f"At today's high of {high_text}°C"
    elif gap > 0:
        phrase = f"{_number(gap)}°C below today's high of {high_text}°C"
    else:
        phrase = f"{_number(abs(gap))}°C above today's high of {high_text}°C"
    if as_json:
        return (
            json.dumps(
                {
                    "temperature_c": temperature_c,
                    "high_c": high_c,
                    "gap_c": gap,
                    "phrase": phrase,
                },
                indent=2,
            )
            + "\n"
        )
    return phrase + "\n"


def format_today_range(day: TomorrowForecast | None, *, as_json: bool) -> str:
    """Print the span from today's forecast low to its forecast high."""
    if day is None or day.temp_low_c is None or day.temp_high_c is None:
        return _unavailable("No forecast range is available.", as_json=as_json)
    span = round(day.temp_high_c - day.temp_low_c, 1)
    if span < 0:
        return _unavailable("No forecast range is available.", as_json=as_json)
    if as_json:
        return (
            json.dumps(
                {"low_c": day.temp_low_c, "high_c": day.temp_high_c, "range_c": span},
                indent=2,
            )
            + "\n"
        )
    return f"Today's range is {_number(span)}°C\n"


def format_in_range(
    temperature_c: float,
    low_c: float | None,
    high_c: float | None,
    *,
    as_json: bool,
) -> str:
    """Say whether the current temperature is inside today's forecast range."""
    if low_c is None or high_c is None or high_c < low_c:
        return _unavailable("No forecast range is available.", as_json=as_json)
    span = f"{_number(low_c)}-{_number(high_c)}°C"
    if temperature_c < low_c:
        phrase = f"Below today's range of {span}"
        inside = False
    elif temperature_c > high_c:
        phrase = f"Above today's range of {span}"
        inside = False
    else:
        phrase = f"Inside today's range of {span}"
        inside = True
    if as_json:
        return (
            json.dumps(
                {
                    "temperature_c": temperature_c,
                    "low_c": low_c,
                    "high_c": high_c,
                    "inside": inside,
                    "phrase": phrase,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
    return phrase + "\n"


def format_today_psr(day: TomorrowForecast | None, *, as_json: bool) -> str:
    """Print today's chance of significant rain."""
    chance = "" if day is None or day.rain_chance is None else day.rain_chance.strip()
    if day is None or not chance:
        return _unavailable("No rain chance is available.", as_json=as_json)
    if as_json:
        return (
            json.dumps({"date": day.date, "rain_chance": chance}, indent=2, ensure_ascii=False)
            + "\n"
        )
    return f"Rain chance: {chance}\n"


def format_today_wind(day: TomorrowForecast | None, *, as_json: bool) -> str:
    """Print today's forecast wind."""
    wind = "" if day is None or day.wind is None else day.wind.strip()
    if day is None or not wind:
        return _unavailable("No forecast wind is available for today.", as_json=as_json)
    if as_json:
        return (
            json.dumps({"date": day.date, "wind": wind}, indent=2, ensure_ascii=False)
            + "\n"
        )
    return f"Wind: {wind}\n"


def format_today_weather(day: TomorrowForecast | None, *, as_json: bool) -> str:
    """Print today's forecast weather."""
    weather = "" if day is None else day.weather.strip()
    if day is None or not weather:
        return _unavailable("No forecast weather is available for today.", as_json=as_json)
    if as_json:
        return (
            json.dumps({"date": day.date, "weather": weather}, indent=2, ensure_ascii=False)
            + "\n"
        )
    return f"Weather: {weather}\n"


def format_today_humidity(day: TomorrowForecast | None, *, as_json: bool) -> str:
    """Print today's forecast humidity."""
    low = None if day is None else day.humidity_low_percent
    high = None if day is None else day.humidity_high_percent
    if day is None or (low is None and high is None):
        return _unavailable("No forecast humidity is available for today.", as_json=as_json)
    if as_json:
        payload: dict[str, object] = {"date": day.date}
        if low is not None:
            payload["humidity_low_percent"] = low
        if high is not None:
            payload["humidity_high_percent"] = high
        return json.dumps(payload, indent=2) + "\n"
    if low is not None and high is not None:
        text = f"{_number(low)}-{_number(high)}%"
    elif low is not None:
        text = f"{_number(low)}%"
    else:
        text = f"{_number(high)}%"
    return f"Humidity: {text}\n"


def format_day_miss(day: int, *, as_json: bool = False) -> str:
    """Say that forecast day N is not in the 9-day list."""
    return _unavailable(f"Forecast day {day} is not available.", as_json=as_json)


def _unavailable(message: str, *, as_json: bool) -> str:
    if as_json:
        return json.dumps({"message": message}, indent=2, ensure_ascii=False) + "\n"
    return message + "\n"


def _hong_kong_today(now: datetime | None = None) -> str:
    """Return today's calendar date in Hong Kong (UTC+8), as YYYY-MM-DD."""
    moment = now.astimezone(_HKT) if now is not None else datetime.now(_HKT)
    return moment.date().isoformat()


def _hong_kong_tomorrow(now: datetime | None = None) -> str:
    """Return tomorrow's calendar date in Hong Kong (UTC+8), as YYYY-MM-DD."""
    moment = now.astimezone(_HKT) if now is not None else datetime.now(_HKT)
    return (moment.date() + timedelta(days=1)).isoformat()


def _hong_kong_yesterday(now: datetime | None = None) -> str:
    """Return yesterday's calendar date in Hong Kong (UTC+8), as YYYY-MM-DD."""
    moment = now.astimezone(_HKT) if now is not None else datetime.now(_HKT)
    return (moment.date() - timedelta(days=1)).isoformat()


_HKT = timezone(timedelta(hours=8))


def parse_wind(payload: dict) -> WindForecast:
    """Turn `fnd` forecastWind fields into one line per day."""
    raw_days = payload.get("weatherForecast")
    days: list[WindDay] = []
    if isinstance(raw_days, list):
        for item in raw_days:
            if not isinstance(item, dict):
                continue
            wind = _text(item.get("forecastWind"))
            if not wind:
                continue
            days.append(
                WindDay(
                    date=_forecast_date(item.get("forecastDate")) or "unknown",
                    week=_text(item.get("week")),
                    wind=wind,
                )
            )
    return WindForecast(
        update_time=_text(payload.get("updateTime")),
        days=tuple(days),
    )


def parse_forecast_icon(payload: dict) -> ForecastIcons:
    """Turn `fnd` ForecastIcon fields into one icon per day."""
    raw_days = payload.get("weatherForecast")
    days: list[ForecastIconDay] = []
    if isinstance(raw_days, list):
        for item in raw_days:
            if not isinstance(item, dict):
                continue
            code = item.get("ForecastIcon")
            if isinstance(code, bool) or not isinstance(code, int):
                continue
            days.append(
                ForecastIconDay(
                    date=_forecast_date(item.get("forecastDate")) or "unknown",
                    week=_text(item.get("week")),
                    icon=code,
                    label=icon_label(code),
                )
            )
    return ForecastIcons(
        update_time=_text(payload.get("updateTime")),
        days=tuple(days),
    )


def parse_quakes(payload: dict) -> QuakeReport:
    """Turn a quick-earthquake message into a one-item list, or none."""
    quake = _quake(payload)
    return QuakeReport(() if quake is None else (quake,))


def format_quakes(report: QuakeReport) -> str:
    """Render recent earthquakes, one event per line."""
    if not report.quakes:
        return "No recent earthquake is reported.\n"
    lines = ["Hong Kong earthquakes"]
    updated = next((quake.update_time for quake in report.quakes if quake.update_time), "")
    if updated:
        lines.append(f"Updated: {updated}")
    for quake in report.quakes:
        magnitude = f"M{_number(quake.magnitude)}" if quake.magnitude is not None else "M?"
        region = quake.region or "unknown region"
        when = quake.time or "unknown time"
        if quake.latitude is not None and quake.longitude is not None:
            place = f"{region} ({_number(quake.latitude)}, {_number(quake.longitude)})"
        else:
            place = region
        lines.append(f"{when}  {magnitude}  {place}")
    return "\n".join(lines) + "\n"


def _quake_ago(when: str, now: datetime) -> str | None:
    """How long ago an earthquake time was, or None if it cannot be used."""
    text = when.strip()
    if not text:
        return None
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=_HKT)
    seconds = int((now - moment).total_seconds())
    if seconds < 0:
        return None
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 24 * 60:
        return _span_phrase(minutes)
    days, rest = divmod(minutes, 24 * 60)
    day_text = "1 day" if days == 1 else f"{days} days"
    hours = rest // 60
    if hours == 0:
        return day_text
    hour_text = "1 hour" if hours == 1 else f"{hours} hours"
    return f"{day_text} {hour_text}"


def format_quake_ago(report: QuakeReport, *, as_json: bool) -> str:
    """Print how long ago the latest earthquake happened."""
    if not report.quakes:
        return _unavailable("No recent earthquake is reported.", as_json=as_json)
    now = _clock()
    quake = next((item for item in report.quakes if _quake_ago(item.time, now)), None)
    ago = _quake_ago(quake.time, now) if quake is not None else None
    if quake is None or ago is None:
        return _unavailable("No earthquake time is available.", as_json=as_json)
    magnitude = f"M{_number(quake.magnitude)}" if quake.magnitude is not None else "M?"
    region = quake.region or "unknown region"
    if ago == "just now":
        phrase = f"Latest earthquake just now: {magnitude} {region}"
    else:
        phrase = f"Latest earthquake was {ago} ago: {magnitude} {region}"
    if as_json:
        payload = {
            "time": quake.time,
            "magnitude": quake.magnitude,
            "region": quake.region,
            "ago": ago,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_felt(payload: dict) -> FeltTremor | None:
    """Turn a locally felt tremor report into one event, or none."""
    region = _text(payload.get("region"))
    when = _text(payload.get("ptime"))
    magnitude = _optional_number(payload.get("mag"))
    intensity = _text(payload.get("intensity"))
    details = _text(payload.get("details"))
    if not region and not when and magnitude is None and not intensity and not details:
        return None
    return FeltTremor(
        time=when,
        update_time=_text(payload.get("updateTime")),
        region=region,
        magnitude=magnitude,
        intensity=intensity,
        latitude=_optional_number(payload.get("lat")),
        longitude=_optional_number(payload.get("lon")),
        details=details,
    )


def format_felt(report: FeltTremor) -> str:
    """Render the locally felt earth tremor."""
    lines = ["Hong Kong felt tremor"]
    if report.update_time:
        lines.append(f"Updated: {report.update_time}")
    magnitude = f"M{_number(report.magnitude)}" if report.magnitude is not None else "M?"
    region = report.region or "unknown region"
    when = report.time or "unknown time"
    if report.latitude is not None and report.longitude is not None:
        place = f"{region} ({_number(report.latitude)}, {_number(report.longitude)})"
    else:
        place = region
    line = f"{when}  {magnitude}  {place}"
    if report.intensity:
        line = f"{line}  intensity {report.intensity}"
    lines.append(line)
    if report.details:
        lines.append(report.details)
    return "\n".join(lines) + "\n"


def format_felt_miss(*, as_json: bool = False) -> str:
    """Say that no locally felt earth tremor is reported."""
    return _unavailable("No locally felt earth tremor is reported.", as_json=as_json)


def _quake(item: dict) -> Earthquake | None:
    region = _text(item.get("region"))
    when = _text(item.get("ptime"))
    magnitude = _optional_number(item.get("mag"))
    if not region and not when and magnitude is None:
        return None
    return Earthquake(
        time=when,
        region=region,
        magnitude=magnitude,
        latitude=_optional_number(item.get("lat")),
        longitude=_optional_number(item.get("lon")),
        update_time=_text(item.get("updateTime")),
    )


def parse_visibility(payload: dict) -> VisibilityReport:
    """Turn an `LTMV` document into one visibility reading per station."""
    raw = payload.get("data")
    if not isinstance(raw, list):
        return VisibilityReport(())
    readings: list[VisibilityReading] = []
    for item in raw:
        if not isinstance(item, list) or len(item) < 3:
            continue
        place = _text(item[1])
        visibility = _text(item[2])
        if not place or not visibility or visibility.casefold() == "n/a":
            continue
        readings.append(VisibilityReading(_visibility_time(item[0]), place, visibility))
    return VisibilityReport(tuple(readings))


def format_visibility(report: VisibilityReport) -> str:
    """Render 10-minute mean visibility, one station per line."""
    if not report.readings:
        return "No visibility readings are available.\n"
    lines = ["Hong Kong visibility"]
    lines.extend(
        f"{reading.time}  {reading.place}  {reading.visibility}" for reading in report.readings
    )
    return "\n".join(lines) + "\n"


def _visibility_km(text: str) -> float | None:
    """Read a visibility such as '14 km' as a number of kilometres."""
    token = text.strip().casefold()
    if token.endswith("km"):
        token = token[:-2].strip()
    if not token:
        return None
    try:
        value = float(token)
    except ValueError:
        return None
    if value < 0:
        return None
    return value


def format_least_vis(report: VisibilityReport, *, as_json: bool) -> str:
    """Print the station or stations with the poorest visibility."""
    ranked: list[tuple[float, VisibilityReading]] = []
    for reading in report.readings:
        kilometres = _visibility_km(reading.visibility)
        if kilometres is None:
            continue
        ranked.append((kilometres, reading))
    if not ranked:
        return _unavailable("No visibility readings are available.", as_json=as_json)
    poorest_km = min(kilometres for kilometres, _reading in ranked)
    poorest = tuple(reading for kilometres, reading in ranked if kilometres == poorest_km)
    places = [reading.place for reading in poorest]
    if len(places) == 1:
        listed = places[0]
    elif len(places) == 2:
        listed = f"{places[0]} and {places[1]}"
    else:
        listed = ", ".join(places[:-1]) + f", and {places[-1]}"
    distance = poorest[0].visibility
    times = {reading.time for reading in poorest}
    if len(times) == 1 and poorest[0].time:
        phrase = f"Poorest visibility: {poorest[0].time}  {listed}  {distance}"
    else:
        phrase = f"Poorest visibility: {listed}, {distance}"
    if as_json:
        payload = {
            "visibility_km": poorest_km,
            "readings": [
                {"time": reading.time, "place": reading.place, "visibility": reading.visibility}
                for reading in poorest
            ],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


_REDUCED_VIS_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_reduced_vis(text: str, lang: str = "en") -> ReducedVisibility | None:
    """Turn the airport visibility CSV into the latest numeric day."""
    station = _REDUCED_VIS_STATIONS.get(lang, _REDUCED_VIS_STATIONS["en"])
    latest: ReducedVisibility | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = ReducedVisibility(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_reduced_vis(reading: ReducedVisibility) -> str:
    """Render the latest daily hours of reduced visibility at the airport."""
    return (
        "Hong Kong reduced visibility\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.hours)} hours\n"
    )


def format_reduced_vis_miss(*, as_json: bool = False) -> str:
    """Say that no reduced-visibility total is available."""
    return _unavailable("No reduced visibility is available.", as_json=as_json)


def parse_tide(payload: dict, year: int) -> TideReport:
    """Turn an `HLT` document into high and low tide events."""
    raw = payload.get("data")
    events: list[TideEvent] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, list) or len(item) < 4:
                continue
            month = _text(item[0]).zfill(2)
            day = _text(item[1]).zfill(2)
            if not month.isdigit() or not day.isdigit():
                continue
            date = f"{year:04d}-{month}-{day}"
            pairs = item[2:]
            for index in range(0, len(pairs) - 1, 2):
                clock = _text(pairs[index])
                height = _text(pairs[index + 1])
                if len(clock) != 4 or not clock.isdigit():
                    continue
                try:
                    metres = float(height)
                except ValueError:
                    continue
                events.append(TideEvent(date, f"{clock[:2]}:{clock[2:]}", metres))
    return TideReport(TIDE_STATION_NAME, tuple(events))


def format_tide(report: TideReport) -> str:
    """Render today's high and low tides."""
    if not report.events:
        return "No tide readings are available.\n"
    lines = ["Hong Kong tide", f"Station: {report.station}"]
    lines.extend(
        f"{event.date}  {event.time}  {_number(event.height_m)} m" for event in report.events
    )
    return "\n".join(lines) + "\n"


def format_tide_miss(*, as_json: bool = False) -> str:
    """Say that no high or low tide readings are available."""
    return _unavailable("No tide readings are available.", as_json=as_json)


def _tide_kind(events: tuple[TideEvent, ...], index: int) -> str | None:
    """Label a tide high or low by comparing it with the tides beside it."""
    height = events[index].height_m
    neighbors: list[float] = []
    if index > 0:
        neighbors.append(events[index - 1].height_m)
    if index + 1 < len(events):
        neighbors.append(events[index + 1].height_m)
    if not neighbors:
        return None
    if all(height > other for other in neighbors):
        return "high"
    if all(height < other for other in neighbors):
        return "low"
    return None


def _next_tide_phrase(kind: str | None, seconds: int, height_m: float) -> str:
    """Say whether the chosen tide is ahead, now, or already past."""
    label = {"high": "High tide", "low": "Low tide"}.get(kind or "", "Tide")
    height = f"{_number(height_m)} m"
    if abs(seconds) < 60:
        return f"{label} now, {height}"
    span = _span_phrase(abs(seconds) // 60)
    if seconds > 0:
        return f"{label} in {span}, {height}"
    return f"{label} was {span} ago, {height}"


def format_next_tide(report: TideReport, *, as_json: bool) -> str:
    """Print how long until the next high or low tide."""
    now = _clock()
    upcoming: tuple[int, TideEvent, int] | None = None
    recent: tuple[int, TideEvent, int] | None = None
    for index, event in enumerate(report.events):
        moment = _clock_moment(event.date, event.time)
        if moment is None:
            continue
        seconds = int((moment - now).total_seconds())
        if seconds >= -59:
            if upcoming is None or seconds < upcoming[2]:
                upcoming = (index, event, seconds)
        elif recent is None or seconds > recent[2]:
            recent = (index, event, seconds)
    chosen = upcoming if upcoming is not None else recent
    if chosen is None:
        return _unavailable("No tide readings are available.", as_json=as_json)
    index, event, seconds = chosen
    kind = _tide_kind(report.events, index)
    phrase = _next_tide_phrase(kind, seconds, event.height_m)
    if as_json:
        payload = {
            "kind": kind,
            "time": event.time,
            "height_m": event.height_m,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_tide_hour(payload: dict, year: int) -> HourlyTideReport:
    """Turn an `HHOT` document into one height per hour."""
    fields = payload.get("fields")
    labels = [_text(field) for field in fields] if isinstance(fields, list) else []
    raw = payload.get("data")
    hours: list[HourlyTideReading] = []
    date = ""
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, list) or len(item) < 3:
                continue
            month = _text(item[0])
            day = _text(item[1])
            if not month.isdigit() or not day.isdigit():
                continue
            date = f"{year:04d}-{month.zfill(2)}-{day.zfill(2)}"
            for index, raw_height in enumerate(item[2:], start=1):
                height = _hour_mm(raw_height)
                if height is None:
                    continue
                label = labels[index + 1] if index + 1 < len(labels) else ""
                hour = label if label.isdigit() else f"{index:02d}"
                hours.append(HourlyTideReading(f"{hour.zfill(2)}:00", height))
            break
    return HourlyTideReport(TIDE_STATION_NAME, date, tuple(hours))


def format_tide_hour(report: HourlyTideReport) -> str:
    """Render today's hourly tide heights."""
    lines = ["Hong Kong hourly tide", f"Station: {report.station}"]
    for reading in report.hours:
        lines.append(f"{report.date}  {reading.hour}  {_number(reading.height_m)} m")
    return "\n".join(lines) + "\n"


def format_tide_hour_miss(*, as_json: bool = False) -> str:
    """Say that no hourly tide heights are available."""
    return _unavailable("No hourly tide heights are available.", as_json=as_json)


def _tide_minutes(hour: str) -> int | None:
    """Minutes after midnight for an hourly tide label, including 24:00."""
    text = hour.strip()
    if len(text) != 5 or text[2] != ":":
        return None
    hours, minutes = text[:2], text[3:]
    if not hours.isdigit() or not minutes.isdigit():
        return None
    return int(hours) * 60 + int(minutes)


def _tide_turn_pair(
    hours: tuple[HourlyTideReading, ...], now: datetime
) -> tuple[HourlyTideReading, HourlyTideReading] | None:
    """The hourly step that contains now, or the nearest end pair."""
    usable = []
    for reading in hours:
        minutes = _tide_minutes(reading.hour)
        if minutes is None:
            continue
        usable.append((minutes, reading))
    if len(usable) < 2:
        return None
    usable.sort(key=lambda item: item[0])
    moment = now if now.tzinfo is not None else now.replace(tzinfo=_HKT)
    local = moment.astimezone(_HKT)
    minute = local.hour * 60 + local.minute
    for index in range(len(usable) - 1):
        if usable[index][0] <= minute < usable[index + 1][0]:
            return usable[index][1], usable[index + 1][1]
    if minute < usable[0][0]:
        return usable[0][1], usable[1][1]
    return usable[-2][1], usable[-1][1]


def format_tide_turn(report: HourlyTideReport, *, as_json: bool) -> str:
    """Print whether the Quarry Bay tide is rising or falling this hour."""
    pair = _tide_turn_pair(report.hours, _clock())
    if pair is None:
        return _unavailable("No tide turn is available.", as_json=as_json)
    start, end = pair
    gap = round(end.height_m - start.height_m, 2)
    if gap > 0:
        turn = "rising"
    elif gap < 0:
        turn = "falling"
    else:
        turn = "steady"
    station = report.station or "the tide station"
    span = (
        f"{start.hour} {_number(start.height_m)} m to "
        f"{end.hour} {_number(end.height_m)} m"
    )
    if report.date:
        phrase = f"Tide is {turn} at {station}: {report.date} {span}"
    else:
        phrase = f"Tide is {turn} at {station}: {span}"
    if as_json:
        payload = {
            "station": report.station,
            "date": report.date,
            "from": start.hour,
            "to": end.hour,
            "from_m": start.height_m,
            "to_m": end.height_m,
            "turn": turn,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def _tide_stamp(date: str, clock: str) -> str:
    """Return `YYYY-MM-DD HH:MM` when both parts look like a tide timestamp."""
    day = date.replace("-", "")
    minute = clock.replace(":", "")
    if len(date) == 10 and date[4] == "-" and date[7] == "-" and day.isdigit():
        if len(clock) == 5 and clock[2] == ":" and minute.isdigit():
            return f"{date} {clock}"
    return ""


def parse_tide_latest(text: str) -> LatestTideReport:
    """Turn the latest-tide CSV into the newest time, one row per station."""
    stations: list[LatestTideReading] = []
    latest = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 4:
            continue
        place = _text(row[0]).lstrip("\ufeff")
        stamp = _tide_stamp(_text(row[1]), _text(row[2]))
        height = _hour_mm(row[3])
        if not place or not stamp or height is None:
            continue
        if stamp > latest:
            latest = stamp
            stations = []
        if stamp == latest:
            stations.append(LatestTideReading(place, height))
    return LatestTideReport(latest, tuple(stations))


def format_tide_latest(report: LatestTideReport) -> str:
    """Render the latest observed tide height, one station per line."""
    lines = ["Hong Kong latest tide"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        lines.append(f"{reading.place}  {_number(reading.height_m)} m")
    return "\n".join(lines) + "\n"


def format_tide_latest_miss(*, as_json: bool = False) -> str:
    """Say that no latest tide heights are available."""
    return _unavailable("No latest tide heights are available.", as_json=as_json)


def _tide_places(readings: tuple[LatestTideReading, ...]) -> str:
    places = [reading.place for reading in readings]
    if len(places) == 1:
        return places[0]
    if len(places) == 2:
        return f"{places[0]} and {places[1]}"
    return ", ".join(places[:-1]) + f", and {places[-1]}"


def format_tide_span(report: LatestTideReport, *, as_json: bool) -> str:
    """Print the gap between the lowest and highest latest tide heights."""
    if len(report.stations) < 2:
        return _unavailable("No tide span is available.", as_json=as_json)
    low = min(round(reading.height_m, 2) for reading in report.stations)
    high = max(round(reading.height_m, 2) for reading in report.stations)
    lowest = tuple(
        reading for reading in report.stations if round(reading.height_m, 2) == low
    )
    highest = tuple(
        reading for reading in report.stations if round(reading.height_m, 2) == high
    )
    span = round(high - low, 2)
    if span == 0:
        detail = f"tides match at {_number(high)} m"
    else:
        detail = (
            f"{_number(span)} m, from {_tide_places(lowest)} {_number(low)} m "
            f"to {_tide_places(highest)} {_number(high)} m"
        )
    if report.obs_time:
        phrase = f"Tide span: {report.obs_time}  {detail}"
    else:
        phrase = f"Tide span: {detail}"
    if as_json:
        payload = {
            "recorded": report.obs_time,
            "span_m": span,
            "low_m": low,
            "high_m": high,
            "low_stations": [reading.place for reading in lowest],
            "high_stations": [reading.place for reading in highest],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def _aqhi_description(text: str) -> tuple[str, str, str, str, str] | None:
    """Split `Station - Area: 3 Low - updated` into its fields."""
    parts = [part.strip() for part in text.split(" - ")]
    if len(parts) < 2 or not parts[0]:
        return None
    area, sep, values = parts[1].partition(":")
    tokens = values.split()
    if not sep or not area.strip() or not tokens:
        return None
    aqhi = tokens[0]
    if not aqhi.rstrip("+").isdigit() or aqhi.count("+") > 1:
        return None
    updated = " - ".join(parts[2:]).strip()
    return parts[0], area.strip(), aqhi, " ".join(tokens[1:]), updated


def parse_aqhi(raw: str) -> AqhiReport:
    """Turn an AQHI station RSS document into one reading per station."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise WeatherError("the AQHI feed returned invalid XML") from exc
    readings: list[AqhiReading] = []
    updated = ""
    for item in root.iter("item"):
        parsed = _aqhi_description(_text(item.findtext("description")))
        if parsed is None:
            continue
        station, area, aqhi, risk, when = parsed
        if not updated and when:
            updated = when
        readings.append(AqhiReading(station, area, aqhi, risk))
    return AqhiReport(updated, tuple(readings))


def format_aqhi(report: AqhiReport) -> str:
    """Render the current AQHI, one station per line."""
    if not report.readings:
        return "No AQHI readings are available.\n"
    lines = ["Hong Kong AQHI"]
    if report.updated:
        lines.append(f"Updated: {report.updated}")
    for reading in report.readings:
        line = f"{reading.station}  {reading.area}  {reading.aqhi}"
        if reading.health_risk:
            line = f"{line}  {reading.health_risk}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def format_aqhi_miss(*, as_json: bool = False) -> str:
    """Say that no AQHI station readings are available."""
    return _unavailable("No AQHI readings are available.", as_json=as_json)


_AQHI_SEVERITY = (
    ("serious", "嚴重", "严重"),
    ("very high", "甚高"),
    ("high", "高"),
    ("moderate", "中"),
    ("low", "低"),
)


def _aqhi_severity(risk: str) -> int:
    folded = risk.casefold()
    for index, names in enumerate(_AQHI_SEVERITY):
        if folded in names:
            return index
    return len(_AQHI_SEVERITY)


def format_aqhi_mix(report: AqhiReport, *, as_json: bool) -> str:
    """Print how many stations fall in each AQHI health-risk band."""
    counts: dict[str, int] = {}
    for reading in report.readings:
        if not reading.health_risk:
            continue
        counts[reading.health_risk] = counts.get(reading.health_risk, 0) + 1
    if not counts:
        return _unavailable("No AQHI readings are available.", as_json=as_json)
    bands = sorted(counts, key=lambda risk: (_aqhi_severity(risk), risk.casefold()))
    phrase = "AQHI: " + ", ".join(f"{counts[risk]} {risk}" for risk in bands)
    if as_json:
        payload = {
            "updated": report.updated,
            "stations": sum(counts.values()),
            "bands": [{"risk": risk, "count": counts[risk]} for risk in bands],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_sunrise(payload: dict) -> Sunrise | None:
    """Turn an `SRS` document into today's sunrise, transit, and sunset."""
    raw = payload.get("data")
    if not isinstance(raw, list):
        return None
    for item in raw:
        if not isinstance(item, list) or len(item) < 4:
            continue
        date = _text(item[0])
        rise = _text(item[1])
        transit = _text(item[2])
        sunset = _text(item[3])
        if date and (rise or transit or sunset):
            return Sunrise(date, rise, transit, sunset)
    return None


def format_sunrise(reading: Sunrise) -> str:
    """Render today's sunrise, sun transit, and sunset."""
    lines = ["Hong Kong sunrise", reading.date]
    if reading.rise:
        lines.append(f"Rise: {reading.rise}")
    if reading.transit:
        lines.append(f"Transit: {reading.transit}")
    if reading.set:
        lines.append(f"Set: {reading.set}")
    return "\n".join(lines) + "\n"


def format_sunrise_miss(*, as_json: bool = False) -> str:
    """Say that today's sunrise times are not available."""
    return _unavailable("No sunrise times are available.", as_json=as_json)


def _clock_moment(date_text: str, clock: str) -> datetime | None:
    """Combine a YYYY-MM-DD date and an HH:MM clock into one HKT moment."""
    parts = clock.strip().split(":")
    if len(parts) != 2:
        return None
    try:
        day = datetime.fromisoformat(date_text.strip()).date()
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=_HKT)


def _sunset_moment(reading: Sunrise) -> datetime | None:
    """Combine the sunrise report's date and sunset clock into one HKT moment."""
    return _clock_moment(reading.date, reading.set)


def _span_phrase(minutes: int) -> str:
    """Format a positive number of minutes as hours and minutes."""
    if minutes < 60:
        return "1 min" if minutes == 1 else f"{minutes} min"
    hours, remaining = divmod(minutes, 60)
    hour_text = "1 hour" if hours == 1 else f"{hours} hours"
    if remaining == 0:
        return hour_text
    minute_text = "1 min" if remaining == 1 else f"{remaining} min"
    return f"{hour_text} {minute_text}"


def _until_sunset_phrase(moment: datetime, now: datetime) -> str:
    """Say whether sunset is ahead, now, or already past."""
    seconds = int((moment - now).total_seconds())
    if abs(seconds) < 60:
        return "Sunset now"
    span = _span_phrase(abs(seconds) // 60)
    if seconds > 0:
        return f"Sunset in {span}"
    return f"Sunset was {span} ago"


def format_until_sunset(reading: Sunrise | None, *, as_json: bool) -> str:
    """Print how long until today's sunset."""
    moment = _sunset_moment(reading) if reading is not None else None
    if reading is None or moment is None:
        return _unavailable("No sunset time is available.", as_json=as_json)
    phrase = _until_sunset_phrase(moment, _clock())
    if as_json:
        return json.dumps({"sunset": reading.set, "until": phrase}, indent=2) + "\n"
    return phrase + "\n"


def _since_sunrise_phrase(moment: datetime, now: datetime) -> str:
    """Say whether sunrise is ahead, now, or already past."""
    seconds = int((moment - now).total_seconds())
    if abs(seconds) < 60:
        return "Sunrise now"
    span = _span_phrase(abs(seconds) // 60)
    if seconds > 0:
        return f"Sunrise in {span}"
    return f"Sunrise was {span} ago"


def format_since_sunrise(reading: Sunrise | None, *, as_json: bool) -> str:
    """Print how long it has been since today's sunrise."""
    moment = _clock_moment(reading.date, reading.rise) if reading is not None else None
    if reading is None or moment is None:
        return _unavailable("No sunrise time is available.", as_json=as_json)
    phrase = _since_sunrise_phrase(moment, _clock())
    if as_json:
        return json.dumps({"sunrise": reading.rise, "since": phrase}, indent=2) + "\n"
    return phrase + "\n"


def format_sun_up(reading: Sunrise | None, *, as_json: bool) -> str:
    """Say whether the sun is above the horizon."""
    up = (
        _moon_is_up(reading.rise, reading.set, _clock())
        if reading is not None
        else None
    )
    if reading is None or up is None:
        return _unavailable("No sun times are available.", as_json=as_json)
    phrase = "The sun is up" if up else "The sun is down"
    if as_json:
        payload = {"up": up, "rise": reading.rise, "set": reading.set, "phrase": phrase}
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def _until_transit_phrase(moment: datetime, now: datetime) -> str:
    """Say whether sun transit is ahead, now, or already past."""
    seconds = int((moment - now).total_seconds())
    if abs(seconds) < 60:
        return "Transit now"
    span = _span_phrase(abs(seconds) // 60)
    if seconds > 0:
        return f"Transit in {span}"
    return f"Transit was {span} ago"


def format_until_transit(reading: Sunrise | None, *, as_json: bool) -> str:
    """Print how long until today's sun transit."""
    moment = _clock_moment(reading.date, reading.transit) if reading is not None else None
    if reading is None or moment is None:
        return _unavailable("No sun transit time is available.", as_json=as_json)
    phrase = _until_transit_phrase(moment, _clock())
    if as_json:
        return json.dumps({"transit": reading.transit, "until": phrase}, indent=2) + "\n"
    return phrase + "\n"


def _clock_minutes(clock: str) -> int | None:
    """Turn an HH:MM clock into minutes after midnight."""
    parts = clock.strip().split(":")
    if len(parts) != 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour * 60 + minute


def format_daylight(reading: Sunrise | None, *, as_json: bool) -> str:
    """Print how long the sun is up, from sunrise to sunset."""
    if reading is None:
        return _unavailable("No daylight length is available.", as_json=as_json)
    rise = _clock_minutes(reading.rise)
    sunset = _clock_minutes(reading.set)
    if rise is None or sunset is None or sunset <= rise:
        return _unavailable("No daylight length is available.", as_json=as_json)
    phrase = _span_phrase(sunset - rise)
    if as_json:
        return (
            json.dumps({"rise": reading.rise, "set": reading.set, "daylight": phrase}, indent=2)
            + "\n"
        )
    return f"Daylight {phrase}\n"


def parse_moon(payload: dict) -> Moon | None:
    """Turn an `MRS` document into today's moonrise, transit, and moonset."""
    reading = parse_sunrise(payload)
    if reading is None:
        return None
    return Moon(reading.date, reading.rise, reading.transit, reading.set)


def format_moon(reading: Moon) -> str:
    """Render today's moonrise, moon transit, and moonset."""
    lines = ["Hong Kong moon", reading.date]
    if reading.rise:
        lines.append(f"Rise: {reading.rise}")
    if reading.transit:
        lines.append(f"Transit: {reading.transit}")
    if reading.set:
        lines.append(f"Set: {reading.set}")
    return "\n".join(lines) + "\n"


def format_moon_miss(*, as_json: bool = False) -> str:
    """Say that today's moon times are not available."""
    return _unavailable("No moon times are available.", as_json=as_json)


def _until_moonset_phrase(moment: datetime, now: datetime) -> str:
    """Say whether moonset is ahead, now, or already past."""
    seconds = int((moment - now).total_seconds())
    if abs(seconds) < 60:
        return "Moonset now"
    span = _span_phrase(abs(seconds) // 60)
    if seconds > 0:
        return f"Moonset in {span}"
    return f"Moonset was {span} ago"


def format_until_moonset(reading: Moon | None, *, as_json: bool) -> str:
    """Print how long until today's moonset."""
    moment = _clock_moment(reading.date, reading.set) if reading is not None else None
    if reading is None or moment is None:
        return _unavailable("No moonset time is available.", as_json=as_json)
    phrase = _until_moonset_phrase(moment, _clock())
    if as_json:
        return json.dumps({"moonset": reading.set, "until": phrase}, indent=2) + "\n"
    return phrase + "\n"


def _moon_is_up(rise: str, set_clock: str, now: datetime) -> bool | None:
    """True when the moon is up, using today's rise and set clocks."""
    rise_min = _clock_minutes(rise)
    set_min = _clock_minutes(set_clock)
    if rise_min is None or set_min is None or rise_min == set_min:
        return None
    moment = now.astimezone(_HKT)
    now_min = moment.hour * 60 + moment.minute
    if set_min > rise_min:
        return rise_min <= now_min < set_min
    return now_min >= rise_min or now_min < set_min


def format_moon_up(reading: Moon | None, *, as_json: bool) -> str:
    """Say whether the moon is above the horizon."""
    up = _moon_is_up(reading.rise, reading.set, _clock()) if reading is not None else None
    if reading is None or up is None:
        return _unavailable("No moon times are available.", as_json=as_json)
    phrase = "The moon is up" if up else "The moon is down"
    if as_json:
        return (
            json.dumps(
                {"up": up, "rise": reading.rise, "set": reading.set},
                indent=2,
            )
            + "\n"
        )
    return phrase + "\n"


def parse_lunar(payload: dict, date: str) -> LunarDate | None:
    """Turn a lunar-date document into today's Gregorian and lunar labels."""
    lunar_year = _text(payload.get("LunarYear"))
    lunar_date = _text(payload.get("LunarDate"))
    if not lunar_year and not lunar_date:
        return None
    return LunarDate(date, lunar_year, lunar_date)


def format_lunar(reading: LunarDate) -> str:
    """Render today's lunar date."""
    lines = ["Hong Kong lunar date", reading.date]
    if reading.lunar_year:
        lines.append(reading.lunar_year)
    if reading.lunar_date:
        lines.append(reading.lunar_date)
    return "\n".join(lines) + "\n"


def format_lunar_miss(*, as_json: bool = False) -> str:
    """Say that today's lunar date is not available."""
    return _unavailable("No lunar date is available.", as_json=as_json)


def _visibility_time(value: object) -> str:
    text = _text(value)
    if len(text) == 12 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]} {text[8:10]}:{text[10:12]}"
    return text


def _optional_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def format_wind(report: WindForecast) -> str:
    """Render forecast wind, one day per line."""
    if not report.days:
        return "No forecast wind is available.\n"
    lines = ["Hong Kong forecast wind"]
    if report.update_time:
        lines.append(f"Updated: {report.update_time}")
    for day in report.days:
        heading = " ".join(part for part in (day.date, day.week) if part)
        lines.append(f"{heading}  {day.wind}".strip())
    return "\n".join(lines) + "\n"


def _max_force(text: str) -> int | None:
    """Highest Beaufort number in an English or Chinese wind sentence."""
    found: list[int] = []
    lower = text.lower()
    start = 0
    while True:
        index = lower.find("force", start)
        if index < 0:
            break
        rest = text[index + len("force") :].lstrip()
        digits = ""
        for char in rest:
            if char.isdigit():
                digits += char
            elif digits or not char.isspace():
                break
        if digits:
            found.append(int(digits))
        start = index + len("force")
    for mark in ("級", "级"):
        start = 0
        while True:
            index = text.find(mark, start)
            if index < 0:
                break
            digits = ""
            cursor = index - 1
            while cursor >= 0 and text[cursor].isdigit():
                digits = text[cursor] + digits
                cursor -= 1
            if digits:
                found.append(int(digits))
            start = index + len(mark)
    if not found:
        return None
    return max(found)


def format_wind_ease(report: WindForecast, *, as_json: bool) -> str:
    """Print the first forecast day whose strongest force is lighter."""
    previous: int | None = None
    chosen: tuple[WindDay, int, int] | None = None
    for day in report.days:
        force = _max_force(day.wind)
        if force is None:
            continue
        if previous is not None and force < previous:
            chosen = (day, previous, force)
            break
        previous = force
    if chosen is None:
        return _unavailable("No lighter wind day is in the forecast.", as_json=as_json)
    day, before, after = chosen
    heading = " ".join(part for part in (day.date, day.week) if part)
    if heading:
        phrase = (
            f"Wind eases on {heading}, from force {before} to force {after}: {day.wind}"
        )
    else:
        phrase = f"Wind eases from force {before} to force {after}: {day.wind}"
    if as_json:
        payload = {
            "date": day.date,
            "week": day.week,
            "wind": day.wind,
            "from_force": before,
            "to_force": after,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_gust(text: str) -> GustReport:
    """Turn the regional 10-minute wind CSV into one row per station."""
    stations: list[GustReading] = []
    obs_time = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 5:
            continue
        place = _text(row[1])
        direction = _text(row[2])
        if direction.upper() == "N/A":
            direction = ""
        speed = _hour_mm(row[3])
        gust = _hour_mm(row[4])
        if not place or (speed is None and gust is None):
            continue
        clock = _text(row[0])
        if not obs_time and len(clock) == 12 and clock.isdigit():
            obs_time = f"{clock[:4]}-{clock[4:6]}-{clock[6:8]} {clock[8:10]}:{clock[10:12]}"
        stations.append(GustReading(place, direction, speed, gust))
    return GustReport(obs_time, tuple(stations))


def format_gust(report: GustReport) -> str:
    """Render the latest 10-minute wind and gust, one station per line."""
    lines = ["Hong Kong wind gusts"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        parts = [reading.place]
        if reading.direction:
            parts.append(reading.direction)
        if reading.speed_kmh is not None:
            parts.append(f"{_number(reading.speed_kmh)} km/h")
        if reading.gust_kmh is not None:
            parts.append(f"gust {_number(reading.gust_kmh)} km/h")
        lines.append("  ".join(parts))
    return "\n".join(lines) + "\n"


def format_gust_miss(*, as_json: bool = False) -> str:
    """Say that no 10-minute wind gusts are available."""
    return _unavailable("No wind gusts are available.", as_json=as_json)


def format_strongest_gust(report: GustReport, *, as_json: bool) -> str:
    """Print the station or stations with the strongest gust."""
    ranked = [reading for reading in report.stations if reading.gust_kmh is not None]
    if not ranked:
        return _unavailable("No wind gusts are available.", as_json=as_json)
    peak = max(reading.gust_kmh for reading in ranked)
    strongest = tuple(reading for reading in ranked if reading.gust_kmh == peak)
    places = [reading.place for reading in strongest]
    if len(places) == 1:
        listed = places[0]
    elif len(places) == 2:
        listed = f"{places[0]} and {places[1]}"
    else:
        listed = ", ".join(places[:-1]) + f", and {places[-1]}"
    speed = f"{_number(peak)} km/h"
    if len(strongest) == 1 and strongest[0].direction:
        detail = f"{listed}  {strongest[0].direction}  {speed}"
    else:
        detail = f"{listed}, {speed}"
    if report.obs_time:
        phrase = f"Strongest gust: {report.obs_time}  {detail}"
    else:
        phrase = f"Strongest gust: {detail}"
    if as_json:
        payload = {
            "recorded": report.obs_time,
            "gust_kmh": peak,
            "stations": [
                {
                    "place": reading.place,
                    "direction": reading.direction,
                    "gust_kmh": reading.gust_kmh,
                }
                for reading in strongest
            ],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def _gust_gap_kmh(reading: GustReading) -> float:
    return round(reading.gust_kmh - reading.speed_kmh, 1)


def _gust_gap_relation(gap: float, wind_kmh: float) -> str:
    wind = f"{_number(wind_kmh)} km/h"
    if gap > 0:
        return f"{_number(gap)} km/h above {wind}"
    if gap < 0:
        return f"{_number(abs(gap))} km/h below {wind}"
    return f"gust matches its {wind} wind"


def format_gust_gap(report: GustReport, *, as_json: bool) -> str:
    """Print where the gust exceeds the mean wind by the most."""
    ranked = [
        reading
        for reading in report.stations
        if reading.gust_kmh is not None and reading.speed_kmh is not None
    ]
    if not ranked:
        return _unavailable("No gust gap is available.", as_json=as_json)
    peak = max(_gust_gap_kmh(reading) for reading in ranked)
    widest = tuple(reading for reading in ranked if _gust_gap_kmh(reading) == peak)
    if len(widest) == 1:
        reading = widest[0]
        relation = _gust_gap_relation(peak, reading.speed_kmh)
        if reading.direction:
            detail = f"{reading.place}  {reading.direction}  {relation}"
        else:
            detail = f"{reading.place}  {relation}"
    else:
        places = [reading.place for reading in widest]
        if len(places) == 2:
            listed = f"{places[0]} and {places[1]}"
        else:
            listed = ", ".join(places[:-1]) + f", and {places[-1]}"
        if peak > 0:
            detail = f"{listed}, {_number(peak)} km/h above the wind"
        elif peak < 0:
            detail = f"{listed}, {_number(abs(peak))} km/h below the wind"
        else:
            detail = f"{listed}, gust matches the wind"
    if report.obs_time:
        phrase = f"Largest gust gap: {report.obs_time}  {detail}"
    else:
        phrase = f"Largest gust gap: {detail}"
    if as_json:
        payload = {
            "recorded": report.obs_time,
            "gap_kmh": peak,
            "stations": [
                {
                    "place": reading.place,
                    "direction": reading.direction,
                    "wind_kmh": reading.speed_kmh,
                    "gust_kmh": reading.gust_kmh,
                    "gap_kmh": _gust_gap_kmh(reading),
                }
                for reading in widest
            ],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


_PREVAILING_STATIONS = {
    "en": "Waglan Island",
    "tc": "橫瀾島",
    "sc": "横澜岛",
}


def parse_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Waglan prevailing-wind CSV into the latest numeric day."""
    station = _PREVAILING_STATIONS.get(lang, _PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_prevailing(reading: PrevailingWind) -> str:
    """Render the latest daily prevailing wind direction at Waglan Island."""
    return (
        "Hong Kong prevailing wind\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.direction_deg)}°\n"
    )


def format_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no prevailing wind direction is available."""
    return _unavailable("No prevailing wind is available.", as_json=as_json)


_CHEUNG_PREVAILING_STATIONS = {
    "en": "Cheung Chau",
    "tc": "長洲",
    "sc": "长洲",
}


def parse_cheung_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Cheung Chau prevailing-wind CSV into the latest numeric day."""
    station = _CHEUNG_PREVAILING_STATIONS.get(lang, _CHEUNG_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau prevailing wind direction is available."""
    return _unavailable("No Cheung Chau prevailing wind is available.", as_json=as_json)


_PING_CHAU_STATIONS = {
    "en": "Ping Chau",
    "tc": "平洲",
    "sc": "平洲",
}


def parse_ping_chau_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Ping Chau prevailing-wind CSV into the latest numeric day."""
    station = _PING_CHAU_STATIONS.get(lang, _PING_CHAU_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ping_chau_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Ping Chau prevailing wind direction is available."""
    return _unavailable("No Ping Chau prevailing wind is available.", as_json=as_json)


_TAI_MO_TO_STATIONS = {
    "en": "Tai Mo To",
    "tc": "大磨刀",
    "sc": "大磨刀",
}


def parse_tai_mo_to_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Tai Mo To prevailing-wind CSV into the latest numeric day."""
    station = _TAI_MO_TO_STATIONS.get(lang, _TAI_MO_TO_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_to_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo To prevailing wind direction is available."""
    return _unavailable("No Tai Mo To prevailing wind is available.", as_json=as_json)


_TAI_PO_KAU_PREVAILING_STATIONS = {
    "en": "Tai Po Kau",
    "tc": "大埔滘",
    "sc": "大埔滘",
}


def parse_tai_po_kau_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Tai Po Kau prevailing-wind CSV into the latest numeric day."""
    station = _TAI_PO_KAU_PREVAILING_STATIONS.get(lang, _TAI_PO_KAU_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_po_kau_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Po Kau prevailing wind direction is available."""
    return _unavailable("No Tai Po Kau prevailing wind is available.", as_json=as_json)


_PARK_PREVAILING_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_park_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the King's Park prevailing-wind CSV into the latest numeric day."""
    station = _PARK_PREVAILING_STATIONS.get(lang, _PARK_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_park_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park prevailing wind direction is available."""
    return _unavailable("No King's Park prevailing wind is available.", as_json=as_json)


_LAU_FAU_PREVAILING_STATIONS = {
    "en": "Lau Fau Shan",
    "tc": "流浮山",
    "sc": "流浮山",
}


def parse_lau_fau_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Lau Fau Shan prevailing-wind CSV into the latest numeric day."""
    station = _LAU_FAU_PREVAILING_STATIONS.get(lang, _LAU_FAU_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lau_fau_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Lau Fau Shan prevailing wind direction is available."""
    return _unavailable("No Lau Fau Shan prevailing wind is available.", as_json=as_json)


_SHA_LO_WAN_PREVAILING_STATIONS = {
    "en": "Sha Lo Wan",
    "tc": "沙螺灣",
    "sc": "沙螺湾",
}


def parse_sha_lo_wan_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Sha Lo Wan prevailing-wind CSV into the latest numeric day."""
    station = _SHA_LO_WAN_PREVAILING_STATIONS.get(
        lang, _SHA_LO_WAN_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_lo_wan_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Lo Wan prevailing wind direction is available."""
    return _unavailable("No Sha Lo Wan prevailing wind is available.", as_json=as_json)


_WONG_CHUK_HANG_PREVAILING_STATIONS = {
    "en": "Wong Chuk Hang",
    "tc": "黃竹坑",
    "sc": "黄竹坑",
}


def parse_wong_chuk_hang_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Wong Chuk Hang prevailing-wind CSV into the latest numeric day."""
    station = _WONG_CHUK_HANG_PREVAILING_STATIONS.get(
        lang, _WONG_CHUK_HANG_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_chuk_hang_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Wong Chuk Hang prevailing wind direction is available."""
    return _unavailable(
        "No Wong Chuk Hang prevailing wind is available.", as_json=as_json
    )


_SAI_KUNG_PREVAILING_STATIONS = {
    "en": "Sai Kung",
    "tc": "西貢",
    "sc": "西贡",
}


def parse_sai_kung_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Sai Kung prevailing-wind CSV into the latest numeric day."""
    station = _SAI_KUNG_PREVAILING_STATIONS.get(lang, _SAI_KUNG_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sai_kung_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Sai Kung prevailing wind direction is available."""
    return _unavailable("No Sai Kung prevailing wind is available.", as_json=as_json)


_TSEUNG_KWAN_O_PREVAILING_STATIONS = {
    "en": "Tseung Kwan O",
    "tc": "將軍澳",
    "sc": "将军澳",
}


def parse_tseung_kwan_o_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Tseung Kwan O prevailing-wind CSV into the latest numeric day."""
    station = _TSEUNG_KWAN_O_PREVAILING_STATIONS.get(
        lang, _TSEUNG_KWAN_O_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tseung_kwan_o_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Tseung Kwan O prevailing wind direction is available."""
    return _unavailable(
        "No Tseung Kwan O prevailing wind is available.", as_json=as_json
    )


_SHEK_KONG_PREVAILING_STATIONS = {
    "en": "Shek Kong",
    "tc": "石崗",
    "sc": "石岗",
}


def parse_shek_kong_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Shek Kong prevailing-wind CSV into the latest numeric day."""
    station = _SHEK_KONG_PREVAILING_STATIONS.get(lang, _SHEK_KONG_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shek_kong_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Shek Kong prevailing wind direction is available."""
    return _unavailable("No Shek Kong prevailing wind is available.", as_json=as_json)


_SHA_TIN_PREVAILING_STATIONS = {
    "en": "Sha Tin",
    "tc": "沙田",
    "sc": "沙田",
}


def parse_sha_tin_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Sha Tin prevailing-wind CSV into the latest numeric day."""
    station = _SHA_TIN_PREVAILING_STATIONS.get(lang, _SHA_TIN_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_tin_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Tin prevailing wind direction is available."""
    return _unavailable("No Sha Tin prevailing wind is available.", as_json=as_json)


_TA_KWU_LING_PREVAILING_STATIONS = {
    "en": "Ta Kwu Ling",
    "tc": "打鼓嶺",
    "sc": "打鼓岭",
}


def parse_ta_kwu_ling_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Ta Kwu Ling prevailing-wind CSV into the latest numeric day."""
    station = _TA_KWU_LING_PREVAILING_STATIONS.get(
        lang, _TA_KWU_LING_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ta_kwu_ling_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Ta Kwu Ling prevailing wind direction is available."""
    return _unavailable(
        "No Ta Kwu Ling prevailing wind is available.", as_json=as_json
    )


_WETLAND_PREVAILING_STATIONS = {
    "en": "Wetland Park",
    "tc": "濕地公園",
    "sc": "湿地公园",
}


def parse_wetland_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Wetland Park prevailing-wind CSV into the latest numeric day."""
    station = _WETLAND_PREVAILING_STATIONS.get(lang, _WETLAND_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wetland_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Wetland Park prevailing wind direction is available."""
    return _unavailable("No Wetland Park prevailing wind is available.", as_json=as_json)


_TAI_MO_PREVAILING_STATIONS = {
    "en": "Tai Mo Shan",
    "tc": "大帽山",
    "sc": "大帽山",
}


def parse_tai_mo_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Tai Mo Shan prevailing-wind CSV into the latest numeric day."""
    station = _TAI_MO_PREVAILING_STATIONS.get(lang, _TAI_MO_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo Shan prevailing wind direction is available."""
    return _unavailable("No Tai Mo Shan prevailing wind is available.", as_json=as_json)


_AIRPORT_PREVAILING_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_airport_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the airport prevailing-wind CSV into the latest numeric day."""
    station = _AIRPORT_PREVAILING_STATIONS.get(lang, _AIRPORT_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_airport_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no airport prevailing wind direction is available."""
    return _unavailable("No airport prevailing wind is available.", as_json=as_json)


_KAI_TAK_PREVAILING_STATIONS = {
    "en": "Kai Tak",
    "tc": "啟德",
    "sc": "启德",
}


def parse_kai_tak_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Kai Tak prevailing-wind CSV into the latest numeric day."""
    station = _KAI_TAK_PREVAILING_STATIONS.get(lang, _KAI_TAK_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kai_tak_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Kai Tak prevailing wind direction is available."""
    return _unavailable("No Kai Tak prevailing wind is available.", as_json=as_json)


_GREEN_ISLAND_PREVAILING_STATIONS = {
    "en": "Green Island",
    "tc": "青洲",
    "sc": "青洲",
}


def parse_green_island_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Green Island prevailing-wind CSV into the latest numeric day."""
    station = _GREEN_ISLAND_PREVAILING_STATIONS.get(
        lang, _GREEN_ISLAND_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_green_island_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Green Island prevailing wind direction is available."""
    return _unavailable(
        "No Green Island prevailing wind is available.", as_json=as_json
    )


_NGONG_PING_PREVAILING_STATIONS = {
    "en": "Ngong Ping",
    "tc": "昂坪",
    "sc": "昂坪",
}


def parse_ngong_ping_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Ngong Ping prevailing-wind CSV into the latest numeric day."""
    station = _NGONG_PING_PREVAILING_STATIONS.get(
        lang, _NGONG_PING_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ngong_ping_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Ngong Ping prevailing wind direction is available."""
    return _unavailable(
        "No Ngong Ping prevailing wind is available.", as_json=as_json
    )


_TAI_MEI_TUK_PREVAILING_STATIONS = {
    "en": "Tai Mei Tuk",
    "tc": "大美督",
    "sc": "大美督",
}


def parse_tai_mei_tuk_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Tai Mei Tuk prevailing-wind CSV into the latest numeric day."""
    station = _TAI_MEI_TUK_PREVAILING_STATIONS.get(
        lang, _TAI_MEI_TUK_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mei_tuk_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mei Tuk prevailing wind direction is available."""
    return _unavailable(
        "No Tai Mei Tuk prevailing wind is available.", as_json=as_json
    )


_CENTRAL_PIER_PREVAILING_STATIONS = {
    "en": "Central Pier",
    "tc": "中環碼頭",
    "sc": "中环码头",
}


def parse_central_pier_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Central Pier prevailing-wind CSV into the latest numeric day."""
    station = _CENTRAL_PIER_PREVAILING_STATIONS.get(
        lang, _CENTRAL_PIER_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_central_pier_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Central Pier prevailing wind direction is available."""
    return _unavailable("No Central Pier prevailing wind is available.", as_json=as_json)


_NEI_LAK_SHAN_PREVAILING_STATIONS = {
    "en": "Nei Lak Shan",
    "tc": "彌勒山",
    "sc": "弥勒山",
}


def parse_nei_lak_shan_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Nei Lak Shan prevailing-wind CSV into the latest numeric day."""
    station = _NEI_LAK_SHAN_PREVAILING_STATIONS.get(
        lang, _NEI_LAK_SHAN_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_nei_lak_shan_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Nei Lak Shan prevailing wind direction is available."""
    return _unavailable(
        "No Nei Lak Shan prevailing wind is available.", as_json=as_json
    )


_BUOY_2_PREVAILING_STATIONS = {
    "en": "Automatic Weather Buoy No.2 (Hong Kong International Airport, West)",
    "tc": "自動氣象浮標2號 (香港國際機場西面)",
    "sc": "自动气象浮标2号 (香港国际机场西面)",
}


def parse_buoy_2_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the weather buoy No.2 prevailing-wind CSV into the latest numeric day."""
    station = _BUOY_2_PREVAILING_STATIONS.get(lang, _BUOY_2_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_2_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.2 prevailing wind direction is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) "
        "prevailing wind is available.",
        as_json=as_json,
    )


_BUOY_8_PREVAILING_STATIONS = {
    "en": "Automatic Weather Buoy No.8 (Hong Kong International Airport, East)",
    "tc": "自動氣象浮標8號 (香港國際機場東面)",
    "sc": "自动气象浮标8号 (香港国际机场东面)",
}


def parse_buoy_8_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the weather buoy No.8 prevailing-wind CSV into the latest numeric day."""
    station = _BUOY_8_PREVAILING_STATIONS.get(lang, _BUOY_8_PREVAILING_STATIONS["en"])
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_8_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.8 prevailing wind direction is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.8 (Hong Kong International Airport, East) "
        "prevailing wind is available.",
        as_json=as_json,
    )


_CHEUNG_CHAU_BEACH_PREVAILING_STATIONS = {
    "en": "Cheung Chau Beach",
    "tc": "長洲泳灘",
    "sc": "长洲泳滩",
}


def parse_cheung_chau_beach_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Cheung Chau Beach prevailing-wind CSV into the latest numeric day."""
    station = _CHEUNG_CHAU_BEACH_PREVAILING_STATIONS.get(
        lang, _CHEUNG_CHAU_BEACH_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_chau_beach_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau Beach prevailing wind direction is available."""
    return _unavailable(
        "No Cheung Chau Beach prevailing wind is available.",
        as_json=as_json,
    )


_NORTH_POINT_PREVAILING_STATIONS = {
    "en": "North Point",
    "tc": "北角",
    "sc": "北角",
}


def parse_north_point_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the North Point prevailing-wind CSV into the latest numeric day."""
    station = _NORTH_POINT_PREVAILING_STATIONS.get(
        lang, _NORTH_POINT_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_north_point_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no North Point prevailing wind direction is available."""
    return _unavailable(
        "No North Point prevailing wind is available.",
        as_json=as_json,
    )


_SHA_CHAU_PREVAILING_STATIONS = {
    "en": "Sha Chau",
    "tc": "沙洲",
    "sc": "沙洲",
}


def parse_sha_chau_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Sha Chau prevailing-wind CSV into the latest numeric day."""
    station = _SHA_CHAU_PREVAILING_STATIONS.get(
        lang, _SHA_CHAU_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_chau_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Chau prevailing wind direction is available."""
    return _unavailable(
        "No Sha Chau prevailing wind is available.",
        as_json=as_json,
    )


_STAR_FERRY_PREVAILING_STATIONS = {
    "en": "Star Ferry(Kowloon)",
    "tc": "九龍天星碼頭",
    "sc": "九龙天星码头",
}


def parse_star_ferry_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Star Ferry(Kowloon) prevailing-wind CSV into the latest numeric day."""
    station = _STAR_FERRY_PREVAILING_STATIONS.get(
        lang, _STAR_FERRY_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_star_ferry_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Star Ferry(Kowloon) prevailing wind direction is available."""
    return _unavailable(
        "No Star Ferry(Kowloon) prevailing wind is available.",
        as_json=as_json,
    )


_TUEN_MUN_GOVERNMENT_OFFICES_PREVAILING_STATIONS = {
    "en": "Tuen Mun Government Offices",
    "tc": "屯門政府合署",
    "sc": "屯门政府合署",
}


def parse_tuen_mun_government_offices_prevailing(
    text: str, lang: str = "en"
) -> PrevailingWind | None:
    """Turn the Tuen Mun Government Offices prevailing-wind CSV into the latest numeric day."""
    station = _TUEN_MUN_GOVERNMENT_OFFICES_PREVAILING_STATIONS.get(
        lang, _TUEN_MUN_GOVERNMENT_OFFICES_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tuen_mun_government_offices_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Tuen Mun Government Offices prevailing wind direction is available."""
    return _unavailable(
        "No Tuen Mun Government Offices prevailing wind is available.",
        as_json=as_json,
    )


_YI_TUNG_SHAN_PREVAILING_STATIONS = {
    "en": "Yi Tung Shan",
    "tc": "二東山",
    "sc": "二东山",
}


def parse_yi_tung_shan_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Yi Tung Shan prevailing-wind CSV into the latest numeric day."""
    station = _YI_TUNG_SHAN_PREVAILING_STATIONS.get(
        lang, _YI_TUNG_SHAN_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_yi_tung_shan_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Yi Tung Shan prevailing wind direction is available."""
    return _unavailable(
        "No Yi Tung Shan prevailing wind is available.",
        as_json=as_json,
    )


_TAP_MUN_EAST_PREVAILING_STATIONS = {
    "en": "Tap Mun East",
    "tc": "塔門東",
    "sc": "塔门东",
}


def parse_tap_mun_east_prevailing(text: str, lang: str = "en") -> PrevailingWind | None:
    """Turn the Tap Mun East prevailing-wind CSV into the latest numeric day."""
    station = _TAP_MUN_EAST_PREVAILING_STATIONS.get(
        lang, _TAP_MUN_EAST_PREVAILING_STATIONS["en"]
    )
    latest: PrevailingWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = PrevailingWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tap_mun_east_prevailing_miss(*, as_json: bool = False) -> str:
    """Say that no Tap Mun East prevailing wind direction is available."""
    return _unavailable(
        "No Tap Mun East prevailing wind is available.",
        as_json=as_json,
    )


_MEAN_WIND_STATIONS = {
    "en": "Waglan Island",
    "tc": "橫瀾島",
    "sc": "横澜岛",
}


def parse_mean_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Waglan mean-wind CSV into the latest numeric day."""
    station = _MEAN_WIND_STATIONS.get(lang, _MEAN_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_mean_wind(reading: MeanWind) -> str:
    """Render the latest daily mean wind speed at Waglan Island."""
    return (
        "Hong Kong mean wind speed\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.wind_km_h)} km/h\n"
    )


def format_mean_wind_miss(*, as_json: bool = False) -> str:
    """Say that no daily mean wind speed is available."""
    return _unavailable("No mean wind speed is available.", as_json=as_json)


_CHEUNG_WIND_STATIONS = {
    "en": "Cheung Chau",
    "tc": "長洲",
    "sc": "长洲",
}


def parse_cheung_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Cheung Chau mean-wind CSV into the latest numeric day."""
    station = _CHEUNG_WIND_STATIONS.get(lang, _CHEUNG_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau mean wind speed is available."""
    return _unavailable("No Cheung Chau mean wind speed is available.", as_json=as_json)


_LAU_FAU_WIND_STATIONS = {
    "en": "Lau Fau Shan",
    "tc": "流浮山",
    "sc": "流浮山",
}


def parse_lau_fau_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Lau Fau Shan mean-wind CSV into the latest numeric day."""
    station = _LAU_FAU_WIND_STATIONS.get(lang, _LAU_FAU_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lau_fau_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Lau Fau Shan mean wind speed is available."""
    return _unavailable("No Lau Fau Shan mean wind speed is available.", as_json=as_json)


_PENG_CHAU_WIND_STATIONS = {
    "en": "Peng Chau",
    "tc": "坪洲",
    "sc": "坪洲",
}


def parse_peng_chau_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Peng Chau mean-wind CSV into the latest numeric day."""
    station = _PENG_CHAU_WIND_STATIONS.get(lang, _PENG_CHAU_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_peng_chau_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Peng Chau mean wind speed is available."""
    return _unavailable("No Peng Chau mean wind speed is available.", as_json=as_json)


_TAI_PO_KAU_WIND_STATIONS = {
    "en": "Tai Po Kau",
    "tc": "大埔滘",
    "sc": "大埔滘",
}


def parse_tai_po_kau_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Tai Po Kau mean-wind CSV into the latest numeric day."""
    station = _TAI_PO_KAU_WIND_STATIONS.get(lang, _TAI_PO_KAU_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_po_kau_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Po Kau mean wind speed is available."""
    return _unavailable("No Tai Po Kau mean wind speed is available.", as_json=as_json)


def parse_tai_mo_to_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Tai Mo To mean-wind CSV into the latest numeric day."""
    station = _TAI_MO_TO_STATIONS.get(lang, _TAI_MO_TO_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_to_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo To mean wind speed is available."""
    return _unavailable("No Tai Mo To mean wind speed is available.", as_json=as_json)


_TAI_MO_WIND_STATIONS = {
    "en": "Tai Mo Shan",
    "tc": "大帽山",
    "sc": "大帽山",
}


def parse_tai_mo_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Tai Mo Shan mean-wind CSV into the latest numeric day."""
    station = _TAI_MO_WIND_STATIONS.get(lang, _TAI_MO_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo Shan mean wind speed is available."""
    return _unavailable(
        "No Tai Mo Shan mean wind speed is available.", as_json=as_json
    )


_TATE_WIND_STATIONS = {
    "en": "Tate's Cairn",
    "tc": "大老山",
    "sc": "大老山",
}


def parse_tate_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Tate's Cairn mean-wind CSV into the latest numeric day."""
    station = _TATE_WIND_STATIONS.get(lang, _TATE_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tate_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Tate's Cairn mean wind speed is available."""
    return _unavailable(
        "No Tate's Cairn mean wind speed is available.", as_json=as_json
    )


_SHEK_KONG_WIND_STATIONS = {
    "en": "Shek Kong",
    "tc": "石崗",
    "sc": "石岗",
}


def parse_shek_kong_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Shek Kong mean-wind CSV into the latest numeric day."""
    station = _SHEK_KONG_WIND_STATIONS.get(lang, _SHEK_KONG_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shek_kong_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Shek Kong mean wind speed is available."""
    return _unavailable(
        "No Shek Kong mean wind speed is available.", as_json=as_json
    )


_SAI_KUNG_WIND_STATIONS = {
    "en": "Sai Kung",
    "tc": "西貢",
    "sc": "西贡",
}


def parse_sai_kung_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Sai Kung mean-wind CSV into the latest numeric day."""
    station = _SAI_KUNG_WIND_STATIONS.get(lang, _SAI_KUNG_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sai_kung_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Sai Kung mean wind speed is available."""
    return _unavailable(
        "No Sai Kung mean wind speed is available.", as_json=as_json
    )


_SHA_TIN_WIND_STATIONS = {
    "en": "Sha Tin",
    "tc": "沙田",
    "sc": "沙田",
}


def parse_sha_tin_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Sha Tin mean-wind CSV into the latest numeric day."""
    station = _SHA_TIN_WIND_STATIONS.get(lang, _SHA_TIN_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_tin_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Tin mean wind speed is available."""
    return _unavailable(
        "No Sha Tin mean wind speed is available.", as_json=as_json
    )


_WONG_CHUK_HANG_WIND_STATIONS = {
    "en": "Wong Chuk Hang",
    "tc": "黃竹坑",
    "sc": "黄竹坑",
}


def parse_wong_chuk_hang_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Wong Chuk Hang mean-wind CSV into the latest numeric day."""
    station = _WONG_CHUK_HANG_WIND_STATIONS.get(lang, _WONG_CHUK_HANG_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_chuk_hang_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Wong Chuk Hang mean wind speed is available."""
    return _unavailable(
        "No Wong Chuk Hang mean wind speed is available.", as_json=as_json
    )


_PARK_WIND_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_park_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the King's Park mean-wind CSV into the latest numeric day."""
    station = _PARK_WIND_STATIONS.get(lang, _PARK_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_park_wind_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park mean wind speed is available."""
    return _unavailable(
        "No King's Park mean wind speed is available.", as_json=as_json
    )


_WETLAND_WIND_STATIONS = {
    "en": "Wetland Park",
    "tc": "濕地公園",
    "sc": "湿地公园",
}


def parse_wetland_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Wetland Park mean-wind CSV into the latest numeric day."""
    station = _WETLAND_WIND_STATIONS.get(lang, _WETLAND_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wetland_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Wetland Park mean wind speed is available."""
    return _unavailable(
        "No Wetland Park mean wind speed is available.", as_json=as_json
    )


_TSEUNG_KWAN_O_WIND_STATIONS = {
    "en": "Tseung Kwan O",
    "tc": "將軍澳",
    "sc": "将军澳",
}


def parse_tseung_kwan_o_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Tseung Kwan O mean-wind CSV into the latest numeric day."""
    station = _TSEUNG_KWAN_O_WIND_STATIONS.get(lang, _TSEUNG_KWAN_O_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tseung_kwan_o_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Tseung Kwan O mean wind speed is available."""
    return _unavailable(
        "No Tseung Kwan O mean wind speed is available.", as_json=as_json
    )


_TA_KWU_LING_WIND_STATIONS = {
    "en": "Ta Kwu Ling",
    "tc": "打鼓嶺",
    "sc": "打鼓岭",
}


def parse_ta_kwu_ling_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Ta Kwu Ling mean-wind CSV into the latest numeric day."""
    station = _TA_KWU_LING_WIND_STATIONS.get(lang, _TA_KWU_LING_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ta_kwu_ling_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Ta Kwu Ling mean wind speed is available."""
    return _unavailable(
        "No Ta Kwu Ling mean wind speed is available.", as_json=as_json
    )


_SHA_LO_WAN_WIND_STATIONS = {
    "en": "Sha Lo Wan",
    "tc": "沙螺灣",
    "sc": "沙螺湾",
}


def parse_sha_lo_wan_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Sha Lo Wan mean-wind CSV into the latest numeric day."""
    station = _SHA_LO_WAN_WIND_STATIONS.get(lang, _SHA_LO_WAN_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_lo_wan_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Lo Wan mean wind speed is available."""
    return _unavailable(
        "No Sha Lo Wan mean wind speed is available.", as_json=as_json
    )


_PING_CHAU_WIND_STATIONS = {
    "en": "Ping Chau",
    "tc": "平洲",
    "sc": "平洲",
}


def parse_ping_chau_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Ping Chau mean-wind CSV into the latest numeric day."""
    station = _PING_CHAU_WIND_STATIONS.get(lang, _PING_CHAU_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ping_chau_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Ping Chau mean wind speed is available."""
    return _unavailable(
        "No Ping Chau mean wind speed is available.", as_json=as_json
    )


_AIRPORT_WIND_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_airport_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the airport mean-wind CSV into the latest numeric day."""
    station = _AIRPORT_WIND_STATIONS.get(lang, _AIRPORT_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_airport_wind_miss(*, as_json: bool = False) -> str:
    """Say that no airport mean wind speed is available."""
    return _unavailable("No airport mean wind speed is available.", as_json=as_json)


_GREEN_ISLAND_WIND_STATIONS = {
    "en": "Green Island",
    "tc": "青洲",
    "sc": "青洲",
}


def parse_green_island_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Green Island mean-wind CSV into the latest numeric day."""
    station = _GREEN_ISLAND_WIND_STATIONS.get(
        lang, _GREEN_ISLAND_WIND_STATIONS["en"]
    )
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_green_island_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Green Island mean wind speed is available."""
    return _unavailable(
        "No Green Island mean wind speed is available.", as_json=as_json
    )


_NGONG_PING_WIND_STATIONS = {
    "en": "Ngong Ping",
    "tc": "昂坪",
    "sc": "昂坪",
}


def parse_ngong_ping_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Ngong Ping mean-wind CSV into the latest numeric day."""
    station = _NGONG_PING_WIND_STATIONS.get(lang, _NGONG_PING_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ngong_ping_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Ngong Ping mean wind speed is available."""
    return _unavailable(
        "No Ngong Ping mean wind speed is available.", as_json=as_json
    )


_TAI_MEI_TUK_WIND_STATIONS = {
    "en": "Tai Mei Tuk",
    "tc": "大美督",
    "sc": "大美督",
}


def parse_tai_mei_tuk_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Tai Mei Tuk mean-wind CSV into the latest numeric day."""
    station = _TAI_MEI_TUK_WIND_STATIONS.get(lang, _TAI_MEI_TUK_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mei_tuk_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mei Tuk mean wind speed is available."""
    return _unavailable("No Tai Mei Tuk mean wind speed is available.", as_json=as_json)


_LAMMA_ISLAND_WIND_STATIONS = {
    "en": "Lamma Island",
    "tc": "南丫島",
    "sc": "南丫岛",
}


def parse_lamma_island_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Lamma Island mean-wind CSV into the latest numeric day."""
    station = _LAMMA_ISLAND_WIND_STATIONS.get(lang, _LAMMA_ISLAND_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lamma_island_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Lamma Island mean wind speed is available."""
    return _unavailable("No Lamma Island mean wind speed is available.", as_json=as_json)


_KAI_TAK_WIND_STATIONS = {
    "en": "Kai Tak",
    "tc": "啟德",
    "sc": "启德",
}


def parse_kai_tak_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Kai Tak mean-wind CSV into the latest numeric day."""
    station = _KAI_TAK_WIND_STATIONS.get(lang, _KAI_TAK_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kai_tak_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Kai Tak mean wind speed is available."""
    return _unavailable("No Kai Tak mean wind speed is available.", as_json=as_json)


_CENTRAL_PIER_WIND_STATIONS = {
    "en": "Central Pier",
    "tc": "中環碼頭",
    "sc": "中环码头",
}


def parse_central_pier_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Central Pier mean-wind CSV into the latest numeric day."""
    station = _CENTRAL_PIER_WIND_STATIONS.get(lang, _CENTRAL_PIER_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_central_pier_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Central Pier mean wind speed is available."""
    return _unavailable("No Central Pier mean wind speed is available.", as_json=as_json)


_NEI_LAK_SHAN_WIND_STATIONS = {
    "en": "Nei Lak Shan",
    "tc": "彌勒山",
    "sc": "弥勒山",
}


def parse_nei_lak_shan_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Nei Lak Shan mean-wind CSV into the latest numeric day."""
    station = _NEI_LAK_SHAN_WIND_STATIONS.get(lang, _NEI_LAK_SHAN_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_nei_lak_shan_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Nei Lak Shan mean wind speed is available."""
    return _unavailable(
        "No Nei Lak Shan mean wind speed is available.", as_json=as_json
    )


_BUOY_2_WIND_STATIONS = {
    "en": "Automatic Weather Buoy No.2 (Hong Kong International Airport, West)",
    "tc": "自動氣象浮標2號 (香港國際機場西面)",
    "sc": "自动气象浮标2号 (香港国际机场西面)",
}


def parse_buoy_2_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the weather buoy No.2 mean-wind CSV into the latest numeric day."""
    station = _BUOY_2_WIND_STATIONS.get(lang, _BUOY_2_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_2_wind_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.2 mean wind speed is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) "
        "mean wind speed is available.",
        as_json=as_json,
    )


_BUOY_8_WIND_STATIONS = {
    "en": "Automatic Weather Buoy No.8 (Hong Kong International Airport, East)",
    "tc": "自動氣象浮標8號 (香港國際機場東面)",
    "sc": "自动气象浮标8号 (香港国际机场东面)",
}


def parse_buoy_8_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the weather buoy No.8 mean-wind CSV into the latest numeric day."""
    station = _BUOY_8_WIND_STATIONS.get(lang, _BUOY_8_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_8_wind_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.8 mean wind speed is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.8 (Hong Kong International Airport, East) "
        "mean wind speed is available.",
        as_json=as_json,
    )


_CHEUNG_CHAU_BEACH_WIND_STATIONS = {
    "en": "Cheung Chau Beach",
    "tc": "長洲泳灘",
    "sc": "长洲泳滩",
}


def parse_cheung_chau_beach_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Cheung Chau Beach mean-wind CSV into the latest numeric day."""
    station = _CHEUNG_CHAU_BEACH_WIND_STATIONS.get(
        lang, _CHEUNG_CHAU_BEACH_WIND_STATIONS["en"]
    )
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_chau_beach_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau Beach mean wind speed is available."""
    return _unavailable(
        "No Cheung Chau Beach mean wind speed is available.",
        as_json=as_json,
    )


_NORTH_POINT_WIND_STATIONS = {
    "en": "North Point",
    "tc": "北角",
    "sc": "北角",
}


def parse_north_point_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the North Point mean-wind CSV into the latest numeric day."""
    station = _NORTH_POINT_WIND_STATIONS.get(lang, _NORTH_POINT_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_north_point_wind_miss(*, as_json: bool = False) -> str:
    """Say that no North Point mean wind speed is available."""
    return _unavailable(
        "No North Point mean wind speed is available.",
        as_json=as_json,
    )


_SHA_CHAU_WIND_STATIONS = {
    "en": "Sha Chau",
    "tc": "沙洲",
    "sc": "沙洲",
}


def parse_sha_chau_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Sha Chau mean-wind CSV into the latest numeric day."""
    station = _SHA_CHAU_WIND_STATIONS.get(lang, _SHA_CHAU_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_chau_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Chau mean wind speed is available."""
    return _unavailable(
        "No Sha Chau mean wind speed is available.",
        as_json=as_json,
    )


_STAR_FERRY_WIND_STATIONS = {
    "en": "Star Ferry(Kowloon)",
    "tc": "九龍天星碼頭",
    "sc": "九龙天星码头",
}


def parse_star_ferry_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Star Ferry(Kowloon) mean-wind CSV into the latest numeric day."""
    station = _STAR_FERRY_WIND_STATIONS.get(lang, _STAR_FERRY_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_star_ferry_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Star Ferry(Kowloon) mean wind speed is available."""
    return _unavailable(
        "No Star Ferry(Kowloon) mean wind speed is available.",
        as_json=as_json,
    )


_TUEN_MUN_GOVERNMENT_OFFICES_WIND_STATIONS = {
    "en": "Tuen Mun Government Offices",
    "tc": "屯門政府合署",
    "sc": "屯门政府合署",
}


def parse_tuen_mun_government_offices_wind(
    text: str, lang: str = "en"
) -> MeanWind | None:
    """Turn the Tuen Mun Government Offices mean-wind CSV into the latest numeric day."""
    station = _TUEN_MUN_GOVERNMENT_OFFICES_WIND_STATIONS.get(
        lang, _TUEN_MUN_GOVERNMENT_OFFICES_WIND_STATIONS["en"]
    )
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tuen_mun_government_offices_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Tuen Mun Government Offices mean wind speed is available."""
    return _unavailable(
        "No Tuen Mun Government Offices mean wind speed is available.",
        as_json=as_json,
    )


_YI_TUNG_SHAN_WIND_STATIONS = {
    "en": "Yi Tung Shan",
    "tc": "二東山",
    "sc": "二东山",
}


def parse_yi_tung_shan_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Yi Tung Shan mean-wind CSV into the latest numeric day."""
    station = _YI_TUNG_SHAN_WIND_STATIONS.get(lang, _YI_TUNG_SHAN_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_yi_tung_shan_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Yi Tung Shan mean wind speed is available."""
    return _unavailable(
        "No Yi Tung Shan mean wind speed is available.",
        as_json=as_json,
    )


_TAP_MUN_EAST_WIND_STATIONS = {
    "en": "Tap Mun East",
    "tc": "塔門東",
    "sc": "塔门东",
}


def parse_tap_mun_east_wind(text: str, lang: str = "en") -> MeanWind | None:
    """Turn the Tap Mun East mean-wind CSV into the latest numeric day."""
    station = _TAP_MUN_EAST_WIND_STATIONS.get(lang, _TAP_MUN_EAST_WIND_STATIONS["en"])
    latest: MeanWind | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanWind(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tap_mun_east_wind_miss(*, as_json: bool = False) -> str:
    """Say that no Tap Mun East mean wind speed is available."""
    return _unavailable(
        "No Tap Mun East mean wind speed is available.",
        as_json=as_json,
    )


def parse_minute_temp(text: str) -> MinuteTempReport:
    """Turn the regional 1-minute temperature CSV into one row per station."""
    stations: list[MinuteTempReading] = []
    obs_time = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 3:
            continue
        place = _text(row[1])
        temperature = _hour_mm(row[2])
        if not place or temperature is None:
            continue
        clock = _text(row[0])
        if not obs_time and len(clock) == 12 and clock.isdigit():
            obs_time = f"{clock[:4]}-{clock[4:6]}-{clock[6:8]} {clock[8:10]}:{clock[10:12]}"
        stations.append(MinuteTempReading(place, temperature))
    return MinuteTempReport(obs_time, tuple(stations))


def format_minute_temp(report: MinuteTempReport) -> str:
    """Render the latest 1-minute mean temperature, one station per line."""
    lines = ["Hong Kong 1-minute temperature"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        lines.append(f"{reading.place}  {_number(reading.temperature_c)}°C")
    return "\n".join(lines) + "\n"


def format_minute_temp_miss(*, as_json: bool = False) -> str:
    """Say that no 1-minute temperatures are available."""
    return _unavailable("No 1-minute temperatures are available.", as_json=as_json)


def parse_minute_humidity(text: str) -> MinuteHumidityReport:
    """Turn the regional 1-minute humidity CSV into one row per station."""
    stations: list[MinuteHumidityReading] = []
    obs_time = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 3:
            continue
        place = _text(row[1])
        humidity = _hour_mm(row[2])
        if not place or humidity is None:
            continue
        clock = _text(row[0])
        if not obs_time and len(clock) == 12 and clock.isdigit():
            obs_time = f"{clock[:4]}-{clock[4:6]}-{clock[6:8]} {clock[8:10]}:{clock[10:12]}"
        stations.append(MinuteHumidityReading(place, humidity))
    return MinuteHumidityReport(obs_time, tuple(stations))


def format_minute_humidity(report: MinuteHumidityReport) -> str:
    """Render the latest 1-minute mean humidity, one station per line."""
    lines = ["Hong Kong 1-minute humidity"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        lines.append(f"{reading.place}  {_number(reading.humidity_percent)}%")
    return "\n".join(lines) + "\n"


def format_minute_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no 1-minute humidity readings are available."""
    return _unavailable("No 1-minute humidity readings are available.", as_json=as_json)


_MEAN_HUMIDITY_STATIONS = {
    "en": "Hong Kong Observatory",
    "tc": "香港天文台",
    "sc": "香港天文台",
}


def parse_mean_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Observatory humidity CSV into the latest numeric day."""
    station = _MEAN_HUMIDITY_STATIONS.get(lang, _MEAN_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_mean_humidity(reading: MeanHumidity) -> str:
    """Render the latest daily mean humidity at the Observatory."""
    return (
        "Hong Kong daily mean humidity\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.humidity_percent)}%\n"
    )


def format_mean_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no daily mean humidity is available."""
    return _unavailable("No daily mean humidity is available.", as_json=as_json)


_TAI_MO_HUMIDITY_STATIONS = {
    "en": "Tai Mo Shan",
    "tc": "大帽山",
    "sc": "大帽山",
}


def parse_tai_mo_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Tai Mo Shan humidity CSV into the latest numeric day."""
    station = _TAI_MO_HUMIDITY_STATIONS.get(lang, _TAI_MO_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo Shan humidity is available."""
    return _unavailable("No Tai Mo Shan humidity is available.", as_json=as_json)


_WAGLAN_HUMIDITY_STATIONS = {
    "en": "Waglan Island",
    "tc": "橫瀾島",
    "sc": "横澜岛",
}


def parse_waglan_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Waglan Island humidity CSV into the latest numeric day."""
    station = _WAGLAN_HUMIDITY_STATIONS.get(lang, _WAGLAN_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_waglan_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Waglan Island humidity is available."""
    return _unavailable("No Waglan Island humidity is available.", as_json=as_json)


_TATE_HUMIDITY_STATIONS = {
    "en": "Tate's Cairn",
    "tc": "大老山",
    "sc": "大老山",
}


def parse_tate_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Tate's Cairn humidity CSV into the latest numeric day."""
    station = _TATE_HUMIDITY_STATIONS.get(lang, _TATE_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tate_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Tate's Cairn humidity is available."""
    return _unavailable("No Tate's Cairn humidity is available.", as_json=as_json)


_TA_KWU_LING_STATIONS = {
    "en": "Ta Kwu Ling",
    "tc": "打鼓嶺",
    "sc": "打鼓岭",
}


def parse_ta_kwu_ling_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Ta Kwu Ling humidity CSV into the latest numeric day."""
    station = _TA_KWU_LING_STATIONS.get(lang, _TA_KWU_LING_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ta_kwu_ling_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Ta Kwu Ling humidity is available."""
    return _unavailable("No Ta Kwu Ling humidity is available.", as_json=as_json)


_WETLAND_HUMIDITY_STATIONS = {
    "en": "Wetland Park",
    "tc": "濕地公園",
    "sc": "湿地公园",
}


def parse_wetland_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Wetland Park humidity CSV into the latest numeric day."""
    station = _WETLAND_HUMIDITY_STATIONS.get(lang, _WETLAND_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wetland_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Wetland Park humidity is available."""
    return _unavailable("No Wetland Park humidity is available.", as_json=as_json)


_SHEK_KONG_HUMIDITY_STATIONS = {
    "en": "Shek Kong",
    "tc": "石崗",
    "sc": "石岗",
}


def parse_shek_kong_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Shek Kong humidity CSV into the latest numeric day."""
    station = _SHEK_KONG_HUMIDITY_STATIONS.get(lang, _SHEK_KONG_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shek_kong_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Shek Kong humidity is available."""
    return _unavailable("No Shek Kong humidity is available.", as_json=as_json)


_LAU_FAU_HUMIDITY_STATIONS = {
    "en": "Lau Fau Shan",
    "tc": "流浮山",
    "sc": "流浮山",
}


def parse_lau_fau_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Lau Fau Shan humidity CSV into the latest numeric day."""
    station = _LAU_FAU_HUMIDITY_STATIONS.get(lang, _LAU_FAU_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lau_fau_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Lau Fau Shan humidity is available."""
    return _unavailable("No Lau Fau Shan humidity is available.", as_json=as_json)


_PARK_HUMIDITY_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_park_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the King's Park humidity CSV into the latest numeric day."""
    station = _PARK_HUMIDITY_STATIONS.get(lang, _PARK_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_park_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park humidity is available."""
    return _unavailable("No King's Park humidity is available.", as_json=as_json)


_SAI_KUNG_HUMIDITY_STATIONS = {
    "en": "Sai Kung",
    "tc": "西貢",
    "sc": "西贡",
}


def parse_sai_kung_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Sai Kung humidity CSV into the latest numeric day."""
    station = _SAI_KUNG_HUMIDITY_STATIONS.get(lang, _SAI_KUNG_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sai_kung_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Sai Kung humidity is available."""
    return _unavailable("No Sai Kung humidity is available.", as_json=as_json)


_CHEUNG_HUMIDITY_STATIONS = {
    "en": "Cheung Chau",
    "tc": "長洲",
    "sc": "长洲",
}


def parse_cheung_chau_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Cheung Chau humidity CSV into the latest numeric day."""
    station = _CHEUNG_HUMIDITY_STATIONS.get(lang, _CHEUNG_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_chau_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau humidity is available."""
    return _unavailable("No Cheung Chau humidity is available.", as_json=as_json)


_SHA_TIN_HUMIDITY_STATIONS = {
    "en": "Sha Tin",
    "tc": "沙田",
    "sc": "沙田",
}


def parse_sha_tin_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Sha Tin humidity CSV into the latest numeric day."""
    station = _SHA_TIN_HUMIDITY_STATIONS.get(lang, _SHA_TIN_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_tin_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Tin humidity is available."""
    return _unavailable("No Sha Tin humidity is available.", as_json=as_json)


_SHEUNG_SHUI_HUMIDITY_STATIONS = {
    "en": "Sheung Shui",
    "tc": "上水",
    "sc": "上水",
}


def parse_sheung_shui_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Sheung Shui humidity CSV into the latest numeric day."""
    station = _SHEUNG_SHUI_HUMIDITY_STATIONS.get(lang, _SHEUNG_SHUI_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sheung_shui_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Sheung Shui humidity is available."""
    return _unavailable("No Sheung Shui humidity is available.", as_json=as_json)


_WONG_CHUK_HANG_HUMIDITY_STATIONS = {
    "en": "Wong Chuk Hang",
    "tc": "黃竹坑",
    "sc": "黄竹坑",
}


def parse_wong_chuk_hang_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Wong Chuk Hang humidity CSV into the latest numeric day."""
    station = _WONG_CHUK_HANG_HUMIDITY_STATIONS.get(lang, _WONG_CHUK_HANG_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_chuk_hang_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Wong Chuk Hang humidity is available."""
    return _unavailable("No Wong Chuk Hang humidity is available.", as_json=as_json)


_TSEUNG_KWAN_O_HUMIDITY_STATIONS = {
    "en": "Tseung Kwan O",
    "tc": "將軍澳",
    "sc": "将军澳",
}


def parse_tseung_kwan_o_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Tseung Kwan O humidity CSV into the latest numeric day."""
    station = _TSEUNG_KWAN_O_HUMIDITY_STATIONS.get(
        lang, _TSEUNG_KWAN_O_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tseung_kwan_o_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Tseung Kwan O humidity is available."""
    return _unavailable(
        "No Tseung Kwan O humidity is available.", as_json=as_json
    )


_PENG_CHAU_HUMIDITY_STATIONS = {
    "en": "Peng Chau",
    "tc": "坪洲",
    "sc": "坪洲",
}


def parse_peng_chau_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Peng Chau humidity CSV into the latest numeric day."""
    station = _PENG_CHAU_HUMIDITY_STATIONS.get(lang, _PENG_CHAU_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_peng_chau_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Peng Chau humidity is available."""
    return _unavailable("No Peng Chau humidity is available.", as_json=as_json)


_SHA_LO_WAN_HUMIDITY_STATIONS = {
    "en": "Sha Lo Wan",
    "tc": "沙螺灣",
    "sc": "沙螺湾",
}


def parse_sha_lo_wan_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Sha Lo Wan humidity CSV into the latest numeric day."""
    station = _SHA_LO_WAN_HUMIDITY_STATIONS.get(lang, _SHA_LO_WAN_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_lo_wan_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Lo Wan humidity is available."""
    return _unavailable("No Sha Lo Wan humidity is available.", as_json=as_json)


_AIRPORT_HUMIDITY_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_airport_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the airport humidity CSV into the latest numeric day."""
    station = _AIRPORT_HUMIDITY_STATIONS.get(lang, _AIRPORT_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_airport_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no airport humidity is available."""
    return _unavailable("No airport humidity is available.", as_json=as_json)


_TSUEN_WAN_HUMIDITY_STATIONS = {
    "en": "Tsuen Wan",
    "tc": "荃灣",
    "sc": "荃湾",
}


def parse_tsuen_wan_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Tsuen Wan humidity CSV into the latest numeric day."""
    station = _TSUEN_WAN_HUMIDITY_STATIONS.get(
        lang, _TSUEN_WAN_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tsuen_wan_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan humidity is available."""
    return _unavailable("No Tsuen Wan humidity is available.", as_json=as_json)


_HONG_KONG_PARK_HUMIDITY_STATIONS = {
    "en": "Hong Kong Park",
    "tc": "香港公園",
    "sc": "香港公园",
}


def parse_hong_kong_park_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Hong Kong Park humidity CSV into the latest numeric day."""
    station = _HONG_KONG_PARK_HUMIDITY_STATIONS.get(
        lang, _HONG_KONG_PARK_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_hong_kong_park_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Hong Kong Park humidity is available."""
    return _unavailable("No Hong Kong Park humidity is available.", as_json=as_json)


_CLEAR_WATER_BAY_HUMIDITY_STATIONS = {
    "en": "Clear Water Bay",
    "tc": "清水灣",
    "sc": "清水湾",
}


def parse_clear_water_bay_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Clear Water Bay humidity CSV into the latest numeric day."""
    station = _CLEAR_WATER_BAY_HUMIDITY_STATIONS.get(
        lang, _CLEAR_WATER_BAY_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_clear_water_bay_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Clear Water Bay humidity is available."""
    return _unavailable("No Clear Water Bay humidity is available.", as_json=as_json)


_SHAU_KEI_WAN_HUMIDITY_STATIONS = {
    "en": "Shau Kei Wan",
    "tc": "筲箕灣",
    "sc": "筲箕湾",
}


def parse_shau_kei_wan_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Shau Kei Wan humidity CSV into the latest numeric day."""
    station = _SHAU_KEI_WAN_HUMIDITY_STATIONS.get(
        lang, _SHAU_KEI_WAN_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shau_kei_wan_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Shau Kei Wan humidity is available."""
    return _unavailable("No Shau Kei Wan humidity is available.", as_json=as_json)


_KAU_SAI_CHAU_HUMIDITY_STATIONS = {
    "en": "Kau Sai Chau",
    "tc": "滘西洲",
    "sc": "滘西洲",
}


def parse_kau_sai_chau_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Kau Sai Chau humidity CSV into the latest numeric day."""
    station = _KAU_SAI_CHAU_HUMIDITY_STATIONS.get(
        lang, _KAU_SAI_CHAU_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kau_sai_chau_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Kau Sai Chau humidity is available."""
    return _unavailable("No Kau Sai Chau humidity is available.", as_json=as_json)


_PAK_TAM_CHUNG_HUMIDITY_STATIONS = {
    "en": "Pak Tam Chung (Tsak Yue Wu)",
    "tc": "北潭涌(鯽魚湖)",
    "sc": "北潭涌(鲫鱼湖)",
}


def parse_pak_tam_chung_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Pak Tam Chung humidity CSV into the latest numeric day."""
    station = _PAK_TAM_CHUNG_HUMIDITY_STATIONS.get(
        lang, _PAK_TAM_CHUNG_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_pak_tam_chung_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Pak Tam Chung (Tsak Yue Wu) humidity is available."""
    return _unavailable(
        "No Pak Tam Chung (Tsak Yue Wu) humidity is available.",
        as_json=as_json,
    )


_BEAS_RIVER_HUMIDITY_STATIONS = {
    "en": "Beas River",
    "tc": "上水雙魚河",
    "sc": "上水双鱼河",
}


def parse_beas_river_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Beas River humidity CSV into the latest numeric day."""
    station = _BEAS_RIVER_HUMIDITY_STATIONS.get(lang, _BEAS_RIVER_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_beas_river_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Beas River humidity is available."""
    return _unavailable("No Beas River humidity is available.", as_json=as_json)


_RUNWAY_PARK_HUMIDITY_STATIONS = {
    "en": "Kai Tak Runway Park",
    "tc": "啟德跑道公園",
    "sc": "启德跑道公园",
}


def parse_runway_park_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Kai Tak Runway Park humidity CSV into the latest numeric day."""
    station = _RUNWAY_PARK_HUMIDITY_STATIONS.get(
        lang, _RUNWAY_PARK_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_runway_park_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Kai Tak Runway Park humidity is available."""
    return _unavailable(
        "No Kai Tak Runway Park humidity is available.", as_json=as_json
    )


_KOWLOON_CITY_HUMIDITY_STATIONS = {
    "en": "Kowloon City",
    "tc": "九龍城",
    "sc": "九龙城",
}


def parse_kowloon_city_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Kowloon City humidity CSV into the latest numeric day."""
    station = _KOWLOON_CITY_HUMIDITY_STATIONS.get(
        lang, _KOWLOON_CITY_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kowloon_city_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Kowloon City humidity is available."""
    return _unavailable("No Kowloon City humidity is available.", as_json=as_json)


_NEI_LAK_SHAN_HUMIDITY_STATIONS = {
    "en": "Nei Lak Shan",
    "tc": "彌勒山",
    "sc": "弥勒山",
}


def parse_nei_lak_shan_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Nei Lak Shan humidity CSV into the latest numeric day."""
    station = _NEI_LAK_SHAN_HUMIDITY_STATIONS.get(
        lang, _NEI_LAK_SHAN_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_nei_lak_shan_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Nei Lak Shan humidity is available."""
    return _unavailable("No Nei Lak Shan humidity is available.", as_json=as_json)


_NEW_TSING_YI_HUMIDITY_STATIONS = {
    "en": "New Tsing Yi Station",
    "tc": "新青衣站",
    "sc": "新青衣站",
}


def parse_new_tsing_yi_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the New Tsing Yi Station humidity CSV into the latest numeric day."""
    station = _NEW_TSING_YI_HUMIDITY_STATIONS.get(
        lang, _NEW_TSING_YI_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_new_tsing_yi_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no New Tsing Yi Station humidity is available."""
    return _unavailable(
        "No New Tsing Yi Station humidity is available.", as_json=as_json
    )


_SHING_MUN_VALLEY_HUMIDITY_STATIONS = {
    "en": "Tsuen Wan Shing Mun Valley",
    "tc": "荃灣城門谷",
    "sc": "荃湾城门谷",
}


def parse_shing_mun_valley_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Tsuen Wan Shing Mun Valley humidity CSV into the latest numeric day."""
    station = _SHING_MUN_VALLEY_HUMIDITY_STATIONS.get(
        lang, _SHING_MUN_VALLEY_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shing_mun_valley_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan Shing Mun Valley humidity is available."""
    return _unavailable(
        "No Tsuen Wan Shing Mun Valley humidity is available.", as_json=as_json
    )


_TUEN_MUN_HOME_HUMIDITY_STATIONS = {
    "en": "Tuen Mun Children and Juvenile Home",
    "tc": "屯門兒童及青少年院",
    "sc": "屯门儿童及青少年院",
}


def parse_tuen_mun_home_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the Tuen Mun Children and Juvenile Home humidity CSV into the latest numeric day."""
    station = _TUEN_MUN_HOME_HUMIDITY_STATIONS.get(
        lang, _TUEN_MUN_HOME_HUMIDITY_STATIONS["en"]
    )
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tuen_mun_home_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no Tuen Mun Children and Juvenile Home humidity is available."""
    return _unavailable(
        "No Tuen Mun Children and Juvenile Home humidity is available.",
        as_json=as_json,
    )


_BUOY_2_HUMIDITY_STATIONS = {
    "en": "Automatic Weather Buoy No.2 (Hong Kong International Airport, West)",
    "tc": "自動氣象浮標2號 (香港國際機場西面)",
    "sc": "自动气象浮标2号 (香港国际机场西面)",
}


def parse_buoy_2_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the weather buoy No.2 humidity CSV into the latest numeric day."""
    station = _BUOY_2_HUMIDITY_STATIONS.get(lang, _BUOY_2_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_2_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.2 humidity is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) "
        "humidity is available.",
        as_json=as_json,
    )


_BUOY_8_HUMIDITY_STATIONS = {
    "en": "Automatic Weather Buoy No.8 (Hong Kong International Airport, East)",
    "tc": "自動氣象浮標8號 (香港國際機場東面)",
    "sc": "自动气象浮标8号 (香港国际机场东面)",
}


def parse_buoy_8_humidity(text: str, lang: str = "en") -> MeanHumidity | None:
    """Turn the weather buoy No.8 humidity CSV into the latest numeric day."""
    station = _BUOY_8_HUMIDITY_STATIONS.get(lang, _BUOY_8_HUMIDITY_STATIONS["en"])
    latest: MeanHumidity | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanHumidity(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_8_humidity_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.8 humidity is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.8 (Hong Kong International Airport, East) "
        "humidity is available.",
        as_json=as_json,
    )


def parse_since_midnight(text: str) -> SinceMidnightReport:
    """Turn the since-midnight temperature CSV into one row per station."""
    stations: list[SinceMidnightReading] = []
    obs_time = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 4:
            continue
        place = _text(row[1])
        high = _hour_mm(row[2])
        low = _hour_mm(row[3])
        if not place or (high is None and low is None):
            continue
        clock = _text(row[0])
        if not obs_time and len(clock) == 12 and clock.isdigit():
            obs_time = f"{clock[:4]}-{clock[4:6]}-{clock[6:8]} {clock[8:10]}:{clock[10:12]}"
        stations.append(SinceMidnightReading(place, high, low))
    return SinceMidnightReport(obs_time, tuple(stations))


def format_since_midnight(report: SinceMidnightReport) -> str:
    """Render each station's high and low since midnight."""
    lines = ["Hong Kong temperature since midnight"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        parts = [reading.place]
        if reading.temp_high_c is not None:
            parts.append(f"high {_number(reading.temp_high_c)}°C")
        if reading.temp_low_c is not None:
            parts.append(f"low {_number(reading.temp_low_c)}°C")
        lines.append("  ".join(parts))
    return "\n".join(lines) + "\n"


def format_since_midnight_miss(*, as_json: bool = False) -> str:
    """Say that no temperatures since midnight are available."""
    return _unavailable("No temperatures since midnight are available.", as_json=as_json)


def _midnight_span(reading: SinceMidnightReading) -> float | None:
    """High minus low since midnight, when both readings are present."""
    if reading.temp_high_c is None or reading.temp_low_c is None:
        return None
    span = round(reading.temp_high_c - reading.temp_low_c, 1)
    if span < 0:
        return None
    return span


def format_midnight_span(report: SinceMidnightReport, *, as_json: bool) -> str:
    """Print the station with the widest temperature range since midnight."""
    if not report.stations:
        return _unavailable("No temperatures since midnight are available.", as_json=as_json)
    spans = [(reading, _midnight_span(reading)) for reading in report.stations]
    usable = [(reading, span) for reading, span in spans if span is not None]
    if not usable:
        return _unavailable("No temperature range since midnight is available.", as_json=as_json)
    peak = max(span for _, span in usable)
    winners = [(reading, span) for reading, span in usable if span == peak]

    def clause(reading: SinceMidnightReading, span: float) -> str:
        return (
            f"{reading.place}  {_number(span)}°C, "
            f"from {_number(reading.temp_low_c)}°C to {_number(reading.temp_high_c)}°C"
        )

    listed = "; ".join(clause(reading, span) for reading, span in winners)
    if report.obs_time:
        phrase = f"Widest since midnight: {report.obs_time}  {listed}"
    else:
        phrase = f"Widest since midnight: {listed}"
    if as_json:
        payload = {
            "time": report.obs_time,
            "span_c": peak,
            "places": [
                {
                    "place": reading.place,
                    "high_c": reading.temp_high_c,
                    "low_c": reading.temp_low_c,
                    "span_c": span,
                }
                for reading, span in winners
            ],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_pressure(text: str) -> PressureReport:
    """Turn the regional sea-level pressure CSV into one row per station."""
    stations: list[PressureReading] = []
    obs_time = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 3:
            continue
        place = _text(row[1])
        pressure = _hour_mm(row[2])
        if not place or pressure is None:
            continue
        clock = _text(row[0])
        if not obs_time and len(clock) == 12 and clock.isdigit():
            obs_time = f"{clock[:4]}-{clock[4:6]}-{clock[6:8]} {clock[8:10]}:{clock[10:12]}"
        stations.append(PressureReading(place, pressure))
    return PressureReport(obs_time, tuple(stations))


def format_pressure(report: PressureReport) -> str:
    """Render the latest 1-minute mean sea level pressure, one station per line."""
    lines = ["Hong Kong sea level pressure"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        lines.append(f"{reading.place}  {_number(reading.pressure_hpa)} hPa")
    return "\n".join(lines) + "\n"


def format_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no sea level pressure is available."""
    return _unavailable("No sea level pressure is available.", as_json=as_json)


def _pressure_places(places: list[str]) -> str:
    """Join station names for a shared pressure reading."""
    if len(places) == 1:
        return places[0]
    if len(places) == 2:
        return f"{places[0]} and {places[1]}"
    return ", ".join(places[:-1]) + f", and {places[-1]}"


def format_high_pressure(report: PressureReport, *, as_json: bool) -> str:
    """Print the station with the highest latest sea level pressure."""
    if not report.stations:
        return _unavailable("No sea level pressure is available.", as_json=as_json)
    peak = max(round(reading.pressure_hpa, 1) for reading in report.stations)
    winners = [
        reading
        for reading in report.stations
        if round(reading.pressure_hpa, 1) == peak
    ]
    places = _pressure_places([reading.place for reading in winners])
    height = f"{_number(peak)} hPa"
    if report.obs_time:
        phrase = f"Highest pressure: {report.obs_time}  {places}  {height}"
    else:
        phrase = f"Highest pressure: {places}  {height}"
    if as_json:
        payload = {
            "time": report.obs_time,
            "places": [reading.place for reading in winners],
            "pressure_hpa": peak,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


_MEAN_PRESSURE_STATIONS = {
    "en": "Hong Kong Observatory",
    "tc": "香港天文台",
    "sc": "香港天文台",
}


def parse_mean_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Observatory pressure CSV into the latest numeric day."""
    station = _MEAN_PRESSURE_STATIONS.get(lang, _MEAN_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_mean_pressure(reading: MeanPressure) -> str:
    """Render the latest daily mean pressure at the Observatory."""
    return (
        "Hong Kong daily mean pressure\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.pressure_hpa)} hPa\n"
    )


def format_mean_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no daily mean pressure is available."""
    return _unavailable("No daily mean pressure is available.", as_json=as_json)


_PARK_PRESSURE_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_park_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the King's Park pressure CSV into the latest numeric day."""
    station = _PARK_PRESSURE_STATIONS.get(lang, _PARK_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_park_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park pressure is available."""
    return _unavailable("No King's Park pressure is available.", as_json=as_json)


_SHA_TIN_STATIONS = {
    "en": "Sha Tin",
    "tc": "沙田",
    "sc": "沙田",
}


def parse_sha_tin_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Sha Tin pressure CSV into the latest numeric day."""
    station = _SHA_TIN_STATIONS.get(lang, _SHA_TIN_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_tin_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Tin pressure is available."""
    return _unavailable("No Sha Tin pressure is available.", as_json=as_json)


_SHEUNG_SHUI_PRESSURE_STATIONS = {
    "en": "Sheung Shui",
    "tc": "上水",
    "sc": "上水",
}


def parse_sheung_shui_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Sheung Shui pressure CSV into the latest numeric day."""
    station = _SHEUNG_SHUI_PRESSURE_STATIONS.get(lang, _SHEUNG_SHUI_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sheung_shui_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Sheung Shui pressure is available."""
    return _unavailable("No Sheung Shui pressure is available.", as_json=as_json)


_WAGLAN_PRESSURE_STATIONS = {
    "en": "Waglan Island",
    "tc": "橫瀾島",
    "sc": "横澜岛",
}


def parse_waglan_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Waglan Island pressure CSV into the latest numeric day."""
    station = _WAGLAN_PRESSURE_STATIONS.get(lang, _WAGLAN_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_waglan_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Waglan Island pressure is available."""
    return _unavailable("No Waglan Island pressure is available.", as_json=as_json)


_CHEUNG_PRESSURE_STATIONS = {
    "en": "Cheung Chau",
    "tc": "長洲",
    "sc": "长洲",
}


def parse_cheung_chau_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Cheung Chau pressure CSV into the latest numeric day."""
    station = _CHEUNG_PRESSURE_STATIONS.get(lang, _CHEUNG_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_chau_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau pressure is available."""
    return _unavailable("No Cheung Chau pressure is available.", as_json=as_json)


_LAU_FAU_PRESSURE_STATIONS = {
    "en": "Lau Fau Shan",
    "tc": "流浮山",
    "sc": "流浮山",
}


def parse_lau_fau_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Lau Fau Shan pressure CSV into the latest numeric day."""
    station = _LAU_FAU_PRESSURE_STATIONS.get(lang, _LAU_FAU_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lau_fau_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Lau Fau Shan pressure is available."""
    return _unavailable("No Lau Fau Shan pressure is available.", as_json=as_json)


_TATE_PRESSURE_STATIONS = {
    "en": "Tate's Cairn",
    "tc": "大老山",
    "sc": "大老山",
}


def parse_tate_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Tate's Cairn pressure CSV into the latest numeric day."""
    station = _TATE_PRESSURE_STATIONS.get(lang, _TATE_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tate_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Tate's Cairn pressure is available."""
    return _unavailable("No Tate's Cairn pressure is available.", as_json=as_json)


_WETLAND_PRESSURE_STATIONS = {
    "en": "Wetland Park",
    "tc": "濕地公園",
    "sc": "湿地公园",
}


def parse_wetland_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Wetland Park pressure CSV into the latest numeric day."""
    station = _WETLAND_PRESSURE_STATIONS.get(lang, _WETLAND_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wetland_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Wetland Park pressure is available."""
    return _unavailable("No Wetland Park pressure is available.", as_json=as_json)


_PENG_CHAU_PRESSURE_STATIONS = {
    "en": "Peng Chau",
    "tc": "坪洲",
    "sc": "坪洲",
}


def parse_peng_chau_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Peng Chau pressure CSV into the latest numeric day."""
    station = _PENG_CHAU_PRESSURE_STATIONS.get(lang, _PENG_CHAU_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_peng_chau_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Peng Chau pressure is available."""
    return _unavailable("No Peng Chau pressure is available.", as_json=as_json)


_TAI_MO_PRESSURE_STATIONS = {
    "en": "Tai Mo Shan",
    "tc": "大帽山",
    "sc": "大帽山",
}


def parse_tai_mo_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Tai Mo Shan pressure CSV into the latest numeric day."""
    station = _TAI_MO_PRESSURE_STATIONS.get(lang, _TAI_MO_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo Shan pressure is available."""
    return _unavailable("No Tai Mo Shan pressure is available.", as_json=as_json)


_SHA_LO_WAN_PRESSURE_STATIONS = {
    "en": "Sha Lo Wan",
    "tc": "沙螺灣",
    "sc": "沙螺湾",
}


def parse_sha_lo_wan_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Sha Lo Wan pressure CSV into the latest numeric day."""
    station = _SHA_LO_WAN_PRESSURE_STATIONS.get(lang, _SHA_LO_WAN_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_lo_wan_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Lo Wan pressure is available."""
    return _unavailable("No Sha Lo Wan pressure is available.", as_json=as_json)


_SHEK_KONG_PRESSURE_STATIONS = {
    "en": "Shek Kong",
    "tc": "石崗",
    "sc": "石岗",
}


def parse_shek_kong_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Shek Kong pressure CSV into the latest numeric day."""
    station = _SHEK_KONG_PRESSURE_STATIONS.get(lang, _SHEK_KONG_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shek_kong_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Shek Kong pressure is available."""
    return _unavailable("No Shek Kong pressure is available.", as_json=as_json)


_TA_KWU_LING_PRESSURE_STATIONS = {
    "en": "Ta Kwu Ling",
    "tc": "打鼓嶺",
    "sc": "打鼓岭",
}


def parse_ta_kwu_ling_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Ta Kwu Ling pressure CSV into the latest numeric day."""
    station = _TA_KWU_LING_PRESSURE_STATIONS.get(
        lang, _TA_KWU_LING_PRESSURE_STATIONS["en"]
    )
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ta_kwu_ling_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Ta Kwu Ling pressure is available."""
    return _unavailable("No Ta Kwu Ling pressure is available.", as_json=as_json)


_AIRPORT_PRESSURE_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_airport_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the airport pressure CSV into the latest numeric day."""
    station = _AIRPORT_PRESSURE_STATIONS.get(lang, _AIRPORT_PRESSURE_STATIONS["en"])
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_airport_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no airport pressure is available."""
    return _unavailable("No airport pressure is available.", as_json=as_json)


_NEI_LAK_SHAN_PRESSURE_STATIONS = {
    "en": "Nei Lak Shan",
    "tc": "彌勒山",
    "sc": "弥勒山",
}


def parse_nei_lak_shan_pressure(text: str, lang: str = "en") -> MeanPressure | None:
    """Turn the Nei Lak Shan pressure CSV into the latest numeric day."""
    station = _NEI_LAK_SHAN_PRESSURE_STATIONS.get(
        lang, _NEI_LAK_SHAN_PRESSURE_STATIONS["en"]
    )
    latest: MeanPressure | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanPressure(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_nei_lak_shan_pressure_miss(*, as_json: bool = False) -> str:
    """Say that no Nei Lak Shan pressure is available."""
    return _unavailable("No Nei Lak Shan pressure is available.", as_json=as_json)


def parse_minute_grass(text: str) -> MinuteGrassReport:
    """Turn the regional grass-temperature CSV into one row per station."""
    stations: list[MinuteGrassReading] = []
    obs_time = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 3:
            continue
        place = _text(row[1])
        grass = _hour_mm(row[2])
        if not place or grass is None:
            continue
        clock = _text(row[0])
        if not obs_time and len(clock) == 12 and clock.isdigit():
            obs_time = f"{clock[:4]}-{clock[4:6]}-{clock[6:8]} {clock[8:10]}:{clock[10:12]}"
        stations.append(MinuteGrassReading(place, grass))
    return MinuteGrassReport(obs_time, tuple(stations))


def format_minute_grass(report: MinuteGrassReport) -> str:
    """Render the latest 1-minute mean grass temperature, one station per line."""
    lines = ["Hong Kong 1-minute grass temperature"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        lines.append(f"{reading.place}  {_number(reading.grass_c)}°C")
    return "\n".join(lines) + "\n"


def format_minute_grass_miss(*, as_json: bool = False) -> str:
    """Say that no 1-minute grass temperatures are available."""
    return _unavailable("No 1-minute grass temperatures are available.", as_json=as_json)


_DAILY_GRASS_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_daily_grass(text: str, lang: str = "en") -> DailyGrass | None:
    """Turn the King's Park grass-temperature CSV into the latest numeric day."""
    station = _DAILY_GRASS_STATIONS.get(lang, _DAILY_GRASS_STATIONS["en"])
    latest: DailyGrass | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyGrass(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_daily_grass(reading: DailyGrass) -> str:
    """Render the latest daily grass minimum at King's Park."""
    return (
        "Hong Kong daily grass temperature\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.grass_c)}°C\n"
    )


def format_daily_grass_miss(*, as_json: bool = False) -> str:
    """Say that no daily grass minimum is available."""
    return _unavailable("No daily grass temperature is available.", as_json=as_json)


_OBS_GRASS_STATIONS = {
    "en": "Hong Kong Observatory",
    "tc": "香港天文台",
    "sc": "香港天文台",
}


def parse_obs_grass(text: str, lang: str = "en") -> DailyGrass | None:
    """Turn the Observatory grass-temperature CSV into the latest numeric day."""
    station = _OBS_GRASS_STATIONS.get(lang, _OBS_GRASS_STATIONS["en"])
    latest: DailyGrass | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyGrass(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_obs_grass_miss(*, as_json: bool = False) -> str:
    """Say that no Observatory grass minimum is available."""
    return _unavailable("No Observatory grass temperature is available.", as_json=as_json)


def _signed_change(value: str) -> float | None:
    """Parse a temperature change such as `+0.4`, `-0.6`, or `N/A`."""
    text = value.strip()
    sign = 1.0
    if text.startswith(("+", "-")):
        sign = -1.0 if text.startswith("-") else 1.0
        text = text[1:]
    number = _hour_mm(text)
    if number is None:
        return None
    return sign * number


def parse_temp_diff(text: str) -> TempDiffReport:
    """Turn the past-24-hour temperature-difference CSV into one row per station."""
    stations: list[TempDiffReading] = []
    obs_time = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 3:
            continue
        place = _text(row[1])
        change = _signed_change(row[2]) if isinstance(row[2], str) else None
        if not place or change is None:
            continue
        clock = _text(row[0])
        if not obs_time and len(clock) == 12 and clock.isdigit():
            obs_time = f"{clock[:4]}-{clock[4:6]}-{clock[6:8]} {clock[8:10]}:{clock[10:12]}"
        stations.append(TempDiffReading(place, change))
    return TempDiffReport(obs_time, tuple(stations))


def format_temp_diff(report: TempDiffReport) -> str:
    """Render the past 24-hour temperature change, one station per line."""
    lines = ["Hong Kong 24-hour temperature change"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        number = _number(abs(reading.change_c))
        if reading.change_c > 0:
            signed = f"+{number}"
        elif reading.change_c < 0:
            signed = f"-{number}"
        else:
            signed = "0"
        lines.append(f"{reading.place}  {signed}°C")
    return "\n".join(lines) + "\n"


def format_temp_diff_miss(*, as_json: bool = False) -> str:
    """Say that no 24-hour temperature changes are available."""
    return _unavailable("No 24-hour temperature changes are available.", as_json=as_json)


def _cooler_clause(count: int) -> str:
    if count == 0:
        return "no station is cooler than 24 hours ago"
    if count == 1:
        return "1 station is cooler than 24 hours ago"
    return f"{count} stations are cooler than 24 hours ago"


def _warmer_clause(count: int) -> str:
    if count == 0:
        return "none are warmer"
    if count == 1:
        return "1 is warmer"
    return f"{count} are warmer"


def format_temp_shift(report: TempDiffReport, *, as_json: bool) -> str:
    """Count stations that are cooler or warmer than 24 hours ago."""
    if not report.stations:
        return _unavailable(
            "No 24-hour temperature changes are available.", as_json=as_json
        )
    cooler = sum(reading.change_c < 0 for reading in report.stations)
    warmer = sum(reading.change_c > 0 for reading in report.stations)
    unchanged = len(report.stations) - cooler - warmer
    if cooler == 0 and warmer == 0:
        body = "no station has changed temperature in 24 hours"
    else:
        body = f"{_cooler_clause(cooler)}, and {_warmer_clause(warmer)}"
    if report.obs_time:
        phrase = f"At {report.obs_time}, {body}."
    else:
        phrase = body[0].upper() + body[1:] + "."
    if as_json:
        payload = {
            "time": report.obs_time,
            "cooler": cooler,
            "warmer": warmer,
            "unchanged": unchanged,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_heat_index(text: str) -> HeatIndexReport:
    """Turn the heat-index CSV into the latest minute, one row per station."""
    stations: list[HeatIndexReading] = []
    latest = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 3:
            continue
        place = _text(row[1])
        value = _hour_mm(row[2])
        clock = _text(row[0])
        if not place or value is None or len(clock) != 12 or not clock.isdigit():
            continue
        if clock > latest:
            latest = clock
            stations = []
        if clock == latest:
            stations.append(HeatIndexReading(place, value))
    obs_time = ""
    if latest:
        obs_time = f"{latest[:4]}-{latest[4:6]}-{latest[6:8]} {latest[8:10]}:{latest[10:12]}"
    return HeatIndexReport(obs_time, tuple(stations))


def format_heat_index(report: HeatIndexReport) -> str:
    """Render the latest 10-minute mean Hong Kong Heat Index."""
    lines = ["Hong Kong heat index"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        lines.append(f"{reading.place}  {_number(reading.heat_index)}")
    return "\n".join(lines) + "\n"


def format_heat_index_miss(*, as_json: bool = False) -> str:
    """Say that no heat index is available."""
    return _unavailable("No heat index is available.", as_json=as_json)


def format_heat_gap(
    report: HeatIndexReport | None,
    place: str,
    air_c: float,
    *,
    as_json: bool,
) -> str:
    """Compare one station's heat index with the current air temperature."""
    if report is None or not report.stations:
        return _unavailable("No heat index is available.", as_json=as_json)
    match = next((reading for reading in report.stations if reading.place == place), None)
    if match is None:
        return _unavailable(f"No heat index is available for {place}.", as_json=as_json)
    gap = round(match.heat_index - air_c, 1)
    index = _number(match.heat_index)
    air = _number(air_c)
    if gap > 0:
        phrase = (
            f"Heat index at {place} is {index}, {_number(gap)} above the {air}°C air."
        )
    elif gap < 0:
        phrase = (
            f"Heat index at {place} is {index}, {_number(abs(gap))} below the {air}°C air."
        )
    else:
        phrase = f"Heat index at {place} matches the {air}°C air."
    if as_json:
        payload = {
            "place": place,
            "heat_index": match.heat_index,
            "temperature_c": air_c,
            "gap": gap,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


_DAILY_HEAT_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_daily_heat(text: str, lang: str = "en") -> DailyHeat | None:
    """Turn the King's Park maximum-heat-index CSV into the latest numeric day."""
    station = _DAILY_HEAT_STATIONS.get(lang, _DAILY_HEAT_STATIONS["en"])
    latest: DailyHeat | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyHeat(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_daily_heat(reading: DailyHeat) -> str:
    """Render the latest daily maximum Hong Kong Heat Index at King's Park."""
    return (
        "Hong Kong daily heat index\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.heat_index)}\n"
    )


def format_daily_heat_miss(*, as_json: bool = False) -> str:
    """Say that no daily maximum heat index is available."""
    return _unavailable("No daily maximum heat index is available.", as_json=as_json)


def parse_mean_heat(text: str, lang: str = "en") -> DailyHeat | None:
    """Turn the King's Park mean-heat-index CSV into the latest numeric day."""
    station = _DAILY_HEAT_STATIONS.get(lang, _DAILY_HEAT_STATIONS["en"])
    latest: DailyHeat | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyHeat(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_mean_heat(reading: DailyHeat) -> str:
    """Render the latest daily mean Hong Kong Heat Index at King's Park."""
    return (
        "Hong Kong daily mean heat index\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.heat_index)}\n"
    )


def format_mean_heat_miss(*, as_json: bool = False) -> str:
    """Say that no daily mean heat index is available."""
    return _unavailable("No daily mean heat index is available.", as_json=as_json)


def parse_wbgt(text: str) -> WbgtReport:
    """Turn the WBGT CSV into the latest minute, one row per station."""
    stations: list[WbgtReading] = []
    latest = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 3:
            continue
        place = _text(row[1])
        value = _hour_mm(row[2])
        clock = _text(row[0])
        if not place or value is None or len(clock) != 12 or not clock.isdigit():
            continue
        if clock > latest:
            latest = clock
            stations = []
        if clock == latest:
            stations.append(WbgtReading(place, value))
    obs_time = ""
    if latest:
        obs_time = f"{latest[:4]}-{latest[4:6]}-{latest[6:8]} {latest[8:10]}:{latest[10:12]}"
    return WbgtReport(obs_time, tuple(stations))


def format_wbgt(report: WbgtReport) -> str:
    """Render the latest 60-minute mean Wet Bulb Globe Temperature."""
    lines = ["Hong Kong wet bulb globe temperature"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        lines.append(f"{reading.place}  {_number(reading.wbgt_c)}°C")
    return "\n".join(lines) + "\n"


def format_wbgt_miss(*, as_json: bool = False) -> str:
    """Say that no wet bulb globe temperature is available."""
    return _unavailable("No wet bulb globe temperature is available.", as_json=as_json)


_WET_BULB_STATIONS = {
    "en": "Hong Kong Observatory",
    "tc": "香港天文台",
    "sc": "香港天文台",
}


def parse_wet_bulb(text: str, lang: str = "en") -> WetBulb | None:
    """Turn the Observatory wet-bulb CSV into the latest numeric day."""
    station = _WET_BULB_STATIONS.get(lang, _WET_BULB_STATIONS["en"])
    latest: WetBulb | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = WetBulb(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wet_bulb(reading: WetBulb) -> str:
    """Render the latest daily mean wet-bulb temperature at the Observatory."""
    return (
        "Hong Kong wet bulb temperature\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.wet_bulb_c)}°C\n"
    )


def format_wet_bulb_miss(*, as_json: bool = False) -> str:
    """Say that no daily mean wet-bulb temperature is available."""
    return _unavailable("No wet bulb temperature is available.", as_json=as_json)


_AIRPORT_WET_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_airport_wet(text: str, lang: str = "en") -> WetBulb | None:
    """Turn the airport wet-bulb CSV into the latest numeric day."""
    station = _AIRPORT_WET_STATIONS.get(lang, _AIRPORT_WET_STATIONS["en"])
    latest: WetBulb | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = WetBulb(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_airport_wet_miss(*, as_json: bool = False) -> str:
    """Say that no airport wet-bulb temperature is available."""
    return _unavailable("No airport wet bulb temperature is available.", as_json=as_json)


_PARK_WET_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_park_wet(text: str, lang: str = "en") -> WetBulb | None:
    """Turn the King's Park wet-bulb CSV into the latest numeric day."""
    station = _PARK_WET_STATIONS.get(lang, _PARK_WET_STATIONS["en"])
    latest: WetBulb | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = WetBulb(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_park_wet_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park wet-bulb temperature is available."""
    return _unavailable("No King's Park wet bulb temperature is available.", as_json=as_json)


_SHA_LO_WAN_STATIONS = {
    "en": "Sha Lo Wan",
    "tc": "沙螺灣",
    "sc": "沙螺湾",
}


def parse_sha_lo_wan_wet(text: str, lang: str = "en") -> WetBulb | None:
    """Turn the Sha Lo Wan wet-bulb CSV into the latest numeric day."""
    station = _SHA_LO_WAN_STATIONS.get(lang, _SHA_LO_WAN_STATIONS["en"])
    latest: WetBulb | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = WetBulb(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_lo_wan_wet_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Lo Wan wet-bulb temperature is available."""
    return _unavailable("No Sha Lo Wan wet bulb temperature is available.", as_json=as_json)


_NEI_LAK_SHAN_WET_STATIONS = {
    "en": "Nei Lak Shan",
    "tc": "彌勒山",
    "sc": "弥勒山",
}


def parse_nei_lak_shan_wet(text: str, lang: str = "en") -> WetBulb | None:
    """Turn the Nei Lak Shan wet-bulb CSV into the latest numeric day."""
    station = _NEI_LAK_SHAN_WET_STATIONS.get(lang, _NEI_LAK_SHAN_WET_STATIONS["en"])
    latest: WetBulb | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = WetBulb(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_nei_lak_shan_wet_miss(*, as_json: bool = False) -> str:
    """Say that no Nei Lak Shan wet-bulb temperature is available."""
    return _unavailable(
        "No Nei Lak Shan wet bulb temperature is available.",
        as_json=as_json,
    )


def parse_solar(text: str) -> SolarReport:
    """Turn the solar CSV into the latest minute, one row per station."""
    stations: list[SolarReading] = []
    latest = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 5:
            continue
        place = _text(row[1])
        global_w = _hour_mm(row[2])
        direct_w = _hour_mm(row[3])
        diffuse_w = _hour_mm(row[4])
        clock = _text(row[0])
        if (
            not place
            or global_w is None
            or direct_w is None
            or diffuse_w is None
            or len(clock) != 12
            or not clock.isdigit()
        ):
            continue
        if clock > latest:
            latest = clock
            stations = []
        if clock == latest:
            stations.append(SolarReading(place, global_w, direct_w, diffuse_w))
    obs_time = ""
    if latest:
        obs_time = f"{latest[:4]}-{latest[4:6]}-{latest[6:8]} {latest[8:10]}:{latest[10:12]}"
    return SolarReport(obs_time, tuple(stations))


def format_solar(report: SolarReport) -> str:
    """Render the latest 1-minute solar radiation, one station per line."""
    lines = ["Hong Kong solar radiation"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        lines.append(
            f"{reading.place}  global {_number(reading.global_w_m2)}"
            f"  direct {_number(reading.direct_w_m2)}"
            f"  diffuse {_number(reading.diffuse_w_m2)} W/m²"
        )
    return "\n".join(lines) + "\n"


def format_solar_miss(*, as_json: bool = False) -> str:
    """Say that no solar radiation is available."""
    return _unavailable("No solar radiation is available.", as_json=as_json)


_GLOBAL_SOLAR_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_global_solar(text: str, lang: str = "en") -> GlobalSolar | None:
    """Turn the King's Park global-solar CSV into the latest numeric day."""
    station = _GLOBAL_SOLAR_STATIONS.get(lang, _GLOBAL_SOLAR_STATIONS["en"])
    latest: GlobalSolar | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = GlobalSolar(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_global_solar(reading: GlobalSolar) -> str:
    """Render the latest daily global solar radiation at King's Park."""
    return (
        "Hong Kong global solar radiation\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.global_solar_mj_m2)} MJ/m²\n"
    )


def format_global_solar_miss(*, as_json: bool = False) -> str:
    """Say that no daily global solar radiation is available."""
    return _unavailable("No global solar radiation is available.", as_json=as_json)


_KAU_SAI_CHAU_SOLAR_STATIONS = {
    "en": "Kau Sai Chau",
    "tc": "滘西洲",
    "sc": "滘西洲",
}


def parse_kau_sai_chau_solar(text: str, lang: str = "en") -> GlobalSolar | None:
    """Turn the Kau Sai Chau global-solar CSV into the latest numeric day."""
    station = _KAU_SAI_CHAU_SOLAR_STATIONS.get(lang, _KAU_SAI_CHAU_SOLAR_STATIONS["en"])
    latest: GlobalSolar | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = GlobalSolar(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kau_sai_chau_solar_miss(*, as_json: bool = False) -> str:
    """Say that no Kau Sai Chau global solar radiation is available."""
    return _unavailable(
        "No Kau Sai Chau global solar radiation is available.",
        as_json=as_json,
    )


def format_forecast_icon(report: ForecastIcons) -> str:
    """Render each day's forecast icon."""
    lines = ["Hong Kong forecast icons"]
    if report.update_time:
        lines.append(f"Updated: {report.update_time}")
    for day in report.days:
        heading = " ".join(part for part in (day.date, day.week) if part)
        lines.append(f"{heading}  {day.icon}  {day.label}".strip())
    return "\n".join(lines) + "\n"


def format_forecast_icon_miss(*, as_json: bool = False) -> str:
    """Say that the 9-day forecast has no weather icons."""
    return _unavailable("No forecast icons are available.", as_json=as_json)


def format_today_icon(report: ForecastIcons, *, as_json: bool) -> str:
    """Print today's forecast weather icon."""
    today = _hong_kong_today()
    day = next((item for item in report.days if item.date == today), None)
    if day is None:
        return _unavailable("No forecast icon is available for today.", as_json=as_json)
    if as_json:
        return (
            json.dumps(
                {"date": day.date, "icon": day.icon, "label": day.label},
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
    return f"Icon: {day.icon} {day.label}\n"


def _icon_day_heading(day: ForecastIconDay) -> str:
    """Date and weekday for one forecast icon, when either is present."""
    return " ".join(part for part in (day.date, day.week) if part)


def _join_headings(headings: list[str]) -> str:
    """Join day headings with commas and a final 'and'."""
    if len(headings) == 1:
        return headings[0]
    if len(headings) == 2:
        return f"{headings[0]} and {headings[1]}"
    return ", ".join(headings[:-1]) + f", and {headings[-1]}"


def format_sunny_days(report: ForecastIcons, *, as_json: bool) -> str:
    """Print the 9-day forecast days whose icon is Sunny."""
    if not report.days:
        return _unavailable("No forecast icons are available.", as_json=as_json)
    sunny = tuple(day for day in report.days if day.icon == 50)
    if not sunny:
        return _unavailable("No sunny day is in the forecast.", as_json=as_json)
    headings = [_icon_day_heading(day) or day.label for day in sunny]
    listed = _join_headings(headings)
    if len(sunny) == 1:
        phrase = f"1 sunny day: {listed}"
    else:
        phrase = f"{len(sunny)} sunny days: {listed}"
    if as_json:
        payload = {
            "count": len(sunny),
            "days": [
                {
                    "date": day.date,
                    "week": day.week,
                    "icon": day.icon,
                    "label": day.label,
                }
                for day in sunny
            ],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_uv(payload: dict) -> UvIndex:
    """Turn the `uvindex` field of an `rhrread` document into a short report."""
    update_time = _text(payload.get("updateTime")) or "unknown"
    raw = payload.get("uvindex")
    if not isinstance(raw, dict):
        return UvIndex(update_time, None, None, None, None)

    nested_update = _text(raw.get("updateTime"))
    if nested_update:
        update_time = nested_update
    readings = raw.get("data")
    reading = readings[0] if isinstance(readings, list) and readings and isinstance(readings[0], dict) else {}
    value = _temp_value(reading)
    if value is None:
        return UvIndex(update_time, None, None, None, None)
    return UvIndex(
        update_time=update_time,
        place=_text(reading.get("place")) or None,
        value=value,
        description=_text(reading.get("desc")) or None,
        record=_text(raw.get("recordDesc")) or None,
    )


def format_uv(report: UvIndex) -> str:
    """Render the UV index as plain text."""
    lines = [
        "Hong Kong UV index",
        "Source: Hong Kong Observatory open data",
        f"Updated: {report.update_time}",
    ]
    if report.value is None:
        lines.append("UV index is not available right now.")
        return "\n".join(lines) + "\n"

    value = _number(report.value)
    if report.place and report.description:
        lines.append(f"{report.place}: {value} ({report.description})")
    elif report.place:
        lines.append(f"{report.place}: {value}")
    elif report.description:
        lines.append(f"UV index: {value} ({report.description})")
    else:
        lines.append(f"UV index: {value}")
    if report.record:
        lines.append(report.record)
    return "\n".join(lines) + "\n"


_FIFTEEN_UV_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_fifteen_uv(text: str, lang: str = "en") -> FifteenUv | None:
    """Turn the 15-minute UV CSV into the latest numeric reading."""
    station = _FIFTEEN_UV_STATIONS.get(lang, _FIFTEEN_UV_STATIONS["en"])
    latest: FifteenUv | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 2:
            continue
        clock = _text(row[0]).lstrip("\ufeff")
        value = _hour_mm(row[1])
        if len(clock) != 12 or not clock.isdigit() or value is None:
            continue
        latest = FifteenUv(
            station,
            f"{clock[:4]}-{clock[4:6]}-{clock[6:8]} {clock[8:10]}:{clock[10:12]}",
            value,
        )
    return latest


def format_fifteen_uv(reading: FifteenUv) -> str:
    """Render the latest 15-minute mean UV index at King's Park."""
    return (
        "Hong Kong 15-minute UV index\n"
        f"Station: {reading.station}\n"
        f"{reading.time}  {_number(reading.uv_index)}\n"
    )


def format_fifteen_uv_miss(*, as_json: bool = False) -> str:
    """Say that no 15-minute UV index is available."""
    return _unavailable("No 15-minute UV index is available.", as_json=as_json)


def _uv_level(value: float) -> str | None:
    """Band for a UV index: low, moderate, high, very high, or extreme."""
    if value < 0:
        return None
    if value < 3:
        return "low"
    if value < 6:
        return "moderate"
    if value < 8:
        return "high"
    if value < 11:
        return "very high"
    return "extreme"


def format_uv_level(reading: FifteenUv | None, *, as_json: bool) -> str:
    """Print the exposure band for the latest 15-minute UV index."""
    level = _uv_level(reading.uv_index) if reading is not None else None
    if reading is None or level is None:
        return _unavailable("No 15-minute UV index is available.", as_json=as_json)
    phrase = f"UV {level}, {_number(reading.uv_index)}"
    if as_json:
        payload = {
            "station": reading.station,
            "time": reading.time,
            "uv": reading.uv_index,
            "level": level,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def format_uv_gap(
    hourly: UvIndex | None, fifteen: FifteenUv | None, *, as_json: bool
) -> str:
    """Print how far the latest 15-minute UV is from the hourly index."""
    hourly_value = hourly.value if hourly is not None else None
    fifteen_value = fifteen.uv_index if fifteen is not None else None
    if hourly_value is None or fifteen_value is None:
        return _unavailable("No UV comparison is available.", as_json=as_json)
    gap = round(fifteen_value - hourly_value, 1)
    if gap == 0:
        phrase = f"15-minute UV matches the hourly index of {_number(hourly_value)}"
    elif gap > 0:
        phrase = (
            f"15-minute UV is {_number(gap)} above the hourly index of "
            f"{_number(hourly_value)}"
        )
    else:
        phrase = (
            f"15-minute UV is {_number(abs(gap))} below the hourly index of "
            f"{_number(hourly_value)}"
        )
    if as_json:
        payload = {
            "fifteen": fifteen_value,
            "hourly": hourly_value,
            "gap": gap,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_icon_time(payload: dict) -> IconUpdate | None:
    """Turn the `rhrread` icon update time into one timestamp."""
    text = _text(payload.get("iconUpdateTime"))
    if not text:
        return None
    return IconUpdate(text)


def format_icon_time(report: IconUpdate) -> str:
    """Render the weather-icon update time."""
    return f"Hong Kong icon update\n{report.updated}\n"


def format_icon_time_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no icon update time."""
    return _unavailable("No icon update time is available.", as_json=as_json)


def parse_icon(payload: dict) -> IconReport | None:
    """Turn the `rhrread` icon field into icon numbers and labels."""
    raw = payload.get("icon")
    if isinstance(raw, bool):
        codes: list[int] = []
    elif isinstance(raw, int):
        codes = [raw]
    elif isinstance(raw, list):
        codes = [code for code in raw if isinstance(code, int) and not isinstance(code, bool)]
    else:
        codes = []
    if not codes:
        return None
    return IconReport(tuple(IconReading(code, icon_label(code)) for code in codes))


def format_icon(report: IconReport) -> str:
    """Render the current weather icon number and label."""
    lines = ["Hong Kong weather icon"]
    lines.extend(f"{icon.code}  {icon.label}" for icon in report.icons)
    return "\n".join(lines) + "\n"


def format_icon_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no weather icon."""
    return _unavailable("No weather icon is available.", as_json=as_json)


def parse_current_updated(payload: dict) -> CurrentUpdated | None:
    """Turn the `rhrread` update time into one timestamp."""
    text = _text(payload.get("updateTime"))
    if not text:
        return None
    return CurrentUpdated(text)


def format_current_updated(report: CurrentUpdated) -> str:
    """Render when the current weather report was updated."""
    return f"Hong Kong weather update\n{report.updated}\n"


def format_current_updated_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no update time."""
    return _unavailable("No weather update time is available.", as_json=as_json)


def parse_tips(payload: dict) -> SpecialTips:
    """Turn an `swt` document into a list of tip descriptions."""
    raw = payload.get("swt", [])
    if isinstance(raw, str):
        raw = [raw] if raw.strip() else []
    if not isinstance(raw, list):
        raise WeatherError("special weather tips are missing from the report")
    tips: list[str] = []
    for item in raw:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = _text(item.get("desc"))
        else:
            continue
        if text:
            tips.append(text)
    return SpecialTips(tuple(tips))


def format_tips(report: SpecialTips) -> str:
    """Render special weather tips as a short list."""
    if not report.tips:
        return "No special weather tips are in force.\n"
    lines = ["Hong Kong special weather tips"]
    lines.extend(f"- {tip}" for tip in report.tips)
    return "\n".join(lines) + "\n"


def _lamppost_time(value: object) -> str:
    clock = _text(value)
    if len(clock) != 14 or not clock.isdigit():
        return ""
    return (
        f"{clock[:4]}-{clock[4:6]}-{clock[6:8]} "
        f"{clock[8:10]}:{clock[10:12]}:{clock[12:14]}"
    )


def parse_lamppost(payload: dict) -> LamppostReading | None:
    """Turn one smart-lamppost payload into temperature, humidity, and wind."""
    if _text(payload.get("message")):
        return None
    body = payload.get("BODY")
    reading = body.get("HKO") if isinstance(body, dict) else None
    if not isinstance(reading, dict):
        return None
    temperature = _hour_mm(reading.get("T0"))
    humidity = _hour_mm(reading.get("RH"))
    wind = _hour_mm(reading.get("WS"))
    direction = _hour_mm(reading.get("WD"))
    if temperature is None and humidity is None and wind is None and direction is None:
        return None
    return LamppostReading(
        _text(payload.get("PI")) or "GF3637",
        _lamppost_time(reading.get("TS")),
        temperature,
        humidity,
        wind,
        direction,
    )


def format_lamppost(reading: LamppostReading) -> str:
    """Render the experimental smart-lamppost reading."""
    parts: list[str] = []
    if reading.temperature_c is not None:
        parts.append(f"{_number(reading.temperature_c)}°C")
    if reading.humidity_percent is not None:
        parts.append(f"humidity {_number(reading.humidity_percent)}%")
    if reading.wind_km_h is not None and reading.direction_deg is not None:
        parts.append(
            f"wind {_number(reading.wind_km_h)} km/h from {_number(reading.direction_deg)}°"
        )
    elif reading.wind_km_h is not None:
        parts.append(f"wind {_number(reading.wind_km_h)} km/h")
    elif reading.direction_deg is not None:
        parts.append(f"wind from {_number(reading.direction_deg)}°")
    lines = ["Hong Kong smart lamppost", f"Lamppost: {reading.lamppost}"]
    detail = "  ".join(parts)
    if reading.time:
        lines.append(f"{reading.time}  {detail}")
    else:
        lines.append(detail)
    return "\n".join(lines) + "\n"


def format_lamppost_miss(*, as_json: bool = False) -> str:
    """Say that the smart lamppost has no reading."""
    return _unavailable("No smart lamppost reading is available.", as_json=as_json)


def parse_stations(payload: dict) -> StationReport:
    """List each place in an `rhrread` document, with humidity when that place has it."""
    humidity: dict[str, float] = {}
    for item in _data_list(payload.get("humidity")):
        place = _text(item.get("place"))
        value = _temp_value(item)
        if place and value is not None:
            humidity[place] = value

    stations: list[StationReading] = []
    seen: set[str] = set()
    for item in _data_list(payload.get("temperature")):
        place = _text(item.get("place"))
        value = _temp_value(item)
        if not place or value is None or place in seen:
            continue
        seen.add(place)
        stations.append(StationReading(place, value, humidity.get(place)))
    for place, value in humidity.items():
        if place not in seen:
            stations.append(StationReading(place, None, value))
    if not stations:
        raise WeatherError("station readings are missing from the report")
    return StationReport(
        update_time=_text(payload.get("updateTime")) or "unknown",
        stations=tuple(stations),
    )


def filter_stations(report: StationReport, name: str) -> StationReport:
    """Keep stations whose place name contains `name`, ignoring case."""
    needle = name.strip().casefold()
    if not needle:
        matches: tuple[StationReading, ...] = ()
    else:
        matches = tuple(
            station for station in report.stations if needle in station.place.casefold()
        )
    return StationReport(update_time=report.update_time, stations=matches)


def format_place_miss(name: str, update_time: str, *, as_json: bool) -> str:
    """Say that no station matched, as text or one JSON object."""
    message = f'No station matches "{name.strip()}".'
    if not as_json:
        return message + "\n"
    return (
        json.dumps(
            {"update_time": update_time, "stations": [], "message": message},
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )


def format_stations(report: StationReport) -> str:
    """Render station temperature and humidity as aligned lines."""
    width = max(len("Place"), *(len(station.place) for station in report.stations))
    lines = [
        "Hong Kong station readings",
        "Source: Hong Kong Observatory open data",
        f"Updated: {report.update_time}",
        "",
        f"{'Place':<{width}}  Temp   Humidity",
    ]
    for station in report.stations:
        temp = (
            f"{_number(station.temperature_c)}°C"
            if station.temperature_c is not None
            else "n/a"
        )
        humid = (
            f"{_number(station.humidity_percent)}%"
            if station.humidity_percent is not None
            else "n/a"
        )
        lines.append(f"{station.place:<{width}}  {temp:<5}  {humid}")
    return "\n".join(lines) + "\n"


def format_places(report: StationReport, *, as_json: bool = False) -> str:
    """List station names from temperature and humidity readings."""
    names = [station.place for station in report.stations]
    if as_json:
        return json.dumps({"places": names}, indent=2, ensure_ascii=False) + "\n"
    return "Hong Kong places\n" + "\n".join(names) + "\n"


def parse_rain(payload: dict) -> RainReport:
    """Turn `rhrread` rainfall data into one reading per place, wettest first."""
    readings: list[RainReading] = []
    seen: set[str] = set()
    for item in _data_list(payload.get("rainfall")):
        place = _text(item.get("place"))
        value = item.get("max")
        if not place or place in seen:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        seen.add(place)
        readings.append(RainReading(place, float(value)))
    readings.sort(key=lambda reading: reading.rainfall_mm, reverse=True)
    return RainReport(tuple(readings))


def format_rain(report: RainReport) -> str:
    """Render district rainfall, one line per place."""
    if not report.readings:
        return "No rainfall readings are available.\n"
    lines = ["Hong Kong rainfall"]
    lines.extend(
        f"{reading.place}  {_number(reading.rainfall_mm)} mm" for reading in report.readings
    )
    return "\n".join(lines) + "\n"


def parse_rain_period(payload: dict) -> RainPeriod | None:
    """Turn the `rhrread` rainfall window into a start and end time."""
    section = payload.get("rainfall")
    if not isinstance(section, dict):
        return None
    start = _text(section.get("startTime"))
    end = _text(section.get("endTime"))
    if not start or not end:
        return None
    return RainPeriod(start, end)


def format_rain_period(period: RainPeriod) -> str:
    """Render the district rainfall observation window."""
    return f"Hong Kong rainfall period\nFrom: {period.start}\nTo: {period.end}\n"


def format_rain_period_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no district rainfall window."""
    return _unavailable("No rainfall period is available.", as_json=as_json)


def _under_maintenance(value: object) -> bool:
    return value is True or (isinstance(value, str) and value.strip().upper() == "TRUE")


def parse_rain_maint(payload: dict) -> RainMaintenance:
    """List districts whose rainfall `main` flag says the gauge is under maintenance."""
    places: list[str] = []
    seen: set[str] = set()
    for item in _data_list(payload.get("rainfall")):
        if not _under_maintenance(item.get("main")):
            continue
        place = _text(item.get("place"))
        if not place or place in seen:
            continue
        seen.add(place)
        places.append(place)
    return RainMaintenance(tuple(places))


def format_rain_maint(report: RainMaintenance) -> str:
    """Render districts whose rainfall gauge is under maintenance."""
    lines = ["Hong Kong rainfall maintenance"]
    lines.extend(report.places)
    return "\n".join(lines) + "\n"


def format_rain_maint_miss(*, as_json: bool = False) -> str:
    """Say that no district rainfall gauge is under maintenance."""
    return _unavailable("No rainfall stations are under maintenance.", as_json=as_json)


def parse_hour_rain(payload: dict) -> HourRainReport:
    """Turn an hourly-rainfall document into station readings, wettest first."""
    raw = payload.get("hourlyRainfall")
    readings: list[HourRainReading] = []
    seen: set[str] = set()
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            place = _text(item.get("automaticWeatherStation"))
            amount = _hour_mm(item.get("value"))
            if not place or place in seen or amount is None:
                continue
            seen.add(place)
            readings.append(
                HourRainReading(place, _text(item.get("automaticWeatherStationID")), amount)
            )
    readings.sort(key=lambda reading: reading.rainfall_mm, reverse=True)
    return HourRainReport(_text(payload.get("obsTime")), tuple(readings))


def format_hour_rain(report: HourRainReport) -> str:
    """Render past-hour rainfall, one station per line."""
    lines = ["Hong Kong hourly rainfall"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    lines.extend(
        f"{reading.place}  {_number(reading.rainfall_mm)} mm" for reading in report.readings
    )
    return "\n".join(lines) + "\n"


def format_hour_rain_miss(*, as_json: bool = False) -> str:
    """Say that no past-hour rainfall readings are available."""
    return _unavailable("No hourly rainfall readings are available.", as_json=as_json)


def format_hour_wettest(reading: HourWettest) -> str:
    """Render the wettest automatic station from the past hour."""
    lines = ["Hong Kong hourly wettest"]
    if reading.obs_time:
        lines.append(f"Recorded: {reading.obs_time}")
    lines.append(f"{reading.place}  {_number(reading.rainfall_mm)} mm")
    return "\n".join(lines) + "\n"


def format_hour_driest(reading: HourDriest) -> str:
    """Render the driest automatic station from the past hour."""
    lines = ["Hong Kong hourly driest"]
    if reading.obs_time:
        lines.append(f"Recorded: {reading.obs_time}")
    lines.append(f"{reading.place}  {_number(reading.rainfall_mm)} mm")
    return "\n".join(lines) + "\n"


def parse_yesterday(payload: dict, date: str) -> YesterdayReport | None:
    """Turn a `RYES` document for the Observatory into yesterday's summary."""
    high = _hour_mm(payload.get("HKOReadingsMaxTemp"))
    low = _hour_mm(payload.get("HKOReadingsMinTemp"))
    rainfall = _hour_mm(payload.get("HKOReadingsRainfall"))
    humidity_high = _hour_mm(payload.get("HKOReadingsMaxRH"))
    humidity_low = _hour_mm(payload.get("HKOReadingsMinRH"))
    if high is None and low is None and rainfall is None and humidity_high is None and humidity_low is None:
        return None
    reported = _text(payload.get("ReportTimeInfoDate"))
    if len(reported) == 8 and reported.isdigit():
        date = f"{reported[:4]}-{reported[4:6]}-{reported[6:8]}"
    return YesterdayReport(date, high, low, rainfall, humidity_high, humidity_low)


def format_yesterday(report: YesterdayReport) -> str:
    """Render yesterday's Observatory temperature, rainfall, and humidity."""
    lines = ["Hong Kong yesterday", report.date]
    if report.temp_high_c is not None:
        lines.append(f"High: {_number(report.temp_high_c)}°C")
    if report.temp_low_c is not None:
        lines.append(f"Low: {_number(report.temp_low_c)}°C")
    if report.rainfall_mm is not None:
        lines.append(f"Rainfall: {_number(report.rainfall_mm)} mm")
    humidity = _humidity_span(report.humidity_low_percent, report.humidity_high_percent)
    if humidity:
        lines.append("Humidity: " + humidity.removeprefix("humidity "))
    return "\n".join(lines) + "\n"


def format_yesterday_miss(*, as_json: bool = False) -> str:
    """Say that yesterday's Observatory summary is not available."""
    return _unavailable("Yesterday's Observatory summary is not available.", as_json=as_json)


def parse_mean_temp(payload: dict) -> DailyMean | None:
    """Turn a `CLMTEMP` table into the latest numeric daily mean."""
    raw = payload.get("data")
    if not isinstance(raw, list):
        return None
    latest: DailyMean | None = None
    for row in raw:
        if not isinstance(row, list) or len(row) < 4:
            continue
        year = _text(row[0])
        month_text = _text(row[1])
        day_text = _text(row[2])
        value = _hour_mm(row[3])
        if (
            value is None
            or len(year) != 4
            or not year.isdigit()
            or not month_text.isdigit()
            or not day_text.isdigit()
        ):
            continue
        latest = DailyMean(f"{year}-{month_text.zfill(2)}-{day_text.zfill(2)}", value)
    return latest


def format_mean_temp(reading: DailyMean) -> str:
    """Render the latest daily mean temperature at the Observatory."""
    return (
        "Hong Kong daily mean temperature\n"
        f"{reading.date}  {_number(reading.temperature_c)}°C\n"
    )


def format_mean_temp_miss(*, as_json: bool = False) -> str:
    """Say that no daily mean temperature is available."""
    return _unavailable("No daily mean temperature is available.", as_json=as_json)


_TAI_MO_STATIONS = {
    "en": "Tai Mo Shan",
    "tc": "大帽山",
    "sc": "大帽山",
}


def parse_tai_mo_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tai Mo Shan temperature CSV into the latest numeric day."""
    station = _TAI_MO_STATIONS.get(lang, _TAI_MO_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_temp(reading: TaiMoTemp) -> str:
    """Render the latest daily mean temperature at Tai Mo Shan."""
    return (
        "Hong Kong daily mean temperature\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.temperature_c)}°C\n"
    )


def format_tai_mo_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo Shan temperature is available."""
    return _unavailable("No Tai Mo Shan temperature is available.", as_json=as_json)


_TATE_TEMP_STATIONS = {
    "en": "Tate's Cairn",
    "tc": "大老山",
    "sc": "大老山",
}


def parse_tate_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tate's Cairn temperature CSV into the latest numeric day."""
    station = _TATE_TEMP_STATIONS.get(lang, _TATE_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tate_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Tate's Cairn temperature is available."""
    return _unavailable("No Tate's Cairn temperature is available.", as_json=as_json)


_SAI_KUNG_TEMP_STATIONS = {
    "en": "Sai Kung",
    "tc": "西貢",
    "sc": "西贡",
}


def parse_sai_kung_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sai Kung temperature CSV into the latest numeric day."""
    station = _SAI_KUNG_TEMP_STATIONS.get(lang, _SAI_KUNG_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sai_kung_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Sai Kung temperature is available."""
    return _unavailable("No Sai Kung temperature is available.", as_json=as_json)


_SHA_TIN_TEMP_STATIONS = {
    "en": "Sha Tin",
    "tc": "沙田",
    "sc": "沙田",
}


def parse_sha_tin_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sha Tin temperature CSV into the latest numeric day."""
    station = _SHA_TIN_TEMP_STATIONS.get(lang, _SHA_TIN_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_tin_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Tin temperature is available."""
    return _unavailable("No Sha Tin temperature is available.", as_json=as_json)


_SHEUNG_SHUI_TEMP_STATIONS = {
    "en": "Sheung Shui",
    "tc": "上水",
    "sc": "上水",
}


def parse_sheung_shui_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sheung Shui mean-temperature CSV into the latest numeric day."""
    station = _SHEUNG_SHUI_TEMP_STATIONS.get(lang, _SHEUNG_SHUI_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sheung_shui_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Sheung Shui temperature is available."""
    return _unavailable("No Sheung Shui temperature is available.", as_json=as_json)


_WONG_CHUK_HANG_TEMP_STATIONS = {
    "en": "Wong Chuk Hang",
    "tc": "黃竹坑",
    "sc": "黄竹坑",
}


def parse_wong_chuk_hang_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Wong Chuk Hang mean-temperature CSV into the latest numeric day."""
    station = _WONG_CHUK_HANG_TEMP_STATIONS.get(lang, _WONG_CHUK_HANG_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_chuk_hang_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Wong Chuk Hang temperature is available."""
    return _unavailable("No Wong Chuk Hang temperature is available.", as_json=as_json)


_LAU_FAU_TEMP_STATIONS = {
    "en": "Lau Fau Shan",
    "tc": "流浮山",
    "sc": "流浮山",
}


def parse_lau_fau_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Lau Fau Shan mean-temperature CSV into the latest numeric day."""
    station = _LAU_FAU_TEMP_STATIONS.get(lang, _LAU_FAU_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lau_fau_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Lau Fau Shan temperature is available."""
    return _unavailable("No Lau Fau Shan temperature is available.", as_json=as_json)


_TSEUNG_KWAN_O_TEMP_STATIONS = {
    "en": "Tseung Kwan O",
    "tc": "將軍澳",
    "sc": "将军澳",
}


def parse_tseung_kwan_o_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tseung Kwan O mean-temperature CSV into the latest numeric day."""
    station = _TSEUNG_KWAN_O_TEMP_STATIONS.get(lang, _TSEUNG_KWAN_O_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tseung_kwan_o_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Tseung Kwan O temperature is available."""
    return _unavailable("No Tseung Kwan O temperature is available.", as_json=as_json)


_SHAM_SHUI_PO_TEMP_STATIONS = {
    "en": "Sham Shui Po",
    "tc": "深水埗",
    "sc": "深水埗",
}


def parse_sham_shui_po_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sham Shui Po mean-temperature CSV into the latest numeric day."""
    station = _SHAM_SHUI_PO_TEMP_STATIONS.get(lang, _SHAM_SHUI_PO_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sham_shui_po_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Sham Shui Po temperature is available."""
    return _unavailable("No Sham Shui Po temperature is available.", as_json=as_json)


_SHEK_KONG_TEMP_STATIONS = {
    "en": "Shek Kong",
    "tc": "石崗",
    "sc": "石岗",
}


def parse_shek_kong_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Shek Kong mean-temperature CSV into the latest numeric day."""
    station = _SHEK_KONG_TEMP_STATIONS.get(lang, _SHEK_KONG_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shek_kong_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Shek Kong temperature is available."""
    return _unavailable("No Shek Kong temperature is available.", as_json=as_json)


_WETLAND_TEMP_STATIONS = {
    "en": "Wetland Park",
    "tc": "濕地公園",
    "sc": "湿地公园",
}


def parse_wetland_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Wetland Park mean-temperature CSV into the latest numeric day."""
    station = _WETLAND_TEMP_STATIONS.get(lang, _WETLAND_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wetland_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Wetland Park temperature is available."""
    return _unavailable("No Wetland Park temperature is available.", as_json=as_json)


_TA_KWU_LING_TEMP_STATIONS = {
    "en": "Ta Kwu Ling",
    "tc": "打鼓嶺",
    "sc": "打鼓岭",
}


def parse_ta_kwu_ling_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Ta Kwu Ling mean-temperature CSV into the latest numeric day."""
    station = _TA_KWU_LING_TEMP_STATIONS.get(lang, _TA_KWU_LING_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ta_kwu_ling_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Ta Kwu Ling temperature is available."""
    return _unavailable(
        "No Ta Kwu Ling temperature is available.", as_json=as_json
    )


_PENG_CHAU_TEMP_STATIONS = {
    "en": "Peng Chau",
    "tc": "坪洲",
    "sc": "坪洲",
}


def parse_peng_chau_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Peng Chau mean-temperature CSV into the latest numeric day."""
    station = _PENG_CHAU_TEMP_STATIONS.get(lang, _PENG_CHAU_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_peng_chau_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Peng Chau temperature is available."""
    return _unavailable("No Peng Chau temperature is available.", as_json=as_json)


_PARK_TEMP_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_park_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the King's Park mean-temperature CSV into the latest numeric day."""
    station = _PARK_TEMP_STATIONS.get(lang, _PARK_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_park_temp_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park temperature is available."""
    return _unavailable("No King's Park temperature is available.", as_json=as_json)


_CHEUNG_CHAU_TEMP_STATIONS = {
    "en": "Cheung Chau",
    "tc": "長洲",
    "sc": "长洲",
}


def parse_cheung_chau_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Cheung Chau mean-temperature CSV into the latest numeric day."""
    station = _CHEUNG_CHAU_TEMP_STATIONS.get(lang, _CHEUNG_CHAU_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_chau_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau temperature is available."""
    return _unavailable("No Cheung Chau temperature is available.", as_json=as_json)


_WAGLAN_TEMP_STATIONS = {
    "en": "Waglan Island",
    "tc": "橫瀾島",
    "sc": "横澜岛",
}


def parse_waglan_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Waglan Island mean-temperature CSV into the latest numeric day."""
    station = _WAGLAN_TEMP_STATIONS.get(lang, _WAGLAN_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_waglan_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Waglan Island temperature is available."""
    return _unavailable("No Waglan Island temperature is available.", as_json=as_json)


_PING_CHAU_TEMP_STATIONS = {
    "en": "Ping Chau",
    "tc": "平洲",
    "sc": "平洲",
}


def parse_ping_chau_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Ping Chau mean-temperature CSV into the latest numeric day."""
    station = _PING_CHAU_TEMP_STATIONS.get(lang, _PING_CHAU_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ping_chau_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Ping Chau temperature is available."""
    return _unavailable("No Ping Chau temperature is available.", as_json=as_json)


_SHA_LO_WAN_TEMP_STATIONS = {
    "en": "Sha Lo Wan",
    "tc": "沙螺灣",
    "sc": "沙螺湾",
}


def parse_sha_lo_wan_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sha Lo Wan mean-temperature CSV into the latest numeric day."""
    station = _SHA_LO_WAN_TEMP_STATIONS.get(lang, _SHA_LO_WAN_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_lo_wan_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Lo Wan temperature is available."""
    return _unavailable("No Sha Lo Wan temperature is available.", as_json=as_json)


_AIRPORT_TEMP_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_airport_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the airport mean-temperature CSV into the latest numeric day."""
    station = _AIRPORT_TEMP_STATIONS.get(lang, _AIRPORT_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_airport_temp_miss(*, as_json: bool = False) -> str:
    """Say that no airport temperature is available."""
    return _unavailable("No airport temperature is available.", as_json=as_json)


_CLEAR_WATER_BAY_TEMP_STATIONS = {
    "en": "Clear Water Bay",
    "tc": "清水灣",
    "sc": "清水湾",
}


def parse_clear_water_bay_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Clear Water Bay mean-temperature CSV into the latest numeric day."""
    station = _CLEAR_WATER_BAY_TEMP_STATIONS.get(
        lang, _CLEAR_WATER_BAY_TEMP_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_clear_water_bay_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Clear Water Bay temperature is available."""
    return _unavailable("No Clear Water Bay temperature is available.", as_json=as_json)


_HONG_KONG_PARK_TEMP_STATIONS = {
    "en": "Hong Kong Park",
    "tc": "香港公園",
    "sc": "香港公园",
}


def parse_hong_kong_park_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Hong Kong Park mean-temperature CSV into the latest numeric day."""
    station = _HONG_KONG_PARK_TEMP_STATIONS.get(
        lang, _HONG_KONG_PARK_TEMP_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_hong_kong_park_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Hong Kong Park temperature is available."""
    return _unavailable("No Hong Kong Park temperature is available.", as_json=as_json)


_NGONG_PING_TEMP_STATIONS = {
    "en": "Ngong Ping",
    "tc": "昂坪",
    "sc": "昂坪",
}


def parse_ngong_ping_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Ngong Ping mean-temperature CSV into the latest numeric day."""
    station = _NGONG_PING_TEMP_STATIONS.get(lang, _NGONG_PING_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ngong_ping_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Ngong Ping temperature is available."""
    return _unavailable("No Ngong Ping temperature is available.", as_json=as_json)


_KWUN_TONG_TEMP_STATIONS = {
    "en": "Kwun Tong",
    "tc": "觀塘",
    "sc": "观塘",
}


def parse_kwun_tong_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kwun Tong mean-temperature CSV into the latest numeric day."""
    station = _KWUN_TONG_TEMP_STATIONS.get(lang, _KWUN_TONG_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kwun_tong_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Kwun Tong temperature is available."""
    return _unavailable("No Kwun Tong temperature is available.", as_json=as_json)


_WONG_TAI_SIN_TEMP_STATIONS = {
    "en": "Wong Tai Sin",
    "tc": "黃大仙",
    "sc": "黄大仙",
}


def parse_wong_tai_sin_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Wong Tai Sin mean-temperature CSV into the latest numeric day."""
    station = _WONG_TAI_SIN_TEMP_STATIONS.get(lang, _WONG_TAI_SIN_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_tai_sin_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Wong Tai Sin temperature is available."""
    return _unavailable("No Wong Tai Sin temperature is available.", as_json=as_json)


_TSUEN_WAN_TEMP_STATIONS = {
    "en": "Tsuen Wan",
    "tc": "荃灣",
    "sc": "荃湾",
}


def parse_tsuen_wan_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tsuen Wan mean-temperature CSV into the latest numeric day."""
    station = _TSUEN_WAN_TEMP_STATIONS.get(lang, _TSUEN_WAN_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tsuen_wan_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan temperature is available."""
    return _unavailable("No Tsuen Wan temperature is available.", as_json=as_json)


_YUEN_LONG_PARK_TEMP_STATIONS = {
    "en": "Yuen Long Park",
    "tc": "元朗公園",
    "sc": "元朗公园",
}


def parse_yuen_long_park_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Yuen Long Park mean-temperature CSV into the latest numeric day."""
    station = _YUEN_LONG_PARK_TEMP_STATIONS.get(
        lang, _YUEN_LONG_PARK_TEMP_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_yuen_long_park_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Yuen Long Park temperature is available."""
    return _unavailable("No Yuen Long Park temperature is available.", as_json=as_json)


_TAP_MUN_TEMP_STATIONS = {
    "en": "Tap Mun",
    "tc": "塔門",
    "sc": "塔门",
}


def parse_tap_mun_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tap Mun mean-temperature CSV into the latest numeric day."""
    station = _TAP_MUN_TEMP_STATIONS.get(lang, _TAP_MUN_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tap_mun_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Tap Mun temperature is available."""
    return _unavailable("No Tap Mun temperature is available.", as_json=as_json)


_SHAU_KEI_WAN_TEMP_STATIONS = {
    "en": "Shau Kei Wan",
    "tc": "筲箕灣",
    "sc": "筲箕湾",
}


def parse_shau_kei_wan_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Shau Kei Wan mean-temperature CSV into the latest numeric day."""
    station = _SHAU_KEI_WAN_TEMP_STATIONS.get(lang, _SHAU_KEI_WAN_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shau_kei_wan_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Shau Kei Wan temperature is available."""
    return _unavailable("No Shau Kei Wan temperature is available.", as_json=as_json)


_HAPPY_VALLEY_TEMP_STATIONS = {
    "en": "Happy Valley",
    "tc": "跑馬地",
    "sc": "跑马地",
}


def parse_happy_valley_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Happy Valley mean-temperature CSV into the latest numeric day."""
    station = _HAPPY_VALLEY_TEMP_STATIONS.get(lang, _HAPPY_VALLEY_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_happy_valley_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Happy Valley temperature is available."""
    return _unavailable("No Happy Valley temperature is available.", as_json=as_json)


_TAI_MEI_TUK_TEMP_STATIONS = {
    "en": "Tai Mei Tuk",
    "tc": "大美督",
    "sc": "大美督",
}


def parse_tai_mei_tuk_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tai Mei Tuk mean-temperature CSV into the latest numeric day."""
    station = _TAI_MEI_TUK_TEMP_STATIONS.get(lang, _TAI_MEI_TUK_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mei_tuk_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mei Tuk temperature is available."""
    return _unavailable("No Tai Mei Tuk temperature is available.", as_json=as_json)


_KAU_SAI_CHAU_TEMP_STATIONS = {
    "en": "Kau Sai Chau",
    "tc": "滘西洲",
    "sc": "滘西洲",
}


def parse_kau_sai_chau_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kau Sai Chau mean-temperature CSV into the latest numeric day."""
    station = _KAU_SAI_CHAU_TEMP_STATIONS.get(lang, _KAU_SAI_CHAU_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kau_sai_chau_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Kau Sai Chau temperature is available."""
    return _unavailable("No Kau Sai Chau temperature is available.", as_json=as_json)


_KADOORIE_FARM_TEMP_STATIONS = {
    "en": "Kadoorie Farm and Botanic Garden",
    "tc": "嘉道理農場暨植物園",
    "sc": "嘉道理农场暨植物园",
}


def parse_kadoorie_farm_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kadoorie Farm mean-temperature CSV into the latest numeric day."""
    station = _KADOORIE_FARM_TEMP_STATIONS.get(lang, _KADOORIE_FARM_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kadoorie_farm_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Kadoorie Farm and Botanic Garden temperature is available."""
    return _unavailable(
        "No Kadoorie Farm and Botanic Garden temperature is available.",
        as_json=as_json,
    )


_THE_PEAK_TEMP_STATIONS = {
    "en": "The Peak",
    "tc": "山頂",
    "sc": "山顶",
}


def parse_the_peak_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn The Peak mean-temperature CSV into the latest numeric day."""
    station = _THE_PEAK_TEMP_STATIONS.get(lang, _THE_PEAK_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_the_peak_temp_miss(*, as_json: bool = False) -> str:
    """Say that no The Peak temperature is available."""
    return _unavailable("No The Peak temperature is available.", as_json=as_json)


_KAT_O_TEMP_STATIONS = {
    "en": "Kat O",
    "tc": "吉澳",
    "sc": "吉澳",
}


def parse_kat_o_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kat O mean-temperature CSV into the latest numeric day."""
    station = _KAT_O_TEMP_STATIONS.get(lang, _KAT_O_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kat_o_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Kat O temperature is available."""
    return _unavailable("No Kat O temperature is available.", as_json=as_json)


_PAK_TAM_CHUNG_TEMP_STATIONS = {
    "en": "Pak Tam Chung (Tsak Yue Wu)",
    "tc": "北潭涌(鯽魚湖)",
    "sc": "北潭涌(鲫鱼湖)",
}


def parse_pak_tam_chung_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Pak Tam Chung mean-temperature CSV into the latest numeric day."""
    station = _PAK_TAM_CHUNG_TEMP_STATIONS.get(lang, _PAK_TAM_CHUNG_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_pak_tam_chung_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Pak Tam Chung (Tsak Yue Wu) temperature is available."""
    return _unavailable(
        "No Pak Tam Chung (Tsak Yue Wu) temperature is available.", as_json=as_json
    )


_BEAS_RIVER_TEMP_STATIONS = {
    "en": "Beas River",
    "tc": "上水雙魚河",
    "sc": "上水双鱼河",
}


def parse_beas_river_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Beas River mean-temperature CSV into the latest numeric day."""
    station = _BEAS_RIVER_TEMP_STATIONS.get(lang, _BEAS_RIVER_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_beas_river_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Beas River temperature is available."""
    return _unavailable("No Beas River temperature is available.", as_json=as_json)


_BLUFF_HEAD_TEMP_STATIONS = {
    "en": "Bluff Head",
    "tc": "黃麻角",
    "sc": "黄麻角",
}


def parse_bluff_head_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Bluff Head mean-temperature CSV into the latest numeric day."""
    station = _BLUFF_HEAD_TEMP_STATIONS.get(lang, _BLUFF_HEAD_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_bluff_head_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Bluff Head temperature is available."""
    return _unavailable("No Bluff Head temperature is available.", as_json=as_json)


_RUNWAY_PARK_TEMP_STATIONS = {
    "en": "Kai Tak Runway Park",
    "tc": "啟德跑道公園",
    "sc": "启德跑道公园",
}


def parse_runway_park_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kai Tak Runway Park mean-temperature CSV into the latest numeric day."""
    station = _RUNWAY_PARK_TEMP_STATIONS.get(lang, _RUNWAY_PARK_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_runway_park_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Kai Tak Runway Park temperature is available."""
    return _unavailable(
        "No Kai Tak Runway Park temperature is available.", as_json=as_json
    )


_KOWLOON_CITY_TEMP_STATIONS = {
    "en": "Kowloon City",
    "tc": "九龍城",
    "sc": "九龙城",
}


def parse_kowloon_city_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kowloon City mean-temperature CSV into the latest numeric day."""
    station = _KOWLOON_CITY_TEMP_STATIONS.get(lang, _KOWLOON_CITY_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kowloon_city_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Kowloon City temperature is available."""
    return _unavailable("No Kowloon City temperature is available.", as_json=as_json)


_NEI_LAK_SHAN_TEMP_STATIONS = {
    "en": "Nei Lak Shan",
    "tc": "彌勒山",
    "sc": "弥勒山",
}


def parse_nei_lak_shan_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Nei Lak Shan mean-temperature CSV into the latest numeric day."""
    station = _NEI_LAK_SHAN_TEMP_STATIONS.get(lang, _NEI_LAK_SHAN_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_nei_lak_shan_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Nei Lak Shan temperature is available."""
    return _unavailable("No Nei Lak Shan temperature is available.", as_json=as_json)


_NEW_TSING_YI_TEMP_STATIONS = {
    "en": "New Tsing Yi Station",
    "tc": "新青衣站",
    "sc": "新青衣站",
}


def parse_new_tsing_yi_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the New Tsing Yi Station mean-temperature CSV into the latest numeric day."""
    station = _NEW_TSING_YI_TEMP_STATIONS.get(lang, _NEW_TSING_YI_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_new_tsing_yi_temp_miss(*, as_json: bool = False) -> str:
    """Say that no New Tsing Yi Station temperature is available."""
    return _unavailable(
        "No New Tsing Yi Station temperature is available.", as_json=as_json
    )


_STANLEY_TEMP_STATIONS = {
    "en": "Stanley",
    "tc": "赤柱",
    "sc": "赤柱",
}


def parse_stanley_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Stanley mean-temperature CSV into the latest numeric day."""
    station = _STANLEY_TEMP_STATIONS.get(lang, _STANLEY_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_stanley_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Stanley temperature is available."""
    return _unavailable("No Stanley temperature is available.", as_json=as_json)


_SHING_MUN_VALLEY_TEMP_STATIONS = {
    "en": "Tsuen Wan Shing Mun Valley",
    "tc": "荃灣城門谷",
    "sc": "荃湾城门谷",
}


def parse_shing_mun_valley_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Shing Mun Valley temperature CSV into the latest numeric day."""
    station = _SHING_MUN_VALLEY_TEMP_STATIONS.get(
        lang, _SHING_MUN_VALLEY_TEMP_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shing_mun_valley_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan Shing Mun Valley temperature is available."""
    return _unavailable(
        "No Tsuen Wan Shing Mun Valley temperature is available.", as_json=as_json
    )


_TUEN_MUN_HOME_TEMP_STATIONS = {
    "en": "Tuen Mun Children and Juvenile Home",
    "tc": "屯門兒童及青少年院",
    "sc": "屯门儿童及青少年院",
}


def parse_tuen_mun_home_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tuen Mun Children and Juvenile Home temperature CSV into the latest numeric day."""
    station = _TUEN_MUN_HOME_TEMP_STATIONS.get(lang, _TUEN_MUN_HOME_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tuen_mun_home_temp_miss(*, as_json: bool = False) -> str:
    """Say that no Tuen Mun Children and Juvenile Home temperature is available."""
    return _unavailable(
        "No Tuen Mun Children and Juvenile Home temperature is available.",
        as_json=as_json,
    )


_BUOY_2_TEMP_STATIONS = {
    "en": "Automatic Weather Buoy No.2 (Hong Kong International Airport, West)",
    "tc": "自動氣象浮標2號 (香港國際機場西面)",
    "sc": "自动气象浮标2号 (香港国际机场西面)",
}


def parse_buoy_2_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the weather buoy No.2 temperature CSV into the latest numeric day."""
    station = _BUOY_2_TEMP_STATIONS.get(lang, _BUOY_2_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_2_temp_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.2 temperature is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) "
        "temperature is available.",
        as_json=as_json,
    )


_BUOY_8_TEMP_STATIONS = {
    "en": "Automatic Weather Buoy No.8 (Hong Kong International Airport, East)",
    "tc": "自動氣象浮標8號 (香港國際機場東面)",
    "sc": "自动气象浮标8号 (香港国际机场东面)",
}


def parse_buoy_8_temp(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the weather buoy No.8 temperature CSV into the latest numeric day."""
    station = _BUOY_8_TEMP_STATIONS.get(lang, _BUOY_8_TEMP_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_8_temp_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.8 temperature is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.8 (Hong Kong International Airport, East) "
        "temperature is available.",
        as_json=as_json,
    )


def parse_tai_mo_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tai Mo Shan minimum-temperature CSV into the latest numeric day."""
    station = _TAI_MO_STATIONS.get(lang, _TAI_MO_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_min(reading: TaiMoTemp) -> str:
    """Render the latest daily minimum temperature at Tai Mo Shan."""
    return (
        "Hong Kong daily minimum temperature\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.temperature_c)}°C\n"
    )


def format_tai_mo_min_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo Shan minimum temperature is available."""
    return _unavailable("No Tai Mo Shan minimum temperature is available.", as_json=as_json)


_TATE_MIN_STATIONS = {
    "en": "Tate's Cairn",
    "tc": "大老山",
    "sc": "大老山",
}


def parse_tate_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tate's Cairn minimum-temperature CSV into the latest numeric day."""
    station = _TATE_MIN_STATIONS.get(lang, _TATE_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tate_min_miss(*, as_json: bool = False) -> str:
    """Say that no Tate's Cairn minimum temperature is available."""
    return _unavailable("No Tate's Cairn minimum temperature is available.", as_json=as_json)


_SAI_KUNG_MIN_STATIONS = {
    "en": "Sai Kung",
    "tc": "西貢",
    "sc": "西贡",
}


def parse_sai_kung_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sai Kung minimum-temperature CSV into the latest numeric day."""
    station = _SAI_KUNG_MIN_STATIONS.get(lang, _SAI_KUNG_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sai_kung_min_miss(*, as_json: bool = False) -> str:
    """Say that no Sai Kung minimum temperature is available."""
    return _unavailable("No Sai Kung minimum temperature is available.", as_json=as_json)


_WONG_CHUK_HANG_MIN_STATIONS = {
    "en": "Wong Chuk Hang",
    "tc": "黃竹坑",
    "sc": "黄竹坑",
}


def parse_wong_chuk_hang_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Wong Chuk Hang minimum-temperature CSV into the latest numeric day."""
    station = _WONG_CHUK_HANG_MIN_STATIONS.get(lang, _WONG_CHUK_HANG_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_chuk_hang_min_miss(*, as_json: bool = False) -> str:
    """Say that no Wong Chuk Hang minimum temperature is available."""
    return _unavailable("No Wong Chuk Hang minimum temperature is available.", as_json=as_json)


_WAGLAN_MIN_STATIONS = {
    "en": "Waglan Island",
    "tc": "橫瀾島",
    "sc": "横澜岛",
}


def parse_waglan_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Waglan Island minimum-temperature CSV into the latest numeric day."""
    station = _WAGLAN_MIN_STATIONS.get(lang, _WAGLAN_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_waglan_min_miss(*, as_json: bool = False) -> str:
    """Say that no Waglan Island minimum temperature is available."""
    return _unavailable("No Waglan Island minimum temperature is available.", as_json=as_json)


_SHA_TIN_MIN_STATIONS = {
    "en": "Sha Tin",
    "tc": "沙田",
    "sc": "沙田",
}


def parse_sha_tin_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sha Tin minimum-temperature CSV into the latest numeric day."""
    station = _SHA_TIN_MIN_STATIONS.get(lang, _SHA_TIN_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_tin_min_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Tin minimum temperature is available."""
    return _unavailable("No Sha Tin minimum temperature is available.", as_json=as_json)


_CHEUNG_MIN_STATIONS = {
    "en": "Cheung Chau",
    "tc": "長洲",
    "sc": "长洲",
}


def parse_cheung_chau_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Cheung Chau minimum-temperature CSV into the latest numeric day."""
    station = _CHEUNG_MIN_STATIONS.get(lang, _CHEUNG_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_chau_min_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau minimum temperature is available."""
    return _unavailable("No Cheung Chau minimum temperature is available.", as_json=as_json)


_PARK_MIN_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_park_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the King's Park minimum-temperature CSV into the latest numeric day."""
    station = _PARK_MIN_STATIONS.get(lang, _PARK_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_park_min_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park minimum temperature is available."""
    return _unavailable("No King's Park minimum temperature is available.", as_json=as_json)


_LAU_FAU_MIN_STATIONS = {
    "en": "Lau Fau Shan",
    "tc": "流浮山",
    "sc": "流浮山",
}


def parse_lau_fau_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Lau Fau Shan minimum-temperature CSV into the latest numeric day."""
    station = _LAU_FAU_MIN_STATIONS.get(lang, _LAU_FAU_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lau_fau_min_miss(*, as_json: bool = False) -> str:
    """Say that no Lau Fau Shan minimum temperature is available."""
    return _unavailable("No Lau Fau Shan minimum temperature is available.", as_json=as_json)


_SHEUNG_SHUI_MIN_STATIONS = {
    "en": "Sheung Shui",
    "tc": "上水",
    "sc": "上水",
}


def parse_sheung_shui_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sheung Shui minimum-temperature CSV into the latest numeric day."""
    station = _SHEUNG_SHUI_MIN_STATIONS.get(lang, _SHEUNG_SHUI_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sheung_shui_min_miss(*, as_json: bool = False) -> str:
    """Say that no Sheung Shui minimum temperature is available."""
    return _unavailable("No Sheung Shui minimum temperature is available.", as_json=as_json)


_TSEUNG_KWAN_O_MIN_STATIONS = {
    "en": "Tseung Kwan O",
    "tc": "將軍澳",
    "sc": "将军澳",
}


def parse_tseung_kwan_o_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tseung Kwan O minimum-temperature CSV into the latest numeric day."""
    station = _TSEUNG_KWAN_O_MIN_STATIONS.get(lang, _TSEUNG_KWAN_O_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tseung_kwan_o_min_miss(*, as_json: bool = False) -> str:
    """Say that no Tseung Kwan O minimum temperature is available."""
    return _unavailable(
        "No Tseung Kwan O minimum temperature is available.", as_json=as_json
    )


_SHAM_SHUI_PO_MIN_STATIONS = {
    "en": "Sham Shui Po",
    "tc": "深水埗",
    "sc": "深水埗",
}


def parse_sham_shui_po_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sham Shui Po minimum-temperature CSV into the latest numeric day."""
    station = _SHAM_SHUI_PO_MIN_STATIONS.get(lang, _SHAM_SHUI_PO_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sham_shui_po_min_miss(*, as_json: bool = False) -> str:
    """Say that no Sham Shui Po minimum temperature is available."""
    return _unavailable(
        "No Sham Shui Po minimum temperature is available.", as_json=as_json
    )


_SHEK_KONG_MIN_STATIONS = {
    "en": "Shek Kong",
    "tc": "石崗",
    "sc": "石岗",
}


def parse_shek_kong_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Shek Kong minimum-temperature CSV into the latest numeric day."""
    station = _SHEK_KONG_MIN_STATIONS.get(lang, _SHEK_KONG_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shek_kong_min_miss(*, as_json: bool = False) -> str:
    """Say that no Shek Kong minimum temperature is available."""
    return _unavailable("No Shek Kong minimum temperature is available.", as_json=as_json)


_WETLAND_MIN_STATIONS = {
    "en": "Wetland Park",
    "tc": "濕地公園",
    "sc": "湿地公园",
}


def parse_wetland_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Wetland Park minimum-temperature CSV into the latest numeric day."""
    station = _WETLAND_MIN_STATIONS.get(lang, _WETLAND_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wetland_min_miss(*, as_json: bool = False) -> str:
    """Say that no Wetland Park minimum temperature is available."""
    return _unavailable("No Wetland Park minimum temperature is available.", as_json=as_json)


_TA_KWU_LING_MIN_STATIONS = {
    "en": "Ta Kwu Ling",
    "tc": "打鼓嶺",
    "sc": "打鼓岭",
}


def parse_ta_kwu_ling_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Ta Kwu Ling minimum-temperature CSV into the latest numeric day."""
    station = _TA_KWU_LING_MIN_STATIONS.get(lang, _TA_KWU_LING_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ta_kwu_ling_min_miss(*, as_json: bool = False) -> str:
    """Say that no Ta Kwu Ling minimum temperature is available."""
    return _unavailable(
        "No Ta Kwu Ling minimum temperature is available.", as_json=as_json
    )


_SHA_LO_WAN_MIN_STATIONS = {
    "en": "Sha Lo Wan",
    "tc": "沙螺灣",
    "sc": "沙螺湾",
}


def parse_sha_lo_wan_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sha Lo Wan minimum-temperature CSV into the latest numeric day."""
    station = _SHA_LO_WAN_MIN_STATIONS.get(lang, _SHA_LO_WAN_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_lo_wan_min_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Lo Wan minimum temperature is available."""
    return _unavailable(
        "No Sha Lo Wan minimum temperature is available.", as_json=as_json
    )


_AIRPORT_MIN_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_airport_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the airport minimum-temperature CSV into the latest numeric day."""
    station = _AIRPORT_MIN_STATIONS.get(lang, _AIRPORT_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_airport_min_miss(*, as_json: bool = False) -> str:
    """Say that no airport minimum temperature is available."""
    return _unavailable("No airport minimum temperature is available.", as_json=as_json)


_YUEN_LONG_PARK_MIN_STATIONS = {
    "en": "Yuen Long Park",
    "tc": "元朗公園",
    "sc": "元朗公园",
}


def parse_yuen_long_park_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Yuen Long Park minimum-temperature CSV into the latest numeric day."""
    station = _YUEN_LONG_PARK_MIN_STATIONS.get(
        lang, _YUEN_LONG_PARK_MIN_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_yuen_long_park_min_miss(*, as_json: bool = False) -> str:
    """Say that no Yuen Long Park minimum temperature is available."""
    return _unavailable(
        "No Yuen Long Park minimum temperature is available.", as_json=as_json
    )


_CLEAR_WATER_BAY_MIN_STATIONS = {
    "en": "Clear Water Bay",
    "tc": "清水灣",
    "sc": "清水湾",
}


def parse_clear_water_bay_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Clear Water Bay minimum-temperature CSV into the latest numeric day."""
    station = _CLEAR_WATER_BAY_MIN_STATIONS.get(
        lang, _CLEAR_WATER_BAY_MIN_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_clear_water_bay_min_miss(*, as_json: bool = False) -> str:
    """Say that no Clear Water Bay minimum temperature is available."""
    return _unavailable(
        "No Clear Water Bay minimum temperature is available.", as_json=as_json
    )


_TAP_MUN_MIN_STATIONS = {
    "en": "Tap Mun",
    "tc": "塔門",
    "sc": "塔门",
}


def parse_tap_mun_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tap Mun minimum-temperature CSV into the latest numeric day."""
    station = _TAP_MUN_MIN_STATIONS.get(lang, _TAP_MUN_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tap_mun_min_miss(*, as_json: bool = False) -> str:
    """Say that no Tap Mun minimum temperature is available."""
    return _unavailable("No Tap Mun minimum temperature is available.", as_json=as_json)


_HONG_KONG_PARK_MIN_STATIONS = {
    "en": "Hong Kong Park",
    "tc": "香港公園",
    "sc": "香港公园",
}


def parse_hong_kong_park_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Hong Kong Park minimum-temperature CSV into the latest numeric day."""
    station = _HONG_KONG_PARK_MIN_STATIONS.get(
        lang, _HONG_KONG_PARK_MIN_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_hong_kong_park_min_miss(*, as_json: bool = False) -> str:
    """Say that no Hong Kong Park minimum temperature is available."""
    return _unavailable(
        "No Hong Kong Park minimum temperature is available.", as_json=as_json
    )


_NGONG_PING_MIN_STATIONS = {
    "en": "Ngong Ping",
    "tc": "昂坪",
    "sc": "昂坪",
}


def parse_ngong_ping_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Ngong Ping minimum-temperature CSV into the latest numeric day."""
    station = _NGONG_PING_MIN_STATIONS.get(lang, _NGONG_PING_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ngong_ping_min_miss(*, as_json: bool = False) -> str:
    """Say that no Ngong Ping minimum temperature is available."""
    return _unavailable(
        "No Ngong Ping minimum temperature is available.", as_json=as_json
    )


_KWUN_TONG_MIN_STATIONS = {
    "en": "Kwun Tong",
    "tc": "觀塘",
    "sc": "观塘",
}


def parse_kwun_tong_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kwun Tong minimum-temperature CSV into the latest numeric day."""
    station = _KWUN_TONG_MIN_STATIONS.get(lang, _KWUN_TONG_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kwun_tong_min_miss(*, as_json: bool = False) -> str:
    """Say that no Kwun Tong minimum temperature is available."""
    return _unavailable(
        "No Kwun Tong minimum temperature is available.", as_json=as_json
    )


_WONG_TAI_SIN_MIN_STATIONS = {
    "en": "Wong Tai Sin",
    "tc": "黃大仙",
    "sc": "黄大仙",
}


def parse_wong_tai_sin_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Wong Tai Sin minimum-temperature CSV into the latest numeric day."""
    station = _WONG_TAI_SIN_MIN_STATIONS.get(lang, _WONG_TAI_SIN_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_tai_sin_min_miss(*, as_json: bool = False) -> str:
    """Say that no Wong Tai Sin minimum temperature is available."""
    return _unavailable(
        "No Wong Tai Sin minimum temperature is available.", as_json=as_json
    )


_TSUEN_WAN_MIN_STATIONS = {
    "en": "Tsuen Wan",
    "tc": "荃灣",
    "sc": "荃湾",
}


def parse_tsuen_wan_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tsuen Wan minimum-temperature CSV into the latest numeric day."""
    station = _TSUEN_WAN_MIN_STATIONS.get(lang, _TSUEN_WAN_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tsuen_wan_min_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan minimum temperature is available."""
    return _unavailable(
        "No Tsuen Wan minimum temperature is available.", as_json=as_json
    )


_KAU_SAI_CHAU_MIN_STATIONS = {
    "en": "Kau Sai Chau",
    "tc": "滘西洲",
    "sc": "滘西洲",
}


def parse_kau_sai_chau_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kau Sai Chau minimum-temperature CSV into the latest numeric day."""
    station = _KAU_SAI_CHAU_MIN_STATIONS.get(lang, _KAU_SAI_CHAU_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kau_sai_chau_min_miss(*, as_json: bool = False) -> str:
    """Say that no Kau Sai Chau minimum temperature is available."""
    return _unavailable(
        "No Kau Sai Chau minimum temperature is available.", as_json=as_json
    )


_KADOORIE_FARM_MIN_STATIONS = {
    "en": "Kadoorie Farm and Botanic Garden",
    "tc": "嘉道理農場暨植物園",
    "sc": "嘉道理农场暨植物园",
}


def parse_kadoorie_farm_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kadoorie Farm minimum-temperature CSV into the latest numeric day."""
    station = _KADOORIE_FARM_MIN_STATIONS.get(lang, _KADOORIE_FARM_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kadoorie_farm_min_miss(*, as_json: bool = False) -> str:
    """Say that no Kadoorie Farm and Botanic Garden minimum temperature is available."""
    return _unavailable(
        "No Kadoorie Farm and Botanic Garden minimum temperature is available.",
        as_json=as_json,
    )


_THE_PEAK_MIN_STATIONS = {
    "en": "The Peak",
    "tc": "山頂",
    "sc": "山顶",
}


def parse_the_peak_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn The Peak minimum-temperature CSV into the latest numeric day."""
    station = _THE_PEAK_MIN_STATIONS.get(lang, _THE_PEAK_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_the_peak_min_miss(*, as_json: bool = False) -> str:
    """Say that no The Peak minimum temperature is available."""
    return _unavailable(
        "No The Peak minimum temperature is available.", as_json=as_json
    )


_KAT_O_MIN_STATIONS = {
    "en": "Kat O",
    "tc": "吉澳",
    "sc": "吉澳",
}


def parse_kat_o_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kat O minimum-temperature CSV into the latest numeric day."""
    station = _KAT_O_MIN_STATIONS.get(lang, _KAT_O_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kat_o_min_miss(*, as_json: bool = False) -> str:
    """Say that no Kat O minimum temperature is available."""
    return _unavailable("No Kat O minimum temperature is available.", as_json=as_json)


_PAK_TAM_CHUNG_MIN_STATIONS = {
    "en": "Pak Tam Chung (Tsak Yue Wu)",
    "tc": "北潭涌(鯽魚湖)",
    "sc": "北潭涌(鲫鱼湖)",
}


def parse_pak_tam_chung_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Pak Tam Chung minimum-temperature CSV into the latest numeric day."""
    station = _PAK_TAM_CHUNG_MIN_STATIONS.get(lang, _PAK_TAM_CHUNG_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_pak_tam_chung_min_miss(*, as_json: bool = False) -> str:
    """Say that no Pak Tam Chung (Tsak Yue Wu) minimum temperature is available."""
    return _unavailable(
        "No Pak Tam Chung (Tsak Yue Wu) minimum temperature is available.",
        as_json=as_json,
    )


_BEAS_RIVER_MIN_STATIONS = {
    "en": "Beas River",
    "tc": "上水雙魚河",
    "sc": "上水双鱼河",
}


def parse_beas_river_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Beas River minimum-temperature CSV into the latest numeric day."""
    station = _BEAS_RIVER_MIN_STATIONS.get(lang, _BEAS_RIVER_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_beas_river_min_miss(*, as_json: bool = False) -> str:
    """Say that no Beas River minimum temperature is available."""
    return _unavailable(
        "No Beas River minimum temperature is available.", as_json=as_json
    )


_KOWLOON_CITY_MIN_STATIONS = {
    "en": "Kowloon City",
    "tc": "九龍城",
    "sc": "九龙城",
}


def parse_kowloon_city_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kowloon City minimum-temperature CSV into the latest numeric day."""
    station = _KOWLOON_CITY_MIN_STATIONS.get(lang, _KOWLOON_CITY_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kowloon_city_min_miss(*, as_json: bool = False) -> str:
    """Say that no Kowloon City minimum temperature is available."""
    return _unavailable(
        "No Kowloon City minimum temperature is available.", as_json=as_json
    )


_NEW_TSING_YI_MIN_STATIONS = {
    "en": "New Tsing Yi Station",
    "tc": "新青衣站",
    "sc": "新青衣站",
}


def parse_new_tsing_yi_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the New Tsing Yi Station minimum-temperature CSV into the latest numeric day."""
    station = _NEW_TSING_YI_MIN_STATIONS.get(lang, _NEW_TSING_YI_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_new_tsing_yi_min_miss(*, as_json: bool = False) -> str:
    """Say that no New Tsing Yi Station minimum temperature is available."""
    return _unavailable(
        "No New Tsing Yi Station minimum temperature is available.", as_json=as_json
    )


_STANLEY_MIN_STATIONS = {
    "en": "Stanley",
    "tc": "赤柱",
    "sc": "赤柱",
}


def parse_stanley_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Stanley minimum-temperature CSV into the latest numeric day."""
    station = _STANLEY_MIN_STATIONS.get(lang, _STANLEY_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_stanley_min_miss(*, as_json: bool = False) -> str:
    """Say that no Stanley minimum temperature is available."""
    return _unavailable(
        "No Stanley minimum temperature is available.", as_json=as_json
    )


_SHING_MUN_VALLEY_MIN_STATIONS = {
    "en": "Tsuen Wan Shing Mun Valley",
    "tc": "荃灣城門谷",
    "sc": "荃湾城门谷",
}


def parse_shing_mun_valley_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Shing Mun Valley minimum-temperature CSV into the latest numeric day."""
    station = _SHING_MUN_VALLEY_MIN_STATIONS.get(
        lang, _SHING_MUN_VALLEY_MIN_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shing_mun_valley_min_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan Shing Mun Valley minimum temperature is available."""
    return _unavailable(
        "No Tsuen Wan Shing Mun Valley minimum temperature is available.",
        as_json=as_json,
    )


_TUEN_MUN_HOME_MIN_STATIONS = {
    "en": "Tuen Mun Children and Juvenile Home",
    "tc": "屯門兒童及青少年院",
    "sc": "屯门儿童及青少年院",
}


def parse_tuen_mun_home_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tuen Mun Children and Juvenile Home minimum CSV into the latest numeric day."""
    station = _TUEN_MUN_HOME_MIN_STATIONS.get(lang, _TUEN_MUN_HOME_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tuen_mun_home_min_miss(*, as_json: bool = False) -> str:
    """Say that no Tuen Mun Children and Juvenile Home minimum temperature is available."""
    return _unavailable(
        "No Tuen Mun Children and Juvenile Home minimum temperature is available.",
        as_json=as_json,
    )


_BUOY_2_MIN_STATIONS = {
    "en": "Automatic Weather Buoy No.2 (Hong Kong International Airport, West)",
    "tc": "自動氣象浮標2號 (香港國際機場西面)",
    "sc": "自动气象浮标2号 (香港国际机场西面)",
}


def parse_buoy_2_min(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the weather buoy No.2 minimum CSV into the latest numeric day."""
    station = _BUOY_2_MIN_STATIONS.get(lang, _BUOY_2_MIN_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_2_min_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.2 minimum temperature is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) "
        "minimum temperature is available.",
        as_json=as_json,
    )


def parse_tai_mo_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tai Mo Shan maximum-temperature CSV into the latest numeric day."""
    station = _TAI_MO_STATIONS.get(lang, _TAI_MO_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_max(reading: TaiMoTemp) -> str:
    """Render the latest daily maximum temperature at Tai Mo Shan."""
    return (
        "Hong Kong daily maximum temperature\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.temperature_c)}°C\n"
    )


def format_tai_mo_max_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo Shan maximum temperature is available."""
    return _unavailable("No Tai Mo Shan maximum temperature is available.", as_json=as_json)


_TSEUNG_KWAN_O_STATIONS = {
    "en": "Tseung Kwan O",
    "tc": "將軍澳",
    "sc": "将军澳",
}


def parse_tseung_kwan_o_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tseung Kwan O maximum-temperature CSV into the latest numeric day."""
    station = _TSEUNG_KWAN_O_STATIONS.get(lang, _TSEUNG_KWAN_O_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tseung_kwan_o_max_miss(*, as_json: bool = False) -> str:
    """Say that no Tseung Kwan O maximum temperature is available."""
    return _unavailable(
        "No Tseung Kwan O maximum temperature is available.", as_json=as_json
    )


_SHEUNG_SHUI_STATIONS = {
    "en": "Sheung Shui",
    "tc": "上水",
    "sc": "上水",
}


def parse_sheung_shui_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sheung Shui maximum-temperature CSV into the latest numeric day."""
    station = _SHEUNG_SHUI_STATIONS.get(lang, _SHEUNG_SHUI_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sheung_shui_max_miss(*, as_json: bool = False) -> str:
    """Say that no Sheung Shui maximum temperature is available."""
    return _unavailable(
        "No Sheung Shui maximum temperature is available.", as_json=as_json
    )


_WAGLAN_MAX_STATIONS = {
    "en": "Waglan Island",
    "tc": "橫瀾島",
    "sc": "横澜岛",
}


def parse_waglan_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Waglan Island maximum-temperature CSV into the latest numeric day."""
    station = _WAGLAN_MAX_STATIONS.get(lang, _WAGLAN_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_waglan_max_miss(*, as_json: bool = False) -> str:
    """Say that no Waglan Island maximum temperature is available."""
    return _unavailable(
        "No Waglan Island maximum temperature is available.", as_json=as_json
    )


_SHEK_KONG_MAX_STATIONS = {
    "en": "Shek Kong",
    "tc": "石崗",
    "sc": "石岗",
}


def parse_shek_kong_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Shek Kong maximum-temperature CSV into the latest numeric day."""
    station = _SHEK_KONG_MAX_STATIONS.get(lang, _SHEK_KONG_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shek_kong_max_miss(*, as_json: bool = False) -> str:
    """Say that no Shek Kong maximum temperature is available."""
    return _unavailable("No Shek Kong maximum temperature is available.", as_json=as_json)


_CHEUNG_MAX_STATIONS = {
    "en": "Cheung Chau",
    "tc": "長洲",
    "sc": "长洲",
}


def parse_cheung_chau_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Cheung Chau maximum-temperature CSV into the latest numeric day."""
    station = _CHEUNG_MAX_STATIONS.get(lang, _CHEUNG_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_chau_max_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau maximum temperature is available."""
    return _unavailable("No Cheung Chau maximum temperature is available.", as_json=as_json)


_PARK_MAX_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_park_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the King's Park maximum-temperature CSV into the latest numeric day."""
    station = _PARK_MAX_STATIONS.get(lang, _PARK_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_park_max_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park maximum temperature is available."""
    return _unavailable("No King's Park maximum temperature is available.", as_json=as_json)


_LAU_FAU_MAX_STATIONS = {
    "en": "Lau Fau Shan",
    "tc": "流浮山",
    "sc": "流浮山",
}


def parse_lau_fau_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Lau Fau Shan maximum-temperature CSV into the latest numeric day."""
    station = _LAU_FAU_MAX_STATIONS.get(lang, _LAU_FAU_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lau_fau_max_miss(*, as_json: bool = False) -> str:
    """Say that no Lau Fau Shan maximum temperature is available."""
    return _unavailable("No Lau Fau Shan maximum temperature is available.", as_json=as_json)


_SAI_KUNG_MAX_STATIONS = {
    "en": "Sai Kung",
    "tc": "西貢",
    "sc": "西贡",
}


def parse_sai_kung_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sai Kung maximum-temperature CSV into the latest numeric day."""
    station = _SAI_KUNG_MAX_STATIONS.get(lang, _SAI_KUNG_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sai_kung_max_miss(*, as_json: bool = False) -> str:
    """Say that no Sai Kung maximum temperature is available."""
    return _unavailable("No Sai Kung maximum temperature is available.", as_json=as_json)


_SHA_TIN_MAX_STATIONS = {
    "en": "Sha Tin",
    "tc": "沙田",
    "sc": "沙田",
}


def parse_sha_tin_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sha Tin maximum-temperature CSV into the latest numeric day."""
    station = _SHA_TIN_MAX_STATIONS.get(lang, _SHA_TIN_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_tin_max_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Tin maximum temperature is available."""
    return _unavailable("No Sha Tin maximum temperature is available.", as_json=as_json)


_TATE_MAX_STATIONS = {
    "en": "Tate's Cairn",
    "tc": "大老山",
    "sc": "大老山",
}


def parse_tate_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tate's Cairn maximum-temperature CSV into the latest numeric day."""
    station = _TATE_MAX_STATIONS.get(lang, _TATE_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tate_max_miss(*, as_json: bool = False) -> str:
    """Say that no Tate's Cairn maximum temperature is available."""
    return _unavailable("No Tate's Cairn maximum temperature is available.", as_json=as_json)


_WONG_CHUK_HANG_MAX_STATIONS = {
    "en": "Wong Chuk Hang",
    "tc": "黃竹坑",
    "sc": "黄竹坑",
}


def parse_wong_chuk_hang_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Wong Chuk Hang maximum-temperature CSV into the latest numeric day."""
    station = _WONG_CHUK_HANG_MAX_STATIONS.get(lang, _WONG_CHUK_HANG_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_chuk_hang_max_miss(*, as_json: bool = False) -> str:
    """Say that no Wong Chuk Hang maximum temperature is available."""
    return _unavailable("No Wong Chuk Hang maximum temperature is available.", as_json=as_json)


_SHAM_SHUI_PO_MAX_STATIONS = {
    "en": "Sham Shui Po",
    "tc": "深水埗",
    "sc": "深水埗",
}


def parse_sham_shui_po_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sham Shui Po maximum-temperature CSV into the latest numeric day."""
    station = _SHAM_SHUI_PO_MAX_STATIONS.get(lang, _SHAM_SHUI_PO_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sham_shui_po_max_miss(*, as_json: bool = False) -> str:
    """Say that no Sham Shui Po maximum temperature is available."""
    return _unavailable(
        "No Sham Shui Po maximum temperature is available.", as_json=as_json
    )


_WETLAND_MAX_STATIONS = {
    "en": "Wetland Park",
    "tc": "濕地公園",
    "sc": "湿地公园",
}


def parse_wetland_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Wetland Park maximum-temperature CSV into the latest numeric day."""
    station = _WETLAND_MAX_STATIONS.get(lang, _WETLAND_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wetland_max_miss(*, as_json: bool = False) -> str:
    """Say that no Wetland Park maximum temperature is available."""
    return _unavailable(
        "No Wetland Park maximum temperature is available.", as_json=as_json
    )


_TA_KWU_LING_MAX_STATIONS = {
    "en": "Ta Kwu Ling",
    "tc": "打鼓嶺",
    "sc": "打鼓岭",
}


def parse_ta_kwu_ling_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Ta Kwu Ling maximum-temperature CSV into the latest numeric day."""
    station = _TA_KWU_LING_MAX_STATIONS.get(lang, _TA_KWU_LING_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ta_kwu_ling_max_miss(*, as_json: bool = False) -> str:
    """Say that no Ta Kwu Ling maximum temperature is available."""
    return _unavailable(
        "No Ta Kwu Ling maximum temperature is available.", as_json=as_json
    )


_SHA_LO_WAN_MAX_STATIONS = {
    "en": "Sha Lo Wan",
    "tc": "沙螺灣",
    "sc": "沙螺湾",
}


def parse_sha_lo_wan_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Sha Lo Wan maximum-temperature CSV into the latest numeric day."""
    station = _SHA_LO_WAN_MAX_STATIONS.get(lang, _SHA_LO_WAN_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_lo_wan_max_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Lo Wan maximum temperature is available."""
    return _unavailable(
        "No Sha Lo Wan maximum temperature is available.", as_json=as_json
    )


_AIRPORT_MAX_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_airport_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the airport maximum-temperature CSV into the latest numeric day."""
    station = _AIRPORT_MAX_STATIONS.get(lang, _AIRPORT_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_airport_max_miss(*, as_json: bool = False) -> str:
    """Say that no airport maximum temperature is available."""
    return _unavailable("No airport maximum temperature is available.", as_json=as_json)


_YUEN_LONG_PARK_MAX_STATIONS = {
    "en": "Yuen Long Park",
    "tc": "元朗公園",
    "sc": "元朗公园",
}


def parse_yuen_long_park_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Yuen Long Park maximum-temperature CSV into the latest numeric day."""
    station = _YUEN_LONG_PARK_MAX_STATIONS.get(
        lang, _YUEN_LONG_PARK_MAX_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_yuen_long_park_max_miss(*, as_json: bool = False) -> str:
    """Say that no Yuen Long Park maximum temperature is available."""
    return _unavailable(
        "No Yuen Long Park maximum temperature is available.", as_json=as_json
    )


_CLEAR_WATER_BAY_MAX_STATIONS = {
    "en": "Clear Water Bay",
    "tc": "清水灣",
    "sc": "清水湾",
}


def parse_clear_water_bay_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Clear Water Bay maximum-temperature CSV into the latest numeric day."""
    station = _CLEAR_WATER_BAY_MAX_STATIONS.get(
        lang, _CLEAR_WATER_BAY_MAX_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_clear_water_bay_max_miss(*, as_json: bool = False) -> str:
    """Say that no Clear Water Bay maximum temperature is available."""
    return _unavailable(
        "No Clear Water Bay maximum temperature is available.", as_json=as_json
    )


_TAP_MUN_MAX_STATIONS = {
    "en": "Tap Mun",
    "tc": "塔門",
    "sc": "塔门",
}


def parse_tap_mun_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tap Mun maximum-temperature CSV into the latest numeric day."""
    station = _TAP_MUN_MAX_STATIONS.get(lang, _TAP_MUN_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tap_mun_max_miss(*, as_json: bool = False) -> str:
    """Say that no Tap Mun maximum temperature is available."""
    return _unavailable("No Tap Mun maximum temperature is available.", as_json=as_json)


_HONG_KONG_PARK_MAX_STATIONS = {
    "en": "Hong Kong Park",
    "tc": "香港公園",
    "sc": "香港公园",
}


def parse_hong_kong_park_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Hong Kong Park maximum-temperature CSV into the latest numeric day."""
    station = _HONG_KONG_PARK_MAX_STATIONS.get(
        lang, _HONG_KONG_PARK_MAX_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_hong_kong_park_max_miss(*, as_json: bool = False) -> str:
    """Say that no Hong Kong Park maximum temperature is available."""
    return _unavailable(
        "No Hong Kong Park maximum temperature is available.", as_json=as_json
    )


_NGONG_PING_MAX_STATIONS = {
    "en": "Ngong Ping",
    "tc": "昂坪",
    "sc": "昂坪",
}


def parse_ngong_ping_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Ngong Ping maximum-temperature CSV into the latest numeric day."""
    station = _NGONG_PING_MAX_STATIONS.get(lang, _NGONG_PING_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ngong_ping_max_miss(*, as_json: bool = False) -> str:
    """Say that no Ngong Ping maximum temperature is available."""
    return _unavailable(
        "No Ngong Ping maximum temperature is available.", as_json=as_json
    )


_KWUN_TONG_MAX_STATIONS = {
    "en": "Kwun Tong",
    "tc": "觀塘",
    "sc": "观塘",
}


def parse_kwun_tong_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kwun Tong maximum-temperature CSV into the latest numeric day."""
    station = _KWUN_TONG_MAX_STATIONS.get(lang, _KWUN_TONG_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kwun_tong_max_miss(*, as_json: bool = False) -> str:
    """Say that no Kwun Tong maximum temperature is available."""
    return _unavailable(
        "No Kwun Tong maximum temperature is available.", as_json=as_json
    )


_WONG_TAI_SIN_MAX_STATIONS = {
    "en": "Wong Tai Sin",
    "tc": "黃大仙",
    "sc": "黄大仙",
}


def parse_wong_tai_sin_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Wong Tai Sin maximum-temperature CSV into the latest numeric day."""
    station = _WONG_TAI_SIN_MAX_STATIONS.get(lang, _WONG_TAI_SIN_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_tai_sin_max_miss(*, as_json: bool = False) -> str:
    """Say that no Wong Tai Sin maximum temperature is available."""
    return _unavailable(
        "No Wong Tai Sin maximum temperature is available.", as_json=as_json
    )


_TSUEN_WAN_MAX_STATIONS = {
    "en": "Tsuen Wan",
    "tc": "荃灣",
    "sc": "荃湾",
}


def parse_tsuen_wan_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tsuen Wan maximum-temperature CSV into the latest numeric day."""
    station = _TSUEN_WAN_MAX_STATIONS.get(lang, _TSUEN_WAN_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tsuen_wan_max_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan maximum temperature is available."""
    return _unavailable(
        "No Tsuen Wan maximum temperature is available.", as_json=as_json
    )


_KAU_SAI_CHAU_MAX_STATIONS = {
    "en": "Kau Sai Chau",
    "tc": "滘西洲",
    "sc": "滘西洲",
}


def parse_kau_sai_chau_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kau Sai Chau maximum-temperature CSV into the latest numeric day."""
    station = _KAU_SAI_CHAU_MAX_STATIONS.get(lang, _KAU_SAI_CHAU_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kau_sai_chau_max_miss(*, as_json: bool = False) -> str:
    """Say that no Kau Sai Chau maximum temperature is available."""
    return _unavailable(
        "No Kau Sai Chau maximum temperature is available.", as_json=as_json
    )


_KADOORIE_FARM_MAX_STATIONS = {
    "en": "Kadoorie Farm and Botanic Garden",
    "tc": "嘉道理農場暨植物園",
    "sc": "嘉道理农场暨植物园",
}


def parse_kadoorie_farm_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kadoorie Farm maximum-temperature CSV into the latest numeric day."""
    station = _KADOORIE_FARM_MAX_STATIONS.get(lang, _KADOORIE_FARM_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kadoorie_farm_max_miss(*, as_json: bool = False) -> str:
    """Say that no Kadoorie Farm and Botanic Garden maximum temperature is available."""
    return _unavailable(
        "No Kadoorie Farm and Botanic Garden maximum temperature is available.",
        as_json=as_json,
    )


_THE_PEAK_MAX_STATIONS = {
    "en": "The Peak",
    "tc": "山頂",
    "sc": "山顶",
}


def parse_the_peak_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn The Peak maximum-temperature CSV into the latest numeric day."""
    station = _THE_PEAK_MAX_STATIONS.get(lang, _THE_PEAK_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_the_peak_max_miss(*, as_json: bool = False) -> str:
    """Say that no The Peak maximum temperature is available."""
    return _unavailable(
        "No The Peak maximum temperature is available.", as_json=as_json
    )


_KAT_O_MAX_STATIONS = {
    "en": "Kat O",
    "tc": "吉澳",
    "sc": "吉澳",
}


def parse_kat_o_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kat O maximum-temperature CSV into the latest numeric day."""
    station = _KAT_O_MAX_STATIONS.get(lang, _KAT_O_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kat_o_max_miss(*, as_json: bool = False) -> str:
    """Say that no Kat O maximum temperature is available."""
    return _unavailable("No Kat O maximum temperature is available.", as_json=as_json)


_PAK_TAM_CHUNG_MAX_STATIONS = {
    "en": "Pak Tam Chung (Tsak Yue Wu)",
    "tc": "北潭涌(鯽魚湖)",
    "sc": "北潭涌(鲫鱼湖)",
}


def parse_pak_tam_chung_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Pak Tam Chung maximum-temperature CSV into the latest numeric day."""
    station = _PAK_TAM_CHUNG_MAX_STATIONS.get(lang, _PAK_TAM_CHUNG_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_pak_tam_chung_max_miss(*, as_json: bool = False) -> str:
    """Say that no Pak Tam Chung (Tsak Yue Wu) maximum temperature is available."""
    return _unavailable(
        "No Pak Tam Chung (Tsak Yue Wu) maximum temperature is available.",
        as_json=as_json,
    )


_BEAS_RIVER_MAX_STATIONS = {
    "en": "Beas River",
    "tc": "上水雙魚河",
    "sc": "上水双鱼河",
}


def parse_beas_river_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Beas River maximum-temperature CSV into the latest numeric day."""
    station = _BEAS_RIVER_MAX_STATIONS.get(lang, _BEAS_RIVER_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_beas_river_max_miss(*, as_json: bool = False) -> str:
    """Say that no Beas River maximum temperature is available."""
    return _unavailable(
        "No Beas River maximum temperature is available.", as_json=as_json
    )


_KOWLOON_CITY_MAX_STATIONS = {
    "en": "Kowloon City",
    "tc": "九龍城",
    "sc": "九龙城",
}


def parse_kowloon_city_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Kowloon City maximum-temperature CSV into the latest numeric day."""
    station = _KOWLOON_CITY_MAX_STATIONS.get(lang, _KOWLOON_CITY_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kowloon_city_max_miss(*, as_json: bool = False) -> str:
    """Say that no Kowloon City maximum temperature is available."""
    return _unavailable(
        "No Kowloon City maximum temperature is available.", as_json=as_json
    )


_NEW_TSING_YI_MAX_STATIONS = {
    "en": "New Tsing Yi Station",
    "tc": "新青衣站",
    "sc": "新青衣站",
}


def parse_new_tsing_yi_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the New Tsing Yi Station maximum-temperature CSV into the latest numeric day."""
    station = _NEW_TSING_YI_MAX_STATIONS.get(lang, _NEW_TSING_YI_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_new_tsing_yi_max_miss(*, as_json: bool = False) -> str:
    """Say that no New Tsing Yi Station maximum temperature is available."""
    return _unavailable(
        "No New Tsing Yi Station maximum temperature is available.", as_json=as_json
    )


_STANLEY_MAX_STATIONS = {
    "en": "Stanley",
    "tc": "赤柱",
    "sc": "赤柱",
}


def parse_stanley_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Stanley maximum-temperature CSV into the latest numeric day."""
    station = _STANLEY_MAX_STATIONS.get(lang, _STANLEY_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_stanley_max_miss(*, as_json: bool = False) -> str:
    """Say that no Stanley maximum temperature is available."""
    return _unavailable(
        "No Stanley maximum temperature is available.", as_json=as_json
    )


_SHING_MUN_VALLEY_MAX_STATIONS = {
    "en": "Tsuen Wan Shing Mun Valley",
    "tc": "荃灣城門谷",
    "sc": "荃湾城门谷",
}


def parse_shing_mun_valley_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Shing Mun Valley maximum-temperature CSV into the latest numeric day."""
    station = _SHING_MUN_VALLEY_MAX_STATIONS.get(
        lang, _SHING_MUN_VALLEY_MAX_STATIONS["en"]
    )
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shing_mun_valley_max_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan Shing Mun Valley maximum temperature is available."""
    return _unavailable(
        "No Tsuen Wan Shing Mun Valley maximum temperature is available.",
        as_json=as_json,
    )


_TUEN_MUN_HOME_MAX_STATIONS = {
    "en": "Tuen Mun Children and Juvenile Home",
    "tc": "屯門兒童及青少年院",
    "sc": "屯门儿童及青少年院",
}


def parse_tuen_mun_home_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the Tuen Mun Children and Juvenile Home maximum CSV into the latest numeric day."""
    station = _TUEN_MUN_HOME_MAX_STATIONS.get(lang, _TUEN_MUN_HOME_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tuen_mun_home_max_miss(*, as_json: bool = False) -> str:
    """Say that no Tuen Mun Children and Juvenile Home maximum temperature is available."""
    return _unavailable(
        "No Tuen Mun Children and Juvenile Home maximum temperature is available.",
        as_json=as_json,
    )


_BUOY_2_MAX_STATIONS = {
    "en": "Automatic Weather Buoy No.2 (Hong Kong International Airport, West)",
    "tc": "自動氣象浮標2號 (香港國際機場西面)",
    "sc": "自动气象浮标2号 (香港国际机场西面)",
}


def parse_buoy_2_max(text: str, lang: str = "en") -> TaiMoTemp | None:
    """Turn the weather buoy No.2 maximum CSV into the latest numeric day."""
    station = _BUOY_2_MAX_STATIONS.get(lang, _BUOY_2_MAX_STATIONS["en"])
    latest: TaiMoTemp | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = TaiMoTemp(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_2_max_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.2 maximum temperature is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) "
        "maximum temperature is available.",
        as_json=as_json,
    )


def parse_max_temp(payload: dict) -> DailyMax | None:
    """Turn a `CLMMAXT` table into the latest numeric daily maximum."""
    raw = payload.get("data")
    if not isinstance(raw, list):
        return None
    latest: DailyMax | None = None
    for row in raw:
        if not isinstance(row, list) or len(row) < 4:
            continue
        year = _text(row[0])
        month_text = _text(row[1])
        day_text = _text(row[2])
        value = _hour_mm(row[3])
        if (
            value is None
            or len(year) != 4
            or not year.isdigit()
            or not month_text.isdigit()
            or not day_text.isdigit()
        ):
            continue
        latest = DailyMax(f"{year}-{month_text.zfill(2)}-{day_text.zfill(2)}", value)
    return latest


def format_max_temp(reading: DailyMax) -> str:
    """Render the latest daily maximum temperature at the Observatory."""
    return (
        "Hong Kong daily maximum temperature\n"
        f"{reading.date}  {_number(reading.temperature_c)}°C\n"
    )


def format_max_temp_miss(*, as_json: bool = False) -> str:
    """Say that no daily maximum temperature is available."""
    return _unavailable("No daily maximum temperature is available.", as_json=as_json)


def parse_min_temp(payload: dict) -> DailyMin | None:
    """Turn a `CLMMINT` table into the latest numeric daily minimum."""
    raw = payload.get("data")
    if not isinstance(raw, list):
        return None
    latest: DailyMin | None = None
    for row in raw:
        if not isinstance(row, list) or len(row) < 4:
            continue
        year = _text(row[0])
        month_text = _text(row[1])
        day_text = _text(row[2])
        value = _hour_mm(row[3])
        if (
            value is None
            or len(year) != 4
            or not year.isdigit()
            or not month_text.isdigit()
            or not day_text.isdigit()
        ):
            continue
        latest = DailyMin(f"{year}-{month_text.zfill(2)}-{day_text.zfill(2)}", value)
    return latest


def format_min_temp(reading: DailyMin) -> str:
    """Render the latest daily minimum temperature at the Observatory."""
    return (
        "Hong Kong daily minimum temperature\n"
        f"{reading.date}  {_number(reading.temperature_c)}°C\n"
    )


def format_min_temp_miss(*, as_json: bool = False) -> str:
    """Say that no daily minimum temperature is available."""
    return _unavailable("No daily minimum temperature is available.", as_json=as_json)


_DEW_STATIONS = {
    "en": "Hong Kong Observatory",
    "tc": "香港天文台",
    "sc": "香港天文台",
}


def parse_dew_point(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Observatory dew-point CSV into the latest numeric day."""
    station = _DEW_STATIONS.get(lang, _DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_dew_point(reading: DewPoint) -> str:
    """Render the latest daily mean dew point at the Observatory."""
    return (
        "Hong Kong dew point\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.dew_point_c)}°C\n"
    )


def format_dew_point_miss(*, as_json: bool = False) -> str:
    """Say that no daily mean dew point is available."""
    return _unavailable("No dew point is available.", as_json=as_json)


_PARK_DEW_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_park_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the King's Park dew-point CSV into the latest numeric day."""
    station = _PARK_DEW_STATIONS.get(lang, _PARK_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_park_dew_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park dew point is available."""
    return _unavailable("No King's Park dew point is available.", as_json=as_json)


_CHEUNG_DEW_STATIONS = {
    "en": "Cheung Chau",
    "tc": "長洲",
    "sc": "长洲",
}


def parse_cheung_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Cheung Chau dew-point CSV into the latest numeric day."""
    station = _CHEUNG_DEW_STATIONS.get(lang, _CHEUNG_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau dew point is available."""
    return _unavailable("No Cheung Chau dew point is available.", as_json=as_json)


_WONG_CHUK_HANG_STATIONS = {
    "en": "Wong Chuk Hang",
    "tc": "黃竹坑",
    "sc": "黄竹坑",
}


def parse_wong_chuk_hang_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Wong Chuk Hang dew-point CSV into the latest numeric day."""
    station = _WONG_CHUK_HANG_STATIONS.get(lang, _WONG_CHUK_HANG_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_chuk_hang_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Wong Chuk Hang dew point is available."""
    return _unavailable("No Wong Chuk Hang dew point is available.", as_json=as_json)


_SAI_KUNG_DEW_STATIONS = {
    "en": "Sai Kung",
    "tc": "西貢",
    "sc": "西贡",
}


def parse_sai_kung_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Sai Kung dew-point CSV into the latest numeric day."""
    station = _SAI_KUNG_DEW_STATIONS.get(lang, _SAI_KUNG_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sai_kung_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Sai Kung dew point is available."""
    return _unavailable("No Sai Kung dew point is available.", as_json=as_json)


_SHA_TIN_DEW_STATIONS = {
    "en": "Sha Tin",
    "tc": "沙田",
    "sc": "沙田",
}


def parse_sha_tin_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Sha Tin dew-point CSV into the latest numeric day."""
    station = _SHA_TIN_DEW_STATIONS.get(lang, _SHA_TIN_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_tin_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Tin dew point is available."""
    return _unavailable("No Sha Tin dew point is available.", as_json=as_json)


_SHEUNG_SHUI_DEW_STATIONS = {
    "en": "Sheung Shui",
    "tc": "上水",
    "sc": "上水",
}


def parse_sheung_shui_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Sheung Shui dew-point CSV into the latest numeric day."""
    station = _SHEUNG_SHUI_DEW_STATIONS.get(lang, _SHEUNG_SHUI_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sheung_shui_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Sheung Shui dew point is available."""
    return _unavailable("No Sheung Shui dew point is available.", as_json=as_json)


_WAGLAN_DEW_STATIONS = {
    "en": "Waglan Island",
    "tc": "橫瀾島",
    "sc": "横澜岛",
}


def parse_waglan_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Waglan Island dew-point CSV into the latest numeric day."""
    station = _WAGLAN_DEW_STATIONS.get(lang, _WAGLAN_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_waglan_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Waglan Island dew point is available."""
    return _unavailable("No Waglan Island dew point is available.", as_json=as_json)


_LAU_FAU_DEW_STATIONS = {
    "en": "Lau Fau Shan",
    "tc": "流浮山",
    "sc": "流浮山",
}


def parse_lau_fau_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Lau Fau Shan dew-point CSV into the latest numeric day."""
    station = _LAU_FAU_DEW_STATIONS.get(lang, _LAU_FAU_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lau_fau_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Lau Fau Shan dew point is available."""
    return _unavailable("No Lau Fau Shan dew point is available.", as_json=as_json)


_WETLAND_DEW_STATIONS = {
    "en": "Wetland Park",
    "tc": "濕地公園",
    "sc": "湿地公园",
}


def parse_wetland_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Wetland Park dew-point CSV into the latest numeric day."""
    station = _WETLAND_DEW_STATIONS.get(lang, _WETLAND_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wetland_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Wetland Park dew point is available."""
    return _unavailable("No Wetland Park dew point is available.", as_json=as_json)


_TA_KWU_LING_DEW_STATIONS = {
    "en": "Ta Kwu Ling",
    "tc": "打鼓嶺",
    "sc": "打鼓岭",
}


def parse_ta_kwu_ling_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Ta Kwu Ling dew-point CSV into the latest numeric day."""
    station = _TA_KWU_LING_DEW_STATIONS.get(lang, _TA_KWU_LING_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ta_kwu_ling_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Ta Kwu Ling dew point is available."""
    return _unavailable("No Ta Kwu Ling dew point is available.", as_json=as_json)


_SHEK_KONG_DEW_STATIONS = {
    "en": "Shek Kong",
    "tc": "石崗",
    "sc": "石岗",
}


def parse_shek_kong_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Shek Kong dew-point CSV into the latest numeric day."""
    station = _SHEK_KONG_DEW_STATIONS.get(lang, _SHEK_KONG_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shek_kong_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Shek Kong dew point is available."""
    return _unavailable("No Shek Kong dew point is available.", as_json=as_json)


_TSEUNG_KWAN_O_DEW_STATIONS = {
    "en": "Tseung Kwan O",
    "tc": "將軍澳",
    "sc": "将军澳",
}


def parse_tseung_kwan_o_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Tseung Kwan O dew-point CSV into the latest numeric day."""
    station = _TSEUNG_KWAN_O_DEW_STATIONS.get(lang, _TSEUNG_KWAN_O_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tseung_kwan_o_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Tseung Kwan O dew point is available."""
    return _unavailable("No Tseung Kwan O dew point is available.", as_json=as_json)


_TAI_MO_DEW_STATIONS = {
    "en": "Tai Mo Shan",
    "tc": "大帽山",
    "sc": "大帽山",
}


def parse_tai_mo_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Tai Mo Shan dew-point CSV into the latest numeric day."""
    station = _TAI_MO_DEW_STATIONS.get(lang, _TAI_MO_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo Shan dew point is available."""
    return _unavailable("No Tai Mo Shan dew point is available.", as_json=as_json)


_PENG_CHAU_DEW_STATIONS = {
    "en": "Peng Chau",
    "tc": "坪洲",
    "sc": "坪洲",
}


def parse_peng_chau_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Peng Chau dew-point CSV into the latest numeric day."""
    station = _PENG_CHAU_DEW_STATIONS.get(lang, _PENG_CHAU_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_peng_chau_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Peng Chau dew point is available."""
    return _unavailable("No Peng Chau dew point is available.", as_json=as_json)


_SHA_LO_WAN_DEW_STATIONS = {
    "en": "Sha Lo Wan",
    "tc": "沙螺灣",
    "sc": "沙螺湾",
}


def parse_sha_lo_wan_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Sha Lo Wan dew-point CSV into the latest numeric day."""
    station = _SHA_LO_WAN_DEW_STATIONS.get(lang, _SHA_LO_WAN_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_lo_wan_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Lo Wan dew point is available."""
    return _unavailable("No Sha Lo Wan dew point is available.", as_json=as_json)


_AIRPORT_DEW_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_airport_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the airport dew-point CSV into the latest numeric day."""
    station = _AIRPORT_DEW_STATIONS.get(lang, _AIRPORT_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_airport_dew_miss(*, as_json: bool = False) -> str:
    """Say that no airport dew point is available."""
    return _unavailable("No airport dew point is available.", as_json=as_json)


_CLEAR_WATER_BAY_DEW_STATIONS = {
    "en": "Clear Water Bay",
    "tc": "清水灣",
    "sc": "清水湾",
}


def parse_clear_water_bay_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Clear Water Bay dew-point CSV into the latest numeric day."""
    station = _CLEAR_WATER_BAY_DEW_STATIONS.get(
        lang, _CLEAR_WATER_BAY_DEW_STATIONS["en"]
    )
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_clear_water_bay_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Clear Water Bay dew point is available."""
    return _unavailable(
        "No Clear Water Bay dew point is available.", as_json=as_json
    )


_HONG_KONG_PARK_DEW_STATIONS = {
    "en": "Hong Kong Park",
    "tc": "香港公園",
    "sc": "香港公园",
}


def parse_hong_kong_park_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Hong Kong Park dew-point CSV into the latest numeric day."""
    station = _HONG_KONG_PARK_DEW_STATIONS.get(
        lang, _HONG_KONG_PARK_DEW_STATIONS["en"]
    )
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_hong_kong_park_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Hong Kong Park dew point is available."""
    return _unavailable("No Hong Kong Park dew point is available.", as_json=as_json)


_TSUEN_WAN_DEW_STATIONS = {
    "en": "Tsuen Wan",
    "tc": "荃灣",
    "sc": "荃湾",
}


def parse_tsuen_wan_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Tsuen Wan dew-point CSV into the latest numeric day."""
    station = _TSUEN_WAN_DEW_STATIONS.get(lang, _TSUEN_WAN_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tsuen_wan_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan dew point is available."""
    return _unavailable("No Tsuen Wan dew point is available.", as_json=as_json)


_SHAU_KEI_WAN_DEW_STATIONS = {
    "en": "Shau Kei Wan",
    "tc": "筲箕灣",
    "sc": "筲箕湾",
}


def parse_shau_kei_wan_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Shau Kei Wan dew-point CSV into the latest numeric day."""
    station = _SHAU_KEI_WAN_DEW_STATIONS.get(lang, _SHAU_KEI_WAN_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shau_kei_wan_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Shau Kei Wan dew point is available."""
    return _unavailable("No Shau Kei Wan dew point is available.", as_json=as_json)


_KAU_SAI_CHAU_DEW_STATIONS = {
    "en": "Kau Sai Chau",
    "tc": "滘西洲",
    "sc": "滘西洲",
}


def parse_kau_sai_chau_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Kau Sai Chau dew-point CSV into the latest numeric day."""
    station = _KAU_SAI_CHAU_DEW_STATIONS.get(lang, _KAU_SAI_CHAU_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kau_sai_chau_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Kau Sai Chau dew point is available."""
    return _unavailable("No Kau Sai Chau dew point is available.", as_json=as_json)


_PAK_TAM_CHUNG_DEW_STATIONS = {
    "en": "Pak Tam Chung (Tsak Yue Wu)",
    "tc": "北潭涌(鯽魚湖)",
    "sc": "北潭涌(鲫鱼湖)",
}


def parse_pak_tam_chung_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Pak Tam Chung dew-point CSV into the latest numeric day."""
    station = _PAK_TAM_CHUNG_DEW_STATIONS.get(lang, _PAK_TAM_CHUNG_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_pak_tam_chung_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Pak Tam Chung (Tsak Yue Wu) dew point is available."""
    return _unavailable(
        "No Pak Tam Chung (Tsak Yue Wu) dew point is available.",
        as_json=as_json,
    )


_BEAS_RIVER_DEW_STATIONS = {
    "en": "Beas River",
    "tc": "上水雙魚河",
    "sc": "上水双鱼河",
}


def parse_beas_river_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Beas River dew-point CSV into the latest numeric day."""
    station = _BEAS_RIVER_DEW_STATIONS.get(lang, _BEAS_RIVER_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_beas_river_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Beas River dew point is available."""
    return _unavailable("No Beas River dew point is available.", as_json=as_json)


_RUNWAY_PARK_DEW_STATIONS = {
    "en": "Kai Tak Runway Park",
    "tc": "啟德跑道公園",
    "sc": "启德跑道公园",
}


def parse_runway_park_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Kai Tak Runway Park dew-point CSV into the latest numeric day."""
    station = _RUNWAY_PARK_DEW_STATIONS.get(lang, _RUNWAY_PARK_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_runway_park_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Kai Tak Runway Park dew point is available."""
    return _unavailable(
        "No Kai Tak Runway Park dew point is available.", as_json=as_json
    )


_KOWLOON_CITY_DEW_STATIONS = {
    "en": "Kowloon City",
    "tc": "九龍城",
    "sc": "九龙城",
}


def parse_kowloon_city_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Kowloon City dew-point CSV into the latest numeric day."""
    station = _KOWLOON_CITY_DEW_STATIONS.get(lang, _KOWLOON_CITY_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kowloon_city_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Kowloon City dew point is available."""
    return _unavailable("No Kowloon City dew point is available.", as_json=as_json)


_NEI_LAK_SHAN_DEW_STATIONS = {
    "en": "Nei Lak Shan",
    "tc": "彌勒山",
    "sc": "弥勒山",
}


def parse_nei_lak_shan_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Nei Lak Shan dew-point CSV into the latest numeric day."""
    station = _NEI_LAK_SHAN_DEW_STATIONS.get(lang, _NEI_LAK_SHAN_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_nei_lak_shan_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Nei Lak Shan dew point is available."""
    return _unavailable("No Nei Lak Shan dew point is available.", as_json=as_json)


_NEW_TSING_YI_DEW_STATIONS = {
    "en": "New Tsing Yi Station",
    "tc": "新青衣站",
    "sc": "新青衣站",
}


def parse_new_tsing_yi_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the New Tsing Yi Station dew-point CSV into the latest numeric day."""
    station = _NEW_TSING_YI_DEW_STATIONS.get(lang, _NEW_TSING_YI_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_new_tsing_yi_dew_miss(*, as_json: bool = False) -> str:
    """Say that no New Tsing Yi Station dew point is available."""
    return _unavailable(
        "No New Tsing Yi Station dew point is available.", as_json=as_json
    )


_TATE_DEW_STATIONS = {
    "en": "Tate's Cairn",
    "tc": "大老山",
    "sc": "大老山",
}


def parse_tate_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Tate's Cairn dew-point CSV into the latest numeric day."""
    station = _TATE_DEW_STATIONS.get(lang, _TATE_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tate_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Tate's Cairn dew point is available."""
    return _unavailable("No Tate's Cairn dew point is available.", as_json=as_json)


_SHING_MUN_VALLEY_DEW_STATIONS = {
    "en": "Tsuen Wan Shing Mun Valley",
    "tc": "荃灣城門谷",
    "sc": "荃湾城门谷",
}


def parse_shing_mun_valley_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Tsuen Wan Shing Mun Valley dew-point CSV into the latest numeric day."""
    station = _SHING_MUN_VALLEY_DEW_STATIONS.get(
        lang, _SHING_MUN_VALLEY_DEW_STATIONS["en"]
    )
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shing_mun_valley_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan Shing Mun Valley dew point is available."""
    return _unavailable(
        "No Tsuen Wan Shing Mun Valley dew point is available.", as_json=as_json
    )


_TUEN_MUN_HOME_DEW_STATIONS = {
    "en": "Tuen Mun Children and Juvenile Home",
    "tc": "屯門兒童及青少年院",
    "sc": "屯门儿童及青少年院",
}


def parse_tuen_mun_home_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the Tuen Mun Children and Juvenile Home dew-point CSV into the latest numeric day."""
    station = _TUEN_MUN_HOME_DEW_STATIONS.get(lang, _TUEN_MUN_HOME_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tuen_mun_home_dew_miss(*, as_json: bool = False) -> str:
    """Say that no Tuen Mun Children and Juvenile Home dew point is available."""
    return _unavailable(
        "No Tuen Mun Children and Juvenile Home dew point is available.",
        as_json=as_json,
    )


_BUOY_2_DEW_STATIONS = {
    "en": "Automatic Weather Buoy No.2 (Hong Kong International Airport, West)",
    "tc": "自動氣象浮標2號 (香港國際機場西面)",
    "sc": "自动气象浮标2号 (香港国际机场西面)",
}


def parse_buoy_2_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the weather buoy No.2 dew-point CSV into the latest numeric day."""
    station = _BUOY_2_DEW_STATIONS.get(lang, _BUOY_2_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_2_dew_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.2 dew point is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) "
        "dew point is available.",
        as_json=as_json,
    )


_BUOY_8_DEW_STATIONS = {
    "en": "Automatic Weather Buoy No.8 (Hong Kong International Airport, East)",
    "tc": "自動氣象浮標8號 (香港國際機場東面)",
    "sc": "自动气象浮标8号 (香港国际机场东面)",
}


def parse_buoy_8_dew(text: str, lang: str = "en") -> DewPoint | None:
    """Turn the weather buoy No.8 dew-point CSV into the latest numeric day."""
    station = _BUOY_8_DEW_STATIONS.get(lang, _BUOY_8_DEW_STATIONS["en"])
    latest: DewPoint | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DewPoint(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_buoy_8_dew_miss(*, as_json: bool = False) -> str:
    """Say that no weather buoy No.8 dew point is available."""
    return _unavailable(
        "No Automatic Weather Buoy No.8 (Hong Kong International Airport, East) "
        "dew point is available.",
        as_json=as_json,
    )


_CLOUD_STATIONS = {
    "en": "Hong Kong Observatory",
    "tc": "香港天文台",
    "sc": "香港天文台",
}


def parse_cloud(text: str, lang: str = "en") -> CloudAmount | None:
    """Turn the Observatory cloud-amount CSV into the latest numeric day."""
    station = _CLOUD_STATIONS.get(lang, _CLOUD_STATIONS["en"])
    latest: CloudAmount | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = CloudAmount(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cloud(reading: CloudAmount) -> str:
    """Render the latest daily mean cloud amount at the Observatory."""
    return (
        "Hong Kong cloud amount\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.cloud_percent)}%\n"
    )


def format_cloud_miss(*, as_json: bool = False) -> str:
    """Say that no daily mean cloud amount is available."""
    return _unavailable("No cloud amount is available.", as_json=as_json)


_EVAP_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_evaporation(text: str, lang: str = "en") -> Evaporation | None:
    """Turn the King's Park evaporation CSV into the latest numeric day."""
    station = _EVAP_STATIONS.get(lang, _EVAP_STATIONS["en"])
    latest: Evaporation | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = Evaporation(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_evaporation(reading: Evaporation) -> str:
    """Render the latest daily total evaporation at King's Park."""
    return (
        "Hong Kong evaporation\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.evaporation_mm)} mm\n"
    )


def format_evaporation_miss(*, as_json: bool = False) -> str:
    """Say that no daily total evaporation is available."""
    return _unavailable("No evaporation is available.", as_json=as_json)


_EVAPOTRANSPIRATION_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_evapotranspiration(text: str, lang: str = "en") -> Evapotranspiration | None:
    """Turn the King's Park monthly evapotranspiration CSV into the latest month."""
    station = _EVAPOTRANSPIRATION_STATIONS.get(lang, _EVAPOTRANSPIRATION_STATIONS["en"])
    latest: Evapotranspiration | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit()) or value is None:
            continue
        latest = Evapotranspiration(
            station,
            f"{int(year):04d}-{int(month):02d}",
            value,
        )
    return latest


def format_evapotranspiration(reading: Evapotranspiration) -> str:
    """Render the latest monthly potential evapotranspiration at King's Park."""
    return (
        "Hong Kong potential evapotranspiration\n"
        f"Station: {reading.station}\n"
        f"{reading.month}  {_number(reading.evapotranspiration_mm)} mm\n"
    )


def format_evapotranspiration_miss(*, as_json: bool = False) -> str:
    """Say that no potential evapotranspiration is available."""
    return _unavailable("No potential evapotranspiration is available.", as_json=as_json)


def parse_grass(payload: dict, date: str) -> GrassMinimum | None:
    """Turn a `RYES` document into yesterday's grass minimum temperature."""
    grass = _hour_mm(payload.get("HKOReadingsMinGrassTemp"))
    if grass is None:
        return None
    reported = _text(payload.get("ReportTimeInfoDate"))
    if len(reported) == 8 and reported.isdigit():
        date = f"{reported[:4]}-{reported[4:6]}-{reported[6:8]}"
    return GrassMinimum(date, grass)


def format_grass(reading: GrassMinimum) -> str:
    """Render yesterday's grass minimum at the Observatory."""
    return (
        "Hong Kong grass minimum\n"
        f"{reading.date}\n"
        f"{_number(reading.grass_min_c)}°C\n"
    )


def format_grass_miss(*, as_json: bool = False) -> str:
    """Say that yesterday's grass minimum is not available."""
    return _unavailable("No grass minimum is available.", as_json=as_json)


def parse_sunshine(payload: dict, date: str) -> Sunshine | None:
    """Turn a `RYES` document into yesterday's sunshine duration at King's Park."""
    hours = _hour_mm(payload.get("KingsParkReadingsSunShine"))
    if hours is None:
        return None
    reported = _text(payload.get("ReportTimeInfoDate"))
    if len(reported) == 8 and reported.isdigit():
        date = f"{reported[:4]}-{reported[4:6]}-{reported[6:8]}"
    return Sunshine(SUNSHINE_STATION_NAME, date, hours)


def format_sunshine(reading: Sunshine) -> str:
    """Render yesterday's sunshine duration at King's Park."""
    return (
        "Hong Kong sunshine\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.hours)} hours\n"
    )


def format_sunshine_miss(*, as_json: bool = False) -> str:
    """Say that yesterday's sunshine duration is not available."""
    return _unavailable("No sunshine duration is available.", as_json=as_json)


_DAILY_SUN_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_daily_sun(text: str, lang: str = "en") -> DailySun | None:
    """Turn the King's Park sunshine CSV into the latest numeric day."""
    station = _DAILY_SUN_STATIONS.get(lang, _DAILY_SUN_STATIONS["en"])
    latest: DailySun | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailySun(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_daily_sun(reading: DailySun) -> str:
    """Render the latest daily bright sunshine total at King's Park."""
    return (
        "Hong Kong daily sunshine\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.hours)} hours\n"
    )


def format_daily_sun_miss(*, as_json: bool = False) -> str:
    """Say that no daily sunshine total is available."""
    return _unavailable("No daily sunshine is available.", as_json=as_json)


def parse_max_uv(payload: dict, date: str) -> MaxUv | None:
    """Turn a `RYES` document into yesterday's maximum UV index at King's Park."""
    index = _hour_mm(payload.get("KingsParkReadingsMaxUVIndex"))
    if index is None:
        return None
    reported = _text(payload.get("ReportTimeInfoDate"))
    if len(reported) == 8 and reported.isdigit():
        date = f"{reported[:4]}-{reported[4:6]}-{reported[6:8]}"
    return MaxUv(SUNSHINE_STATION_NAME, date, index)


def format_max_uv(reading: MaxUv) -> str:
    """Render yesterday's maximum UV index at King's Park."""
    return (
        "Hong Kong maximum UV index\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.uv_index)}\n"
    )


def format_max_uv_miss(*, as_json: bool = False) -> str:
    """Say that yesterday's maximum UV index is not available."""
    return _unavailable("No maximum UV index is available.", as_json=as_json)


_UV_PEAK_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}
_UV_PEAK_MISSING = {"", "***", "N/A", "n/a", "----", "////"}


def parse_uv_peak(text: str, lang: str = "en") -> UvPeak | None:
    """Turn the King's Park maximum-UV CSV into the latest numeric day."""
    station = _UV_PEAK_STATIONS.get(lang, _UV_PEAK_STATIONS["en"])
    latest: UvPeak | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        period = _text(row[4]) if len(row) > 4 else ""
        if period in _UV_PEAK_MISSING:
            period = ""
        latest = UvPeak(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
            period,
        )
    return latest


def format_uv_peak(reading: UvPeak) -> str:
    """Render the latest daily maximum UV index and when it occurred."""
    line = f"{reading.date}  {_number(reading.uv_index)}"
    if reading.period:
        line = f"{line}  {reading.period}"
    return (
        "Hong Kong daily maximum UV\n"
        f"Station: {reading.station}\n"
        f"{line}\n"
    )


def format_uv_peak_miss(*, as_json: bool = False) -> str:
    """Say that no daily maximum UV index is available."""
    return _unavailable("No daily maximum UV index is available.", as_json=as_json)


def parse_mean_uv(payload: dict, date: str) -> MeanUv | None:
    """Turn a `RYES` document into yesterday's mean UV index at King's Park."""
    index = _hour_mm(payload.get("KingsParkReadingsMeanUVIndex"))
    if index is None:
        return None
    reported = _text(payload.get("ReportTimeInfoDate"))
    if len(reported) == 8 and reported.isdigit():
        date = f"{reported[:4]}-{reported[4:6]}-{reported[6:8]}"
    return MeanUv(SUNSHINE_STATION_NAME, date, index)


def format_mean_uv(reading: MeanUv) -> str:
    """Render yesterday's mean UV index at King's Park."""
    return (
        "Hong Kong mean UV index\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.uv_index)}\n"
    )


def format_mean_uv_miss(*, as_json: bool = False) -> str:
    """Say that yesterday's mean UV index is not available."""
    return _unavailable("No mean UV index is available.", as_json=as_json)


_DAILY_UV_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_daily_uv(text: str, lang: str = "en") -> MeanUv | None:
    """Turn the King's Park daily-mean-UV CSV into the latest numeric day."""
    station = _DAILY_UV_STATIONS.get(lang, _DAILY_UV_STATIONS["en"])
    latest: MeanUv | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = MeanUv(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_daily_uv_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park daily mean UV index is available."""
    return _unavailable(
        "No King's Park daily mean UV index is available.", as_json=as_json
    )


def parse_dose(payload: dict, date: str) -> GammaDose | None:
    """Turn a `RYES` document into yesterday's gamma dose rate at King's Park."""
    dose = _hour_mm(payload.get("KingsParkMicrosieverts"))
    if dose is None:
        return None
    reported = _text(payload.get("ReportTimeInfoDate"))
    if len(reported) == 8 and reported.isdigit():
        date = f"{reported[:4]}-{reported[4:6]}-{reported[6:8]}"
    return GammaDose(SUNSHINE_STATION_NAME, date, dose)


def format_dose(reading: GammaDose) -> str:
    """Render yesterday's gamma dose rate at King's Park."""
    return (
        "Hong Kong gamma dose rate\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.dose_usv_h)} µSv/h\n"
    )


def format_dose_miss(*, as_json: bool = False) -> str:
    """Say that yesterday's gamma dose rate is not available."""
    return _unavailable("No gamma dose rate is available.", as_json=as_json)


def parse_hourly_dose(text: str) -> HourlyDoseReport:
    """Turn the hourly dose CSV into the latest hour, one row per station."""
    stations: list[HourlyDoseReading] = []
    latest = ""
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 3:
            continue
        place = _text(row[1])
        value = _hour_mm(row[2])
        clock = _text(row[0])
        if not place or value is None or len(clock) != 10 or not clock.isdigit():
            continue
        if clock > latest:
            latest = clock
            stations = []
        if clock == latest:
            stations.append(HourlyDoseReading(place, value))
    obs_time = ""
    if latest:
        obs_time = f"{latest[:4]}-{latest[4:6]}-{latest[6:8]} {latest[8:10]}:00"
    return HourlyDoseReport(obs_time, tuple(stations))


def format_hourly_dose(report: HourlyDoseReport) -> str:
    """Render the latest hourly mean ambient gamma dose rate."""
    lines = ["Hong Kong hourly gamma dose rate"]
    if report.obs_time:
        lines.append(f"Recorded: {report.obs_time}")
    for reading in report.stations:
        lines.append(f"{reading.place}  {_number(reading.dose_usv_h)} µSv/h")
    return "\n".join(lines) + "\n"


def format_hourly_dose_miss(*, as_json: bool = False) -> str:
    """Say that no hourly gamma dose rate is available."""
    return _unavailable("No hourly gamma dose rate is available.", as_json=as_json)


def parse_accum_rain(payload: dict, date: str) -> AccumulatedRainfall | None:
    """Turn a `RYES` document into accumulated rainfall since 1 January."""
    rainfall = _hour_mm(payload.get("HKOReadingsAccumRainfall"))
    if rainfall is None:
        return None
    reported = _text(payload.get("ReportTimeInfoDate"))
    if len(reported) == 8 and reported.isdigit():
        date = f"{reported[:4]}-{reported[4:6]}-{reported[6:8]}"
    return AccumulatedRainfall(date, rainfall)


def format_accum_rain(reading: AccumulatedRainfall) -> str:
    """Render accumulated rainfall at the Observatory through yesterday."""
    return (
        "Hong Kong accumulated rainfall\n"
        f"{reading.date}\n"
        f"{_number(reading.rainfall_mm)} mm\n"
    )


def format_accum_rain_miss(*, as_json: bool = False) -> str:
    """Say that accumulated rainfall since 1 January is not available."""
    return _unavailable("No accumulated rainfall is available.", as_json=as_json)


def parse_avg_rain(payload: dict, date: str) -> AverageRainfall | None:
    """Turn a `RYES` document into the climatological rainfall normal."""
    rainfall = _hour_mm(payload.get("HKOReadingsAvgRainfall"))
    if rainfall is None:
        return None
    reported = _text(payload.get("ReportTimeInfoDate"))
    if len(reported) == 8 and reported.isdigit():
        date = f"{reported[:4]}-{reported[4:6]}-{reported[6:8]}"
    return AverageRainfall(date, rainfall)


def format_avg_rain(reading: AverageRainfall) -> str:
    """Render the climatological rainfall normal through yesterday."""
    return (
        "Hong Kong average rainfall\n"
        f"{reading.date}\n"
        f"{_number(reading.rainfall_mm)} mm\n"
    )


def format_avg_rain_miss(*, as_json: bool = False) -> str:
    """Say that the climatological rainfall normal is not available."""
    return _unavailable("No average rainfall is available.", as_json=as_json)


def parse_rain_vs_normal(payload: dict, date: str) -> RainComparison | None:
    """Turn a `RYES` document into accumulated rainfall against its normal."""
    accumulated = _hour_mm(payload.get("HKOReadingsAccumRainfall"))
    normal = _hour_mm(payload.get("HKOReadingsAvgRainfall"))
    if accumulated is None or normal is None:
        return None
    reported = _text(payload.get("ReportTimeInfoDate"))
    if len(reported) == 8 and reported.isdigit():
        date = f"{reported[:4]}-{reported[4:6]}-{reported[6:8]}"
    return RainComparison(date, accumulated, normal)


def _rain_vs_normal_phrase(accumulated_mm: float, normal_mm: float) -> tuple[float, str]:
    """Signed millimetres from normal, and the clause that states it."""
    gap = round(accumulated_mm - normal_mm, 1)
    normal = f"{_number(normal_mm)} mm"
    if gap > 0:
        relation = f"is {_number(gap)} mm above the normal of {normal}"
    elif gap < 0:
        relation = f"is {_number(abs(gap))} mm below the normal of {normal}"
    else:
        relation = f"matches the normal of {normal}"
    return gap, relation


def format_rain_vs_normal(reading: RainComparison | None, *, as_json: bool) -> str:
    """Print how far accumulated rainfall is from the climatological normal."""
    if reading is None:
        return _unavailable("No rainfall comparison is available.", as_json=as_json)
    gap, relation = _rain_vs_normal_phrase(reading.accumulated_mm, reading.normal_mm)
    if reading.date:
        phrase = f"Through {reading.date}, rainfall {relation}"
    else:
        phrase = f"Rainfall {relation}"
    if as_json:
        payload = {
            "date": reading.date,
            "accumulated_mm": reading.accumulated_mm,
            "normal_mm": reading.normal_mm,
            "difference_mm": gap,
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


def parse_radiation(payload: dict, date: str) -> RadiationReport | None:
    """Turn a `RYES` document into yesterday's outdoor radiation report."""
    report = _text(payload.get("HongKongDesc"))
    if not report:
        return None
    reported = _text(payload.get("ReportTimeInfoDate"))
    if len(reported) == 8 and reported.isdigit():
        date = f"{reported[:4]}-{reported[4:6]}-{reported[6:8]}"
    return RadiationReport(date, report)


def format_radiation(reading: RadiationReport) -> str:
    """Render yesterday's outdoor gamma radiation report."""
    return f"Hong Kong radiation\n{reading.date}\n{reading.report}\n"


def format_radiation_miss(*, as_json: bool = False) -> str:
    """Say that yesterday's radiation report is not available."""
    return _unavailable("No radiation report is available.", as_json=as_json)


def parse_bulletin(payload: dict) -> WeatherBulletin | None:
    """Turn a `RYES` document into the bulletin issue date and time."""
    raw_date = _text(payload.get("BulletinDate"))
    raw_time = _text(payload.get("BulletinTime"))
    if len(raw_date) == 8 and raw_date.isdigit():
        date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
    else:
        date = ""
    if len(raw_time) == 4 and raw_time.isdigit():
        clock = f"{raw_time[:2]}:{raw_time[2:]}"
    else:
        clock = raw_time
    if not date and not clock:
        return None
    return WeatherBulletin(date, clock)


def format_bulletin(bulletin: WeatherBulletin) -> str:
    """Render when yesterday's Observatory bulletin was issued."""
    issued = " ".join(part for part in (bulletin.date, bulletin.time) if part)
    return f"Hong Kong weather bulletin\n{issued}\n"


def format_bulletin_miss(*, as_json: bool = False) -> str:
    """Say that the bulletin issue time is not available."""
    return _unavailable("No weather bulletin time is available.", as_json=as_json)


def parse_radiation_note(payload: dict) -> RadiationNote | None:
    """Turn a `RYES` document into the outdoor radiation range note."""
    note = _text(payload.get("NoteDesc"))
    if not note:
        return None
    return RadiationNote(note)


def format_radiation_note(reading: RadiationNote) -> str:
    """Render the note on the normal outdoor radiation range."""
    return f"Hong Kong radiation note\n{reading.note}\n"


def format_radiation_note_miss(*, as_json: bool = False) -> str:
    """Say that the radiation range note is not available."""
    return _unavailable("No radiation note is available.", as_json=as_json)


def parse_radiation_weather(payload: dict) -> RadiationWeather | None:
    """Turn a `RYES` document into the weather-variation radiation note."""
    note = _text(payload.get("NoteDesc1"))
    if not note:
        return None
    return RadiationWeather(note)


def format_radiation_weather(reading: RadiationWeather) -> str:
    """Render how outdoor radiation varies with the weather."""
    return f"Hong Kong radiation weather\n{reading.note}\n"


def format_radiation_weather_miss(*, as_json: bool = False) -> str:
    """Say that the weather-variation radiation note is not available."""
    return _unavailable("No radiation weather note is available.", as_json=as_json)


def parse_radiation_ground(payload: dict) -> RadiationGround | None:
    """Turn a `RYES` document into the ground-variation radiation note."""
    note = _text(payload.get("NoteDesc2"))
    if not note:
        return None
    return RadiationGround(note)


def format_radiation_ground(reading: RadiationGround) -> str:
    """Render how outdoor radiation varies with the ground."""
    return f"Hong Kong radiation ground\n{reading.note}\n"


def format_radiation_ground_miss(*, as_json: bool = False) -> str:
    """Say that the ground-variation radiation note is not available."""
    return _unavailable("No radiation ground note is available.", as_json=as_json)


def parse_radiation_provisional(payload: dict) -> RadiationProvisional | None:
    """Turn a `RYES` document into the provisional radiation note."""
    note = _text(payload.get("NoteDesc3"))
    if not note:
        return None
    return RadiationProvisional(note)


def format_radiation_provisional(reading: RadiationProvisional) -> str:
    """Render the provisional-data note on the radiation report."""
    return f"Hong Kong radiation provisional\n{reading.note}\n"


def format_radiation_provisional_miss(*, as_json: bool = False) -> str:
    """Say that the provisional radiation note is not available."""
    return _unavailable("No radiation provisional note is available.", as_json=as_json)


def _hour_mm(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if text.replace(".", "", 1).isdigit():
            return float(text)
    return None


def format_wettest(reading: WettestReading) -> str:
    """Render the wettest district from the current report."""
    return f"Hong Kong wettest\n{reading.place}  {_number(reading.rainfall_mm)} mm\n"


def format_wettest_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no rainfall readings."""
    return _unavailable("No rainfall readings are available.", as_json=as_json)


def format_driest(reading: DriestReading) -> str:
    """Render the driest district from the current report."""
    return f"Hong Kong driest\n{reading.place}  {_number(reading.rainfall_mm)} mm\n"


def format_driest_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no rainfall readings."""
    return _unavailable("No rainfall readings are available.", as_json=as_json)


def _nowcast_clock(value: str) -> str:
    clock = _text(value)
    if len(clock) != 12 or not clock.isdigit():
        return ""
    return f"{clock[:4]}-{clock[4:6]}-{clock[6:8]} {clock[8:10]}:{clock[10:12]}"


def parse_nowcast(text: str) -> NowcastReport:
    """Turn the nowcast grid into the heaviest cell of each half-hour."""
    updated_raw = ""
    updated = ""
    peaks: dict[str, NowcastPeak] = {}
    rows = csv.reader(io.StringIO(text))
    next(rows, None)
    for row in rows:
        if len(row) < 5:
            continue
        raw_updated = _text(row[0])
        ending = _nowcast_clock(row[1])
        latitude = _hour_mm(row[2])
        longitude = _hour_mm(row[3])
        rainfall = _hour_mm(row[4])
        if (
            not ending
            or latitude is None
            or longitude is None
            or rainfall is None
            or len(raw_updated) != 12
            or not raw_updated.isdigit()
        ):
            continue
        if raw_updated > updated_raw:
            updated_raw = raw_updated
            updated = _nowcast_clock(raw_updated)
            peaks = {}
        current = peaks.get(ending)
        if current is None or rainfall > current.rainfall_mm:
            peaks[ending] = NowcastPeak(ending, latitude, longitude, rainfall)
    periods = tuple(peaks[key] for key in sorted(peaks))
    return NowcastReport(updated, periods)


def format_nowcast(report: NowcastReport) -> str:
    """Render the heaviest nowcast cell in each half-hour."""
    lines = ["Hong Kong rainfall nowcast"]
    if report.updated:
        lines.append(f"Updated: {report.updated}")
    for period in report.periods:
        lines.append(
            f"{period.ending}  {_number(period.latitude)}°N"
            f"  {_number(period.longitude)}°E"
            f"  {_number(period.rainfall_mm)} mm"
        )
    return "\n".join(lines) + "\n"


def format_nowcast_miss(*, as_json: bool = False) -> str:
    """Say that no rainfall nowcast is available."""
    return _unavailable("No rainfall nowcast is available.", as_json=as_json)


def format_nowcast_peak(report: NowcastReport, *, as_json: bool) -> str:
    """Print the half-hour with the heaviest nowcast rainfall."""
    if not report.periods:
        return _unavailable("No rainfall nowcast is available.", as_json=as_json)
    peak = max(round(period.rainfall_mm, 2) for period in report.periods)
    if peak <= 0:
        return _unavailable("No rain is in the nowcast.", as_json=as_json)
    winners = [
        period
        for period in report.periods
        if round(period.rainfall_mm, 2) == peak
    ]
    amount = f"{_number(peak)} mm"
    if len(winners) == 1:
        period = winners[0]
        phrase = (
            f"Heaviest nowcast: {period.ending}  {amount}"
            f" at {_number(period.latitude)}°N {_number(period.longitude)}°E"
        )
    else:
        times = _join_headings([period.ending for period in winners])
        phrase = f"Heaviest nowcast: {amount} at {times}"
    if as_json:
        payload = {
            "updated": report.updated,
            "rainfall_mm": peak,
            "periods": [
                {
                    "ending": period.ending,
                    "latitude": period.latitude,
                    "longitude": period.longitude,
                    "rainfall_mm": period.rainfall_mm,
                }
                for period in winners
            ],
            "phrase": phrase,
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return phrase + "\n"


_DAILY_RAIN_STATIONS = {
    "en": "Hong Kong Observatory",
    "tc": "香港天文台",
    "sc": "香港天文台",
}


def parse_daily_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Observatory rainfall CSV into the latest numeric day."""
    station = _DAILY_RAIN_STATIONS.get(lang, _DAILY_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_daily_rain(reading: DailyRain) -> str:
    """Render the latest daily total rainfall at the Observatory."""
    return (
        "Hong Kong daily rainfall\n"
        f"Station: {reading.station}\n"
        f"{reading.date}  {_number(reading.rainfall_mm)} mm\n"
    )


def format_daily_rain_miss(*, as_json: bool = False) -> str:
    """Say that no daily rainfall total is available."""
    return _unavailable("No daily rainfall is available.", as_json=as_json)


_LAU_FAU_STATIONS = {
    "en": "Lau Fau Shan",
    "tc": "流浮山",
    "sc": "流浮山",
}


def parse_lau_fau_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Lau Fau Shan rainfall CSV into the latest numeric day."""
    station = _LAU_FAU_STATIONS.get(lang, _LAU_FAU_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lau_fau_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Lau Fau Shan rainfall total is available."""
    return _unavailable("No Lau Fau Shan rainfall is available.", as_json=as_json)


_SHEK_KONG_STATIONS = {
    "en": "Shek Kong",
    "tc": "石崗",
    "sc": "石岗",
}


def parse_shek_kong_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Shek Kong rainfall CSV into the latest numeric day."""
    station = _SHEK_KONG_STATIONS.get(lang, _SHEK_KONG_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shek_kong_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Shek Kong rainfall total is available."""
    return _unavailable("No Shek Kong rainfall is available.", as_json=as_json)


_WETLAND_STATIONS = {
    "en": "Wetland Park",
    "tc": "濕地公園",
    "sc": "湿地公园",
}


def parse_wetland_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Wetland Park rainfall CSV into the latest numeric day."""
    station = _WETLAND_STATIONS.get(lang, _WETLAND_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wetland_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Wetland Park rainfall total is available."""
    return _unavailable("No Wetland Park rainfall is available.", as_json=as_json)


_SHAM_SHUI_PO_STATIONS = {
    "en": "Sham Shui Po",
    "tc": "深水埗",
    "sc": "深水埗",
}


def parse_sham_shui_po_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Sham Shui Po rainfall CSV into the latest numeric day."""
    station = _SHAM_SHUI_PO_STATIONS.get(lang, _SHAM_SHUI_PO_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sham_shui_po_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Sham Shui Po rainfall total is available."""
    return _unavailable("No Sham Shui Po rainfall is available.", as_json=as_json)


_PARK_RAIN_STATIONS = {
    "en": "King's Park",
    "tc": "京士柏",
    "sc": "京士柏",
}


def parse_park_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the King's Park rainfall CSV into the latest numeric day."""
    station = _PARK_RAIN_STATIONS.get(lang, _PARK_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_park_rain_miss(*, as_json: bool = False) -> str:
    """Say that no King's Park rainfall total is available."""
    return _unavailable("No King's Park rainfall is available.", as_json=as_json)


def parse_tseung_kwan_o_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tseung Kwan O rainfall CSV into the latest numeric day."""
    station = _TSEUNG_KWAN_O_STATIONS.get(lang, _TSEUNG_KWAN_O_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tseung_kwan_o_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tseung Kwan O rainfall total is available."""
    return _unavailable("No Tseung Kwan O rainfall is available.", as_json=as_json)


_SHEUNG_SHUI_RAIN_STATIONS = {
    "en": "Sheung Shui",
    "tc": "上水",
    "sc": "上水",
}


def parse_sheung_shui_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Sheung Shui rainfall CSV into the latest numeric day."""
    station = _SHEUNG_SHUI_RAIN_STATIONS.get(lang, _SHEUNG_SHUI_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sheung_shui_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Sheung Shui rainfall total is available."""
    return _unavailable("No Sheung Shui rainfall is available.", as_json=as_json)


_SHA_TIN_RAIN_STATIONS = {
    "en": "Sha Tin",
    "tc": "沙田",
    "sc": "沙田",
}


def parse_sha_tin_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Sha Tin rainfall CSV into the latest numeric day."""
    station = _SHA_TIN_RAIN_STATIONS.get(lang, _SHA_TIN_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_tin_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Tin rainfall total is available."""
    return _unavailable("No Sha Tin rainfall is available.", as_json=as_json)


def parse_ta_kwu_ling_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Ta Kwu Ling rainfall CSV into the latest numeric day."""
    station = _TA_KWU_LING_STATIONS.get(lang, _TA_KWU_LING_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ta_kwu_ling_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Ta Kwu Ling rainfall total is available."""
    return _unavailable("No Ta Kwu Ling rainfall is available.", as_json=as_json)


_CHEUNG_RAIN_STATIONS = {
    "en": "Cheung Chau",
    "tc": "長洲",
    "sc": "长洲",
}


def parse_cheung_chau_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Cheung Chau rainfall CSV into the latest numeric day."""
    station = _CHEUNG_RAIN_STATIONS.get(lang, _CHEUNG_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cheung_chau_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Cheung Chau rainfall total is available."""
    return _unavailable("No Cheung Chau rainfall is available.", as_json=as_json)


_WAGLAN_RAIN_STATIONS = {
    "en": "Waglan Island",
    "tc": "橫瀾島",
    "sc": "横澜岛",
}


def parse_waglan_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Waglan Island rainfall CSV into the latest numeric day."""
    station = _WAGLAN_RAIN_STATIONS.get(lang, _WAGLAN_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_waglan_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Waglan Island rainfall total is available."""
    return _unavailable("No Waglan Island rainfall is available.", as_json=as_json)


_TATE_RAIN_STATIONS = {
    "en": "Tate's Cairn",
    "tc": "大老山",
    "sc": "大老山",
}


def parse_tate_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tate's Cairn rainfall CSV into the latest numeric day."""
    station = _TATE_RAIN_STATIONS.get(lang, _TATE_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tate_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tate's Cairn rainfall total is available."""
    return _unavailable("No Tate's Cairn rainfall is available.", as_json=as_json)


_PENG_CHAU_RAIN_STATIONS = {
    "en": "Peng Chau",
    "tc": "坪洲",
    "sc": "坪洲",
}


def parse_peng_chau_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Peng Chau rainfall CSV into the latest numeric day."""
    station = _PENG_CHAU_RAIN_STATIONS.get(lang, _PENG_CHAU_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_peng_chau_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Peng Chau rainfall total is available."""
    return _unavailable("No Peng Chau rainfall is available.", as_json=as_json)


_PING_CHAU_RAIN_STATIONS = {
    "en": "Ping Chau",
    "tc": "平洲",
    "sc": "平洲",
}


def parse_ping_chau_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Ping Chau rainfall CSV into the latest numeric day."""
    station = _PING_CHAU_RAIN_STATIONS.get(lang, _PING_CHAU_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ping_chau_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Ping Chau rainfall total is available."""
    return _unavailable("No Ping Chau rainfall is available.", as_json=as_json)


_TAI_MO_RAIN_STATIONS = {
    "en": "Tai Mo Shan",
    "tc": "大帽山",
    "sc": "大帽山",
}


def parse_tai_mo_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tai Mo Shan rainfall CSV into the latest numeric day."""
    station = _TAI_MO_RAIN_STATIONS.get(lang, _TAI_MO_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mo_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mo Shan rainfall total is available."""
    return _unavailable("No Tai Mo Shan rainfall is available.", as_json=as_json)


_SHA_LO_WAN_RAIN_STATIONS = {
    "en": "Sha Lo Wan",
    "tc": "沙螺灣",
    "sc": "沙螺湾",
}


def parse_sha_lo_wan_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Sha Lo Wan rainfall CSV into the latest numeric day."""
    station = _SHA_LO_WAN_RAIN_STATIONS.get(lang, _SHA_LO_WAN_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_lo_wan_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Lo Wan rainfall total is available."""
    return _unavailable("No Sha Lo Wan rainfall is available.", as_json=as_json)


_AIRPORT_RAIN_STATIONS = {
    "en": "Hong Kong International Airport",
    "tc": "香港國際機場",
    "sc": "香港国际机场",
}


def parse_airport_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the airport rainfall CSV into the latest numeric day."""
    station = _AIRPORT_RAIN_STATIONS.get(lang, _AIRPORT_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_airport_rain_miss(*, as_json: bool = False) -> str:
    """Say that no airport rainfall total is available."""
    return _unavailable("No airport rainfall is available.", as_json=as_json)


_GREEN_ISLAND_RAIN_STATIONS = {
    "en": "Green Island",
    "tc": "青洲",
    "sc": "青洲",
}


def parse_green_island_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Green Island rainfall CSV into the latest numeric day."""
    station = _GREEN_ISLAND_RAIN_STATIONS.get(lang, _GREEN_ISLAND_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_green_island_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Green Island rainfall is available."""
    return _unavailable("No Green Island rainfall is available.", as_json=as_json)


_TSUEN_WAN_RAIN_STATIONS = {
    "en": "Tsuen Wan",
    "tc": "荃灣",
    "sc": "荃湾",
}


def parse_tsuen_wan_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tsuen Wan rainfall CSV into the latest numeric day."""
    station = _TSUEN_WAN_RAIN_STATIONS.get(lang, _TSUEN_WAN_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tsuen_wan_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tsuen Wan rainfall is available."""
    return _unavailable("No Tsuen Wan rainfall is available.", as_json=as_json)


_TAP_MUN_RAIN_STATIONS = {
    "en": "Tap Mun",
    "tc": "塔門",
    "sc": "塔门",
}


def parse_tap_mun_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tap Mun rainfall CSV into the latest numeric day."""
    station = _TAP_MUN_RAIN_STATIONS.get(lang, _TAP_MUN_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tap_mun_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tap Mun rainfall is available."""
    return _unavailable("No Tap Mun rainfall is available.", as_json=as_json)


_CLEAR_WATER_BAY_RAIN_STATIONS = {
    "en": "Clear Water Bay",
    "tc": "清水灣",
    "sc": "清水湾",
}


def parse_clear_water_bay_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Clear Water Bay rainfall CSV into the latest numeric day."""
    station = _CLEAR_WATER_BAY_RAIN_STATIONS.get(
        lang, _CLEAR_WATER_BAY_RAIN_STATIONS["en"]
    )
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_clear_water_bay_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Clear Water Bay rainfall is available."""
    return _unavailable(
        "No Clear Water Bay rainfall is available.", as_json=as_json
    )


_SHAU_KEI_WAN_RAIN_STATIONS = {
    "en": "Shau Kei Wan",
    "tc": "筲箕灣",
    "sc": "筲箕湾",
}


def parse_shau_kei_wan_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Shau Kei Wan rainfall CSV into the latest numeric day."""
    station = _SHAU_KEI_WAN_RAIN_STATIONS.get(lang, _SHAU_KEI_WAN_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_shau_kei_wan_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Shau Kei Wan rainfall is available."""
    return _unavailable("No Shau Kei Wan rainfall is available.", as_json=as_json)


_HAPPY_VALLEY_RAIN_STATIONS = {
    "en": "Happy Valley",
    "tc": "跑馬地",
    "sc": "跑马地",
}


def parse_happy_valley_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Happy Valley rainfall CSV into the latest numeric day."""
    station = _HAPPY_VALLEY_RAIN_STATIONS.get(lang, _HAPPY_VALLEY_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_happy_valley_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Happy Valley rainfall is available."""
    return _unavailable("No Happy Valley rainfall is available.", as_json=as_json)


_TAI_MEI_TUK_RAIN_STATIONS = {
    "en": "Tai Mei Tuk",
    "tc": "大美督",
    "sc": "大美督",
}


def parse_tai_mei_tuk_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tai Mei Tuk rainfall CSV into the latest numeric day."""
    station = _TAI_MEI_TUK_RAIN_STATIONS.get(lang, _TAI_MEI_TUK_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mei_tuk_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mei Tuk rainfall is available."""
    return _unavailable("No Tai Mei Tuk rainfall is available.", as_json=as_json)


_KADOORIE_FARM_RAIN_STATIONS = {
    "en": "Kadoorie Farm and Botanic Garden",
    "tc": "嘉道理農場暨植物園",
    "sc": "嘉道理农场暨植物园",
}


def parse_kadoorie_farm_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Kadoorie Farm rainfall CSV into the latest numeric day."""
    station = _KADOORIE_FARM_RAIN_STATIONS.get(
        lang, _KADOORIE_FARM_RAIN_STATIONS["en"]
    )
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kadoorie_farm_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Kadoorie Farm rainfall is available."""
    return _unavailable(
        "No Kadoorie Farm and Botanic Garden rainfall is available.",
        as_json=as_json,
    )


_THE_PEAK_RAIN_STATIONS = {
    "en": "The Peak",
    "tc": "山頂",
    "sc": "山顶",
}


def parse_the_peak_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn The Peak rainfall CSV into the latest numeric day."""
    station = _THE_PEAK_RAIN_STATIONS.get(lang, _THE_PEAK_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_the_peak_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Peak rainfall is available."""
    return _unavailable("No The Peak rainfall is available.", as_json=as_json)


_PAK_TAM_CHUNG_RAIN_STATIONS = {
    "en": "Pak Tam Chung (Tsak Yue Wu)",
    "tc": "北潭涌(鯽魚湖)",
    "sc": "北潭涌(鲫鱼湖)",
}


def parse_pak_tam_chung_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Pak Tam Chung rainfall CSV into the latest numeric day."""
    station = _PAK_TAM_CHUNG_RAIN_STATIONS.get(
        lang, _PAK_TAM_CHUNG_RAIN_STATIONS["en"]
    )
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_pak_tam_chung_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Pak Tam Chung rainfall is available."""
    return _unavailable(
        "No Pak Tam Chung (Tsak Yue Wu) rainfall is available.",
        as_json=as_json,
    )


_CHING_PAK_HOUSE_RAIN_STATIONS = {
    "en": "Ching Pak House(Tsing Yi)",
    "tc": "青衣(青柏樓)",
    "sc": "青衣(青柏楼)",
}


def parse_ching_pak_house_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Ching Pak House rainfall CSV into the latest numeric day."""
    station = _CHING_PAK_HOUSE_RAIN_STATIONS.get(
        lang, _CHING_PAK_HOUSE_RAIN_STATIONS["en"]
    )
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ching_pak_house_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Ching Pak House rainfall is available."""
    return _unavailable(
        "No Ching Pak House(Tsing Yi) rainfall is available.",
        as_json=as_json,
    )


_KAU_SAI_CHAU_RAIN_STATIONS = {
    "en": "Kau Sai Chau",
    "tc": "滘西洲",
    "sc": "滘西洲",
}


def parse_kau_sai_chau_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Kau Sai Chau rainfall CSV into the latest numeric day."""
    station = _KAU_SAI_CHAU_RAIN_STATIONS.get(lang, _KAU_SAI_CHAU_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kau_sai_chau_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Kau Sai Chau rainfall is available."""
    return _unavailable("No Kau Sai Chau rainfall is available.", as_json=as_json)


_KAI_TAK_RAIN_STATIONS = {
    "en": "Kai Tak",
    "tc": "啟德",
    "sc": "启德",
}


def parse_kai_tak_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Kai Tak rainfall CSV into the latest numeric day."""
    station = _KAI_TAK_RAIN_STATIONS.get(lang, _KAI_TAK_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kai_tak_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Kai Tak rainfall is available."""
    return _unavailable("No Kai Tak rainfall is available.", as_json=as_json)


_SHA_TAU_KOK_RAIN_STATIONS = {
    "en": "Sha Tau Kok",
    "tc": "沙頭角",
    "sc": "沙头角",
}


def parse_sha_tau_kok_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Sha Tau Kok rainfall CSV into the latest numeric day."""
    station = _SHA_TAU_KOK_RAIN_STATIONS.get(lang, _SHA_TAU_KOK_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_sha_tau_kok_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Sha Tau Kok rainfall is available."""
    return _unavailable("No Sha Tau Kok rainfall is available.", as_json=as_json)


_BEAS_RIVER_RAIN_STATIONS = {
    "en": "Beas River",
    "tc": "上水雙魚河",
    "sc": "上水双鱼河",
}


def parse_beas_river_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Beas River rainfall CSV into the latest numeric day."""
    station = _BEAS_RIVER_RAIN_STATIONS.get(lang, _BEAS_RIVER_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_beas_river_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Beas River rainfall is available."""
    return _unavailable("No Beas River rainfall is available.", as_json=as_json)


_KAT_O_RAIN_STATIONS = {
    "en": "Kat O",
    "tc": "吉澳",
    "sc": "吉澳",
}


def parse_kat_o_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Kat O rainfall CSV into the latest numeric day."""
    station = _KAT_O_RAIN_STATIONS.get(lang, _KAT_O_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_kat_o_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Kat O rainfall is available."""
    return _unavailable("No Kat O rainfall is available.", as_json=as_json)


_TAP_SHEK_KOK_RAIN_STATIONS = {
    "en": "Tap Shek Kok",
    "tc": "踏石角",
    "sc": "踏石角",
}


def parse_tap_shek_kok_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tap Shek Kok rainfall CSV into the latest numeric day."""
    station = _TAP_SHEK_KOK_RAIN_STATIONS.get(lang, _TAP_SHEK_KOK_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tap_shek_kok_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tap Shek Kok rainfall is available."""
    return _unavailable("No Tap Shek Kok rainfall is available.", as_json=as_json)


_TSIM_BEI_TSUI_RAIN_STATIONS = {
    "en": "Tsim Bei Tsui",
    "tc": "尖鼻咀",
    "sc": "尖鼻咀",
}


def parse_tsim_bei_tsui_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tsim Bei Tsui rainfall CSV into the latest numeric day."""
    station = _TSIM_BEI_TSUI_RAIN_STATIONS.get(lang, _TSIM_BEI_TSUI_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tsim_bei_tsui_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tsim Bei Tsui rainfall is available."""
    return _unavailable("No Tsim Bei Tsui rainfall is available.", as_json=as_json)


_TAI_MEI_TUK_PUMP_RAIN_STATIONS = {
    "en": "Tai Mei Tuk Pumping Station",
    "tc": "大美督抽水站",
    "sc": "大美督抽水站",
}


def parse_tai_mei_tuk_pump_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tai Mei Tuk Pumping Station rainfall CSV into the latest numeric day."""
    station = _TAI_MEI_TUK_PUMP_RAIN_STATIONS.get(lang, _TAI_MEI_TUK_PUMP_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_mei_tuk_pump_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Mei Tuk Pumping Station rainfall is available."""
    return _unavailable(
        "No Tai Mei Tuk Pumping Station rainfall is available.", as_json=as_json
    )


_NGONG_PING_RESERVOIR_RAIN_STATIONS = {
    "en": "Ngong Ping Fresh Water Reservoir",
    "tc": "昂坪食水配水庫",
    "sc": "昂坪食水配水库",
}


def parse_ngong_ping_reservoir_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Ngong Ping Fresh Water Reservoir rainfall CSV into the latest numeric day."""
    station = _NGONG_PING_RESERVOIR_RAIN_STATIONS.get(
        lang, _NGONG_PING_RESERVOIR_RAIN_STATIONS["en"]
    )
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_ngong_ping_reservoir_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Ngong Ping Fresh Water Reservoir rainfall is available."""
    return _unavailable(
        "No Ngong Ping Fresh Water Reservoir rainfall is available.", as_json=as_json
    )


_DISCOVERY_BAY_RAIN_STATIONS = {
    "en": "Discovery Bay",
    "tc": "愉景灣",
    "sc": "愉景湾",
}


def parse_discovery_bay_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Discovery Bay rainfall CSV into the latest numeric day."""
    station = _DISCOVERY_BAY_RAIN_STATIONS.get(lang, _DISCOVERY_BAY_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_discovery_bay_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Discovery Bay rainfall is available."""
    return _unavailable("No Discovery Bay rainfall is available.", as_json=as_json)


_ADVENTIST_COLLEGE_RAIN_STATIONS = {
    "en": "Hong Kong Adventist College(Sai Kung)",
    "tc": "西貢(香港三育書院)",
    "sc": "西贡(香港三育书院)",
}


def parse_adventist_college_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Hong Kong Adventist College rainfall CSV into the latest numeric day."""
    station = _ADVENTIST_COLLEGE_RAIN_STATIONS.get(
        lang, _ADVENTIST_COLLEGE_RAIN_STATIONS["en"]
    )
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_adventist_college_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Hong Kong Adventist College(Sai Kung) rainfall is available."""
    return _unavailable(
        "No Hong Kong Adventist College(Sai Kung) rainfall is available.",
        as_json=as_json,
    )


_WONG_SHIU_CHI_RAIN_STATIONS = {
    "en": "Tai Po Wong Shiu Chi Secondary School",
    "tc": "大埔王肇枝中學",
    "sc": "大埔王肇枝中学",
}


def parse_wong_shiu_chi_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tai Po Wong Shiu Chi rainfall CSV into the latest numeric day."""
    station = _WONG_SHIU_CHI_RAIN_STATIONS.get(lang, _WONG_SHIU_CHI_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_wong_shiu_chi_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Po Wong Shiu Chi Secondary School rainfall is available."""
    return _unavailable(
        "No Tai Po Wong Shiu Chi Secondary School rainfall is available.",
        as_json=as_json,
    )


_AU_TAU_RAIN_STATIONS = {
    "en": "Au Tau",
    "tc": "凹頭",
    "sc": "凹头",
}


def parse_au_tau_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Au Tau rainfall CSV into the latest numeric day."""
    station = _AU_TAU_RAIN_STATIONS.get(lang, _AU_TAU_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_au_tau_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Au Tau rainfall is available."""
    return _unavailable("No Au Tau rainfall is available.", as_json=as_json)


_LOK_MA_CHAU_RAIN_STATIONS = {
    "en": "Lok Ma Chau",
    "tc": "落馬洲",
    "sc": "落马洲",
}


def parse_lok_ma_chau_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Lok Ma Chau rainfall CSV into the latest numeric day."""
    station = _LOK_MA_CHAU_RAIN_STATIONS.get(lang, _LOK_MA_CHAU_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lok_ma_chau_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Lok Ma Chau rainfall is available."""
    return _unavailable("No Lok Ma Chau rainfall is available.", as_json=as_json)


_PO_PIN_CHAU_RAIN_STATIONS = {
    "en": "Po Pin Chau",
    "tc": "破邊洲",
    "sc": "破边洲",
}


def parse_po_pin_chau_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Po Pin Chau rainfall CSV into the latest numeric day."""
    station = _PO_PIN_CHAU_RAIN_STATIONS.get(lang, _PO_PIN_CHAU_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_po_pin_chau_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Po Pin Chau rainfall is available."""
    return _unavailable("No Po Pin Chau rainfall is available.", as_json=as_json)


_TUEN_MUN_RESERVIOR_RAIN_STATIONS = {
    "en": "Tuen Mun Reservior",
    "tc": "屯門水庫",
    "sc": "屯门水库",
}


def parse_tuen_mun_reservior_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tuen Mun Reservior rainfall CSV into the latest numeric day."""
    station = _TUEN_MUN_RESERVIOR_RAIN_STATIONS.get(
        lang, _TUEN_MUN_RESERVIOR_RAIN_STATIONS["en"]
    )
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tuen_mun_reservior_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tuen Mun Reservior rainfall is available."""
    return _unavailable("No Tuen Mun Reservior rainfall is available.", as_json=as_json)


_TAI_TAN_CAMP_RAIN_STATIONS = {
    "en": "Tai Tan Camp",
    "tc": "大灘訓練營",
    "sc": "大滩训练营",
}


def parse_tai_tan_camp_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tai Tan Camp rainfall CSV into the latest numeric day."""
    station = _TAI_TAN_CAMP_RAIN_STATIONS.get(lang, _TAI_TAN_CAMP_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tai_tan_camp_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tai Tan Camp rainfall is available."""
    return _unavailable("No Tai Tan Camp rainfall is available.", as_json=as_json)


_LAMMA_ISLAND_RAIN_STATIONS = {
    "en": "Lamma Island",
    "tc": "南丫島",
    "sc": "南丫岛",
}


def parse_lamma_island_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Lamma Island rainfall CSV into the latest numeric day."""
    station = _LAMMA_ISLAND_RAIN_STATIONS.get(lang, _LAMMA_ISLAND_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_lamma_island_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Lamma Island rainfall is available."""
    return _unavailable("No Lamma Island rainfall is available.", as_json=as_json)


_TUEN_MUN_HOME_RAIN_STATIONS = {
    "en": "Tuen Mun Children and Juvenile Home",
    "tc": "屯門兒童及青少年院",
    "sc": "屯门儿童及青少年院",
}


def parse_tuen_mun_home_rain(text: str, lang: str = "en") -> DailyRain | None:
    """Turn the Tuen Mun Children and Juvenile Home rainfall CSV into the latest numeric day."""
    station = _TUEN_MUN_HOME_RAIN_STATIONS.get(lang, _TUEN_MUN_HOME_RAIN_STATIONS["en"])
    latest: DailyRain | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyRain(
            station,
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_tuen_mun_home_rain_miss(*, as_json: bool = False) -> str:
    """Say that no Tuen Mun Children and Juvenile Home rainfall is available."""
    return _unavailable(
        "No Tuen Mun Children and Juvenile Home rainfall is available.",
        as_json=as_json,
    )


def parse_rainstorm(payload: dict) -> RainstormReminder | None:
    """Turn the `rhrread` rainstorm reminder into one message."""
    text = _text(payload.get("rainstormReminder"))
    if not text:
        return None
    return RainstormReminder(text)


def format_rainstorm(reminder: RainstormReminder) -> str:
    """Render the rainstorm reminder."""
    return f"Hong Kong rainstorm reminder\n{reminder.reminder}\n"


def format_rainstorm_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no rainstorm reminder."""
    return _unavailable("No rainstorm reminder.", as_json=as_json)


def parse_cyclone(payload: dict) -> CycloneMessage | None:
    """Turn the `rhrread` tropical cyclone message into lines of text."""
    raw = payload.get("tcmessage")
    items = [raw] if isinstance(raw, str) else raw if isinstance(raw, list) else []
    messages: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = (
                _text(item.get("desc"))
                or _text(item.get("message"))
                or _text(item.get("content"))
            )
        else:
            text = _text(item)
        if text:
            messages.append(text)
    if not messages:
        return None
    return CycloneMessage(tuple(messages))


def format_cyclone(report: CycloneMessage) -> str:
    """Render the tropical cyclone message."""
    lines = ["Hong Kong tropical cyclone", *(f"- {message}" for message in report.messages)]
    return "\n".join(lines) + "\n"


def format_cyclone_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no tropical cyclone message."""
    return _unavailable("No tropical cyclone message.", as_json=as_json)


def parse_lightning(payload: dict) -> LightningReport:
    """Turn `rhrread` lightning data into places where lightning occurred."""
    return LightningReport(_lightning(payload))


def format_lightning(report: LightningReport) -> str:
    """Render lightning locations, one place per line."""
    if not report.places:
        return "No lightning is reported.\n"
    lines = ["Hong Kong lightning", *report.places]
    return "\n".join(lines) + "\n"


def parse_strikes(payload: dict) -> LightningCountReport:
    """Turn an `LHL` document into lightning counts by region."""
    raw = payload.get("data")
    counts: list[LightningCount] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, list) or len(item) < 4:
                continue
            kind = _text(item[1])
            region = _text(item[2])
            count = _whole_count(item[3])
            if not kind or not region or count is None:
                continue
            start, end = _strike_period(item[0])
            counts.append(LightningCount(start, end, kind, region, count))
    return LightningCountReport(tuple(counts))


def format_strikes(report: LightningCountReport) -> str:
    """Render hourly lightning counts, one region per line."""
    lines = ["Hong Kong lightning count"]
    for reading in report.counts:
        period = reading.start if not reading.end else f"{reading.start}-{reading.end[11:]}"
        if reading.end and reading.end[:10] != reading.start[:10]:
            period = f"{reading.start}-{reading.end}"
        lines.append(f"{period}  {reading.kind}  {reading.region}  {reading.count}")
    return "\n".join(lines) + "\n"


def format_strikes_miss(*, as_json: bool = False) -> str:
    """Say that no lightning counts are available."""
    return _unavailable("No lightning counts are available.", as_json=as_json)


def parse_daily_strikes(text: str, lang: str = "en") -> DailyStrikes | None:
    """Turn the territory lightning CSV into the latest numeric day."""
    del lang
    latest: DailyStrikes | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = DailyStrikes(
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_daily_strikes(reading: DailyStrikes) -> str:
    """Render the latest daily cloud-to-ground lightning count."""
    return f"Hong Kong daily lightning\n{reading.date}  {_number(reading.count)}\n"


def format_daily_strikes_miss(*, as_json: bool = False) -> str:
    """Say that no daily lightning count is available."""
    return _unavailable("No daily lightning count is available.", as_json=as_json)


def parse_cloud_strikes(text: str, lang: str = "en") -> CloudStrikes | None:
    """Turn the cloud-to-cloud lightning CSV into the latest numeric day."""
    del lang
    latest: CloudStrikes | None = None
    rows = csv.reader(io.StringIO(text))
    for row in rows:
        if len(row) < 4:
            continue
        year = _text(row[0]).lstrip("\ufeff")
        month = _text(row[1])
        day = _text(row[2])
        value = _hour_mm(row[3])
        if not (year.isdigit() and month.isdigit() and day.isdigit()) or value is None:
            continue
        latest = CloudStrikes(
            f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
            value,
        )
    return latest


def format_cloud_strikes(reading: CloudStrikes) -> str:
    """Render the latest daily cloud-to-cloud lightning count."""
    return f"Hong Kong cloud-to-cloud lightning\n{reading.date}  {_number(reading.count)}\n"


def format_cloud_strikes_miss(*, as_json: bool = False) -> str:
    """Say that no cloud-to-cloud lightning count is available."""
    return _unavailable("No cloud-to-cloud lightning count is available.", as_json=as_json)


def _strike_period(value: object) -> tuple[str, str]:
    text = _text(value)
    start, sep, end = text.partition("-")
    if sep and len(start) == 12 and start.isdigit() and len(end) == 12 and end.isdigit():
        return _visibility_time(start), _visibility_time(end)
    return text, ""


def _whole_count(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def parse_humidity(payload: dict) -> HumidityReport:
    """Turn `rhrread` humidity data into one reading per place."""
    section = payload.get("humidity")
    record_time = _text(section.get("recordTime")) if isinstance(section, dict) else ""
    readings: list[HumidityReading] = []
    seen: set[str] = set()
    for item in _data_list(section):
        place = _text(item.get("place"))
        value = item.get("value")
        if not place or place in seen:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        seen.add(place)
        readings.append(HumidityReading(place, float(value)))
    return HumidityReport(record_time, tuple(readings))


def format_humidity(report: HumidityReport) -> str:
    """Render humidity, one line per place."""
    if not report.readings:
        return "No humidity reading is available.\n"
    lines = ["Hong Kong humidity"]
    if report.record_time:
        lines.append(f"Recorded: {report.record_time}")
    lines.extend(
        f"{reading.place}  {_number(reading.humidity_percent)}%" for reading in report.readings
    )
    return "\n".join(lines) + "\n"


def parse_humidity_time(payload: dict) -> HumidityTime | None:
    """Turn the `rhrread` humidity record time into one timestamp."""
    section = payload.get("humidity")
    if not isinstance(section, dict):
        return None
    text = _text(section.get("recordTime"))
    if not text:
        return None
    return HumidityTime(text)


def format_humidity_time(report: HumidityTime) -> str:
    """Render when the current humidity readings were recorded."""
    return f"Hong Kong humidity time\n{report.recorded}\n"


def format_humidity_time_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no humidity record time."""
    return _unavailable("No humidity time is available.", as_json=as_json)


def format_humidest(reading: HumidestReading) -> str:
    """Render the most humid station from the current report."""
    lines = ["Hong Kong humidest"]
    if reading.record_time:
        lines.append(f"Recorded: {reading.record_time}")
    lines.append(f"{reading.place}  {_number(reading.humidity_percent)}%")
    return "\n".join(lines) + "\n"


def format_humidest_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no humidity readings."""
    return _unavailable("No humidity reading is available.", as_json=as_json)


def format_least_humid(reading: LeastHumidReading) -> str:
    """Render the least humid station from the current report."""
    lines = ["Hong Kong least humid"]
    if reading.record_time:
        lines.append(f"Recorded: {reading.record_time}")
    lines.append(f"{reading.place}  {_number(reading.humidity_percent)}%")
    return "\n".join(lines) + "\n"


def format_least_humid_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no humidity readings."""
    return _unavailable("No humidity reading is available.", as_json=as_json)


def parse_temps(payload: dict) -> TempReport:
    """Turn `rhrread` temperature data into one reading per place."""
    section = payload.get("temperature")
    record_time = _text(section.get("recordTime")) if isinstance(section, dict) else ""
    readings: list[TempReading] = []
    seen: set[str] = set()
    for item in _data_list(section):
        place = _text(item.get("place"))
        value = item.get("value")
        if not place or place in seen:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        seen.add(place)
        readings.append(TempReading(place, float(value)))
    return TempReport(record_time, tuple(readings))


def format_temps(report: TempReport) -> str:
    """Render temperatures, one line per place."""
    if not report.readings:
        return "No temperature readings are available.\n"
    lines = ["Hong Kong temperatures"]
    if report.record_time:
        lines.append(f"Recorded: {report.record_time}")
    lines.extend(
        f"{reading.place}  {_number(reading.temperature_c)}°C" for reading in report.readings
    )
    return "\n".join(lines) + "\n"


def parse_temp_time(payload: dict) -> TempTime | None:
    """Turn the `rhrread` temperature record time into one timestamp."""
    section = payload.get("temperature")
    if not isinstance(section, dict):
        return None
    text = _text(section.get("recordTime"))
    if not text:
        return None
    return TempTime(text)


def format_temp_time(report: TempTime) -> str:
    """Render when the current temperatures were recorded."""
    return f"Hong Kong temperature time\n{report.recorded}\n"


def format_temp_time_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no temperature record time."""
    return _unavailable("No temperature time is available.", as_json=as_json)


def format_hottest(reading: HottestReading) -> str:
    """Render the warmest station from the current report."""
    lines = ["Hong Kong hottest"]
    if reading.record_time:
        lines.append(f"Recorded: {reading.record_time}")
    lines.append(f"{reading.place}  {_number(reading.temperature_c)}°C")
    return "\n".join(lines) + "\n"


def format_hottest_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no temperature readings."""
    return _unavailable("No temperature readings are available.", as_json=as_json)


def format_coldest(reading: ColdestReading) -> str:
    """Render the coolest station from the current report."""
    lines = ["Hong Kong coldest"]
    if reading.record_time:
        lines.append(f"Recorded: {reading.record_time}")
    lines.append(f"{reading.place}  {_number(reading.temperature_c)}°C")
    return "\n".join(lines) + "\n"


def format_coldest_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no temperature readings."""
    return _unavailable("No temperature readings are available.", as_json=as_json)


def parse_overnight(payload: dict) -> OvernightMinimum | None:
    """Turn the `rhrread` midnight-to-9am minimum into one sentence."""
    text = _text(payload.get("mintempFrom00To09"))
    if not text:
        return None
    return OvernightMinimum(text)


def format_overnight(reading: OvernightMinimum) -> str:
    """Render the midnight-to-9am minimum temperature note."""
    return f"Hong Kong overnight minimum\n{reading.report}\n"


def format_overnight_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no overnight minimum."""
    return _unavailable("No overnight minimum is available.", as_json=as_json)


def parse_noon_rain(payload: dict) -> NoonRainfall | None:
    """Turn the `rhrread` midnight-to-noon rainfall note into one sentence."""
    text = _text(payload.get("rainfallFrom00To12"))
    if not text:
        return None
    return NoonRainfall(text)


def format_noon_rain(reading: NoonRainfall) -> str:
    """Render the midnight-to-noon rainfall note."""
    return f"Hong Kong noon rainfall\n{reading.report}\n"


def format_noon_rain_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no noon rainfall note."""
    return _unavailable("No noon rainfall note is available.", as_json=as_json)


def parse_month_rain(payload: dict) -> MonthRainfall | None:
    """Turn the `rhrread` last-month rainfall note into one sentence."""
    text = _text(payload.get("rainfallLastMonth"))
    if not text:
        return None
    return MonthRainfall(text)


def format_month_rain(reading: MonthRainfall) -> str:
    """Render last month's rainfall note."""
    return f"Hong Kong last month rainfall\n{reading.report}\n"


def format_month_rain_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no last-month rainfall note."""
    return _unavailable("No last-month rainfall note is available.", as_json=as_json)


def parse_year_rain(payload: dict) -> YearRainfall | None:
    """Turn the `rhrread` January-to-last-month rainfall note into one sentence."""
    text = _text(payload.get("rainfallJanuaryToLastMonth"))
    if not text:
        return None
    return YearRainfall(text)


def format_year_rain(reading: YearRainfall) -> str:
    """Render the January-to-last-month rainfall note."""
    return f"Hong Kong year-to-date rainfall\n{reading.report}\n"


def format_year_rain_miss(*, as_json: bool = False) -> str:
    """Say that the current report has no year-to-date rainfall note."""
    return _unavailable("No year-to-date rainfall note is available.", as_json=as_json)


def format_json(
    report: CurrentWeather
    | LocalForecast
    | ForecastOutlook
    | CoastalForecast
    | CoastReport
    | ForecastPeriod
    | ForecastDesc
    | ForecastUpdated
    | NineUpdated
    | NineWeather
    | NineTemp
    | NineHumidity
    | GeneralSituation
    | FireDanger
    | TcInfo
    | NineDayForecast
    | SeaTemperature
    | SoilReport
    | UvIndex
    | FifteenUv
    | IconUpdate
    | IconReport
    | CurrentUpdated
    | SpecialTips
    | LamppostReading
    | StationReport
    | RainReport
    | RainPeriod
    | RainMaintenance
    | HourRainReport
    | HourWettest
    | HourDriest
    | LightningReport
    | LightningCountReport
    | DailyStrikes
    | CloudStrikes
    | HumidityReport
    | HumidityTime
    | MinuteHumidityReport
    | MeanHumidity
    | TempReport
    | TempTime
    | MinuteTempReport
    | SinceMidnightReport
    | PressureReport
    | MeanPressure
    | MinuteGrassReport
    | DailyGrass
    | TempDiffReport
    | HeatIndexReport
    | DailyHeat
    | WbgtReport
    | WetBulb
    | SolarReport
    | GlobalSolar
    | WindForecast
    | GustReport
    | PrevailingWind
    | MeanWind
    | ForecastIcons
    | QuakeReport
    | FeltTremor
    | TomorrowForecast
    | YesterdayReport
    | DailyMean
    | TaiMoTemp
    | DailyMax
    | DailyMin
    | DewPoint
    | CloudAmount
    | Evaporation
    | Evapotranspiration
    | GrassMinimum
    | Sunshine
    | DailySun
    | MaxUv
    | UvPeak
    | MeanUv
    | GammaDose
    | HourlyDoseReport
    | AccumulatedRainfall
    | AverageRainfall
    | RadiationReport
    | WeatherBulletin
    | RadiationNote
    | RadiationWeather
    | RadiationGround
    | RadiationProvisional
    | PsrForecast
    | WeekendForecast
    | VisibilityReport
    | ReducedVisibility
    | HottestReading
    | ColdestReading
    | OvernightMinimum
    | NoonRainfall
    | MonthRainfall
    | YearRainfall
    | WeatherSummary
    | WarningTimeReport
    | HumidestReading
    | LeastHumidReading
    | WettestReading
    | DriestReading
    | NowcastReport
    | DailyRain
    | RainstormReminder
    | CycloneMessage
    | TideReport
    | HourlyTideReport
    | LatestTideReport
    | AqhiReport
    | Sunrise
    | Moon
    | LunarDate,
) -> str:
    """Render the same report as one JSON object."""
    return json.dumps(asdict(report), indent=2, ensure_ascii=False) + "\n"


def _temperature(payload: dict) -> tuple[str, float]:
    readings = _data_list(payload.get("temperature"))
    if not readings:
        raise WeatherError("current temperature is missing from the report")

    chosen = next(
        (item for item in readings if item.get("place") == HKO_STATION),
        readings[0],
    )
    place = _text(chosen.get("place")) or "Hong Kong"
    value = chosen.get("value")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise WeatherError("current temperature is missing from the report")
    return place, float(value)


def _humidity(payload: dict) -> float | None:
    readings = _data_list(payload.get("humidity"))
    if not readings:
        return None
    preferred = next(
        (item for item in readings if item.get("place") == HKO_STATION),
        readings[0],
    )
    value = preferred.get("value")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return float(value)


def _peak_rainfall(payload: dict) -> tuple[float | None, str | None]:
    readings = _data_list(payload.get("rainfall"))
    best_mm: float | None = None
    best_place: str | None = None
    for item in readings:
        value = item.get("max")
        place = _text(item.get("place"))
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not place:
            continue
        amount = float(value)
        if best_mm is None or amount > best_mm:
            best_mm = amount
            best_place = place
    return best_mm, best_place


def _lightning(payload: dict) -> tuple[str, ...]:
    places: list[str] = []
    for item in _data_list(payload.get("lightning")):
        occur = item.get("occur")
        active = occur is True or (isinstance(occur, str) and occur.lower() == "true")
        place = _text(item.get("place"))
        if active and place:
            places.append(place)
    return tuple(places)


def _conditions(icon: object) -> str:
    codes: list[int] = []
    if isinstance(icon, list):
        codes = [code for code in icon if isinstance(code, int) and not isinstance(code, bool)]
    elif isinstance(icon, int) and not isinstance(icon, bool):
        codes = [icon]
    if not codes:
        return "Unknown"
    return ", ".join(icon_label(code) for code in codes)


def _warnings(raw: object) -> tuple[str, ...]:
    if isinstance(raw, str):
        text = raw.strip()
        return (text,) if text else ()
    if not isinstance(raw, list):
        return ()
    messages = []
    for item in raw:
        text = _text(item)
        if text:
            messages.append(text)
    return tuple(messages)


def _data_list(section: object) -> list[dict]:
    if not isinstance(section, dict):
        return []
    data = section.get("data")
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _forecast_day(item: object) -> ForecastDay | None:
    if not isinstance(item, dict):
        return None
    date = _forecast_date(item.get("forecastDate"))
    weather = _text(item.get("forecastWeather"))
    if not date and not weather:
        return None
    rain = _text(item.get("PSR"))
    return ForecastDay(
        date=date or "unknown",
        week=_text(item.get("week")),
        weather=weather,
        temp_high_c=_temp_value(item.get("forecastMaxtemp")),
        temp_low_c=_temp_value(item.get("forecastMintemp")),
        humidity_high_percent=_temp_value(item.get("forecastMaxrh")),
        humidity_low_percent=_temp_value(item.get("forecastMinrh")),
        rain_chance=rain or None,
    )


def _humidity_span(low: float | None, high: float | None) -> str:
    """Format a relative-humidity range, or one side when the other is missing."""
    if low is not None and high is not None:
        return f"humidity {_number(low)}-{_number(high)}%"
    if low is not None:
        return f"humidity {_number(low)}%"
    if high is not None:
        return f"humidity {_number(high)}%"
    return ""


def _forecast_date(value: object) -> str:
    text = _text(value)
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text


def _temp_value(section: object) -> float | None:
    if not isinstance(section, dict):
        return None
    value = section.get("value")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return float(value)


def _text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _number(value: float) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return str(number)
