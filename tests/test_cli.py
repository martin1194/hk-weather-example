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
    assert "2026-10-03 Saturday  high 31°C  low 27°C  rain Medium High" in out
    assert "Mainly cloudy with occasional showers." in out
    assert "2026-10-04 Sunday  high 30°C  low 25°C" in out
    assert "Sunny periods." in out
    assert "rain" not in out.split("2026-10-04", 1)[1]


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
                "rain_chance": "Low",
            }
        ],
    }


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
    assert out == "Hong Kong rainfall\nWan Chai  0 mm\nSai Kung  2 mm\n"
    assert "28°C" not in out
    assert "Islands District" not in out


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
