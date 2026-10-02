"""Fetch and format Hong Kong Observatory current weather and the local forecast."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

from hk_weather.icons import icon_label

# Hong Kong Observatory open data. No API key.
# rhrread: current weather (and its uvindex field). flw: local forecast.
# fnd: 9-day. warnsum: warnings. swt: special weather tips. UV has no separate dataType; HKO
# returns uvindex as "" when the reading is unavailable.
_API = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
DEFAULT_URL = f"{_API}?dataType=rhrread&lang=en"
FORECAST_URL = f"{_API}?dataType=flw&lang=en"
NINE_DAY_URL = f"{_API}?dataType=fnd&lang=en"
WARNINGS_URL = f"{_API}?dataType=warnsum&lang=en"
TIPS_URL = f"{_API}?dataType=swt&lang=en"
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
class ForecastDay:
    date: str
    week: str
    weather: str
    temp_high_c: float | None
    temp_low_c: float | None
    rain_chance: str | None


@dataclass(frozen=True)
class NineDayForecast:
    update_time: str
    days: tuple[ForecastDay, ...]


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


def fetch_nine_day(
    url: str = NINE_DAY_URL, timeout: float = 10, lang: str = "en"
) -> NineDayForecast:
    """Download the 9-day forecast (`dataType=fnd`)."""
    return parse_nine_day(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_uv(url: str = UV_URL, timeout: float = 10, lang: str = "en") -> UvIndex:
    """Download the UV index from the current weather report (`dataType=rhrread`)."""
    return parse_uv(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_tips(url: str = TIPS_URL, timeout: float = 10, lang: str = "en") -> SpecialTips:
    """Download special weather tips (`dataType=swt`)."""
    return parse_tips(_fetch_json(_apply_lang(url, lang), timeout))


def fetch_stations(url: str = DEFAULT_URL, timeout: float = 10, lang: str = "en") -> StationReport:
    """Download per-station temperature and humidity from the current report."""
    return parse_stations(_fetch_json(_apply_lang(url, lang), timeout))


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
        f"Conditions: {weather.conditions}",
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
    line = (
        f"{weather.conditions}, {_number(weather.temperature_c)}°C, humidity {humidity}"
    )
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
        if day.rain_chance:
            details.append(f"rain {day.rain_chance}")
        lines.append("")
        lines.append(f"{heading}  {'  '.join(details)}".rstrip())
        if day.weather:
            lines.append(day.weather)
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


def format_json(
    report: CurrentWeather | LocalForecast | NineDayForecast | UvIndex | SpecialTips | StationReport,
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
        rain_chance=rain or None,
    )


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
    if value.is_integer():
        return str(int(value))
    return str(value)
