import json
from urllib.error import URLError

import pytest

from hk_weather.cli import main
from hk_weather.hko import CurrentWeather, WeatherError

SAMPLE_WEATHER = CurrentWeather(
    update_time="2026-10-02T23:02:00+08:00",
    conditions="Rain",
    place="Hong Kong Observatory",
    temperature_c=28,
    humidity_percent=85,
    rainfall_mm=None,
    rainfall_place=None,
    lightning_places=(),
    warnings=(),
)


def test_cli_version_prints_package_metadata(monkeypatch, capsys):
    monkeypatch.setattr("importlib.metadata.version", lambda name: "1.2.3")
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out == "hk-weather 1.2.3\n"


def test_cli_prints_report(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.cli.fetch_current",
        lambda timeout, lang="en": SAMPLE_WEATHER,
    )
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Temperature: 28°C" in out


def test_cli_reports_fetch_errors(monkeypatch, capsys):
    def boom(timeout, lang="en"):
        raise WeatherError("could not reach Hong Kong Observatory: down")

    monkeypatch.setattr("hk_weather.cli.fetch_current", boom)
    assert main(["--timeout", "1"]) == 1
    err = capsys.readouterr().err
    assert "could not reach Hong Kong Observatory" in err


def test_cli_rejects_non_positive_timeout(capsys):
    assert main(["--timeout", "0"]) == 2
    assert "timeout" in capsys.readouterr().err


def test_cli_json_prints_one_object(monkeypatch, capsys):
    body = json.dumps(
        {
            "updateTime": "2026-10-02T23:02:00+08:00",
            "icon": [63],
            "temperature": {
                "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
            },
            "humidity": "",
            "rainfall": {"data": [{"place": "Sai Kung", "max": 2, "unit": "mm"}]},
            "lightning": {"data": [{"place": "Lantau", "occur": "true"}]},
            "warningMessage": ["The Thunderstorm Warning has been issued."],
        }
    ).encode()

    class Response:
        def read(self):
            return body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: Response(),
    )
    assert main(["--json"]) == 0
    out = capsys.readouterr().out
    assert "Hong Kong weather" not in out
    assert json.loads(out) == {
        "update_time": "2026-10-02T23:02:00+08:00",
        "conditions": "Rain",
        "place": "Hong Kong Observatory",
        "temperature_c": 28.0,
        "humidity_percent": None,
        "rainfall_mm": 2.0,
        "rainfall_place": "Sai Kung",
        "lightning_places": ["Lantau"],
        "warnings": ["The Thunderstorm Warning has been issued."],
    }


def _json_response(payload: dict):
    body = json.dumps(payload).encode()

    class Response:
        def read(self):
            return body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    return Response()


def test_cli_forecast_prints_plain_text(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "forecastPeriod": "Weather forecast for Hong Kong (Saturday, 3 Oct 2026)",
                "forecastDesc": "Mainly cloudy with occasional showers.",
                "outlook": "Still a few showers on Sunday.",
                "updateTime": "2026-10-03T00:00:00+08:00",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--forecast"]) == 0
    out = capsys.readouterr().out
    assert "dataType=flw" in seen["url"]
    assert "Hong Kong forecast" in out
    assert "Mainly cloudy with occasional showers." in out
    assert "Outlook: Still a few showers on Sunday." in out
    assert "Temperature:" not in out


def test_cli_forecast_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "forecastPeriod": "Tonight",
                "forecastDesc": "Fine and dry.",
                "outlook": "",
                "updateTime": "2026-10-03T12:00:00+08:00",
            }
        ),
    )
    assert main(["--forecast", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "update_time": "2026-10-03T12:00:00+08:00",
        "period": "Tonight",
        "forecast": "Fine and dry.",
        "outlook": "",
    }


def test_cli_warnings_lists_active_codes(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "WTS": {
                    "name": "Thunderstorm Warning",
                    "code": "WTS",
                    "actionCode": "EXTEND",
                },
                "WHOT": {
                    "name": "Very Hot Weather Warning",
                    "code": "WHOT",
                    "actionCode": "CANCEL",
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--warnings"]) == 0
    out = capsys.readouterr().out
    assert "dataType=warnsum" in seen["url"]
    assert "WTS  Thunderstorm Warning" in out
    assert "WHOT" not in out
    assert "Very Hot" not in out
    assert "Temperature:" not in out


def test_cli_warnings_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "WTS": {
                    "name": "Thunderstorm Warning",
                    "code": "WTS",
                    "actionCode": "ISSUE",
                },
                "WHOT": {
                    "name": "Very Hot Weather Warning",
                    "code": "WHOT",
                    "actionCode": "CANCEL",
                },
            }
        ),
    )
    assert main(["--warnings", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "warnings": [{"code": "WTS", "description": "Thunderstorm Warning"}]
    }


def test_cli_warnings_json_when_none_are_in_force(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-w", "--json", "--lang", "tc"]) == 0
    assert "dataType=warnsum" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert json.loads(capsys.readouterr().out) == {"warnings": []}


def test_cli_warnings_when_none_are_in_force(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["-w"]) == 0
    assert capsys.readouterr().out == "No weather warnings are in force.\n"


def test_cli_warning_info_prints_messages(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "details": [
                    {
                        "contents": [
                            "Thunderstorm Warning has been extended.",
                            "  ",
                            "Seek safe shelter if you are outdoors.",
                        ],
                        "warningStatementCode": "WTS",
                        "updateTime": "2026-10-03T05:30:00+08:00",
                    },
                    {
                        "contents": ["The Rainstorm Warning Signal is now Amber."],
                        "subtype": "WRAINA",
                        "warningStatementCode": "WRAIN",
                        "updateTime": "2026-10-03T04:00:00+08:00",
                    },
                    {"contents": [], "warningStatementCode": "WHOT"},
                ]
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-W", "--lang", "tc"]) == 0
    assert "dataType=warningInfo" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong warning information\n"
        "\n"
        "WTS\n"
        "Updated: 2026-10-03T05:30:00+08:00\n"
        "- Thunderstorm Warning has been extended.\n"
        "- Seek safe shelter if you are outdoors.\n"
        "\n"
        "WRAIN  WRAINA\n"
        "Updated: 2026-10-03T04:00:00+08:00\n"
        "- The Rainstorm Warning Signal is now Amber.\n"
    )


def test_cli_warning_info_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "details": [
                    {
                        "contents": ["Seek safe shelter."],
                        "warningStatementCode": "WTS",
                        "updateTime": "2026-10-03T05:30:00+08:00",
                    }
                ]
            }
        ),
    )
    assert main(["--warning-info", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "warnings": [
            {
                "code": "WTS",
                "subtype": "",
                "update_time": "2026-10-03T05:30:00+08:00",
                "contents": ["Seek safe shelter."],
            }
        ]
    }


def test_cli_warning_info_when_none_present(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"details": []}),
    )
    assert main(["--warning-info"]) == 0
    assert capsys.readouterr().out == "No detailed warning information is available.\n"


