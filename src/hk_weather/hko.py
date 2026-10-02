"""Fetch and format Hong Kong Observatory current weather and the local forecast."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

from hk_weather.icons import icon_label

# Hong Kong Observatory open data. No API key.
# rhrread: current weather. flw: local forecast. warnsum: warning summary.
_API = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
DEFAULT_URL = f"{_API}?dataType=rhrread&lang=en"
FORECAST_URL = f"{_API}?dataType=flw&lang=en"
WARNINGS_URL = f"{_API}?dataType=warnsum&lang=en"
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


def fetch_current(url: str = DEFAULT_URL, timeout: float = 10) -> CurrentWeather:
    """Download the current weather report and return a summary."""
    return parse_current_report(_fetch_json(url, timeout))


def fetch_forecast(url: str = FORECAST_URL, timeout: float = 10) -> LocalForecast:
    """Download the local weather forecast (`dataType=flw`)."""
    return parse_forecast(_fetch_json(url, timeout))


def fetch_warnings(url: str = WARNINGS_URL, timeout: float = 10) -> tuple[WeatherWarning, ...]:
    """Download active weather warnings (`dataType=warnsum`)."""
    return parse_warnings(_fetch_json(url, timeout))


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


def format_warnings(warnings: tuple[WeatherWarning, ...]) -> str:
    """Render active warnings as a short list, or a note when none are in force."""
    if not warnings:
        return "No weather warnings are in force.\n"
    lines = ["Hong Kong weather warnings"]
    lines.extend(f"{warning.code}  {warning.description}" for warning in warnings)
    return "\n".join(lines) + "\n"


def format_json(report: CurrentWeather | LocalForecast) -> str:
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


def _text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return str(value)
