"""Fetch and format Hong Kong Observatory current weather and the local forecast."""

from __future__ import annotations

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
FORECAST_URL = f"{_API}?dataType=flw&lang=en"
NINE_DAY_URL = f"{_API}?dataType=fnd&lang=en"
WARNINGS_URL = f"{_API}?dataType=warnsum&lang=en"
WARNING_INFO_URL = f"{_API}?dataType=warningInfo&lang=en"
TIPS_URL = f"{_API}?dataType=swt&lang=en"
# Quick earthquake messages live on earthquake.php. dataType=qem is the latest
# magnitude 6+ event; dataType=eeq is not a valid Observatory parameter.
QUAKE_URL = "https://data.weather.gov.hk/weatherAPI/opendata/earthquake.php?dataType=qem&lang=en"
# Latest 10-minute mean visibility. weather.php rejects dataType=LTMV; this feed
# is the open-data endpoint and needs rformat=json plus lang.
VISIBILITY_URL = (
    "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
    "?dataType=LTMV&rformat=json&lang=en"
)
# Astronomical high and low tides. opendata.php requires a station plus year,
# month, and day; Quarry Bay is the default station. lang is accepted.
TIDE_STATION = "QUB"
TIDE_STATION_NAME = "Quarry Bay"
# Current AQHI by station. weather.php has no AQHI dataType; these are the
# Environmental Protection Department RSS feeds, one file per language.
AQHI_URLS = {
    "en": "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_ind_rss_Eng.xml",
    "tc": "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_ind_rss_ChT.xml",
    "sc": "https://www.aqhi.gov.hk/epd/ddata/html/out/aqhi_ind_rss_ChS.xml",
}
UV_URL = DEFAULT_URL
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
class WeatherWarning:
    code: str
    description: str


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
class WindForecast:
    update_time: str
    days: tuple[WindDay, ...]


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
class VisibilityReading:
    time: str
    place: str
    visibility: str


@dataclass(frozen=True)
class VisibilityReport:
    readings: tuple[VisibilityReading, ...]


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
class SpecialTips:
    tips: tuple[str, ...]


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
class LightningReport:
    places: tuple[str, ...]


@dataclass(frozen=True)
class HumidityReading:
    place: str
    humidity_percent: float


@dataclass(frozen=True)
class HumidityReport:
    record_time: str
    readings: tuple[HumidityReading, ...]


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
class TempReading:
    place: str
    temperature_c: float


@dataclass(frozen=True)
class TempReport:
    record_time: str
    readings: tuple[TempReading, ...]


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
class UvIndex:
    update_time: str
    place: str | None
    value: float | None
    description: str | None
    record: str | None


def fetch_current(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> CurrentWeather:
    """Download the current weather report and return a summary."""
    return parse_current_report(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_forecast(url: str = FORECAST_URL, timeout: float = 10, lang: str = "en") -> LocalForecast:
    """Download the local weather forecast (`dataType=flw`)."""
    return parse_forecast(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_warnings(
    url: str = WARNINGS_URL, timeout: float = 10, lang: str = "en"
) -> tuple[WeatherWarning, ...]:
    """Download active weather warnings (`dataType=warnsum`)."""
    return parse_warnings(_fetch_json(_apply_lang(url, lang), timeout))


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


def fetch_quakes(url: str = QUAKE_URL, timeout: float = 10, lang: str = "en") -> QuakeReport:
    """Download the latest quick earthquake message (`dataType=qem`)."""
    return parse_quakes(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_visibility(
    url: str = VISIBILITY_URL, timeout: float = 10, lang: str = "en"
) -> VisibilityReport:
    """Download the latest 10-minute mean visibility (`dataType=LTMV`)."""
    return parse_visibility(_fetch_json(_apply_lang(url, lang), timeout))


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


def fetch_uv(url: str = UV_URL, timeout: float = 10, lang: str = "en") -> UvIndex:
    """Download the UV index from the current weather report (`dataType=rhrread`)."""
    return parse_uv(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_tips(url: str = TIPS_URL, timeout: float = 10, lang: str = "en") -> SpecialTips:
    """Download special weather tips (`dataType=swt`)."""
    return parse_tips(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_stations(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> StationReport:
    """Download per-station temperature and humidity from the current report."""
    return parse_stations(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_rain(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> RainReport:
    """Download district rainfall from the current report (`dataType=rhrread`)."""
    return parse_rain(_fetch_json(_apply_lang(url, lang), timeout))


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


def fetch_humidity(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> HumidityReport:
    """Download humidity readings from the current report (`dataType=rhrread`)."""
    return parse_humidity(_fetch_json(_apply_lang(url, lang), timeout))


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


def format_json(
    report: CurrentWeather
    | LocalForecast
    | NineDayForecast
    | UvIndex
    | SpecialTips
    | StationReport
    | RainReport
    | LightningReport
    | HumidityReport
    | TempReport
    | WindForecast
    | QuakeReport
    | TomorrowForecast
    | PsrForecast
    | WeekendForecast
    | VisibilityReport
    | HottestReading
    | ColdestReading
    | OvernightMinimum
    | HumidestReading
    | LeastHumidReading
    | WettestReading
    | DriestReading
    | RainstormReminder
    | CycloneMessage
    | TideReport
    | AqhiReport
    | Sunrise
    | Moon,
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