def test_cli_nine_day_prints_compact_summary(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Mainly cloudy with occasional showers.",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                        "forecastMintemp": {"value": 27, "unit": "C"},
                        "forecastMaxrh": {"value": 95, "unit": "percent"},
                        "forecastMinrh": {"value": 75, "unit": "percent"},
                        "PSR": "Medium High",
                    },
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Sunny periods.",
                        "forecastMaxtemp": {"value": 30, "unit": "C"},
                        "forecastMintemp": {"value": 25, "unit": "C"},
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--nine-day"]) == 0
    out = capsys.readouterr().out
    assert "dataType=fnd" in seen["url"]
    assert "2026-10-03 Saturday  high 31°C  low 27°C  humidity 75-95%  rain Medium High" in out
    assert "Mainly cloudy with occasional showers." in out
    assert "2026-10-04 Sunday  high 30°C  low 25°C" in out
    assert "Sunny periods." in out
    sunday = out.split("2026-10-04", 1)[1]
    assert "rain" not in sunday
    assert "humidity" not in sunday


def test_cli_nine_day_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Fine and dry.",
                        "forecastMaxtemp": {"value": 29, "unit": "C"},
                        "forecastMintemp": {"value": 24, "unit": "C"},
                        "forecastMaxrh": {"value": 90, "unit": "percent"},
                        "forecastMinrh": {"value": 65, "unit": "percent"},
                        "PSR": "Low",
                    }
                ],
            }
        ),
    )
    assert main(["-n", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-03T00:00:00+08:00",
        "days": [
            {
                "date": "2026-10-03",
                "week": "Saturday",
                "weather": "Fine and dry.",
                "temp_high_c": 29.0,
                "temp_low_c": 24.0,
                "humidity_high_percent": 90.0,
                "humidity_low_percent": 65.0,
                "rain_chance": "Low",
            }
        ],
    }


def test_cli_today_prints_the_hong_kong_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Mainly cloudy with showers.",
                        "forecastWind": "East force 3.",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                        "forecastMintemp": {"value": 27, "unit": "C"},
                        "forecastMaxrh": {"value": 95, "unit": "percent"},
                        "forecastMinrh": {"value": 75, "unit": "percent"},
                        "PSR": "Medium High",
                    },
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Sunny periods.",
                        "forecastWind": "North force 4.",
                        "forecastMaxtemp": {"value": 30, "unit": "C"},
                        "forecastMintemp": {"value": 25, "unit": "C"},
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-Y", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong forecast for today\n"
        "Source: Hong Kong Observatory open data\n"
        "Updated: 2026-10-03T00:00:00+08:00\n"
        "\n"
        "2026-10-03 Saturday  high 31°C  low 27°C  humidity 75-95%  rain Medium High\n"
        "Mainly cloudy with showers.\n"
        "Wind: East force 3.\n"
    )
    assert "Sunny periods" not in out
    assert "North force" not in out


