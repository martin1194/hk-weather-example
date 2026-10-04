"""Fetch and format Hong Kong Observatory current weather and the local forecast."""

from __future__ import annotations

import csv
import io
import json
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


def format_report(weather: CurrentWeather) -> str:
    """Render current conditions as plain text."""
    lines = [
        "Hong Kong weather",
        "Source: Hong Kong Observatory open data",
        f"Updated: {weather.update_time}",
        f"Conditions: {conditions_with_emoji(weather.conditions)}",
        f"Temperature: {_number(weather.temperature_c)}°C ({weather.place})",
        "Humidity: "
        + (
            f"{_number(weather.humidity_percent)}%"
            if weather.humidity_percent is not None
            else "n/a"
        ),
    ]
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


def format_summary(report: WeatherSummary) -> str:
    """Render a short briefing: conditions, warnings, and today's high and low."""
    lines = ["Hong Kong summary", conditions_with_emoji(report.conditions)]
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
            parts.append(f"high {_number(report.today.high_c)}°C")
        if report.today.low_c is not None:
            parts.append(f"low {_number(report.today.low_c)}°C")
        if report.today.rain_chance:
            parts.append(f"rain {report.today.rain_chance}")
        lines.append("Today: " + "  ".join(parts))
    return "\n".join(lines) + "\n"


def format_short(weather: CurrentWeather) -> str:
    """Render current conditions as one compact line."""
    humidity = (
        f"{_number(weather.humidity_percent)}%"
        if weather.humidity_percent is not None
        else "n/a"
    )
    conditions = conditions_with_emoji(weather.conditions)
    line = f"{conditions}, {_number(weather.temperature_c)}°C, humidity {humidity}"
    if weather.warnings:
        note = _brief_warning(weather.warnings[0])
        extra = len(weather.warnings) - 1
        if extra:
            note = f"{note} (+{extra} more)"
        line = f"{line} — {note}"
    return line + "\n"


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
        return json.dumps(payload, indent=2) + "\n"
    if not warnings:
        return "No weather warnings are in force.\n"
    lines = ["Hong Kong weather warnings"]
    lines.extend(f"{warning.code}  {warning.description}" for warning in warnings)
    return "\n".join(lines) + "\n"


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
        return json.dumps(payload, indent=2) + "\n"
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


def format_day_miss(day: int, *, as_json: bool = False) -> str:
    """Say that forecast day N is not in the 9-day list."""
    return _unavailable(f"Forecast day {day} is not available.", as_json=as_json)


def _unavailable(message: str, *, as_json: bool) -> str:
    if as_json:
        return json.dumps({"message": message}, indent=2) + "\n"
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
        return json.dumps({"places": names}, indent=2) + "\n"
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
    return json.dumps(asdict(report), indent=2) + "\n"


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
