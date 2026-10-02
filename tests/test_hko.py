import json
from unittest.mock import patch
from urllib.error import URLError

import pytest

from hk_weather.hko import (
    DEFAULT_URL,
    FORECAST_URL,
    WeatherError,
    fetch_current,
    fetch_forecast,
    format_forecast,
    format_report,
    parse_current_report,
    parse_forecast,
)

SAMPLE = {
    "updateTime": "2026-10-02T23:02:00+08:00",
    "icon": [63],
    "temperature": {
        "data": [
            {"place": "King's Park", "value": 27, "unit": "C"},
            {"place": "Hong Kong Observatory", "value": 28, "unit": "C"},
        ]
    },
    "humidity": {
        "data": [{"unit": "percent", "value": 85, "place": "Hong Kong Observatory"}]
    },
    "rainfall": {
        "data": [
            {"unit": "mm", "place": "Wan Chai", "max": 0, "main": "FALSE"},
            {"unit": "mm", "place": "Sai Kung", "max": 2, "main": "FALSE"},
        ]
    },
    "lightning": {
        "data": [
            {"place": "Lantau", "occur": "true"},
            {"place": "Sha Tin", "occur": "false"},
        ]
    },
    "warningMessage": [
        "The Thunderstorm Warning has been issued."
    ],
    "uvindex": "",
}


def test_parse_prefers_observatory_station():
    weather = parse_current_report(SAMPLE)
    assert weather.place == "Hong Kong Observatory"
    assert weather.temperature_c == 28
    assert weather.humidity_percent == 85
    assert weather.conditions == "Rain"
    assert weather.rainfall_mm == 2
    assert weather.rainfall_place == "Sai Kung"
    assert weather.lightning_places == ("Lantau",)
    assert weather.warnings == ("The Thunderstorm Warning has been issued.",)


def test_format_report_plain_text():
    text = format_report(parse_current_report(SAMPLE))
    assert text.startswith("Hong Kong weather\n")
    assert "Temperature: 28°C (Hong Kong Observatory)" in text
    assert "Humidity: 85%" in text
    assert "Conditions: Rain" in text
    assert "Rainfall (past hour, highest district): 2 mm (Sai Kung)" in text
    assert "Lightning: Lantau" in text
    assert "- The Thunderstorm Warning has been issued." in text
    assert text.endswith("\n")


def test_missing_humidity_and_unknown_icon():
    payload = {
        "updateTime": "2026-10-02T12:00:00+08:00",
        "icon": [999],
        "temperature": {"data": [{"place": "Chek Lap Kok", "value": 29.5, "unit": "C"}]},
        "humidity": "",
        "warningMessage": "",
    }
    weather = parse_current_report(payload)
    text = format_report(weather)
    assert weather.place == "Chek Lap Kok"
    assert weather.humidity_percent is None
    assert weather.conditions == "Icon 999"
    assert "Humidity: n/a" in text
    assert "Warnings:" not in text
    assert "Rainfall" not in text


def test_missing_temperature_raises():
    with pytest.raises(WeatherError, match="temperature"):
        parse_current_report({"temperature": {"data": []}})


def test_fetch_current_reads_json(monkeypatch):
    class Response:
        def read(self):
            return json.dumps(SAMPLE).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["timeout"] = timeout
        seen["agent"] = request.get_header("User-agent")
        return Response()

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    weather = fetch_current(timeout=3)
    assert seen["url"] == DEFAULT_URL
    assert "rhrread" in seen["url"]
    assert seen["timeout"] == 3
    assert seen["agent"]
    assert weather.temperature_c == 28


def test_fetch_current_network_error():
    with patch(
        "hk_weather.hko.urllib.request.urlopen",
        side_effect=URLError("timed out"),
    ):
        with pytest.raises(WeatherError, match="could not reach"):
            fetch_current()


def test_fetch_current_invalid_json():
    class Response:
        def read(self):
            return b"not-json"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch("hk_weather.hko.urllib.request.urlopen", return_value=Response()):
        with pytest.raises(WeatherError, match="invalid JSON"):
            fetch_current()


FORECAST = {
    "generalSituation": "A long situation paragraph.",
    "tcInfo": "",
    "fireDangerWarning": "",
    "forecastPeriod": "Weather forecast for Hong Kong (Saturday, 3 Oct 2026)",
    "forecastDesc": "Mainly cloudy with occasional showers.",
    "outlook": "Still a few showers on Sunday.",
    "updateTime": "2026-10-03T00:00:00+08:00",
}


def test_parse_forecast_keeps_the_short_fields():
    forecast = parse_forecast(FORECAST)
    text = format_forecast(forecast)
    assert forecast.period.startswith("Weather forecast for Hong Kong")
    assert forecast.forecast == "Mainly cloudy with occasional showers."
    assert "Outlook: Still a few showers on Sunday." in text
    assert "long situation paragraph" not in text


def test_parse_forecast_requires_description():
    with pytest.raises(WeatherError, match="local forecast"):
        parse_forecast({"forecastDesc": "  ", "outlook": "Later."})


def test_fetch_forecast_uses_flw(monkeypatch):
    class Response:
        def read(self):
            return json.dumps(FORECAST).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return Response()

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    forecast = fetch_forecast(timeout=4)
    assert seen["url"] == FORECAST_URL
    assert "dataType=flw" in seen["url"]
    assert forecast.outlook == "Still a few showers on Sunday."