def test_cli_today_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Mainly cloudy with showers.",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                        "forecastMintemp": {"value": 27, "unit": "C"},
                        "forecastMaxrh": {"value": 95, "unit": "percent"},
                        "forecastMinrh": {"value": 75, "unit": "percent"},
                        "PSR": "Medium High",
                    }
                ],
            }
        ),
    )
    assert main(["--today", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-03T00:00:00+08:00",
        "date": "2026-10-03",
        "week": "Saturday",
        "weather": "Mainly cloudy with showers.",
        "temp_high_c": 31.0,
        "temp_low_c": 27.0,
        "humidity_high_percent": 95.0,
        "humidity_low_percent": 75.0,
        "rain_chance": "Medium High",
        "wind": None,
    }


def test_cli_today_when_the_day_is_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Mainly cloudy.",
                    }
                ],
            }
        ),
    )
    assert main(["--today"]) == 0
    assert capsys.readouterr().out == "Today's forecast is not available.\n"
    assert main(["--today", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "Today's forecast is not available."
    }


def test_cli_tomorrow_prints_the_next_hong_kong_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_tomorrow", lambda now=None: "2026-10-04")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Mainly cloudy with showers.",
                        "forecastWind": "East force 3.",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                        "forecastMintemp": {"value": 27, "unit": "C"},
                    },
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Sunny periods.",
                        "forecastWind": "North force 4.",
                        "forecastMaxtemp": {"value": 30, "unit": "C"},
                        "forecastMintemp": {"value": 25, "unit": "C"},
                        "forecastMaxrh": {"value": 95, "unit": "percent"},
                        "forecastMinrh": {"value": 70, "unit": "percent"},
                        "PSR": "Medium",
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-T", "--lang", "sc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=sc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong forecast for tomorrow\n"
        "Source: Hong Kong Observatory open data\n"
        "Updated: 2026-10-03T00:00:00+08:00\n"
        "\n"
        "2026-10-04 Sunday  high 30°C  low 25°C  humidity 70-95%  rain Medium\n"
        "Sunny periods.\n"
        "Wind: North force 4.\n"
    )
    assert "Mainly cloudy" not in out
    assert "East force" not in out


def test_cli_tomorrow_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_tomorrow", lambda now=None: "2026-10-04")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Sunny periods.",
                        "forecastMaxtemp": {"value": 30, "unit": "C"},
                        "forecastMintemp": {"value": 25, "unit": "C"},
                        "forecastMaxrh": {"value": 90, "unit": "percent"},
                        "forecastMinrh": {"value": 65, "unit": "percent"},
                        "PSR": "Low",
                    }
                ],
            }
        ),
    )
    assert main(["--tomorrow", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-03T00:00:00+08:00",
        "date": "2026-10-04",
        "week": "Sunday",
        "weather": "Sunny periods.",
        "temp_high_c": 30.0,
        "temp_low_c": 25.0,
        "humidity_high_percent": 90.0,
        "humidity_low_percent": 65.0,
        "rain_chance": "Low",
        "wind": None,
    }


def test_cli_tomorrow_when_the_day_is_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_tomorrow", lambda now=None: "2026-10-04")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Mainly cloudy.",
                    }
                ],
            }
        ),
    )
    assert main(["--tomorrow"]) == 0
    assert capsys.readouterr().out == "Tomorrow's forecast is not available.\n"
    assert main(["--tomorrow", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "Tomorrow's forecast is not available."
    }


def test_cli_day_prints_the_first_forecast_entry(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Mainly cloudy with showers.",
                        "forecastWind": "East force 3.",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                        "forecastMintemp": {"value": 27, "unit": "C"},
                        "forecastMaxrh": {"value": 95, "unit": "percent"},
                        "forecastMinrh": {"value": 75, "unit": "percent"},
                        "PSR": "High",
                    },
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Sunny periods.",
                        "forecastWind": "North force 4.",
                        "forecastMaxtemp": {"value": 30, "unit": "C"},
                        "forecastMintemp": {"value": 25, "unit": "C"},
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--day", "1", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong forecast day 1\n"
        "Source: Hong Kong Observatory open data\n"
        "Updated: 2026-10-03T00:00:00+08:00\n"
        "\n"
        "2026-10-03 Saturday  high 31°C  low 27°C  humidity 75-95%  rain High\n"
        "Mainly cloudy with showers.\n"
        "Wind: East force 3.\n"
    )
    assert "Sunny periods" not in out


def test_cli_day_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Mainly cloudy.",
                    },
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Sunny periods.",
                        "forecastMaxtemp": {"value": 30, "unit": "C"},
                        "forecastMintemp": {"value": 25, "unit": "C"},
                        "PSR": "Low",
                    },
                ],
            }
        ),
    )
    assert main(["--day", "2", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["date"] == "2026-10-04"
    assert payload["weather"] == "Sunny periods."
    assert payload["temp_high_c"] == 30.0
    assert payload["rain_chance"] == "Low"
    assert payload["wind"] is None


def test_cli_day_when_the_entry_is_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Mainly cloudy.",
                    }
                ]
            }
        ),
    )
    assert main(["--day", "2"]) == 0
    assert capsys.readouterr().out == "Forecast day 2 is not available.\n"
    assert main(["--day", "2", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "Forecast day 2 is not available."}


def test_cli_day_rejects_out_of_range(capsys):
    for value in ("0", "10", "foo"):
        with pytest.raises(SystemExit) as exc:
            main(["--day", value])
        assert exc.value.code == 2
        assert "1 to 9" in capsys.readouterr().err


def test_cli_psr_lists_each_day(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Mainly cloudy with showers.",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                        "PSR": "High",
                    },
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Sunny periods.",
                        "forecastMaxtemp": {"value": 30, "unit": "C"},
                        "PSR": "  ",
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-P", "--lang", "sc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=sc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong chance of significant rain\n"
        "Updated: 2026-10-03T00:00:00+08:00\n"
        "2026-10-03 Saturday  High\n"
        "2026-10-04 Sunday  n/a\n"
    )
    assert "Mainly cloudy" not in out
    assert "31°C" not in out


def test_cli_psr_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Showers.",
                        "PSR": "Medium High",
                    }
                ],
            }
        ),
    )
    assert main(["--psr", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-03T00:00:00+08:00",
        "days": [
            {"date": "2026-10-03", "week": "Saturday", "psr": "Medium High"}
        ],
    }


def test_cli_weekend_prints_saturday_and_sunday(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-02T16:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261002",
                        "week": "Friday",
                        "forecastWeather": "Weekday showers.",
                        "forecastMaxtemp": {"value": 29, "unit": "C"},
                        "forecastMintemp": {"value": 25, "unit": "C"},
                        "PSR": "High",
                    },
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWeather": "Sunny periods.",
                        "forecastWind": "East force 3.",
                        "forecastMaxtemp": {"value": 30, "unit": "C"},
                        "forecastMintemp": {"value": 25, "unit": "C"},
                        "forecastMaxrh": {"value": 95, "unit": "percent"},
                        "forecastMinrh": {"value": 70, "unit": "percent"},
                        "PSR": "Medium",
                    },
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Mainly fine.",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                        "forecastMintemp": {"value": 26, "unit": "C"},
                        "PSR": "Low",
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-E", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong weekend forecast\n"
        "Source: Hong Kong Observatory open data\n"
        "Updated: 2026-10-02T16:00:00+08:00\n"
        "\n"
        "2026-10-03 Saturday  high 30°C  low 25°C  humidity 70-95%  rain Medium\n"
        "Sunny periods.\n"
        "Wind: East force 3.\n"
        "\n"
        "2026-10-04 Sunday  high 31°C  low 26°C  rain Low\n"
        "Mainly fine.\n"
    )
    assert "Weekday showers" not in out
    assert "Friday" not in out


def test_cli_weekend_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-02T16:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "星期六",
                        "forecastWeather": "大致多云。",
                        "forecastWind": "东风三至四级。",
                        "forecastMaxtemp": {"value": 30, "unit": "C"},
                        "forecastMintemp": {"value": 25, "unit": "C"},
                        "PSR": "中",
                    }
                ],
            }
        ),
    )
    assert main(["--weekend", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-02T16:00:00+08:00",
        "days": [
            {
                "date": "2026-10-03",
                "week": "星期六",
                "weather": "大致多云。",
                "temp_high_c": 30.0,
                "temp_low_c": 25.0,
                "humidity_high_percent": None,
                "humidity_low_percent": None,
                "rain_chance": "中",
                "wind": "东风三至四级。",
            }
        ],
    }


def test_cli_weekend_when_none_in_window(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-05T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261005",
                        "week": "Monday",
                        "forecastWeather": "Fine.",
                    }
                ],
            }
        ),
    )
    assert main(["--weekend"]) == 0
    assert capsys.readouterr().out == "No weekend days are in the 9-day forecast.\n"
    assert main(["--weekend", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No weekend days are in the 9-day forecast."
    }


def test_cli_wind_lists_forecast_wind(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWind": "East force 3 to 4.",
                        "forecastWeather": "Mainly cloudy with showers.",
                        "forecastMaxtemp": {"value": 30, "unit": "C"},
                    },
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWind": "  ",
                        "forecastWeather": "Sunny periods.",
                    },
                    {
                        "forecastDate": "20261005",
                        "week": "Monday",
                        "forecastWind": "North force 4.",
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wind", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong forecast wind\n"
        "Updated: 2026-10-03T00:00:00+08:00\n"
        "2026-10-03 Saturday  East force 3 to 4.\n"
        "2026-10-05 Monday  North force 4.\n"
    )
    assert "Mainly cloudy" not in out
    assert "30°C" not in out


def test_cli_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "Saturday",
                        "forecastWind": "East force 3 to 4.",
                    }
                ],
            }
        ),
    )
    assert main(["--wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-03T00:00:00+08:00",
        "days": [
            {
                "date": "2026-10-03",
                "week": "Saturday",
                "wind": "East force 3 to 4.",
            }
        ],
    }


def test_cli_quake_lists_latest_message(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "lat": 51.79,
                "lon": 159.6,
                "mag": 6,
                "region": "off east coast of Kamchatka",
                "ptime": "2026-10-03T00:34:00+08:00",
                "updateTime": "2026-10-03T00:50:00+08:00",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--quake", "--lang", "tc"]) == 0
    assert "earthquake.php" in seen["url"]
    assert "dataType=qem" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong earthquakes\n"
        "Updated: 2026-10-03T00:50:00+08:00\n"
        "2026-10-03T00:34:00+08:00  M6  off east coast of Kamchatka (51.79, 159.6)\n"
    )


def test_cli_quake_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "lat": 22.3,
                "lon": 114.2,
                "mag": 6.4,
                "region": "near Hong Kong",
                "ptime": "2026-10-03T01:00:00+08:00",
                "updateTime": "2026-10-03T01:10:00+08:00",
            }
        ),
    )
    assert main(["--quake", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "quakes": [
            {
                "time": "2026-10-03T01:00:00+08:00",
                "region": "near Hong Kong",
                "magnitude": 6.4,
                "latitude": 22.3,
                "longitude": 114.2,
                "update_time": "2026-10-03T01:10:00+08:00",
            }
        ]
    }


def test_cli_quake_when_none_reported(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--quake"]) == 0
    assert capsys.readouterr().out == "No recent earthquake is reported.\n"


def test_cli_visibility_lists_stations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "fields": ["Date time", "Automatic Weather Station", "10 minute mean visibility"],
                "data": [
                    ["202610030730", "Central", "14 km"],
                    ["202610030730", "Chek Lap Kok", "N/A"],
                    ["202610030730", "Sai Wan Ho", "30 km"],
                    ["bad"],
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-V", "--lang", "tc"]) == 0
    assert "opendata.php" in seen["url"]
    assert "dataType=LTMV" in seen["url"]
    assert "rformat=json" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong visibility\n"
        "2026-10-03 07:30  Central  14 km\n"
        "2026-10-03 07:30  Sai Wan Ho  30 km\n"
    )


def test_cli_visibility_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"data": [["202610030730", "Waglan Island", "10 km"]]}
        ),
    )
    assert main(["--visibility", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "readings": [
            {
                "time": "2026-10-03 07:30",
                "place": "Waglan Island",
                "visibility": "10 km",
            }
        ]
    }


def test_cli_visibility_when_none_available(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"data": [["202610030730", "Chek Lap Kok", "N/A"]]}
        ),
    )
    assert main(["--visibility"]) == 0
    assert capsys.readouterr().out == "No visibility readings are available.\n"


def test_cli_wind_when_none_available(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"weatherForecast": []}),
    )
    assert main(["--wind"]) == 0
    assert capsys.readouterr().out == "No forecast wind is available.\n"


def test_cli_nine_day_missing_forecast_is_an_error(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"weatherForecast": []}),
    )
    assert main(["--nine-day"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "9-day forecast is missing" in captured.err


def test_cli_uv_prints_index(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-08-19T12:02:00+08:00",
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 31, "unit": "C"}]
                },
                "uvindex": {
                    "data": [{"place": "King's Park", "value": 10, "desc": "very high"}],
                    "recordDesc": "During the past hour",
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--uv"]) == 0
    out = capsys.readouterr().out
    assert "dataType=rhrread" in seen["url"]
    assert "King's Park: 10 (very high)" in out
    assert "During the past hour" in out
    assert "Temperature:" not in out


def test_cli_uv_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-08-19T12:02:00+08:00",
                "uvindex": {
                    "data": [{"place": "King's Park", "value": 10, "desc": "very high"}],
                    "recordDesc": "During the past hour",
                },
            }
        ),
    )
    assert main(["-u", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-08-19T12:02:00+08:00",
        "place": "King's Park",
        "value": 10.0,
        "description": "very high",
        "record": "During the past hour",
    }


def test_cli_uv_when_unavailable(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"updateTime": "2026-10-03T01:02:00+08:00", "uvindex": ""}
        ),
    )
    assert main(["--uv"]) == 0
    out = capsys.readouterr().out
    assert "UV index is not available right now." in out
    assert "Temperature:" not in out


@pytest.mark.parametrize(
    ("argv", "query", "payload"),
    [
        (
            ["--lang", "tc"],
            "dataType=rhrread&lang=tc",
            {
                "updateTime": "2026-10-02T23:02:00+08:00",
                "icon": [63],
                "temperature": {
                    "data": [{"place": "香港天文台", "value": 28, "unit": "C"}]
                },
            },
        ),
        (
            ["--lang", "sc", "--json"],
            "dataType=rhrread&lang=sc",
            {
                "updateTime": "2026-10-02T23:02:00+08:00",
                "icon": [63],
                "temperature": {
                    "data": [{"place": "香港天文台", "value": 28, "unit": "C"}]
                },
            },
        ),
        (
            ["--forecast", "--lang", "tc"],
            "dataType=flw&lang=tc",
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "forecastPeriod": "今日",
                "forecastDesc": "大致多雲。",
                "outlook": "",
            },
        ),
        (
            ["--nine-day", "--lang", "sc"],
            "dataType=fnd&lang=sc",
            {
                "updateTime": "2026-10-03T00:00:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261003",
                        "week": "星期六",
                        "forecastWeather": "大致多云。",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                        "forecastMintemp": {"value": 27, "unit": "C"},
                    }
                ],
            },
        ),
        (
            ["--warnings", "--lang", "tc"],
            "dataType=warnsum&lang=tc",
            {"WTS": {"name": "雷暴警告", "code": "WTS", "actionCode": "ISSUE"}},
        ),
        (
            ["--uv", "--lang", "sc", "--json"],
            "dataType=rhrread&lang=sc",
            {
                "updateTime": "2026-08-19T12:02:00+08:00",
                "uvindex": {
                    "data": [{"place": "京士柏", "value": 8, "desc": "甚高"}],
                    "recordDesc": "過去一小時",
                },
            },
        ),
    ],
)
def test_cli_sends_lang_query(monkeypatch, capsys, argv, query, payload):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(payload)

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(argv) == 0
    assert query in seen["url"]
    out = capsys.readouterr().out
    if "--json" in argv:
        assert isinstance(json.loads(out), dict)
    else:
        assert out.endswith("\n")


def test_cli_tips_requests_swt_and_lang(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "swt": [
                    {"desc": "Strong winds are expected from the east.", "updateTime": "2026-10-03T04:00:00+08:00"},
                    {"desc": "  "},
                    "Stay away from the shoreline.",
                ]
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tips", "--lang", "tc"]) == 0
    assert "dataType=swt" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong special weather tips\n"
        "- Strong winds are expected from the east.\n"
        "- Stay away from the shoreline.\n"
    )
    assert "Temperature:" not in out


def test_cli_tips_json_is_one_object(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"swt": [{"desc": "Hot weather. Drink more water."}]})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-t", "--json"]) == 0
    assert "dataType=swt" in seen["url"]
    assert "lang=en" in seen["url"]
    assert json.loads(capsys.readouterr().out) == {
        "tips": ["Hot weather. Drink more water."]
    }


def test_cli_tips_when_none_are_in_force(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"swt": []}),
    )
    assert main(["--tips"]) == 0
    assert capsys.readouterr().out == "No special weather tips are in force.\n"


def test_cli_stations_lists_temperature_and_humidity(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-02T23:02:00+08:00",
                "temperature": {
                    "data": [
                        {"place": "King's Park", "value": 27, "unit": "C"},
                        {"place": "Hong Kong Observatory", "value": 28, "unit": "C"},
                    ]
                },
                "humidity": {
                    "data": [
                        {"place": "Hong Kong Observatory", "value": 85, "unit": "percent"}
                    ]
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--stations"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=en" in seen["url"]
    out = capsys.readouterr().out
    assert "Place" in out and "Temp" in out and "Humidity" in out
    assert "King's Park            27°C   n/a" in out
    assert "Hong Kong Observatory  28°C   85%" in out
    assert "Conditions:" not in out


_STATIONS = {
    "updateTime": "2026-10-02T23:02:00+08:00",
    "temperature": {
        "data": [
            {"place": "King's Park", "value": 27, "unit": "C"},
            {"place": "Hong Kong Observatory", "value": 28, "unit": "C"},
            {"place": "Hong Kong Park", "value": 29, "unit": "C"},
        ]
    },
    "humidity": {
        "data": [{"place": "Hong Kong Observatory", "value": 85, "unit": "percent"}]
    },
}


def test_cli_place_matches_stations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(_STATIONS)

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--place", "park", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert "King's Park" in out
    assert "27°C" in out
    assert "Hong Kong Park" in out
    assert "29°C" in out
    assert "28°C" not in out
    assert "85%" not in out


def test_cli_place_json_is_case_insensitive(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(_STATIONS),
    )
    assert main(["--place", "oBsErVaToRy", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["update_time"] == "2026-10-02T23:02:00+08:00"
    assert payload["stations"] == [
        {
            "place": "Hong Kong Observatory",
            "temperature_c": 28.0,
            "humidity_percent": 85.0,
        }
    ]


def test_cli_place_when_nothing_matches(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(_STATIONS),
    )
    assert main(["--place", "Atlantis"]) == 0
    assert capsys.readouterr().out == 'No station matches "Atlantis".\n'
    assert main(["--place", "Atlantis", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-02T23:02:00+08:00",
        "stations": [],
        "message": 'No station matches "Atlantis".',
    }


def test_cli_list_places_includes_humidity_only_stations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-02T23:02:00+08:00",
                "temperature": {
                    "data": [
                        {"place": "King's Park", "value": 27, "unit": "C"},
                        {"place": "Sha Tin", "value": 26, "unit": "C"},
                    ]
                },
                "humidity": {
                    "data": [
                        {"place": "Sha Tin", "value": 80, "unit": "percent"},
                        {"place": "Chek Lap Kok", "value": 75, "unit": "percent"},
                    ]
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--list-places", "--lang", "sc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=sc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong places\n"
        "King's Park\n"
        "Sha Tin\n"
        "Chek Lap Kok\n"
    )


def test_cli_list_places_json(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
                }
            }
        ),
    )
    assert main(["--list-places", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"places": ["Hong Kong Observatory"]}


def test_cli_place_rejects_blank_name(capsys):
    assert main(["--place", "   "]) == 2
    assert "place must not be empty" in capsys.readouterr().err


def test_cli_stations_missing_readings_is_an_error(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"temperature": {"data": []}, "humidity": ""}),
    )
    assert main(["--stations"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "station readings are missing" in captured.err


def test_cli_short_is_one_line(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-02T23:02:00+08:00",
                "icon": [63],
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
                },
                "humidity": {
                    "data": [{"place": "Hong Kong Observatory", "value": 85, "unit": "percent"}]
                },
                "warningMessage": [
                    "The Thunderstorm Warning has been issued. It will remain effective until 1:00 a.m.",
                    "The Amber Rainstorm Warning Signal is in force.",
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-s"]) == 0
    assert "dataType=rhrread" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Rain, 28°C, humidity 85% — "
        "The Thunderstorm Warning has been issued (+1 more)\n"
    )
    assert "Hong Kong weather" not in out


def test_cli_short_without_warning_or_humidity(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "icon": [50],
                "temperature": {"data": [{"place": "Chek Lap Kok", "value": 30, "unit": "C"}]},
                "humidity": "",
                "warningMessage": "",
            }
        ),
    )
    assert main(["--short"]) == 0
    assert capsys.readouterr().out == "Sunny, 30°C, humidity n/a\n"


def test_cli_rain_lists_districts(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
                },
                "rainfall": {
                    "data": [
                        {"unit": "mm", "place": "Wan Chai", "max": 0, "main": "FALSE"},
                        {"unit": "mm", "place": "Sai Kung", "max": 2, "main": "FALSE"},
                        {"unit": "mm", "place": "Sai Kung", "max": 9, "main": "FALSE"},
                        {"unit": "mm", "place": "Islands District", "main": "FALSE"},
                    ]
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--rain", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert out == "Hong Kong rainfall\nSai Kung  2 mm\nWan Chai  0 mm\n"
    assert "28°C" not in out
    assert "Islands District" not in out


def test_cli_rain_lists_wettest_first(monkeypatch, capsys):
    payload = {
        "rainfall": {
            "data": [
                {"place": "Wan Chai", "max": 0.5, "unit": "mm"},
                {"place": "North", "max": 8, "unit": "mm"},
                {"place": "Wong Tai Sin", "max": 3, "unit": "mm"},
            ]
        }
    }
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(payload),
    )
    assert main(["--rain"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong rainfall\nNorth  8 mm\nWong Tai Sin  3 mm\nWan Chai  0.5 mm\n"
    )
    assert main(["--rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "readings": [
            {"place": "North", "rainfall_mm": 8.0},
            {"place": "Wong Tai Sin", "rainfall_mm": 3.0},
            {"place": "Wan Chai", "rainfall_mm": 0.5},
        ]
    }


def test_cli_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "rainfall": {
                    "data": [{"place": "Sai Kung", "max": 2, "unit": "mm"}]
                }
            }
        ),
    )
    assert main(["-r", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "readings": [{"place": "Sai Kung", "rainfall_mm": 2.0}]
    }


def test_cli_lightning_lists_active_places(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
                },
                "lightning": {
                    "data": [
                        {"place": "Lantau", "occur": "true"},
                        {"place": "Sha Tin", "occur": "false"},
                        {"place": "Tai Po", "occur": True},
                    ]
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lightning", "--lang", "sc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=sc" in seen["url"]
    out = capsys.readouterr().out
    assert out == "Hong Kong lightning\nLantau\nTai Po\n"
    assert "Sha Tin" not in out


def test_cli_lightning_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"lightning": {"data": [{"place": "Lantau", "occur": "true"}]}}
        ),
    )
    assert main(["--lightning", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"places": ["Lantau"]}


def test_cli_lightning_when_none_reported(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"lightning": {"data": [{"place": "Sha Tin", "occur": "false"}]}}
        ),
    )
    assert main(["--lightning"]) == 0
    assert capsys.readouterr().out == "No lightning is reported.\n"


def test_cli_humidity_lists_places(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
                },
                "humidity": {
                    "recordTime": "2026-10-02T23:00:00+08:00",
                    "data": [
                        {"place": "Hong Kong Observatory", "value": 85, "unit": "percent"},
                        {"place": "Hong Kong Observatory", "value": 90, "unit": "percent"},
                        {"place": "King's Park", "unit": "percent"},
                    ],
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--humidity", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong humidity\n"
        "Recorded: 2026-10-02T23:00:00+08:00\n"
        "Hong Kong Observatory  85%\n"
    )
    assert "28°C" not in out
    assert "King's Park" not in out


def test_cli_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "humidity": {
                    "recordTime": "2026-10-02T23:00:00+08:00",
                    "data": [{"place": "Hong Kong Observatory", "value": 85, "unit": "percent"}],
                }
            }
        ),
    )
    assert main(["--humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "record_time": "2026-10-02T23:00:00+08:00",
        "readings": [{"place": "Hong Kong Observatory", "humidity_percent": 85.0}],
    }


def test_cli_temps_lists_places(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "humidity": {
                    "data": [{"place": "Hong Kong Observatory", "value": 85, "unit": "percent"}]
                },
                "temperature": {
                    "recordTime": "2026-10-02T23:00:00+08:00",
                    "data": [
                        {"place": "King's Park", "value": 27, "unit": "C"},
                        {"place": "Hong Kong Observatory", "value": 28, "unit": "C"},
                        {"place": "Hong Kong Observatory", "value": 29, "unit": "C"},
                        {"place": "Sha Tin", "unit": "C"},
                    ],
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--temps", "--lang", "sc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=sc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong temperatures\n"
        "Recorded: 2026-10-02T23:00:00+08:00\n"
        "King's Park  27°C\n"
        "Hong Kong Observatory  28°C\n"
    )
    assert "85%" not in out
    assert "Sha Tin" not in out


def test_cli_temps_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "temperature": {
                    "recordTime": "2026-10-02T23:00:00+08:00",
                    "data": [{"place": "King's Park", "value": 27.5, "unit": "C"}],
                }
            }
        ),
    )
    assert main(["--temps", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "record_time": "2026-10-02T23:00:00+08:00",
        "readings": [{"place": "King's Park", "temperature_c": 27.5}],
    }


def test_cli_temps_when_no_readings(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"temperature": ""}),
    )
    assert main(["--temps"]) == 0
    assert capsys.readouterr().out == "No temperature readings are available.\n"


def test_cli_hottest_prints_warmest_place(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "temperature": {
                    "recordTime": "2026-10-02T23:00:00+08:00",
                    "data": [
                        {"place": "Hong Kong Observatory", "value": 28, "unit": "C"},
                        {"place": "King's Park", "value": 31, "unit": "C"},
                        {"place": "Sha Tin", "value": 31, "unit": "C"},
                        {"place": "Tai Po", "unit": "C"},
                    ],
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-H", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong hottest\n"
        "Recorded: 2026-10-02T23:00:00+08:00\n"
        "King's Park  31°C\n"
    )
    assert "Sha Tin" not in out
    assert "28°C" not in out


def test_cli_hottest_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "temperature": {
                    "recordTime": "2026-10-02T23:00:00+08:00",
                    "data": [
                        {"place": "Hong Kong Observatory", "value": 28, "unit": "C"},
                        {"place": "King's Park", "value": 31, "unit": "C"},
                    ],
                }
            }
        ),
    )
    assert main(["--hottest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "record_time": "2026-10-02T23:00:00+08:00",
        "place": "King's Park",
        "temperature_c": 31.0,
    }


def test_cli_hottest_when_no_readings(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"temperature": ""}),
    )
    assert main(["--hottest"]) == 0
    assert capsys.readouterr().out == "No temperature readings are available.\n"
    assert main(["--hottest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No temperature readings are available."
    }


def test_cli_humidity_when_no_reading(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"humidity": ""}),
    )
    assert main(["--humidity"]) == 0
    assert capsys.readouterr().out == "No humidity reading is available.\n"


def test_cli_rain_when_no_readings(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"rainfall": ""}),
    )
    assert main(["--rain"]) == 0
    assert capsys.readouterr().out == "No rainfall readings are available.\n"


def test_cli_rejects_unknown_lang():
    with pytest.raises(SystemExit) as exc:
        main(["--lang", "fr"])
    assert exc.value.code == 2


def test_cli_json_fetch_error_stays_on_stderr(monkeypatch, capsys):
    def boom(request, timeout):
        raise URLError("down")

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", boom)
    assert main(["--json"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "could not reach Hong Kong Observatory" in captured.err
