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


def _text_response(body: str):
    encoded = body.encode()

    class Response:
        def read(self):
            return encoded

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


def test_cli_outlook_prints_paragraph(monkeypatch, capsys):
    seen = {}
    message = "Still a few showers on Sunday."

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "forecastDesc": "Mainly cloudy with occasional showers.",
                "outlook": f"  {message}  ",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--outlook", "--lang", "tc"]) == 0
    assert "dataType=flw" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong outlook\n{message}\n"


def test_cli_outlook_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"outlook": "Slightly cooler mornings."}),
    )
    assert main(["--outlook", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"outlook": "Slightly cooler mornings."}


def test_cli_outlook_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"forecastDesc": "Fine and dry.", "outlook": "  "}),
    )
    assert main(["--outlook"]) == 0
    assert capsys.readouterr().out == "No outlook is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--outlook", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No outlook is available."}


def test_cli_coastal_prints_area_forecast(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "  2026-10-04T05:30:00+08:00  ",
                "weatherForecast": {
                    "data": [
                        {
                            "locationName": "  Hong Kong Adjacent Waters  ",
                            "windInfo": "  East force 4.  ",
                            "weatherDescription": "  Scattered showers.  ",
                            "seaSituation": "  Moderate seas.  ",
                        },
                        {
                            "locationName": "Blank",
                            "windInfo": "  ",
                            "weatherDescription": "",
                            "seaSituation": "",
                        },
                        {
                            "locationName": "South of Hong Kong",
                            "windInfo": "East force 4.",
                            "weatherDescription": "Showers.",
                            "seaSituation": "Moderate seas.",
                        },
                    ]
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--coastal", "--lang", "tc"]) == 0
    assert seen["url"].endswith("sccw_json_datagov_uc.json")
    assert capsys.readouterr().out == (
        "Hong Kong coastal waters\n"
        "Updated: 2026-10-04T05:30:00+08:00\n"
        "Hong Kong Adjacent Waters  East force 4.  Scattered showers.  Moderate seas.\n"
        "South of Hong Kong  East force 4.  Showers.  Moderate seas.\n"
    )


def test_cli_coastal_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-04T05:30:00+08:00",
                "weatherForecast": {
                    "data": [
                        {
                            "locationName": "Hong Kong Adjacent Waters",
                            "windInfo": "East force 4.",
                            "weatherDescription": "Scattered showers.",
                            "seaSituation": "Moderate seas.",
                        }
                    ]
                },
            }
        ),
    )
    assert main(["--coastal", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-04T05:30:00+08:00",
        "areas": [
            {
                "place": "Hong Kong Adjacent Waters",
                "wind": "East force 4.",
                "weather": "Scattered showers.",
                "sea": "Moderate seas.",
            }
        ],
    }


def test_cli_coastal_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"weatherForecast": {"data": []}}),
    )
    assert main(["--coastal"]) == 0
    assert capsys.readouterr().out == "No coastal waters forecast is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--coastal", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No coastal waters forecast is available."
    }


def test_cli_coast_report_prints_station_observations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "  2026-10-04T05:30:00+08:00  ",
                "weatherReport": {
                    "data": [
                        {
                            "locationName": "  Waglan Island  ",
                            "windInfo": "  Wind east force 1  ",
                            "weatherDescription": "",
                            "visibilityInfo": {"value": 44, "unit": "kilometre"},
                        },
                        {
                            "locationName": "Blank",
                            "windInfo": "",
                            "weatherDescription": "  ",
                            "visibilityInfo": {"value": "", "unit": ""},
                        },
                        {
                            "locationName": "Macau",
                            "windInfo": "Wind east-southeast force 2",
                            "weatherDescription": "Mist",
                            "visibilityInfo": {"value": 35.0, "unit": "km"},
                        },
                    ]
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--coast-report", "--lang", "tc"]) == 0
    assert seen["url"].endswith("sccw_json_datagov_uc.json")
    assert capsys.readouterr().out == (
        "Hong Kong coastal reports\n"
        "Updated: 2026-10-04T05:30:00+08:00\n"
        "Waglan Island  Wind east force 1  visibility 44 km\n"
        "Macau  Wind east-southeast force 2  Mist  visibility 35 km\n"
    )


def test_cli_coast_report_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-04T05:30:00+08:00",
                "weatherReport": {
                    "data": [
                        {
                            "locationName": "Waglan Island",
                            "windInfo": "Wind east force 1",
                            "weatherDescription": "",
                            "visibilityInfo": {"value": 44, "unit": "kilometre"},
                        }
                    ]
                },
            }
        ),
    )
    assert main(["--coast-report", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-04T05:30:00+08:00",
        "stations": [
            {
                "place": "Waglan Island",
                "wind": "Wind east force 1",
                "weather": "",
                "visibility": 44.0,
                "visibility_unit": "km",
            }
        ],
    }


def test_cli_coast_report_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"weatherReport": {"data": []}}),
    )
    assert main(["--coast-report"]) == 0
    assert capsys.readouterr().out == "No coastal station reports are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--coast-report", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No coastal station reports are available."
    }


def test_cli_forecast_period_prints_the_line(monkeypatch, capsys):
    seen = {}
    period = "Weather forecast for tonight and tomorrow"

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "forecastPeriod": f"  {period}  ",
                "forecastDesc": "Mainly cloudy with a few showers.",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--forecast-period", "--lang", "tc"]) == 0
    assert "dataType=flw" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong forecast period\n{period}\n"


def test_cli_forecast_period_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"forecastPeriod": "Weather forecast for tonight and tomorrow"}
        ),
    )
    assert main(["--forecast-period", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "period": "Weather forecast for tonight and tomorrow"
    }


def test_cli_forecast_period_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"forecastDesc": "Fine and dry.", "forecastPeriod": "  "}),
    )
    assert main(["--forecast-period"]) == 0
    assert capsys.readouterr().out == "No forecast period is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--forecast-period", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No forecast period is available."}


def test_cli_forecast_desc_prints_paragraph(monkeypatch, capsys):
    seen = {}
    description = "Mainly cloudy with a few showers and thunderstorms."

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "forecastPeriod": "Weather forecast for tonight and tomorrow",
                "forecastDesc": f"  {description}  ",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--forecast-desc", "--lang", "tc"]) == 0
    assert "dataType=flw" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong forecast description\n{description}\n"


def test_cli_forecast_desc_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"forecastDesc": "Mainly cloudy with a few showers."}
        ),
    )
    assert main(["--forecast-desc", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "description": "Mainly cloudy with a few showers."
    }


def test_cli_forecast_desc_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"forecastPeriod": "Tonight", "forecastDesc": "  "}
        ),
    )
    assert main(["--forecast-desc"]) == 0
    assert capsys.readouterr().out == "No forecast description is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--forecast-desc", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No forecast description is available."
    }


def test_cli_forecast_updated_prints_timestamp(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "forecastDesc": "Mainly cloudy with a few showers.",
                "updateTime": "  2026-10-03T16:45:00+08:00  ",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--forecast-updated", "--lang", "tc"]) == 0
    assert "dataType=flw" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong forecast update\n2026-10-03T16:45:00+08:00\n"


def test_cli_forecast_updated_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"updateTime": "2026-10-03T16:45:00+08:00"}),
    )
    assert main(["--forecast-updated", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"updated": "2026-10-03T16:45:00+08:00"}


def test_cli_forecast_updated_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"forecastDesc": "Fine and dry.", "updateTime": "  "}
        ),
    )
    assert main(["--forecast-updated"]) == 0
    assert capsys.readouterr().out == "No forecast update time is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--forecast-updated", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No forecast update time is available."
    }


def test_cli_situation_prints_paragraph(monkeypatch, capsys):
    seen = {}
    message = (
        "The northeast monsoon is affecting the coast of Guangdong."
    )

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"generalSituation": f"  {message}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--situation", "--lang", "tc"]) == 0
    assert "dataType=flw" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong general situation\n{message}\n"


def test_cli_situation_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"generalSituation": "A dry northeast monsoon is affecting the coast."}
        ),
    )
    assert main(["-g", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "situation": "A dry northeast monsoon is affecting the coast."
    }


def test_cli_situation_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"generalSituation": "   "}),
    )
    assert main(["--situation"]) == 0
    assert capsys.readouterr().out == "No general situation is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--situation", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No general situation is available."
    }


def test_cli_fire_danger_prints_warning(monkeypatch, capsys):
    seen = {}
    message = "The Fire Danger Warning is Yellow."

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"fireDangerWarning": f"  {message}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--fire-danger", "--lang", "sc"]) == 0
    assert "dataType=flw" in seen["url"]
    assert "lang=sc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong fire danger\n{message}\n"


def test_cli_fire_danger_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"fireDangerWarning": "The Fire Danger Warning is Red."}
        ),
    )
    assert main(["-f", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "warning": "The Fire Danger Warning is Red."
    }


def test_cli_fire_danger_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"fireDangerWarning": "   "}),
    )
    assert main(["--fire-danger"]) == 0
    assert capsys.readouterr().out == "No fire danger warning is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--fire-danger", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No fire danger warning is available."
    }


def test_cli_tc_info_prints_paragraph(monkeypatch, capsys):
    seen = {}
    message = (
        "At noon, Typhoon Mangkhut was centred about 510 kilometres southeast of Hong Kong."
    )

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"tcInfo": f"  {message}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tc-info", "--lang", "tc"]) == 0
    assert "dataType=flw" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        f"Hong Kong tropical cyclone information\n{message}\n"
    )


def test_cli_tc_info_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"tcInfo": "There is no tropical cyclone within 800 kilometres of Hong Kong."}
        ),
    )
    assert main(["--tc-info", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "info": "There is no tropical cyclone within 800 kilometres of Hong Kong."
    }


def test_cli_tc_info_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"tcInfo": "   "}),
    )
    assert main(["--tc-info"]) == 0
    assert capsys.readouterr().out == "No tropical cyclone information is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--tc-info", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No tropical cyclone information is available."
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


def test_cli_warning_time_prints_issue_and_expiry(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "WTS": {
                    "name": "Thunderstorm Warning",
                    "code": "WTS",
                    "actionCode": "EXTEND",
                    "issueTime": "2026-10-03T06:00:00+08:00",
                    "updateTime": "2026-10-03T12:00:00+08:00",
                    "expireTime": "2026-10-03T18:00:00+08:00",
                },
                "WHOT": {
                    "name": "Very Hot Weather Warning",
                    "code": "WHOT",
                    "actionCode": "CANCEL",
                    "issueTime": "2026-10-02T06:00:00+08:00",
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--warning-time", "--lang", "tc"]) == 0
    assert "dataType=warnsum" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong warning times\n"
        "WTS  Thunderstorm Warning\n"
        "Issued: 2026-10-03T06:00:00+08:00\n"
        "Updated: 2026-10-03T12:00:00+08:00\n"
        "Expires: 2026-10-03T18:00:00+08:00\n"
    )


def test_cli_warning_time_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "WTS": {
                    "name": "Thunderstorm Warning",
                    "code": "WTS",
                    "actionCode": "ISSUE",
                    "issueTime": "2026-10-03T06:00:00+08:00",
                    "updateTime": "2026-10-03T06:00:00+08:00",
                }
            }
        ),
    )
    assert main(["--warning-time", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "warnings": [
            {
                "code": "WTS",
                "description": "Thunderstorm Warning",
                "issue_time": "2026-10-03T06:00:00+08:00",
                "update_time": "2026-10-03T06:00:00+08:00",
                "expire_time": "",
            }
        ]
    }


def test_cli_warning_time_when_none_are_in_force(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "WHOT": {
                    "name": "Very Hot Weather Warning",
                    "code": "WHOT",
                    "actionCode": "CANCEL",
                    "issueTime": "2026-10-02T06:00:00+08:00",
                }
            }
        ),
    )
    assert main(["--warning-time"]) == 0
    assert capsys.readouterr().out == "No weather warnings are in force.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--warning-time", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No weather warnings are in force."
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


def test_cli_sea_temp_prints_the_reading(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "seaTemp": {
                    "place": "North Point",
                    "value": 29,
                    "unit": "C",
                    "recordTime": "2026-10-03T14:00:00+08:00",
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sea-temp", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong sea temperature\n"
        "North Point  29°C\n"
        "Recorded: 2026-10-03T14:00:00+08:00\n"
    )


def test_cli_sea_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "seaTemp": {
                    "place": "North Point",
                    "value": 29,
                    "unit": "C",
                    "recordTime": "2026-10-03T14:00:00+08:00",
                }
            }
        ),
    )
    assert main(["--sea-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "place": "North Point",
        "temperature_c": 29.0,
        "recorded": "2026-10-03T14:00:00+08:00",
    }


def test_cli_sea_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"seaTemp": {"place": "North Point"}}),
    )
    assert main(["--sea-temp"]) == 0
    assert capsys.readouterr().out == "No sea temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--sea-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No sea temperature is available."}


def test_cli_soil_temp_prints_depths(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "soilTemp": [
                    {
                        "place": "Hong Kong Observatory",
                        "value": 30.6,
                        "unit": "C",
                        "recordTime": "2026-10-03T07:00:00+08:00",
                        "depth": {"unit": "metre", "value": 0.5},
                    },
                    {
                        "place": "Hong Kong Observatory",
                        "value": 30.4,
                        "unit": "C",
                        "recordTime": "2026-10-03T07:00:00+08:00",
                        "depth": {"unit": "metre", "value": 1},
                    },
                    {"place": "Hong Kong Observatory", "value": 29},
                ]
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--soil-temp", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong soil temperature\n"
        "Hong Kong Observatory  0.5 m  30.6°C\n"
        "Hong Kong Observatory  1 m  30.4°C\n"
        "Recorded: 2026-10-03T07:00:00+08:00\n"
    )


def test_cli_soil_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "soilTemp": [
                    {
                        "place": "Hong Kong Observatory",
                        "value": 30.6,
                        "unit": "C",
                        "recordTime": "2026-10-03T07:00:00+08:00",
                        "depth": {"unit": "metre", "value": 0.5},
                    }
                ]
            }
        ),
    )
    assert main(["--soil-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "readings": [
            {
                "place": "Hong Kong Observatory",
                "depth_m": 0.5,
                "temperature_c": 30.6,
                "recorded": "2026-10-03T07:00:00+08:00",
            }
        ]
    }


def test_cli_soil_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"soilTemp": []}),
    )
    assert main(["--soil-temp"]) == 0
    assert capsys.readouterr().out == "No soil temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--soil-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No soil temperature is available."}


def test_cli_nine_situation_prints_paragraph(monkeypatch, capsys):
    seen = {}
    message = (
        "A replenishment of the northeast monsoon will reach the coast of Guangdong."
    )

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"generalSituation": f"  {message}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--nine-situation", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong 9-day situation\n{message}\n"


def test_cli_nine_situation_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"generalSituation": "Showers will lessen early next week."}
        ),
    )
    assert main(["--nine-situation", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "situation": "Showers will lessen early next week."
    }


def test_cli_nine_situation_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"generalSituation": "   "}),
    )
    assert main(["--nine-situation"]) == 0
    assert capsys.readouterr().out == "No 9-day situation is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--nine-situation", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No 9-day situation is available."
    }


def test_cli_nine_updated_prints_timestamp(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"updateTime": "  2026-10-03T16:45:00+08:00  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--nine-updated", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong 9-day update\n2026-10-03T16:45:00+08:00\n"


def test_cli_nine_updated_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"updateTime": "2026-10-03T16:45:00+08:00"}),
    )
    assert main(["--nine-updated", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"updated": "2026-10-03T16:45:00+08:00"}


def test_cli_nine_updated_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"generalSituation": "Fine.", "updateTime": "  "}),
    )
    assert main(["--nine-updated"]) == 0
    assert capsys.readouterr().out == "No 9-day update time is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--nine-updated", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No 9-day update time is available."
    }


def test_cli_nine_weather_lists_each_day(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "  2026-10-03T16:45:00+08:00  ",
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "  Mainly cloudy with a few showers.  ",
                    },
                    {
                        "forecastDate": "20261005",
                        "week": "Monday",
                        "forecastWind": "East force 3.",
                    },
                    {
                        "forecastDate": "20261006",
                        "week": "Tuesday",
                        "forecastWeather": "Sunny periods.",
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--nine-weather", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong 9-day weather\n"
        "Updated: 2026-10-03T16:45:00+08:00\n"
        "2026-10-04 Sunday  Mainly cloudy with a few showers.\n"
        "2026-10-06 Tuesday  Sunny periods.\n"
    )


def test_cli_nine_weather_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T16:45:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Mainly cloudy with a few showers.",
                    }
                ],
            }
        ),
    )
    assert main(["--nine-weather", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-03T16:45:00+08:00",
        "days": [
            {
                "date": "2026-10-04",
                "week": "Sunday",
                "weather": "Mainly cloudy with a few showers.",
            }
        ],
    }


def test_cli_nine_weather_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "weatherForecast": [
                    {"forecastDate": "20261004", "week": "Sunday", "forecastWind": "East force 3."}
                ]
            }
        ),
    )
    assert main(["--nine-weather"]) == 0
    assert capsys.readouterr().out == "No 9-day weather is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--nine-weather", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No 9-day weather is available."}


def test_cli_nine_temp_lists_each_day(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "  2026-10-03T16:45:00+08:00  ",
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                        "forecastMintemp": {"value": 26, "unit": "C"},
                    },
                    {
                        "forecastDate": "20261005",
                        "week": "Monday",
                        "forecastWeather": "Sunny periods.",
                    },
                    {
                        "forecastDate": "20261006",
                        "week": "Tuesday",
                        "forecastMaxtemp": {"value": 30.5, "unit": "C"},
                    },
                    {
                        "forecastDate": "20261007",
                        "week": "Wednesday",
                        "forecastMintemp": {"value": 27, "unit": "C"},
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--nine-temp", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong 9-day temperatures\n"
        "Updated: 2026-10-03T16:45:00+08:00\n"
        "2026-10-04 Sunday  high 31°C  low 26°C\n"
        "2026-10-06 Tuesday  high 30.5°C\n"
        "2026-10-07 Wednesday  low 27°C\n"
    )


def test_cli_nine_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T16:45:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                        "forecastMintemp": {"value": 26, "unit": "C"},
                    }
                ],
            }
        ),
    )
    assert main(["--nine-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-03T16:45:00+08:00",
        "days": [
            {
                "date": "2026-10-04",
                "week": "Sunday",
                "temp_high_c": 31.0,
                "temp_low_c": 26.0,
            }
        ],
    }


def test_cli_nine_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Sunny periods.",
                        "forecastMaxtemp": {"value": True, "unit": "C"},
                    }
                ]
            }
        ),
    )
    assert main(["--nine-temp"]) == 0
    assert capsys.readouterr().out == "No 9-day temperatures are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--nine-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No 9-day temperatures are available."}


def test_cli_nine_humidity_lists_each_day(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "  2026-10-03T16:45:00+08:00  ",
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastMaxrh": {"value": 95, "unit": "percent"},
                        "forecastMinrh": {"value": 65, "unit": "percent"},
                    },
                    {
                        "forecastDate": "20261005",
                        "week": "Monday",
                        "forecastMaxtemp": {"value": 31, "unit": "C"},
                    },
                    {
                        "forecastDate": "20261006",
                        "week": "Tuesday",
                        "forecastMaxrh": {"value": 90.5, "unit": "percent"},
                    },
                    {
                        "forecastDate": "20261007",
                        "week": "Wednesday",
                        "forecastMinrh": {"value": 70, "unit": "percent"},
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--nine-humidity", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong 9-day humidity\n"
        "Updated: 2026-10-03T16:45:00+08:00\n"
        "2026-10-04 Sunday  humidity 65-95%\n"
        "2026-10-06 Tuesday  humidity 90.5%\n"
        "2026-10-07 Wednesday  humidity 70%\n"
    )


def test_cli_nine_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T16:45:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastMaxrh": {"value": 95, "unit": "percent"},
                        "forecastMinrh": {"value": 65, "unit": "percent"},
                    }
                ],
            }
        ),
    )
    assert main(["--nine-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-03T16:45:00+08:00",
        "days": [
            {
                "date": "2026-10-04",
                "week": "Sunday",
                "humidity_high_percent": 95.0,
                "humidity_low_percent": 65.0,
            }
        ],
    }


def test_cli_nine_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "forecastWeather": "Sunny periods.",
                        "forecastMaxrh": {"value": True, "unit": "percent"},
                    }
                ]
            }
        ),
    )
    assert main(["--nine-humidity"]) == 0
    assert capsys.readouterr().out == "No 9-day humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--nine-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No 9-day humidity is available."}


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


def test_cli_yesterday_prints_observatory_summary(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "HKOReadingsMaxTemp": "31.7",
                "HKOReadingsMinTemp": "27.0",
                "HKOReadingsRainfall": "14.1",
                "HKOReadingsMaxRH": "90",
                "HKOReadingsMinRH": "69",
                "ReportTimeInfoDate": "20261002",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--yesterday", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong yesterday\n"
        "2026-10-02\n"
        "High: 31.7°C\n"
        "Low: 27°C\n"
        "Rainfall: 14.1 mm\n"
        "Humidity: 69-90%\n"
    )


def test_cli_yesterday_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "HKOReadingsMaxTemp": "31.7",
                "HKOReadingsMinTemp": "27",
                "HKOReadingsRainfall": "14.1",
                "HKOReadingsMaxRH": "90",
                "HKOReadingsMinRH": "69",
            }
        ),
    )
    assert main(["--yesterday", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "date": "2026-10-02",
        "temp_high_c": 31.7,
        "temp_low_c": 27.0,
        "rainfall_mm": 14.1,
        "humidity_high_percent": 90.0,
        "humidity_low_percent": 69.0,
    }


def test_cli_yesterday_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"HongKongDesc": "background radiation"}),
    )
    assert main(["--yesterday"]) == 0
    assert capsys.readouterr().out == "Yesterday's Observatory summary is not available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--yesterday", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "Yesterday's Observatory summary is not available."
    }


def test_cli_mean_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "data": [
                    ["2026", "1", "1", "18.8", "C"],
                    ["2026", "8", "30", "***", ""],
                    ["2026", "8", "31", "  27.7  ", "C"],
                ]
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--mean-temp", "--lang", "tc"]) == 0
    assert "dataType=CLMTEMP" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "year=2026" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong daily mean temperature\n2026-08-31  27.7°C\n"


def test_cli_mean_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": [["2026", "8", "31", "27.7", "C"]]}),
    )
    assert main(["--mean-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"date": "2026-08-31", "temperature_c": 27.7}


def test_cli_mean_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": [["2026", "8", "31", "***", ""]]}),
    )
    assert main(["--mean-temp"]) == 0
    assert capsys.readouterr().out == "No daily mean temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": []}),
    )
    assert main(["--mean-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No daily mean temperature is available."}


def test_cli_tai_mo_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,23.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  21.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMS_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 大帽山\n"
        "2026-08-31  21.7°C\n"
    )


def test_cli_tai_mo_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,21.7,C\n"
        ),
    )
    assert main(["--tai-mo-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo Shan",
        "date": "2026-08-31",
        "temperature_c": 21.7,
    }


def test_cli_tai_mo_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-temp"]) == 0
    assert capsys.readouterr().out == "No Tai Mo Shan temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo Shan temperature is available."
    }


def test_cli_tate_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,24.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  24.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tate-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TC_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 大老山\n"
        "2026-08-31  24.2°C\n"
    )


def test_cli_tate_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,24.2,C\n"
        ),
    )
    assert main(["--tate-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tate's Cairn",
        "date": "2026-08-31",
        "temperature_c": 24.2,
    }


def test_cli_tate_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tate-temp"]) == 0
    assert capsys.readouterr().out == "No Tate's Cairn temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tate-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tate's Cairn temperature is available."
    }


def test_cli_sai_kung_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,30.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sai-kung-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKG_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 西貢\n"
        "2026-08-31  27.7°C\n"
    )


def test_cli_sai_kung_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.7,C\n"
        ),
    )
    assert main(["--sai-kung-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sai Kung",
        "date": "2026-08-31",
        "temperature_c": 27.7,
    }


def test_cli_sai_kung_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sai-kung-temp"]) == 0
    assert capsys.readouterr().out == "No Sai Kung temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sai-kung-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sai Kung temperature is available."
    }


def test_cli_sha_tin_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,30.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-tin-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SHA_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 沙田\n"
        "2026-08-31  27.5°C\n"
    )


def test_cli_sha_tin_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.5,C\n"
        ),
    )
    assert main(["--sha-tin-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Tin",
        "date": "2026-08-31",
        "temperature_c": 27.5,
    }


def test_cli_sha_tin_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-tin-temp"]) == 0
    assert capsys.readouterr().out == "No Sha Tin temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-tin-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Tin temperature is available."
    }


def test_cli_sheung_shui_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,30.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sheung-shui-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSH_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 上水\n"
        "2026-08-31  27.1°C\n"
    )


def test_cli_sheung_shui_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.1,C\n"
        ),
    )
    assert main(["--sheung-shui-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sheung Shui",
        "date": "2026-08-31",
        "temperature_c": 27.1,
    }


def test_cli_sheung_shui_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sheung-shui-temp"]) == 0
    assert capsys.readouterr().out == "No Sheung Shui temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sheung-shui-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sheung Shui temperature is available."
    }


def test_cli_wong_chuk_hang_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.3,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wong-chuk-hang-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKS_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 黃竹坑\n"
        "2026-08-31  27.7°C\n"
    )


def test_cli_wong_chuk_hang_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.7,C\n"
        ),
    )
    assert main(["--wong-chuk-hang-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wong Chuk Hang",
        "date": "2026-08-31",
        "temperature_c": 27.7,
    }


def test_cli_wong_chuk_hang_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wong-chuk-hang-temp"]) == 0
    assert capsys.readouterr().out == "No Wong Chuk Hang temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wong-chuk-hang-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wong Chuk Hang temperature is available."
    }


def test_cli_lau_fau_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.6,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lau-fau-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_LFS_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 流浮山\n"
        "2026-08-31  26.6°C\n"
    )


def test_cli_lau_fau_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.6,C\n"
        ),
    )
    assert main(["--lau-fau-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Lau Fau Shan",
        "date": "2026-08-31",
        "temperature_c": 26.6,
    }


def test_cli_lau_fau_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--lau-fau-temp"]) == 0
    assert capsys.readouterr().out == "No Lau Fau Shan temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--lau-fau-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Lau Fau Shan temperature is available."
    }


def test_cli_tseung_kwan_o_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tseung-kwan-o-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_JKB_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 將軍澳\n"
        "2026-08-31  26.7°C\n"
    )


def test_cli_tseung_kwan_o_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.7,C\n"
        ),
    )
    assert main(["--tseung-kwan-o-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tseung Kwan O",
        "date": "2026-08-31",
        "temperature_c": 26.7,
    }


def test_cli_tseung_kwan_o_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tseung-kwan-o-temp"]) == 0
    assert capsys.readouterr().out == "No Tseung Kwan O temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tseung-kwan-o-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tseung Kwan O temperature is available."
    }


def test_cli_sham_shui_po_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.9,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sham-shui-po-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSP_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 深水埗\n"
        "2026-08-31  27.5°C\n"
    )


def test_cli_sham_shui_po_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.5,C\n"
        ),
    )
    assert main(["--sham-shui-po-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sham Shui Po",
        "date": "2026-08-31",
        "temperature_c": 27.5,
    }


def test_cli_sham_shui_po_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sham-shui-po-temp"]) == 0
    assert capsys.readouterr().out == "No Sham Shui Po temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sham-shui-po-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sham Shui Po temperature is available."
    }


def test_cli_shek_kong_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,30.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shek-kong-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SEK_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 石崗\n"
        "2026-08-31  27.1°C\n"
    )


def test_cli_shek_kong_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.1,C\n"
        ),
    )
    assert main(["--shek-kong-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shek Kong",
        "date": "2026-08-31",
        "temperature_c": 27.1,
    }


def test_cli_shek_kong_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shek-kong-temp"]) == 0
    assert capsys.readouterr().out == "No Shek Kong temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shek-kong-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shek Kong temperature is available."
    }


def test_cli_wetland_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,30.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wetland-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WLP_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 濕地公園\n"
        "2026-08-31  26.6°C\n"
    )


def test_cli_wetland_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.6,C\n"
        ),
    )
    assert main(["--wetland-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wetland Park",
        "date": "2026-08-31",
        "temperature_c": 26.6,
    }


def test_cli_wetland_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wetland-temp"]) == 0
    assert capsys.readouterr().out == "No Wetland Park temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wetland-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wetland Park temperature is available."
    }


def test_cli_ta_kwu_ling_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,30.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ta-kwu-ling-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TKL_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 打鼓嶺\n"
        "2026-08-31  26.8°C\n"
    )


def test_cli_ta_kwu_ling_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.8,C\n"
        ),
    )
    assert main(["--ta-kwu-ling-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ta Kwu Ling",
        "date": "2026-08-31",
        "temperature_c": 26.8,
    }


def test_cli_ta_kwu_ling_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ta-kwu-ling-temp"]) == 0
    assert capsys.readouterr().out == "No Ta Kwu Ling temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ta-kwu-ling-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ta Kwu Ling temperature is available."
    }


def test_cli_peng_chau_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--peng-chau-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_PEN_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 坪洲\n"
        "2026-08-31  27.6°C\n"
    )


def test_cli_peng_chau_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.6,C\n"
        ),
    )
    assert main(["--peng-chau-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Peng Chau",
        "date": "2026-08-31",
        "temperature_c": 27.6,
    }


def test_cli_peng_chau_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--peng-chau-temp"]) == 0
    assert capsys.readouterr().out == "No Peng Chau temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--peng-chau-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Peng Chau temperature is available."
    }


def test_cli_park_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--park-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 京士柏\n"
        "2026-08-31  27.6°C\n"
    )


def test_cli_park_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.6,C\n"
        ),
    )
    assert main(["--park-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "temperature_c": 27.6,
    }


def test_cli_park_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--park-temp"]) == 0
    assert capsys.readouterr().out == "No King's Park temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--park-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park temperature is available."
    }


def test_cli_cheung_chau_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cheung-chau-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CCH_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 長洲\n"
        "2026-08-31  27°C\n"
    )


def test_cli_cheung_chau_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.0,C\n"
        ),
    )
    assert main(["--cheung-chau-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Cheung Chau",
        "date": "2026-08-31",
        "temperature_c": 27.0,
    }


def test_cli_cheung_chau_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cheung-chau-temp"]) == 0
    assert capsys.readouterr().out == "No Cheung Chau temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cheung-chau-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Cheung Chau temperature is available."
    }


def test_cli_waglan_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--waglan-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WGL_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 橫瀾島\n"
        "2026-08-31  27.6°C\n"
    )


def test_cli_waglan_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.6,C\n"
        ),
    )
    assert main(["--waglan-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Waglan Island",
        "date": "2026-08-31",
        "temperature_c": 27.6,
    }


def test_cli_waglan_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--waglan-temp"]) == 0
    assert capsys.readouterr().out == "No Waglan Island temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--waglan-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Waglan Island temperature is available."
    }


def test_cli_ping_chau_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ping-chau-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_EPC_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 平洲\n"
        "2026-08-31  26°C\n"
    )


def test_cli_ping_chau_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.0,C\n"
        ),
    )
    assert main(["--ping-chau-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ping Chau",
        "date": "2026-08-31",
        "temperature_c": 26.0,
    }


def test_cli_ping_chau_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ping-chau-temp"]) == 0
    assert capsys.readouterr().out == "No Ping Chau temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ping-chau-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ping Chau temperature is available."
    }


def test_cli_sha_lo_wan_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-lo-wan-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SLW_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 沙螺灣\n"
        "2026-08-31  26.6°C\n"
    )


def test_cli_sha_lo_wan_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.6,C\n"
        ),
    )
    assert main(["--sha-lo-wan-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Lo Wan",
        "date": "2026-08-31",
        "temperature_c": 26.6,
    }


def test_cli_sha_lo_wan_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-lo-wan-temp"]) == 0
    assert capsys.readouterr().out == "No Sha Lo Wan temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-lo-wan-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Lo Wan temperature is available."
    }


def test_cli_airport_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,7,29,26.8,C\n"
            "2026,7,30,***,\n"
            "2026,7,31,  26.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--airport-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 香港國際機場\n"
        "2026-07-31  26.2°C\n"
    )


def test_cli_airport_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,26.2,C\n"
        ),
    )
    assert main(["--airport-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-07-31",
        "temperature_c": 26.2,
    }


def test_cli_airport_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,***,\n"
        ),
    )
    assert main(["--airport-temp"]) == 0
    assert capsys.readouterr().out == "No airport temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--airport-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No airport temperature is available."
    }


def test_cli_clear_water_bay_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--clear-water-bay-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CWB_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 清水灣\n"
        "2026-08-31  27°C\n"
    )


def test_cli_clear_water_bay_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.0,C\n"
        ),
    )
    assert main(["--clear-water-bay-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Clear Water Bay",
        "date": "2026-08-31",
        "temperature_c": 27.0,
    }


def test_cli_clear_water_bay_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--clear-water-bay-temp"]) == 0
    assert capsys.readouterr().out == "No Clear Water Bay temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--clear-water-bay-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Clear Water Bay temperature is available."
    }


def test_cli_hong_kong_park_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--hong-kong-park-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKP_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 香港公園\n"
        "2026-08-31  27.1°C\n"
    )


def test_cli_hong_kong_park_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.1,C\n"
        ),
    )
    assert main(["--hong-kong-park-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Park",
        "date": "2026-08-31",
        "temperature_c": 27.1,
    }


def test_cli_hong_kong_park_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--hong-kong-park-temp"]) == 0
    assert capsys.readouterr().out == "No Hong Kong Park temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--hong-kong-park-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Hong Kong Park temperature is available."
    }


def test_cli_ngong_ping_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,24.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  23.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ngong-ping-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_NGP_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 昂坪\n"
        "2026-08-31  23.7°C\n"
    )


def test_cli_ngong_ping_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,23.7,C\n"
        ),
    )
    assert main(["--ngong-ping-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ngong Ping",
        "date": "2026-08-31",
        "temperature_c": 23.7,
    }


def test_cli_ngong_ping_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ngong-ping-temp"]) == 0
    assert capsys.readouterr().out == "No Ngong Ping temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ngong-ping-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ngong Ping temperature is available."
    }


def test_cli_kwun_tong_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--kwun-tong-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KTG_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 觀塘\n"
        "2026-08-31  27.4°C\n"
    )


def test_cli_kwun_tong_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.4,C\n"
        ),
    )
    assert main(["--kwun-tong-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Kwun Tong",
        "date": "2026-08-31",
        "temperature_c": 27.4,
    }


def test_cli_kwun_tong_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--kwun-tong-temp"]) == 0
    assert capsys.readouterr().out == "No Kwun Tong temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--kwun-tong-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Kwun Tong temperature is available."
    }


def test_cli_wong_tai_sin_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wong-tai-sin-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WTS_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 黃大仙\n"
        "2026-08-31  27.7°C\n"
    )


def test_cli_wong_tai_sin_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.7,C\n"
        ),
    )
    assert main(["--wong-tai-sin-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wong Tai Sin",
        "date": "2026-08-31",
        "temperature_c": 27.7,
    }


def test_cli_wong_tai_sin_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wong-tai-sin-temp"]) == 0
    assert capsys.readouterr().out == "No Wong Tai Sin temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wong-tai-sin-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wong Tai Sin temperature is available."
    }


def test_cli_tsuen_wan_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tsuen-wan-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TWN_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 荃灣\n"
        "2026-08-31  26°C\n"
    )


def test_cli_tsuen_wan_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.0,C\n"
        ),
    )
    assert main(["--tsuen-wan-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tsuen Wan",
        "date": "2026-08-31",
        "temperature_c": 26.0,
    }


def test_cli_tsuen_wan_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tsuen-wan-temp"]) == 0
    assert capsys.readouterr().out == "No Tsuen Wan temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tsuen-wan-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tsuen Wan temperature is available."
    }


def test_cli_yuen_long_park_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.3  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--yuen-long-park-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_YLP_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 元朗公園\n"
        "2026-08-31  27.3°C\n"
    )


def test_cli_yuen_long_park_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.3,C\n"
        ),
    )
    assert main(["--yuen-long-park-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Yuen Long Park",
        "date": "2026-08-31",
        "temperature_c": 27.3,
    }


def test_cli_yuen_long_park_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--yuen-long-park-temp"]) == 0
    assert capsys.readouterr().out == "No Yuen Long Park temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--yuen-long-park-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Yuen Long Park temperature is available."
    }


def test_cli_tap_mun_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tap-mun-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TAP_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 塔門\n"
        "2026-08-31  26.7°C\n"
    )


def test_cli_tap_mun_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.7,C\n"
        ),
    )
    assert main(["--tap-mun-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tap Mun",
        "date": "2026-08-31",
        "temperature_c": 26.7,
    }


def test_cli_tap_mun_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tap-mun-temp"]) == 0
    assert capsys.readouterr().out == "No Tap Mun temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tap-mun-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tap Mun temperature is available."
    }


def test_cli_shau_kei_wan_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shau-kei-wan-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKW_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 筲箕灣\n"
        "2026-08-31  27.1°C\n"
    )
    assert main(["--shau-kei-wan-temp", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 筲箕湾\n"
        "2026-08-31  27.1°C\n"
    )


def test_cli_shau_kei_wan_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.1,C\n"
        ),
    )
    assert main(["--shau-kei-wan-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shau Kei Wan",
        "date": "2026-08-31",
        "temperature_c": 27.1,
    }


def test_cli_shau_kei_wan_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shau-kei-wan-temp"]) == 0
    assert capsys.readouterr().out == "No Shau Kei Wan temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shau-kei-wan-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shau Kei Wan temperature is available."
    }


def test_cli_happy_valley_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  28.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--happy-valley-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HPV_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 跑馬地\n"
        "2026-08-31  28.4°C\n"
    )
    assert main(["--happy-valley-temp", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 跑马地\n"
        "2026-08-31  28.4°C\n"
    )


def test_cli_happy_valley_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,28.4,C\n"
        ),
    )
    assert main(["--happy-valley-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Happy Valley",
        "date": "2026-08-31",
        "temperature_c": 28.4,
    }


def test_cli_happy_valley_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--happy-valley-temp"]) == 0
    assert capsys.readouterr().out == "No Happy Valley temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--happy-valley-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Happy Valley temperature is available."
    }


def test_cli_tai_mei_tuk_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mei-tuk-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_PLC_TEMP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 大美督\n"
        "2026-08-31  26.1°C\n"
    )
    assert main(["--tai-mei-tuk-temp", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong daily mean temperature\n"
        "Station: 大美督\n"
        "2026-08-31  26.1°C\n"
    )


def test_cli_tai_mei_tuk_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.1,C\n"
        ),
    )
    assert main(["--tai-mei-tuk-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mei Tuk",
        "date": "2026-08-31",
        "temperature_c": 26.1,
    }


def test_cli_tai_mei_tuk_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mei-tuk-temp"]) == 0
    assert capsys.readouterr().out == "No Tai Mei Tuk temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mei-tuk-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mei Tuk temperature is available."
    }


def test_cli_max_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "data": [
                    ["2026", "1", "1", "19.1", "C"],
                    ["2026", "8", "30", "***", ""],
                    ["2026", "8", "31", "  29.5  ", "C"],
                ]
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--max-temp", "--lang", "tc"]) == 0
    assert "dataType=CLMMAXT" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "year=2026" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong daily maximum temperature\n2026-08-31  29.5°C\n"


def test_cli_max_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": [["2026", "8", "31", "29.5", "C"]]}),
    )
    assert main(["--max-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"date": "2026-08-31", "temperature_c": 29.5}


def test_cli_max_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": [["2026", "8", "31", "***", ""]]}),
    )
    assert main(["--max-temp"]) == 0
    assert capsys.readouterr().out == "No daily maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": []}),
    )
    assert main(["--max-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No daily maximum temperature is available."
    }


def test_cli_min_temp_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "data": [
                    ["2026", "1", "1", "16.2", "C"],
                    ["2026", "8", "30", "***", ""],
                    ["2026", "8", "31", "  26.2  ", "C"],
                ]
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--min-temp", "--lang", "tc"]) == 0
    assert "dataType=CLMMINT" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "year=2026" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong daily minimum temperature\n2026-08-31  26.2°C\n"


def test_cli_min_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": [["2026", "8", "31", "26.2", "C"]]}),
    )
    assert main(["--min-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"date": "2026-08-31", "temperature_c": 26.2}


def test_cli_min_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": [["2026", "8", "31", "***", ""]]}),
    )
    assert main(["--min-temp"]) == 0
    assert capsys.readouterr().out == "No daily minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": []}),
    )
    assert main(["--min-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No daily minimum temperature is available."
    }


def test_cli_tai_mo_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,20.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  19.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMS_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 大帽山\n"
        "2026-08-31  19.5°C\n"
    )


def test_cli_tai_mo_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,19.5,C\n"
        ),
    )
    assert main(["--tai-mo-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo Shan",
        "date": "2026-08-31",
        "temperature_c": 19.5,
    }


def test_cli_tai_mo_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-min"]) == 0
    assert capsys.readouterr().out == "No Tai Mo Shan minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo Shan minimum temperature is available."
    }


def test_cli_tate_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,23.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  22.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tate-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TC_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 大老山\n"
        "2026-08-31  22.1°C\n"
    )


def test_cli_tate_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,22.1,C\n"
        ),
    )
    assert main(["--tate-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tate's Cairn",
        "date": "2026-08-31",
        "temperature_c": 22.1,
    }


def test_cli_tate_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tate-min"]) == 0
    assert capsys.readouterr().out == "No Tate's Cairn minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tate-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tate's Cairn minimum temperature is available."
    }


def test_cli_sai_kung_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sai-kung-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKG_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 西貢\n"
        "2026-08-31  26.9°C\n"
    )


def test_cli_sai_kung_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.9,C\n"
        ),
    )
    assert main(["--sai-kung-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sai Kung",
        "date": "2026-08-31",
        "temperature_c": 26.9,
    }


def test_cli_sai_kung_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sai-kung-min"]) == 0
    assert capsys.readouterr().out == "No Sai Kung minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sai-kung-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sai Kung minimum temperature is available."
    }


def test_cli_wong_chuk_hang_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wong-chuk-hang-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKS_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 黃竹坑\n"
        "2026-08-31  26.6°C\n"
    )


def test_cli_wong_chuk_hang_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.6,C\n"
        ),
    )
    assert main(["--wong-chuk-hang-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wong Chuk Hang",
        "date": "2026-08-31",
        "temperature_c": 26.6,
    }


def test_cli_wong_chuk_hang_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wong-chuk-hang-min"]) == 0
    assert capsys.readouterr().out == "No Wong Chuk Hang minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wong-chuk-hang-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wong Chuk Hang minimum temperature is available."
    }


def test_cli_waglan_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--waglan-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WGL_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 橫瀾島\n"
        "2026-08-31  26°C\n"
    )


def test_cli_waglan_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.0,C\n"
        ),
    )
    assert main(["--waglan-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Waglan Island",
        "date": "2026-08-31",
        "temperature_c": 26.0,
    }


def test_cli_waglan_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--waglan-min"]) == 0
    assert capsys.readouterr().out == "No Waglan Island minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--waglan-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Waglan Island minimum temperature is available."
    }


def test_cli_sha_tin_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-tin-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SHA_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 沙田\n"
        "2026-08-31  26.1°C\n"
    )


def test_cli_sha_tin_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.1,C\n"
        ),
    )
    assert main(["--sha-tin-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Tin",
        "date": "2026-08-31",
        "temperature_c": 26.1,
    }


def test_cli_sha_tin_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-tin-min"]) == 0
    assert capsys.readouterr().out == "No Sha Tin minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-tin-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Tin minimum temperature is available."
    }


def test_cli_cheung_chau_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cheung-chau-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CCH_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 長洲\n"
        "2026-08-31  25.9°C\n"
    )


def test_cli_cheung_chau_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.9,C\n"
        ),
    )
    assert main(["--cheung-chau-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Cheung Chau",
        "date": "2026-08-31",
        "temperature_c": 25.9,
    }


def test_cli_cheung_chau_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cheung-chau-min"]) == 0
    assert capsys.readouterr().out == "No Cheung Chau minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cheung-chau-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Cheung Chau minimum temperature is available."
    }


def test_cli_park_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.9,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--park-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 京士柏\n"
        "2026-08-31  25.7°C\n"
    )


def test_cli_park_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.7,C\n"
        ),
    )
    assert main(["--park-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "temperature_c": 25.7,
    }


def test_cli_park_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--park-min"]) == 0
    assert capsys.readouterr().out == "No King's Park minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--park-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park minimum temperature is available."
    }


def test_cli_lau_fau_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lau-fau-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_LFS_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 流浮山\n"
        "2026-08-31  25.2°C\n"
    )


def test_cli_lau_fau_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.2,C\n"
        ),
    )
    assert main(["--lau-fau-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Lau Fau Shan",
        "date": "2026-08-31",
        "temperature_c": 25.2,
    }


def test_cli_lau_fau_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--lau-fau-min"]) == 0
    assert capsys.readouterr().out == "No Lau Fau Shan minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--lau-fau-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Lau Fau Shan minimum temperature is available."
    }


def test_cli_sheung_shui_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.6,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sheung-shui-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSH_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 上水\n"
        "2026-08-31  25.4°C\n"
    )


def test_cli_sheung_shui_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.4,C\n"
        ),
    )
    assert main(["--sheung-shui-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sheung Shui",
        "date": "2026-08-31",
        "temperature_c": 25.4,
    }


def test_cli_sheung_shui_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sheung-shui-min"]) == 0
    assert capsys.readouterr().out == "No Sheung Shui minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sheung-shui-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sheung Shui minimum temperature is available."
    }


def test_cli_tseung_kwan_o_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tseung-kwan-o-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_JKB_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 將軍澳\n"
        "2026-08-31  25.1°C\n"
    )


def test_cli_tseung_kwan_o_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.1,C\n"
        ),
    )
    assert main(["--tseung-kwan-o-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tseung Kwan O",
        "date": "2026-08-31",
        "temperature_c": 25.1,
    }


def test_cli_tseung_kwan_o_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tseung-kwan-o-min"]) == 0
    assert capsys.readouterr().out == "No Tseung Kwan O minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tseung-kwan-o-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tseung Kwan O minimum temperature is available."
    }


def test_cli_sham_shui_po_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sham-shui-po-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSP_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 深水埗\n"
        "2026-08-31  25.7°C\n"
    )


def test_cli_sham_shui_po_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.7,C\n"
        ),
    )
    assert main(["--sham-shui-po-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sham Shui Po",
        "date": "2026-08-31",
        "temperature_c": 25.7,
    }


def test_cli_sham_shui_po_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sham-shui-po-min"]) == 0
    assert capsys.readouterr().out == "No Sham Shui Po minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sham-shui-po-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sham Shui Po minimum temperature is available."
    }


def test_cli_shek_kong_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.3,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shek-kong-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SEK_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 石崗\n"
        "2026-08-31  25.2°C\n"
    )


def test_cli_shek_kong_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.2,C\n"
        ),
    )
    assert main(["--shek-kong-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shek Kong",
        "date": "2026-08-31",
        "temperature_c": 25.2,
    }


def test_cli_shek_kong_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shek-kong-min"]) == 0
    assert capsys.readouterr().out == "No Shek Kong minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shek-kong-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shek Kong minimum temperature is available."
    }


def test_cli_wetland_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wetland-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WLP_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 濕地公園\n"
        "2026-08-31  25.2°C\n"
    )


def test_cli_wetland_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.2,C\n"
        ),
    )
    assert main(["--wetland-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wetland Park",
        "date": "2026-08-31",
        "temperature_c": 25.2,
    }


def test_cli_wetland_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wetland-min"]) == 0
    assert capsys.readouterr().out == "No Wetland Park minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wetland-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wetland Park minimum temperature is available."
    }


def test_cli_ta_kwu_ling_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ta-kwu-ling-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TKL_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 打鼓嶺\n"
        "2026-08-31  25.1°C\n"
    )


def test_cli_ta_kwu_ling_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.1,C\n"
        ),
    )
    assert main(["--ta-kwu-ling-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ta Kwu Ling",
        "date": "2026-08-31",
        "temperature_c": 25.1,
    }


def test_cli_ta_kwu_ling_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ta-kwu-ling-min"]) == 0
    assert capsys.readouterr().out == "No Ta Kwu Ling minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ta-kwu-ling-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ta Kwu Ling minimum temperature is available."
    }


def test_cli_sha_lo_wan_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-lo-wan-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SLW_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 沙螺灣\n"
        "2026-08-31  25.4°C\n"
    )


def test_cli_sha_lo_wan_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.4,C\n"
        ),
    )
    assert main(["--sha-lo-wan-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Lo Wan",
        "date": "2026-08-31",
        "temperature_c": 25.4,
    }


def test_cli_sha_lo_wan_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-lo-wan-min"]) == 0
    assert capsys.readouterr().out == "No Sha Lo Wan minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-lo-wan-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Lo Wan minimum temperature is available."
    }


def test_cli_airport_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,7,29,25.6,C\n"
            "2026,7,30,***,\n"
            "2026,7,31,  24.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--airport-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 香港國際機場\n"
        "2026-07-31  24.2°C\n"
    )


def test_cli_airport_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,24.2,C\n"
        ),
    )
    assert main(["--airport-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-07-31",
        "temperature_c": 24.2,
    }


def test_cli_airport_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,***,\n"
        ),
    )
    assert main(["--airport-min"]) == 0
    assert capsys.readouterr().out == "No airport minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--airport-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No airport minimum temperature is available."
    }


def test_cli_yuen_long_park_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--yuen-long-park-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_YLP_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 元朗公園\n"
        "2026-08-31  25.6°C\n"
    )


def test_cli_yuen_long_park_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.6,C\n"
        ),
    )
    assert main(["--yuen-long-park-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Yuen Long Park",
        "date": "2026-08-31",
        "temperature_c": 25.6,
    }


def test_cli_yuen_long_park_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--yuen-long-park-min"]) == 0
    assert capsys.readouterr().out == (
        "No Yuen Long Park minimum temperature is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--yuen-long-park-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Yuen Long Park minimum temperature is available."
    }


def test_cli_clear_water_bay_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--clear-water-bay-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CWB_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 清水灣\n"
        "2026-08-31  25.9°C\n"
    )


def test_cli_clear_water_bay_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.9,C\n"
        ),
    )
    assert main(["--clear-water-bay-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Clear Water Bay",
        "date": "2026-08-31",
        "temperature_c": 25.9,
    }


def test_cli_clear_water_bay_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--clear-water-bay-min"]) == 0
    assert capsys.readouterr().out == (
        "No Clear Water Bay minimum temperature is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--clear-water-bay-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Clear Water Bay minimum temperature is available."
    }


def test_cli_tap_mun_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tap-mun-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TAP_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 塔門\n"
        "2026-08-31  25.8°C\n"
    )


def test_cli_tap_mun_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.8,C\n"
        ),
    )
    assert main(["--tap-mun-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tap Mun",
        "date": "2026-08-31",
        "temperature_c": 25.8,
    }


def test_cli_tap_mun_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tap-mun-min"]) == 0
    assert capsys.readouterr().out == "No Tap Mun minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tap-mun-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tap Mun minimum temperature is available."
    }


def test_cli_hong_kong_park_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--hong-kong-park-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKP_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 香港公園\n"
        "2026-08-31  25.8°C\n"
    )


def test_cli_hong_kong_park_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.8,C\n"
        ),
    )
    assert main(["--hong-kong-park-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Park",
        "date": "2026-08-31",
        "temperature_c": 25.8,
    }


def test_cli_hong_kong_park_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--hong-kong-park-min"]) == 0
    assert capsys.readouterr().out == (
        "No Hong Kong Park minimum temperature is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--hong-kong-park-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Hong Kong Park minimum temperature is available."
    }


def test_cli_ngong_ping_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,24.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  22.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ngong-ping-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_NGP_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 昂坪\n"
        "2026-08-31  22.4°C\n"
    )


def test_cli_ngong_ping_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,22.4,C\n"
        ),
    )
    assert main(["--ngong-ping-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ngong Ping",
        "date": "2026-08-31",
        "temperature_c": 22.4,
    }


def test_cli_ngong_ping_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ngong-ping-min"]) == 0
    assert capsys.readouterr().out == "No Ngong Ping minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ngong-ping-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ngong Ping minimum temperature is available."
    }


def test_cli_kwun_tong_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--kwun-tong-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KTG_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 觀塘\n"
        "2026-08-31  25°C\n"
    )


def test_cli_kwun_tong_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.0,C\n"
        ),
    )
    assert main(["--kwun-tong-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Kwun Tong",
        "date": "2026-08-31",
        "temperature_c": 25.0,
    }


def test_cli_kwun_tong_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--kwun-tong-min"]) == 0
    assert capsys.readouterr().out == "No Kwun Tong minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--kwun-tong-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Kwun Tong minimum temperature is available."
    }


def test_cli_wong_tai_sin_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wong-tai-sin-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WTS_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 黃大仙\n"
        "2026-08-31  25.5°C\n"
    )


def test_cli_wong_tai_sin_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.5,C\n"
        ),
    )
    assert main(["--wong-tai-sin-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wong Tai Sin",
        "date": "2026-08-31",
        "temperature_c": 25.5,
    }


def test_cli_wong_tai_sin_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wong-tai-sin-min"]) == 0
    assert capsys.readouterr().out == (
        "No Wong Tai Sin minimum temperature is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wong-tai-sin-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wong Tai Sin minimum temperature is available."
    }


def test_cli_tsuen_wan_min_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  24.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tsuen-wan-min", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TWN_MINT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily minimum temperature\n"
        "Station: 荃灣\n"
        "2026-08-31  24.8°C\n"
    )


def test_cli_tsuen_wan_min_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,24.8,C\n"
        ),
    )
    assert main(["--tsuen-wan-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tsuen Wan",
        "date": "2026-08-31",
        "temperature_c": 24.8,
    }


def test_cli_tsuen_wan_min_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tsuen-wan-min"]) == 0
    assert capsys.readouterr().out == "No Tsuen Wan minimum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tsuen-wan-min", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tsuen Wan minimum temperature is available."
    }


def test_cli_tai_mo_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  24.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMS_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 大帽山\n"
        "2026-08-31  24.1°C\n"
    )


def test_cli_tai_mo_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,24.1,C\n"
        ),
    )
    assert main(["--tai-mo-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo Shan",
        "date": "2026-08-31",
        "temperature_c": 24.1,
    }


def test_cli_tai_mo_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-max"]) == 0
    assert capsys.readouterr().out == "No Tai Mo Shan maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo Shan maximum temperature is available."
    }


def test_cli_tseung_kwan_o_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,30.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  31.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tseung-kwan-o-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_JKB_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 將軍澳\n"
        "2026-08-31  31.2°C\n"
    )


def test_cli_tseung_kwan_o_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,31.2,C\n"
        ),
    )
    assert main(["--tseung-kwan-o-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tseung Kwan O",
        "date": "2026-08-31",
        "temperature_c": 31.2,
    }


def test_cli_tseung_kwan_o_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tseung-kwan-o-max"]) == 0
    assert capsys.readouterr().out == "No Tseung Kwan O maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tseung-kwan-o-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tseung Kwan O maximum temperature is available."
    }


def test_cli_sheung_shui_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,35.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  30.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sheung-shui-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSH_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 上水\n"
        "2026-08-31  30.9°C\n"
    )


def test_cli_sheung_shui_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,30.9,C\n"
        ),
    )
    assert main(["--sheung-shui-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sheung Shui",
        "date": "2026-08-31",
        "temperature_c": 30.9,
    }


def test_cli_sheung_shui_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sheung-shui-max"]) == 0
    assert capsys.readouterr().out == "No Sheung Shui maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sheung-shui-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sheung Shui maximum temperature is available."
    }


def test_cli_waglan_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,32.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  31.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--waglan-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WGL_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 橫瀾島\n"
        "2026-08-31  31.7°C\n"
    )


def test_cli_waglan_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,31.7,C\n"
        ),
    )
    assert main(["--waglan-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Waglan Island",
        "date": "2026-08-31",
        "temperature_c": 31.7,
    }


def test_cli_waglan_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--waglan-max"]) == 0
    assert capsys.readouterr().out == "No Waglan Island maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--waglan-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Waglan Island maximum temperature is available."
    }


def test_cli_shek_kong_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,34.3,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  30.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shek-kong-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SEK_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 石崗\n"
        "2026-08-31  30.5°C\n"
    )


def test_cli_shek_kong_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,30.5,C\n"
        ),
    )
    assert main(["--shek-kong-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shek Kong",
        "date": "2026-08-31",
        "temperature_c": 30.5,
    }


def test_cli_shek_kong_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shek-kong-max"]) == 0
    assert capsys.readouterr().out == "No Shek Kong maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shek-kong-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shek Kong maximum temperature is available."
    }


def test_cli_cheung_chau_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,30.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  30.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cheung-chau-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CCH_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 長洲\n"
        "2026-08-31  30.7°C\n"
    )


def test_cli_cheung_chau_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,30.7,C\n"
        ),
    )
    assert main(["--cheung-chau-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Cheung Chau",
        "date": "2026-08-31",
        "temperature_c": 30.7,
    }


def test_cli_cheung_chau_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cheung-chau-max"]) == 0
    assert capsys.readouterr().out == "No Cheung Chau maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cheung-chau-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Cheung Chau maximum temperature is available."
    }


def test_cli_park_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,32.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  30.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--park-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 京士柏\n"
        "2026-08-31  30.4°C\n"
    )


def test_cli_park_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,30.4,C\n"
        ),
    )
    assert main(["--park-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "temperature_c": 30.4,
    }


def test_cli_park_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--park-max"]) == 0
    assert capsys.readouterr().out == "No King's Park maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--park-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park maximum temperature is available."
    }


def test_cli_lau_fau_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,33.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  29.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lau-fau-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_LFS_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 流浮山\n"
        "2026-08-31  29.4°C\n"
    )


def test_cli_lau_fau_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,29.4,C\n"
        ),
    )
    assert main(["--lau-fau-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Lau Fau Shan",
        "date": "2026-08-31",
        "temperature_c": 29.4,
    }


def test_cli_lau_fau_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--lau-fau-max"]) == 0
    assert capsys.readouterr().out == "No Lau Fau Shan maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--lau-fau-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Lau Fau Shan maximum temperature is available."
    }


def test_cli_sai_kung_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,34.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  29.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sai-kung-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKG_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 西貢\n"
        "2026-08-31  29.9°C\n"
    )


def test_cli_sai_kung_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,29.9,C\n"
        ),
    )
    assert main(["--sai-kung-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sai Kung",
        "date": "2026-08-31",
        "temperature_c": 29.9,
    }


def test_cli_sai_kung_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sai-kung-max"]) == 0
    assert capsys.readouterr().out == "No Sai Kung maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sai-kung-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sai Kung maximum temperature is available."
    }


def test_cli_sha_tin_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,31.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  30.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-tin-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SHA_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 沙田\n"
        "2026-08-31  30.4°C\n"
    )


def test_cli_sha_tin_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,30.4,C\n"
        ),
    )
    assert main(["--sha-tin-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Tin",
        "date": "2026-08-31",
        "temperature_c": 30.4,
    }


def test_cli_sha_tin_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-tin-max"]) == 0
    assert capsys.readouterr().out == "No Sha Tin maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-tin-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Tin maximum temperature is available."
    }


def test_cli_tate_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,31.6,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  29.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tate-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TC_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 大老山\n"
        "2026-08-31  29.4°C\n"
    )


def test_cli_tate_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,29.4,C\n"
        ),
    )
    assert main(["--tate-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tate's Cairn",
        "date": "2026-08-31",
        "temperature_c": 29.4,
    }


def test_cli_tate_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tate-max"]) == 0
    assert capsys.readouterr().out == "No Tate's Cairn maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tate-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tate's Cairn maximum temperature is available."
    }


def test_cli_wong_chuk_hang_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,31.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  29.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wong-chuk-hang-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKS_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 黃竹坑\n"
        "2026-08-31  29.9°C\n"
    )


def test_cli_wong_chuk_hang_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,29.9,C\n"
        ),
    )
    assert main(["--wong-chuk-hang-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wong Chuk Hang",
        "date": "2026-08-31",
        "temperature_c": 29.9,
    }


def test_cli_wong_chuk_hang_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wong-chuk-hang-max"]) == 0
    assert capsys.readouterr().out == "No Wong Chuk Hang maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wong-chuk-hang-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wong Chuk Hang maximum temperature is available."
    }


def test_cli_sham_shui_po_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,33.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  31.3  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sham-shui-po-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSP_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 深水埗\n"
        "2026-08-31  31.3°C\n"
    )


def test_cli_sham_shui_po_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,31.3,C\n"
        ),
    )
    assert main(["--sham-shui-po-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sham Shui Po",
        "date": "2026-08-31",
        "temperature_c": 31.3,
    }


def test_cli_sham_shui_po_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sham-shui-po-max"]) == 0
    assert capsys.readouterr().out == "No Sham Shui Po maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sham-shui-po-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sham Shui Po maximum temperature is available."
    }


def test_cli_wetland_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,34.3,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  29.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wetland-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WLP_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 濕地公園\n"
        "2026-08-31  29.9°C\n"
    )


def test_cli_wetland_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,29.9,C\n"
        ),
    )
    assert main(["--wetland-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wetland Park",
        "date": "2026-08-31",
        "temperature_c": 29.9,
    }


def test_cli_wetland_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wetland-max"]) == 0
    assert capsys.readouterr().out == "No Wetland Park maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wetland-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wetland Park maximum temperature is available."
    }


def test_cli_ta_kwu_ling_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,35.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  30.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ta-kwu-ling-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TKL_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 打鼓嶺\n"
        "2026-08-31  30.2°C\n"
    )


def test_cli_ta_kwu_ling_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,30.2,C\n"
        ),
    )
    assert main(["--ta-kwu-ling-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ta Kwu Ling",
        "date": "2026-08-31",
        "temperature_c": 30.2,
    }


def test_cli_ta_kwu_ling_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ta-kwu-ling-max"]) == 0
    assert capsys.readouterr().out == "No Ta Kwu Ling maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ta-kwu-ling-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ta Kwu Ling maximum temperature is available."
    }


def test_cli_sha_lo_wan_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,31.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  29.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-lo-wan-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SLW_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 沙螺灣\n"
        "2026-08-31  29.1°C\n"
    )


def test_cli_sha_lo_wan_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,29.1,C\n"
        ),
    )
    assert main(["--sha-lo-wan-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Lo Wan",
        "date": "2026-08-31",
        "temperature_c": 29.1,
    }


def test_cli_sha_lo_wan_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-lo-wan-max"]) == 0
    assert capsys.readouterr().out == "No Sha Lo Wan maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-lo-wan-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Lo Wan maximum temperature is available."
    }


def test_cli_airport_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,7,29,28.3,C\n"
            "2026,7,30,***,\n"
            "2026,7,31,  28.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--airport-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 香港國際機場\n"
        "2026-07-31  28.2°C\n"
    )


def test_cli_airport_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,28.2,C\n"
        ),
    )
    assert main(["--airport-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-07-31",
        "temperature_c": 28.2,
    }


def test_cli_airport_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,***,\n"
        ),
    )
    assert main(["--airport-max"]) == 0
    assert capsys.readouterr().out == "No airport maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--airport-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No airport maximum temperature is available."
    }


def test_cli_yuen_long_park_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,35.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  31.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--yuen-long-park-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_YLP_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 元朗公園\n"
        "2026-08-31  31.4°C\n"
    )


def test_cli_yuen_long_park_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,31.4,C\n"
        ),
    )
    assert main(["--yuen-long-park-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Yuen Long Park",
        "date": "2026-08-31",
        "temperature_c": 31.4,
    }


def test_cli_yuen_long_park_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--yuen-long-park-max"]) == 0
    assert capsys.readouterr().out == "No Yuen Long Park maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--yuen-long-park-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Yuen Long Park maximum temperature is available."
    }


def test_cli_clear_water_bay_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,32.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  31.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--clear-water-bay-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CWB_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 清水灣\n"
        "2026-08-31  31.1°C\n"
    )


def test_cli_clear_water_bay_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,31.1,C\n"
        ),
    )
    assert main(["--clear-water-bay-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Clear Water Bay",
        "date": "2026-08-31",
        "temperature_c": 31.1,
    }


def test_cli_clear_water_bay_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--clear-water-bay-max"]) == 0
    assert capsys.readouterr().out == (
        "No Clear Water Bay maximum temperature is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--clear-water-bay-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Clear Water Bay maximum temperature is available."
    }


def test_cli_tap_mun_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,33.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  29.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tap-mun-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TAP_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 塔門\n"
        "2026-08-31  29.4°C\n"
    )


def test_cli_tap_mun_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,29.4,C\n"
        ),
    )
    assert main(["--tap-mun-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tap Mun",
        "date": "2026-08-31",
        "temperature_c": 29.4,
    }


def test_cli_tap_mun_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tap-mun-max"]) == 0
    assert capsys.readouterr().out == "No Tap Mun maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tap-mun-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tap Mun maximum temperature is available."
    }


def test_cli_hong_kong_park_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,32.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  29.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--hong-kong-park-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKP_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 香港公園\n"
        "2026-08-31  29.5°C\n"
    )


def test_cli_hong_kong_park_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,29.5,C\n"
        ),
    )
    assert main(["--hong-kong-park-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Park",
        "date": "2026-08-31",
        "temperature_c": 29.5,
    }


def test_cli_hong_kong_park_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--hong-kong-park-max"]) == 0
    assert capsys.readouterr().out == (
        "No Hong Kong Park maximum temperature is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--hong-kong-park-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Hong Kong Park maximum temperature is available."
    }


def test_cli_ngong_ping_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.6,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  27.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ngong-ping-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_NGP_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 昂坪\n"
        "2026-08-31  27.1°C\n"
    )


def test_cli_ngong_ping_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,27.1,C\n"
        ),
    )
    assert main(["--ngong-ping-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ngong Ping",
        "date": "2026-08-31",
        "temperature_c": 27.1,
    }


def test_cli_ngong_ping_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ngong-ping-max"]) == 0
    assert capsys.readouterr().out == "No Ngong Ping maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ngong-ping-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ngong Ping maximum temperature is available."
    }


def test_cli_kwun_tong_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,34.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  31.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--kwun-tong-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KTG_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 觀塘\n"
        "2026-08-31  31°C\n"
    )


def test_cli_kwun_tong_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,31.0,C\n"
        ),
    )
    assert main(["--kwun-tong-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Kwun Tong",
        "date": "2026-08-31",
        "temperature_c": 31.0,
    }


def test_cli_kwun_tong_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--kwun-tong-max"]) == 0
    assert capsys.readouterr().out == "No Kwun Tong maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--kwun-tong-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Kwun Tong maximum temperature is available."
    }


def test_cli_wong_tai_sin_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,34.9,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  32.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wong-tai-sin-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WTS_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 黃大仙\n"
        "2026-08-31  32.4°C\n"
    )


def test_cli_wong_tai_sin_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,32.4,C\n"
        ),
    )
    assert main(["--wong-tai-sin-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wong Tai Sin",
        "date": "2026-08-31",
        "temperature_c": 32.4,
    }


def test_cli_wong_tai_sin_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wong-tai-sin-max"]) == 0
    assert capsys.readouterr().out == (
        "No Wong Tai Sin maximum temperature is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wong-tai-sin-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wong Tai Sin maximum temperature is available."
    }


def test_cli_tsuen_wan_max_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,31.9,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  28.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tsuen-wan-max", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TWN_MAXT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum temperature\n"
        "Station: 荃灣\n"
        "2026-08-31  28.8°C\n"
    )


def test_cli_tsuen_wan_max_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,28.8,C\n"
        ),
    )
    assert main(["--tsuen-wan-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tsuen Wan",
        "date": "2026-08-31",
        "temperature_c": 28.8,
    }


def test_cli_tsuen_wan_max_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tsuen-wan-max"]) == 0
    assert capsys.readouterr().out == "No Tsuen Wan maximum temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tsuen-wan-max", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tsuen Wan maximum temperature is available."
    }


def test_cli_dew_point_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,1,1,12.9,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,25.0,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--dew-point", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKO_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 香港天文台\n"
        "2026-08-31  25°C\n"
    )


def test_cli_dew_point_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.0,C\n"
        ),
    )
    assert main(["--dew-point", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Observatory",
        "date": "2026-08-31",
        "dew_point_c": 25.0,
    }


def test_cli_dew_point_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--dew-point"]) == 0
    assert capsys.readouterr().out == "No dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--dew-point", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No dew point is available."}


def test_cli_park_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,25.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  24.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--park-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 京士柏\n"
        "2026-08-31  24.7°C\n"
    )


def test_cli_park_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,24.7,C\n"
        ),
    )
    assert main(["--park-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "dew_point_c": 24.7,
    }


def test_cli_park_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--park-dew"]) == 0
    assert capsys.readouterr().out == "No King's Park dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--park-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park dew point is available."
    }


def test_cli_cheung_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cheung-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CCH_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 長洲\n"
        "2026-08-31  25.6°C\n"
    )


def test_cli_cheung_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.6,C\n"
        ),
    )
    assert main(["--cheung-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Cheung Chau",
        "date": "2026-08-31",
        "dew_point_c": 25.6,
    }


def test_cli_cheung_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cheung-dew"]) == 0
    assert capsys.readouterr().out == "No Cheung Chau dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cheung-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Cheung Chau dew point is available."
    }


def test_cli_wong_chuk_hang_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wong-chuk-hang-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKS_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 黃竹坑\n"
        "2026-08-31  25.9°C\n"
    )


def test_cli_wong_chuk_hang_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.9,C\n"
        ),
    )
    assert main(["--wong-chuk-hang-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wong Chuk Hang",
        "date": "2026-08-31",
        "dew_point_c": 25.9,
    }


def test_cli_wong_chuk_hang_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wong-chuk-hang-dew"]) == 0
    assert capsys.readouterr().out == "No Wong Chuk Hang dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wong-chuk-hang-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wong Chuk Hang dew point is available."
    }


def test_cli_sai_kung_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sai-kung-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKG_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 西貢\n"
        "2026-08-31  25.2°C\n"
    )


def test_cli_sai_kung_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.2,C\n"
        ),
    )
    assert main(["--sai-kung-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sai Kung",
        "date": "2026-08-31",
        "dew_point_c": 25.2,
    }


def test_cli_sai_kung_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sai-kung-dew"]) == 0
    assert capsys.readouterr().out == "No Sai Kung dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sai-kung-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sai Kung dew point is available."
    }


def test_cli_sha_tin_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-tin-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SHA_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 沙田\n"
        "2026-08-31  25.4°C\n"
    )


def test_cli_sha_tin_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.4,C\n"
        ),
    )
    assert main(["--sha-tin-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Tin",
        "date": "2026-08-31",
        "dew_point_c": 25.4,
    }


def test_cli_sha_tin_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-tin-dew"]) == 0
    assert capsys.readouterr().out == "No Sha Tin dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-tin-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Tin dew point is available."
    }


def test_cli_sheung_shui_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  24.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sheung-shui-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSH_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 上水\n"
        "2026-08-31  24.8°C\n"
    )


def test_cli_sheung_shui_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,24.8,C\n"
        ),
    )
    assert main(["--sheung-shui-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sheung Shui",
        "date": "2026-08-31",
        "dew_point_c": 24.8,
    }


def test_cli_sheung_shui_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sheung-shui-dew"]) == 0
    assert capsys.readouterr().out == "No Sheung Shui dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sheung-shui-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sheung Shui dew point is available."
    }


def test_cli_waglan_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--waglan-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WGL_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 橫瀾島\n"
        "2026-08-31  26°C\n"
    )


def test_cli_waglan_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.0,C\n"
        ),
    )
    assert main(["--waglan-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Waglan Island",
        "date": "2026-08-31",
        "dew_point_c": 26.0,
    }


def test_cli_waglan_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--waglan-dew"]) == 0
    assert capsys.readouterr().out == "No Waglan Island dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--waglan-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Waglan Island dew point is available."
    }


def test_cli_lau_fau_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lau-fau-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_LFS_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 流浮山\n"
        "2026-08-31  25.7°C\n"
    )


def test_cli_lau_fau_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.7,C\n"
        ),
    )
    assert main(["--lau-fau-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Lau Fau Shan",
        "date": "2026-08-31",
        "dew_point_c": 25.7,
    }


def test_cli_lau_fau_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--lau-fau-dew"]) == 0
    assert capsys.readouterr().out == "No Lau Fau Shan dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--lau-fau-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Lau Fau Shan dew point is available."
    }


def test_cli_wetland_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wetland-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WLP_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 濕地公園\n"
        "2026-08-31  25.9°C\n"
    )


def test_cli_wetland_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.9,C\n"
        ),
    )
    assert main(["--wetland-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wetland Park",
        "date": "2026-08-31",
        "dew_point_c": 25.9,
    }


def test_cli_wetland_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wetland-dew"]) == 0
    assert capsys.readouterr().out == "No Wetland Park dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wetland-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wetland Park dew point is available."
    }


def test_cli_ta_kwu_ling_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ta-kwu-ling-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TKL_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 打鼓嶺\n"
        "2026-08-31  25.7°C\n"
    )


def test_cli_ta_kwu_ling_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.7,C\n"
        ),
    )
    assert main(["--ta-kwu-ling-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ta Kwu Ling",
        "date": "2026-08-31",
        "dew_point_c": 25.7,
    }


def test_cli_ta_kwu_ling_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ta-kwu-ling-dew"]) == 0
    assert capsys.readouterr().out == "No Ta Kwu Ling dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ta-kwu-ling-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ta Kwu Ling dew point is available."
    }


def test_cli_shek_kong_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shek-kong-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SEK_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 石崗\n"
        "2026-08-31  25.8°C\n"
    )


def test_cli_shek_kong_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.8,C\n"
        ),
    )
    assert main(["--shek-kong-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shek Kong",
        "date": "2026-08-31",
        "dew_point_c": 25.8,
    }


def test_cli_shek_kong_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shek-kong-dew"]) == 0
    assert capsys.readouterr().out == "No Shek Kong dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shek-kong-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shek Kong dew point is available."
    }


def test_cli_tseung_kwan_o_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tseung-kwan-o-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_JKB_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 將軍澳\n"
        "2026-08-31  25.6°C\n"
    )


def test_cli_tseung_kwan_o_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.6,C\n"
        ),
    )
    assert main(["--tseung-kwan-o-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tseung Kwan O",
        "date": "2026-08-31",
        "dew_point_c": 25.6,
    }


def test_cli_tseung_kwan_o_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tseung-kwan-o-dew"]) == 0
    assert capsys.readouterr().out == "No Tseung Kwan O dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tseung-kwan-o-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tseung Kwan O dew point is available."
    }


def test_cli_tai_mo_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,22.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  21.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMS_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 大帽山\n"
        "2026-08-31  21.1°C\n"
    )


def test_cli_tai_mo_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,21.1,C\n"
        ),
    )
    assert main(["--tai-mo-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo Shan",
        "date": "2026-08-31",
        "dew_point_c": 21.1,
    }


def test_cli_tai_mo_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-dew"]) == 0
    assert capsys.readouterr().out == "No Tai Mo Shan dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo Shan dew point is available."
    }


def test_cli_peng_chau_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  24.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--peng-chau-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_PEN_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 坪洲\n"
        "2026-08-31  24.7°C\n"
    )


def test_cli_peng_chau_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,24.7,C\n"
        ),
    )
    assert main(["--peng-chau-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Peng Chau",
        "date": "2026-08-31",
        "dew_point_c": 24.7,
    }


def test_cli_peng_chau_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--peng-chau-dew"]) == 0
    assert capsys.readouterr().out == "No Peng Chau dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--peng-chau-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Peng Chau dew point is available."
    }


def test_cli_sha_lo_wan_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-lo-wan-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SLW_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 沙螺灣\n"
        "2026-08-31  25.6°C\n"
    )


def test_cli_sha_lo_wan_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.6,C\n"
        ),
    )
    assert main(["--sha-lo-wan-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Lo Wan",
        "date": "2026-08-31",
        "dew_point_c": 25.6,
    }


def test_cli_sha_lo_wan_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-lo-wan-dew"]) == 0
    assert capsys.readouterr().out == "No Sha Lo Wan dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-lo-wan-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Lo Wan dew point is available."
    }


def test_cli_airport_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,7,29,24.1,C\n"
            "2026,7,30,***,\n"
            "2026,7,31,  23.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--airport-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 香港國際機場\n"
        "2026-07-31  23.7°C\n"
    )


def test_cli_airport_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,23.7,C\n"
        ),
    )
    assert main(["--airport-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-07-31",
        "dew_point_c": 23.7,
    }


def test_cli_airport_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,***,\n"
        ),
    )
    assert main(["--airport-dew"]) == 0
    assert capsys.readouterr().out == "No airport dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--airport-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No airport dew point is available."
    }


def test_cli_clear_water_bay_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.3,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--clear-water-bay-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CWB_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 清水灣\n"
        "2026-08-31  25°C\n"
    )
    assert main(["--clear-water-bay-dew", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 清水湾\n"
        "2026-08-31  25°C\n"
    )


def test_cli_clear_water_bay_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.0,C\n"
        ),
    )
    assert main(["--clear-water-bay-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Clear Water Bay",
        "date": "2026-08-31",
        "dew_point_c": 25.0,
    }


def test_cli_clear_water_bay_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--clear-water-bay-dew"]) == 0
    assert capsys.readouterr().out == "No Clear Water Bay dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--clear-water-bay-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Clear Water Bay dew point is available."
    }


def test_cli_hong_kong_park_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--hong-kong-park-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKP_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 香港公園\n"
        "2026-08-31  25.1°C\n"
    )
    assert main(["--hong-kong-park-dew", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 香港公园\n"
        "2026-08-31  25.1°C\n"
    )


def test_cli_hong_kong_park_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.1,C\n"
        ),
    )
    assert main(["--hong-kong-park-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Park",
        "date": "2026-08-31",
        "dew_point_c": 25.1,
    }


def test_cli_hong_kong_park_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--hong-kong-park-dew"]) == 0
    assert capsys.readouterr().out == "No Hong Kong Park dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--hong-kong-park-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Hong Kong Park dew point is available."
    }


def test_cli_tsuen_wan_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.3,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  24.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tsuen-wan-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TWN_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 荃灣\n"
        "2026-08-31  24.8°C\n"
    )
    assert main(["--tsuen-wan-dew", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 荃湾\n"
        "2026-08-31  24.8°C\n"
    )


def test_cli_tsuen_wan_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,24.8,C\n"
        ),
    )
    assert main(["--tsuen-wan-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tsuen Wan",
        "date": "2026-08-31",
        "dew_point_c": 24.8,
    }


def test_cli_tsuen_wan_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tsuen-wan-dew"]) == 0
    assert capsys.readouterr().out == "No Tsuen Wan dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tsuen-wan-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tsuen Wan dew point is available."
    }


def test_cli_shau_kei_wan_dew_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,25.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shau-kei-wan-dew", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKW_DEW_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 筲箕灣\n"
        "2026-08-31  25.2°C\n"
    )
    assert main(["--shau-kei-wan-dew", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong dew point\n"
        "Station: 筲箕湾\n"
        "2026-08-31  25.2°C\n"
    )


def test_cli_shau_kei_wan_dew_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.2,C\n"
        ),
    )
    assert main(["--shau-kei-wan-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shau Kei Wan",
        "date": "2026-08-31",
        "dew_point_c": 25.2,
    }


def test_cli_shau_kei_wan_dew_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shau-kei-wan-dew"]) == 0
    assert capsys.readouterr().out == "No Shau Kei Wan dew point is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shau-kei-wan-dew", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shau Kei Wan dew point is available."
    }


def test_cli_cloud_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,1,1,43,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  88  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cloud", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKO_CLD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong cloud amount\n"
        "Station: 香港天文台\n"
        "2026-08-31  88%\n"
    )


def test_cli_cloud_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,88,C\n"
        ),
    )
    assert main(["--cloud", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Observatory",
        "date": "2026-08-31",
        "cloud_percent": 88.0,
    }


def test_cli_cloud_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cloud"]) == 0
    assert capsys.readouterr().out == "No cloud amount is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cloud", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No cloud amount is available."}


def test_cli_evaporation_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,1,1,3.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  2.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--evaporation", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_EVAP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong evaporation\n"
        "Station: 京士柏\n"
        "2026-08-31  2.5 mm\n"
    )


def test_cli_evaporation_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,2.5,C\n"
        ),
    )
    assert main(["--evaporation", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "evaporation_mm": 2.5,
    }


def test_cli_evaporation_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--evaporation"]) == 0
    assert capsys.readouterr().out == "No evaporation is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--evaporation", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No evaporation is available."}


def test_cli_evapotranspiration_prints_latest_month(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,4,,40.0,C\n"
            "2026,7,,***,\n"
            "2026,8,,  43.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--evapotranspiration", "--lang", "tc"]) == 0
    assert seen["url"].endswith("monthly_KP_EVAPTRAN_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong potential evapotranspiration\n"
        "Station: 京士柏\n"
        "2026-08  43.6 mm\n"
    )


def test_cli_evapotranspiration_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,,43.6,C\n"
        ),
    )
    assert main(["--evapotranspiration", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "month": "2026-08",
        "evapotranspiration_mm": 43.6,
    }


def test_cli_evapotranspiration_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,,***,\n"
        ),
    )
    assert main(["--evapotranspiration"]) == 0
    assert capsys.readouterr().out == "No potential evapotranspiration is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--evapotranspiration", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No potential evapotranspiration is available."
    }


def test_cli_grass_prints_yesterday_minimum(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "HKOReadingsMinGrassTemp": "26.4",
                "ReportTimeInfoDate": "20261002",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--grass", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong grass minimum\n"
        "2026-10-02\n"
        "26.4°C\n"
    )


def test_cli_grass_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"HKOReadingsMinGrassTemp": "26.4"}),
    )
    assert main(["--grass", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "date": "2026-10-02",
        "grass_min_c": 26.4,
    }


def test_cli_grass_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"HKOReadingsMaxTemp": "31.7"}),
    )
    assert main(["--grass"]) == 0
    assert capsys.readouterr().out == "No grass minimum is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--grass", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No grass minimum is available."}


def test_cli_sunshine_prints_yesterday_hours(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "KingsParkReadingsSunShine": "  4.7  ",
                "ReportTimeInfoDate": "20261002",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sunshine", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=KP" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong sunshine\n"
        "Station: King's Park\n"
        "2026-10-02  4.7 hours\n"
    )


def test_cli_sunshine_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"KingsParkReadingsSunShine": "4.7"}),
    )
    assert main(["--sunshine", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-10-02",
        "hours": 4.7,
    }


def test_cli_sunshine_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"KingsParkReadingsSunShine": "***"}),
    )
    assert main(["--sunshine"]) == 0
    assert capsys.readouterr().out == "No sunshine duration is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--sunshine", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No sunshine duration is available."}


def test_cli_daily_sun_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,1.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  2.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--daily-sun", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_SUN_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily sunshine\n"
        "Station: 京士柏\n"
        "2026-08-31  2.2 hours\n"
    )


def test_cli_daily_sun_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,2.2,C\n"
        ),
    )
    assert main(["--daily-sun", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "hours": 2.2,
    }


def test_cli_daily_sun_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--daily-sun"]) == 0
    assert capsys.readouterr().out == "No daily sunshine is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--daily-sun", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No daily sunshine is available."}


def test_cli_max_uv_prints_yesterday_index(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "KingsParkReadingsMaxUVIndex": "  6  ",
                "ReportTimeInfoDate": "20261002",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--max-uv", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=KP" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong maximum UV index\n"
        "Station: King's Park\n"
        "2026-10-02  6\n"
    )


def test_cli_max_uv_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"KingsParkReadingsMaxUVIndex": "6"}),
    )
    assert main(["--max-uv", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-10-02",
        "uv_index": 6,
    }


def test_cli_max_uv_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"KingsParkReadingsMaxUVIndex": "***"}),
    )
    assert main(["--max-uv"]) == 0
    assert capsys.readouterr().out == "No maximum UV index is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--max-uv", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No maximum UV index is available."}


def test_cli_uv_peak_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,記錄時間/Time recorded,數據完整性/data Completeness\n"
            "2026,8,29,10,13:00-13:15,C\n"
            "2026,8,30,***,*** ,\n"
            "2026,8,31,  5  ,10:00-10:15,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--uv-peak", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_MAXUV_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily maximum UV\n"
        "Station: 京士柏\n"
        "2026-08-31  5  10:00-10:15\n"
    )


def test_cli_uv_peak_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Time,Completeness\n"
            "2026,8,31,5,10:00-10:15,C\n"
        ),
    )
    assert main(["--uv-peak", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "uv_index": 5.0,
        "period": "10:00-10:15",
    }


def test_cli_uv_peak_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Time,Completeness\n"
            "2026,8,31,***,***,\n"
        ),
    )
    assert main(["--uv-peak"]) == 0
    assert capsys.readouterr().out == "No daily maximum UV index is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--uv-peak", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No daily maximum UV index is available."
    }


def test_cli_mean_uv_prints_yesterday_index(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "KingsParkReadingsMeanUVIndex": "  2  ",
                "ReportTimeInfoDate": "20261002",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--mean-uv", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=KP" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong mean UV index\n"
        "Station: King's Park\n"
        "2026-10-02  2\n"
    )


def test_cli_mean_uv_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"KingsParkReadingsMeanUVIndex": "2"}),
    )
    assert main(["--mean-uv", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-10-02",
        "uv_index": 2,
    }


def test_cli_mean_uv_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"KingsParkReadingsMeanUVIndex": "***"}),
    )
    assert main(["--mean-uv"]) == 0
    assert capsys.readouterr().out == "No mean UV index is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--mean-uv", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No mean UV index is available."}


def test_cli_daily_uv_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--daily-uv", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_UV_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean UV index\n"
        "Station: 京士柏\n"
        "2026-08-31  2\n"
    )


def test_cli_daily_uv_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,2,C\n"
        ),
    )
    assert main(["--daily-uv", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "uv_index": 2.0,
    }


def test_cli_daily_uv_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--daily-uv"]) == 0
    assert capsys.readouterr().out == "No King's Park daily mean UV index is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--daily-uv", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park daily mean UV index is available."
    }


def test_cli_dose_prints_yesterday_rate(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "KingsParkMicrosieverts": "  0.15  ",
                "ReportTimeInfoDate": "20261002",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--dose", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=KP" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong gamma dose rate\n"
        "Station: King's Park\n"
        "2026-10-02  0.15 µSv/h\n"
    )


def test_cli_dose_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"KingsParkMicrosieverts": "0.15"}),
    )
    assert main(["--dose", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-10-02",
        "dose_usv_h": 0.15,
    }


def test_cli_dose_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"KingsParkMicrosieverts": "***"}),
    )
    assert main(["--dose"]) == 0
    assert capsys.readouterr().out == "No gamma dose rate is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--dose", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No gamma dose rate is available."}


def test_cli_hourly_dose_prints_latest_hour(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Station,Hourly mean ambient gamma radiation dose rate (microsievert per hour)\n"
            "2026100402,Ping Chau,0.08\n"
            "2026100403,King's Park,  0.14  \n"
            "2026100403,Cape D'Aguilar,N/A\n"
            "2026100403,Chek Lap Kok,0.15\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--hourly-dose", "--lang", "tc"]) == 0
    assert seen["url"].endswith("latest_hourly_rmn_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong hourly gamma dose rate\n"
        "Recorded: 2026-10-04 03:00\n"
        "King's Park  0.14 µSv/h\n"
        "Chek Lap Kok  0.15 µSv/h\n"
    )


def test_cli_hourly_dose_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Dose\n"
            "2026100403,King's Park,0.14\n"
        ),
    )
    assert main(["--hourly-dose", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 03:00",
        "stations": [{"place": "King's Park", "dose_usv_h": 0.14}],
    }


def test_cli_hourly_dose_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Dose\n"
            "2026100403,Ping Chau,N/A\n"
        ),
    )
    assert main(["--hourly-dose"]) == 0
    assert capsys.readouterr().out == "No hourly gamma dose rate is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--hourly-dose", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No hourly gamma dose rate is available."
    }


def test_cli_accum_rain_prints_january_total(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "HKOReadingsAccumRainfall": "2466.0",
                "ReportTimeInfoDate": "20261002",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--accum-rain", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong accumulated rainfall\n"
        "2026-10-02\n"
        "2466 mm\n"
    )


def test_cli_accum_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"HKOReadingsAccumRainfall": "2466.0"}),
    )
    assert main(["--accum-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "date": "2026-10-02",
        "rainfall_mm": 2466.0,
    }


def test_cli_accum_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"HKOReadingsRainfall": "14.1"}),
    )
    assert main(["--accum-rain"]) == 0
    assert capsys.readouterr().out == "No accumulated rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--accum-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No accumulated rainfall is available."
    }


def test_cli_avg_rain_prints_climatological_normal(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "HKOReadingsAvgRainfall": "2252.8",
                "ReportTimeInfoDate": "20261002",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--avg-rain", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong average rainfall\n"
        "2026-10-02\n"
        "2252.8 mm\n"
    )


def test_cli_avg_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"HKOReadingsAvgRainfall": "2252.8"}),
    )
    assert main(["--avg-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "date": "2026-10-02",
        "rainfall_mm": 2252.8,
    }


def test_cli_avg_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"HKOReadingsAccumRainfall": "2466.0"}),
    )
    assert main(["--avg-rain"]) == 0
    assert capsys.readouterr().out == "No average rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--avg-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No average rainfall is available."}


def test_cli_radiation_prints_yesterday_report(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    report = (
        "Average ambient gamma radiation dose rate taken outdoors in Hong Kong "
        "ranged from 0.08 to 0.15 microsievert per hour."
    )

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "HongKongDesc": report,
                "ReportTimeInfoDate": "20261002",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--radiation", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong radiation\n2026-10-02\n{report}\n"


def test_cli_radiation_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"HongKongDesc": "Dose rate ranged from 0.08 to 0.15 microsievert per hour."}
        ),
    )
    assert main(["--radiation", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "date": "2026-10-02",
        "report": "Dose rate ranged from 0.08 to 0.15 microsievert per hour.",
    }


def test_cli_radiation_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"HKOReadingsMaxTemp": "31.7"}),
    )
    assert main(["--radiation"]) == 0
    assert capsys.readouterr().out == "No radiation report is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--radiation", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No radiation report is available."}


def test_cli_bulletin_prints_issue_time(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"BulletinDate": "20261003", "BulletinTime": "0015"})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--bulletin", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong weather bulletin\n2026-10-03 00:15\n"


def test_cli_bulletin_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"BulletinDate": "20261003", "BulletinTime": "0015"}),
    )
    assert main(["--bulletin", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"date": "2026-10-03", "time": "00:15"}


def test_cli_bulletin_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"HongKongDesc": "background radiation"}),
    )
    assert main(["--bulletin"]) == 0
    assert capsys.readouterr().out == "No weather bulletin time is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--bulletin", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No weather bulletin time is available."
    }


def test_cli_radiation_note_prints_the_range(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    note = (
        "The hourly mean ambient gamma radiation dose rate may vary "
        "between 0.06 and 0.3 microsievert per hour."
    )

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"NoteDesc": f"  {note}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--radiation-note", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong radiation note\n{note}\n"


def test_cli_radiation_note_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"NoteDesc": "Dose rate may vary between 0.06 and 0.3 microsievert per hour."}
        ),
    )
    assert main(["--radiation-note", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "note": "Dose rate may vary between 0.06 and 0.3 microsievert per hour."
    }


def test_cli_radiation_note_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"HongKongDesc": "background radiation"}),
    )
    assert main(["--radiation-note"]) == 0
    assert capsys.readouterr().out == "No radiation note is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--radiation-note", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No radiation note is available."}


def test_cli_radiation_weather_prints_the_note(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    note = "The variation of the dose rate may be due to the effect of weather."

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"NoteDesc1": f"  {note}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--radiation-weather", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong radiation weather\n{note}\n"


def test_cli_radiation_weather_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"NoteDesc1": "The variation of the dose rate may be due to the effect of weather."}
        ),
    )
    assert main(["--radiation-weather", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "note": "The variation of the dose rate may be due to the effect of weather."
    }


def test_cli_radiation_weather_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"NoteDesc": "Dose rate may vary."}),
    )
    assert main(["--radiation-weather"]) == 0
    assert capsys.readouterr().out == "No radiation weather note is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--radiation-weather", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No radiation weather note is available."
    }


def test_cli_radiation_ground_prints_the_note(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    note = "The spatial variation of the dose rate may be due to differences in rock and soil."

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"NoteDesc2": f"  {note}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--radiation-ground", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong radiation ground\n{note}\n"


def test_cli_radiation_ground_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "NoteDesc2": (
                    "The spatial variation of the dose rate may be due to "
                    "differences in rock and soil."
                )
            }
        ),
    )
    assert main(["--radiation-ground", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "note": (
            "The spatial variation of the dose rate may be due to differences in rock and soil."
        )
    }


def test_cli_radiation_ground_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"NoteDesc1": "Varies with the weather."}),
    )
    assert main(["--radiation-ground"]) == 0
    assert capsys.readouterr().out == "No radiation ground note is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--radiation-ground", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No radiation ground note is available."
    }


def test_cli_radiation_provisional_prints_the_note(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    note = "The data displayed is provisional and subject to revision."

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"NoteDesc3": f"  {note}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--radiation-provisional", "--lang", "tc"]) == 0
    assert "dataType=RYES" in seen["url"]
    assert "station=HKO" in seen["url"]
    assert "date=20261002" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong radiation provisional\n{note}\n"


def test_cli_radiation_provisional_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"NoteDesc3": "The data displayed is provisional and subject to revision."}
        ),
    )
    assert main(["--radiation-provisional", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "note": "The data displayed is provisional and subject to revision."
    }


def test_cli_radiation_provisional_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_yesterday", lambda now=None: "2026-10-02")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"NoteDesc2": "Varies with the ground."}),
    )
    assert main(["--radiation-provisional"]) == 0
    assert capsys.readouterr().out == "No radiation provisional note is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--radiation-provisional", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No radiation provisional note is available."
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


def test_cli_gust_prints_latest_stations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Automatic Weather Station,Direction,Speed,Gust\n"
            "202610040110,Central Pier,East,  5  ,9\n"
            "202610040110,Cheung Chau,N/A,N/A,N/A\n"
            "202610040110,Kai Tak,Southeast,3,4\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--gust", "--lang", "tc"]) == 0
    assert seen["url"].endswith("latest_10min_wind_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong wind gusts\n"
        "Recorded: 2026-10-04 01:10\n"
        "Central Pier  East  5 km/h  gust 9 km/h\n"
        "Kai Tak  Southeast  3 km/h  gust 4 km/h\n"
    )


def test_cli_gust_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Direction,Speed,Gust\n"
            "202610040110,Central Pier,East,5,9\n"
        ),
    )
    assert main(["--gust", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 01:10",
        "stations": [
            {
                "place": "Central Pier",
                "direction": "East",
                "speed_kmh": 5,
                "gust_kmh": 9,
            }
        ],
    }


def test_cli_gust_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Direction,Speed,Gust\n"
            "202610040110,Central Pier,N/A,N/A,N/A\n"
        ),
    )
    assert main(["--gust"]) == 0
    assert capsys.readouterr().out == "No wind gusts are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--gust", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No wind gusts are available."}


def test_cli_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,28,070,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,360,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WGL_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 橫瀾島\n"
        "2026-08-31  360°\n"
    )


def test_cli_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,28,070,C\n"
        ),
    )
    assert main(["--prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Waglan Island",
        "date": "2026-08-28",
        "direction_deg": 70.0,
    }


def test_cli_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--prevailing"]) == 0
    assert capsys.readouterr().out == "No prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No prevailing wind is available."}


def test_cli_cheung_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,180,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  360  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cheung-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CCH_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 長洲\n"
        "2026-08-31  360°\n"
    )


def test_cli_cheung_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,360,C\n"
        ),
    )
    assert main(["--cheung-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Cheung Chau",
        "date": "2026-08-31",
        "direction_deg": 360.0,
    }


def test_cli_cheung_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cheung-prevailing"]) == 0
    assert capsys.readouterr().out == "No Cheung Chau prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cheung-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Cheung Chau prevailing wind is available."
    }


def test_cli_ping_chau_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,170,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  330  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ping-chau-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_EPC_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 平洲\n"
        "2026-08-31  330°\n"
    )


def test_cli_ping_chau_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,330,C\n"
        ),
    )
    assert main(["--ping-chau-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ping Chau",
        "date": "2026-08-31",
        "direction_deg": 330.0,
    }


def test_cli_ping_chau_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ping-chau-prevailing"]) == 0
    assert capsys.readouterr().out == "No Ping Chau prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ping-chau-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ping Chau prevailing wind is available."
    }


def test_cli_tai_mo_to_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,090,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  310  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-to-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMT_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 大磨刀\n"
        "2026-08-31  310°\n"
    )


def test_cli_tai_mo_to_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,310,C\n"
        ),
    )
    assert main(["--tai-mo-to-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo To",
        "date": "2026-08-31",
        "direction_deg": 310.0,
    }


def test_cli_tai_mo_to_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-to-prevailing"]) == 0
    assert capsys.readouterr().out == "No Tai Mo To prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-to-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo To prevailing wind is available."
    }


def test_cli_tai_po_kau_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,090,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  260  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-po-kau-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TPK_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 大埔滘\n"
        "2026-08-31  260°\n"
    )


def test_cli_tai_po_kau_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,260,C\n"
        ),
    )
    assert main(["--tai-po-kau-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Po Kau",
        "date": "2026-08-31",
        "direction_deg": 260.0,
    }


def test_cli_tai_po_kau_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-po-kau-prevailing"]) == 0
    assert capsys.readouterr().out == "No Tai Po Kau prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-po-kau-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Po Kau prevailing wind is available."
    }


def test_cli_park_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,110,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  270  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--park-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 京士柏\n"
        "2026-08-31  270°\n"
    )


def test_cli_park_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,270,C\n"
        ),
    )
    assert main(["--park-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "direction_deg": 270.0,
    }


def test_cli_park_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--park-prevailing"]) == 0
    assert capsys.readouterr().out == "No King's Park prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--park-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park prevailing wind is available."
    }


def test_cli_lau_fau_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,230,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  360  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lau-fau-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_LFS_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 流浮山\n"
        "2026-08-31  360°\n"
    )


def test_cli_lau_fau_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,360,C\n"
        ),
    )
    assert main(["--lau-fau-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Lau Fau Shan",
        "date": "2026-08-31",
        "direction_deg": 360.0,
    }


def test_cli_lau_fau_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--lau-fau-prevailing"]) == 0
    assert capsys.readouterr().out == "No Lau Fau Shan prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--lau-fau-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Lau Fau Shan prevailing wind is available."
    }


def test_cli_sha_lo_wan_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,230,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  260  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-lo-wan-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SLW_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 沙螺灣\n"
        "2026-08-31  260°\n"
    )


def test_cli_sha_lo_wan_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,260,C\n"
        ),
    )
    assert main(["--sha-lo-wan-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Lo Wan",
        "date": "2026-08-31",
        "direction_deg": 260.0,
    }


def test_cli_sha_lo_wan_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-lo-wan-prevailing"]) == 0
    assert capsys.readouterr().out == "No Sha Lo Wan prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-lo-wan-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Lo Wan prevailing wind is available."
    }


def test_cli_wong_chuk_hang_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,220,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  130  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wong-chuk-hang-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKS_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 黃竹坑\n"
        "2026-08-31  130°\n"
    )


def test_cli_wong_chuk_hang_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,130,C\n"
        ),
    )
    assert main(["--wong-chuk-hang-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wong Chuk Hang",
        "date": "2026-08-31",
        "direction_deg": 130.0,
    }


def test_cli_wong_chuk_hang_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wong-chuk-hang-prevailing"]) == 0
    assert capsys.readouterr().out == (
        "No Wong Chuk Hang prevailing wind is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wong-chuk-hang-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wong Chuk Hang prevailing wind is available."
    }


def test_cli_sai_kung_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,170,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  030  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sai-kung-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKG_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 西貢\n"
        "2026-08-31  30°\n"
    )


def test_cli_sai_kung_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,030,C\n"
        ),
    )
    assert main(["--sai-kung-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sai Kung",
        "date": "2026-08-31",
        "direction_deg": 30.0,
    }


def test_cli_sai_kung_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sai-kung-prevailing"]) == 0
    assert capsys.readouterr().out == "No Sai Kung prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sai-kung-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sai Kung prevailing wind is available."
    }


def test_cli_tseung_kwan_o_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,200,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  090  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tseung-kwan-o-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_JKB_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 將軍澳\n"
        "2026-08-31  90°\n"
    )


def test_cli_tseung_kwan_o_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,090,C\n"
        ),
    )
    assert main(["--tseung-kwan-o-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tseung Kwan O",
        "date": "2026-08-31",
        "direction_deg": 90.0,
    }


def test_cli_tseung_kwan_o_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tseung-kwan-o-prevailing"]) == 0
    assert capsys.readouterr().out == "No Tseung Kwan O prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tseung-kwan-o-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tseung Kwan O prevailing wind is available."
    }


def test_cli_shek_kong_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,250,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  060  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shek-kong-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SEK_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 石崗\n"
        "2026-08-31  60°\n"
    )


def test_cli_shek_kong_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,060,C\n"
        ),
    )
    assert main(["--shek-kong-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shek Kong",
        "date": "2026-08-31",
        "direction_deg": 60.0,
    }


def test_cli_shek_kong_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shek-kong-prevailing"]) == 0
    assert capsys.readouterr().out == "No Shek Kong prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shek-kong-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shek Kong prevailing wind is available."
    }


def test_cli_sha_tin_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,220,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  010  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-tin-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SHA_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 沙田\n"
        "2026-08-31  10°\n"
    )


def test_cli_sha_tin_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,010,C\n"
        ),
    )
    assert main(["--sha-tin-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Tin",
        "date": "2026-08-31",
        "direction_deg": 10.0,
    }


def test_cli_sha_tin_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-tin-prevailing"]) == 0
    assert capsys.readouterr().out == "No Sha Tin prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-tin-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Tin prevailing wind is available."
    }


def test_cli_ta_kwu_ling_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,230,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  100  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ta-kwu-ling-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TKL_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 打鼓嶺\n"
        "2026-08-31  100°\n"
    )


def test_cli_ta_kwu_ling_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,100,C\n"
        ),
    )
    assert main(["--ta-kwu-ling-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ta Kwu Ling",
        "date": "2026-08-31",
        "direction_deg": 100.0,
    }


def test_cli_ta_kwu_ling_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ta-kwu-ling-prevailing"]) == 0
    assert capsys.readouterr().out == "No Ta Kwu Ling prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ta-kwu-ling-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ta Kwu Ling prevailing wind is available."
    }


def test_cli_wetland_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,220,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  320  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wetland-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WLP_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 濕地公園\n"
        "2026-08-31  320°\n"
    )


def test_cli_wetland_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,320,C\n"
        ),
    )
    assert main(["--wetland-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wetland Park",
        "date": "2026-08-31",
        "direction_deg": 320.0,
    }


def test_cli_wetland_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wetland-prevailing"]) == 0
    assert capsys.readouterr().out == "No Wetland Park prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wetland-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wetland Park prevailing wind is available."
    }


def test_cli_tai_mo_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,240,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  020  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMS_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 大帽山\n"
        "2026-08-31  20°\n"
    )


def test_cli_tai_mo_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,020,C\n"
        ),
    )
    assert main(["--tai-mo-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo Shan",
        "date": "2026-08-31",
        "direction_deg": 20.0,
    }


def test_cli_tai_mo_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-prevailing"]) == 0
    assert capsys.readouterr().out == "No Tai Mo Shan prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo Shan prevailing wind is available."
    }


def test_cli_airport_prevailing_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,7,29,100,C\n"
            "2026,7,30,***,\n"
            "2026,7,31,  090  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--airport-prevailing", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_PDIR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong prevailing wind\n"
        "Station: 香港國際機場\n"
        "2026-07-31  90°\n"
    )


def test_cli_airport_prevailing_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,090,C\n"
        ),
    )
    assert main(["--airport-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-07-31",
        "direction_deg": 90.0,
    }


def test_cli_airport_prevailing_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,***,\n"
        ),
    )
    assert main(["--airport-prevailing"]) == 0
    assert capsys.readouterr().out == "No airport prevailing wind is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--airport-prevailing", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No airport prevailing wind is available."
    }


def test_cli_mean_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,6.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  5.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--mean-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WGL_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 橫瀾島\n"
        "2026-08-31  5.9 km/h\n"
    )


def test_cli_mean_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,5.9,C\n"
        ),
    )
    assert main(["--mean-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Waglan Island",
        "date": "2026-08-31",
        "wind_km_h": 5.9,
    }


def test_cli_mean_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--mean-wind"]) == 0
    assert capsys.readouterr().out == "No mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--mean-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No mean wind speed is available."
    }


def test_cli_cheung_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,13.3,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  9.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cheung-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CCH_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 長洲\n"
        "2026-08-31  9.2 km/h\n"
    )


def test_cli_cheung_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,9.2,C\n"
        ),
    )
    assert main(["--cheung-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Cheung Chau",
        "date": "2026-08-31",
        "wind_km_h": 9.2,
    }


def test_cli_cheung_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cheung-wind"]) == 0
    assert capsys.readouterr().out == "No Cheung Chau mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cheung-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Cheung Chau mean wind speed is available."
    }


def test_cli_lau_fau_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,8.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  6.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lau-fau-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_LFS_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 流浮山\n"
        "2026-08-31  6.8 km/h\n"
    )


def test_cli_lau_fau_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,6.8,C\n"
        ),
    )
    assert main(["--lau-fau-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Lau Fau Shan",
        "date": "2026-08-31",
        "wind_km_h": 6.8,
    }


def test_cli_lau_fau_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--lau-fau-wind"]) == 0
    assert capsys.readouterr().out == "No Lau Fau Shan mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--lau-fau-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Lau Fau Shan mean wind speed is available."
    }


def test_cli_peng_chau_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,5.3,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  9.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--peng-chau-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_PEN_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 坪洲\n"
        "2026-08-31  9.7 km/h\n"
    )


def test_cli_peng_chau_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,9.7,C\n"
        ),
    )
    assert main(["--peng-chau-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Peng Chau",
        "date": "2026-08-31",
        "wind_km_h": 9.7,
    }


def test_cli_peng_chau_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--peng-chau-wind"]) == 0
    assert capsys.readouterr().out == "No Peng Chau mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--peng-chau-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Peng Chau mean wind speed is available."
    }


def test_cli_tai_po_kau_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,7.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  4.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-po-kau-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TPK_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 大埔滘\n"
        "2026-08-31  4.8 km/h\n"
    )


def test_cli_tai_po_kau_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,4.8,C\n"
        ),
    )
    assert main(["--tai-po-kau-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Po Kau",
        "date": "2026-08-31",
        "wind_km_h": 4.8,
    }


def test_cli_tai_po_kau_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-po-kau-wind"]) == 0
    assert capsys.readouterr().out == "No Tai Po Kau mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-po-kau-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Po Kau mean wind speed is available."
    }


def test_cli_tai_mo_to_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,12.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  7.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-to-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMT_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 大磨刀\n"
        "2026-08-31  7.4 km/h\n"
    )


def test_cli_tai_mo_to_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,7.4,C\n"
        ),
    )
    assert main(["--tai-mo-to-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo To",
        "date": "2026-08-31",
        "wind_km_h": 7.4,
    }


def test_cli_tai_mo_to_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-to-wind"]) == 0
    assert capsys.readouterr().out == "No Tai Mo To mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-to-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo To mean wind speed is available."
    }


def test_cli_tai_mo_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,14.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  10.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMS_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 大帽山\n"
        "2026-08-31  10.9 km/h\n"
    )


def test_cli_tai_mo_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,10.9,C\n"
        ),
    )
    assert main(["--tai-mo-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo Shan",
        "date": "2026-08-31",
        "wind_km_h": 10.9,
    }


def test_cli_tai_mo_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-wind"]) == 0
    assert capsys.readouterr().out == "No Tai Mo Shan mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo Shan mean wind speed is available."
    }


def test_cli_tate_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,12.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  9.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tate-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TC_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 大老山\n"
        "2026-08-31  9.8 km/h\n"
    )


def test_cli_tate_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,9.8,C\n"
        ),
    )
    assert main(["--tate-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tate's Cairn",
        "date": "2026-08-31",
        "wind_km_h": 9.8,
    }


def test_cli_tate_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tate-wind"]) == 0
    assert capsys.readouterr().out == "No Tate's Cairn mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tate-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tate's Cairn mean wind speed is available."
    }


def test_cli_shek_kong_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,3.9,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  3.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shek-kong-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SEK_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 石崗\n"
        "2026-08-31  3.1 km/h\n"
    )


def test_cli_shek_kong_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,3.1,C\n"
        ),
    )
    assert main(["--shek-kong-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shek Kong",
        "date": "2026-08-31",
        "wind_km_h": 3.1,
    }


def test_cli_shek_kong_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shek-kong-wind"]) == 0
    assert capsys.readouterr().out == "No Shek Kong mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shek-kong-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shek Kong mean wind speed is available."
    }


def test_cli_sai_kung_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,5.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  6.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sai-kung-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKG_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 西貢\n"
        "2026-08-31  6.6 km/h\n"
    )


def test_cli_sai_kung_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,6.6,C\n"
        ),
    )
    assert main(["--sai-kung-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sai Kung",
        "date": "2026-08-31",
        "wind_km_h": 6.6,
    }


def test_cli_sai_kung_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sai-kung-wind"]) == 0
    assert capsys.readouterr().out == "No Sai Kung mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sai-kung-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sai Kung mean wind speed is available."
    }


def test_cli_sha_tin_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,6.9,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  3.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-tin-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SHA_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 沙田\n"
        "2026-08-31  3.9 km/h\n"
    )


def test_cli_sha_tin_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,3.9,C\n"
        ),
    )
    assert main(["--sha-tin-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Tin",
        "date": "2026-08-31",
        "wind_km_h": 3.9,
    }


def test_cli_sha_tin_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-tin-wind"]) == 0
    assert capsys.readouterr().out == "No Sha Tin mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-tin-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Tin mean wind speed is available."
    }


def test_cli_wong_chuk_hang_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,3.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  2.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wong-chuk-hang-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKS_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 黃竹坑\n"
        "2026-08-31  2.1 km/h\n"
    )


def test_cli_wong_chuk_hang_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,2.1,C\n"
        ),
    )
    assert main(["--wong-chuk-hang-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wong Chuk Hang",
        "date": "2026-08-31",
        "wind_km_h": 2.1,
    }


def test_cli_wong_chuk_hang_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wong-chuk-hang-wind"]) == 0
    assert capsys.readouterr().out == (
        "No Wong Chuk Hang mean wind speed is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wong-chuk-hang-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wong Chuk Hang mean wind speed is available."
    }


def test_cli_park_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,8.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  4.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--park-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 京士柏\n"
        "2026-08-31  4.8 km/h\n"
    )


def test_cli_park_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,4.8,C\n"
        ),
    )
    assert main(["--park-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "wind_km_h": 4.8,
    }


def test_cli_park_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--park-wind"]) == 0
    assert capsys.readouterr().out == "No King's Park mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--park-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park mean wind speed is available."
    }


def test_cli_wetland_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,2.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  0.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wetland-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WLP_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 濕地公園\n"
        "2026-08-31  0.2 km/h\n"
    )


def test_cli_wetland_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,0.2,C\n"
        ),
    )
    assert main(["--wetland-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wetland Park",
        "date": "2026-08-31",
        "wind_km_h": 0.2,
    }


def test_cli_wetland_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wetland-wind"]) == 0
    assert capsys.readouterr().out == "No Wetland Park mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wetland-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wetland Park mean wind speed is available."
    }


def test_cli_tseung_kwan_o_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,4.9,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  3.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tseung-kwan-o-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_JKB_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 將軍澳\n"
        "2026-08-31  3.4 km/h\n"
    )


def test_cli_tseung_kwan_o_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,3.4,C\n"
        ),
    )
    assert main(["--tseung-kwan-o-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tseung Kwan O",
        "date": "2026-08-31",
        "wind_km_h": 3.4,
    }


def test_cli_tseung_kwan_o_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tseung-kwan-o-wind"]) == 0
    assert capsys.readouterr().out == (
        "No Tseung Kwan O mean wind speed is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tseung-kwan-o-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tseung Kwan O mean wind speed is available."
    }


def test_cli_ta_kwu_ling_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,3.9,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  2.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ta-kwu-ling-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TKL_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 打鼓嶺\n"
        "2026-08-31  2.9 km/h\n"
    )


def test_cli_ta_kwu_ling_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,2.9,C\n"
        ),
    )
    assert main(["--ta-kwu-ling-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ta Kwu Ling",
        "date": "2026-08-31",
        "wind_km_h": 2.9,
    }


def test_cli_ta_kwu_ling_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ta-kwu-ling-wind"]) == 0
    assert capsys.readouterr().out == "No Ta Kwu Ling mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ta-kwu-ling-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ta Kwu Ling mean wind speed is available."
    }


def test_cli_sha_lo_wan_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,8.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  4.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-lo-wan-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SLW_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 沙螺灣\n"
        "2026-08-31  4.5 km/h\n"
    )


def test_cli_sha_lo_wan_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,4.5,C\n"
        ),
    )
    assert main(["--sha-lo-wan-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Lo Wan",
        "date": "2026-08-31",
        "wind_km_h": 4.5,
    }


def test_cli_sha_lo_wan_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-lo-wan-wind"]) == 0
    assert capsys.readouterr().out == "No Sha Lo Wan mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-lo-wan-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Lo Wan mean wind speed is available."
    }


def test_cli_ping_chau_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,1.9,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  1.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ping-chau-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_EPC_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 平洲\n"
        "2026-08-31  1.5 km/h\n"
    )


def test_cli_ping_chau_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,1.5,C\n"
        ),
    )
    assert main(["--ping-chau-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ping Chau",
        "date": "2026-08-31",
        "wind_km_h": 1.5,
    }


def test_cli_ping_chau_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ping-chau-wind"]) == 0
    assert capsys.readouterr().out == "No Ping Chau mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ping-chau-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ping Chau mean wind speed is available."
    }


def test_cli_airport_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,7,29,15.9,C\n"
            "2026,7,30,***,\n"
            "2026,7,31,  14.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--airport-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 香港國際機場\n"
        "2026-07-31  14 km/h\n"
    )


def test_cli_airport_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,14.0,C\n"
        ),
    )
    assert main(["--airport-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-07-31",
        "wind_km_h": 14.0,
    }


def test_cli_airport_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,***,\n"
        ),
    )
    assert main(["--airport-wind"]) == 0
    assert capsys.readouterr().out == "No airport mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--airport-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No airport mean wind speed is available."
    }


def test_cli_green_island_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,14.3,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  9.3  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--green-island-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_GI_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 青洲\n"
        "2026-08-31  9.3 km/h\n"
    )


def test_cli_green_island_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,9.3,C\n"
        ),
    )
    assert main(["--green-island-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Green Island",
        "date": "2026-08-31",
        "wind_km_h": 9.3,
    }


def test_cli_green_island_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--green-island-wind"]) == 0
    assert capsys.readouterr().out == "No Green Island mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--green-island-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Green Island mean wind speed is available."
    }


def test_cli_ngong_ping_wind_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,16.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  12.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ngong-ping-wind", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_NGP_WSPD_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 昂坪\n"
        "2026-08-31  12.5 km/h\n"
    )
    assert main(["--ngong-ping-wind", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong mean wind speed\n"
        "Station: 昂坪\n"
        "2026-08-31  12.5 km/h\n"
    )


def test_cli_ngong_ping_wind_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,12.5,C\n"
        ),
    )
    assert main(["--ngong-ping-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ngong Ping",
        "date": "2026-08-31",
        "wind_km_h": 12.5,
    }


def test_cli_ngong_ping_wind_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ngong-ping-wind"]) == 0
    assert capsys.readouterr().out == "No Ngong Ping mean wind speed is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ngong-ping-wind", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ngong Ping mean wind speed is available."
    }


def test_cli_forecast_icon_lists_each_day(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2026-10-03T16:45:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "ForecastIcon": 54,
                        "forecastWind": "East force 4.",
                    },
                    {
                        "forecastDate": "20261005",
                        "week": "Monday",
                        "forecastWeather": "Sunny periods.",
                    },
                    {
                        "forecastDate": "20261006",
                        "week": "Tuesday",
                        "ForecastIcon": 52,
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--forecast-icon", "--lang", "tc"]) == 0
    assert "dataType=fnd" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong forecast icons\n"
        "Updated: 2026-10-03T16:45:00+08:00\n"
        "2026-10-04 Sunday  54  Sunny Intervals with Showers\n"
        "2026-10-06 Tuesday  52  Sunny Intervals\n"
    )


def test_cli_forecast_icon_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-03T16:45:00+08:00",
                "weatherForecast": [
                    {
                        "forecastDate": "20261004",
                        "week": "Sunday",
                        "ForecastIcon": 54,
                    }
                ],
            }
        ),
    )
    assert main(["--forecast-icon", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "update_time": "2026-10-03T16:45:00+08:00",
        "days": [
            {
                "date": "2026-10-04",
                "week": "Sunday",
                "icon": 54,
                "label": "Sunny Intervals with Showers",
            }
        ],
    }


def test_cli_forecast_icon_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"weatherForecast": [{"forecastDate": "20261004", "week": "Sunday"}]}
        ),
    )
    assert main(["--forecast-icon"]) == 0
    assert capsys.readouterr().out == "No forecast icons are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--forecast-icon", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No forecast icons are available."}


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


def test_cli_felt_prints_tremor(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "updateTime": "2020-09-01T08:30:00+08:00",
                "ptime": "2020-09-01T08:19:00+08:00",
                "mag": 2.1,
                "region": "  near Cheung Chau  ",
                "intensity": "III",
                "lat": 22.2,
                "lon": 114.1,
                "details": "A minor tremor was felt locally.",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--felt", "--lang", "tc"]) == 0
    assert "dataType=feltearthquake" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong felt tremor\n"
        "Updated: 2020-09-01T08:30:00+08:00\n"
        "2020-09-01T08:19:00+08:00  M2.1  near Cheung Chau (22.2, 114.1)  intensity III\n"
        "A minor tremor was felt locally.\n"
    )


def test_cli_felt_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2020-09-01T08:30:00+08:00",
                "ptime": "2020-09-01T08:19:00+08:00",
                "mag": 2,
                "region": "near Cheung Chau",
                "intensity": "III",
                "lat": 22.2,
                "lon": 114.1,
                "details": "A minor tremor was felt locally.",
            }
        ),
    )
    assert main(["-q", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "time": "2020-09-01T08:19:00+08:00",
        "update_time": "2020-09-01T08:30:00+08:00",
        "region": "near Cheung Chau",
        "magnitude": 2.0,
        "intensity": "III",
        "latitude": 22.2,
        "longitude": 114.1,
        "details": "A minor tremor was felt locally.",
    }


def test_cli_felt_when_none_reported(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--felt"]) == 0
    assert capsys.readouterr().out == "No locally felt earth tremor is reported.\n"
    assert main(["--felt", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No locally felt earth tremor is reported."
    }


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


def test_cli_tide_lists_high_and_low(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "fields": [
                    "Month",
                    "Date",
                    "Time",
                    "Height(m)",
                    "Time",
                    "Height(m)",
                    "Time",
                    "Height(m)",
                    "Time",
                    "Height(m)",
                ],
                "data": [["10", "03", "0105", "2.44", "0857", "0.84", "", "", "bad", "1"]],
            }
        )

    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda: "2026-10-03")
    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-I", "--lang", "tc"]) == 0
    assert "opendata.php" in seen["url"]
    assert "dataType=HLT" in seen["url"]
    assert "station=QUB" in seen["url"]
    assert "year=2026" in seen["url"]
    assert "month=10" in seen["url"]
    assert "day=3" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong tide\n"
        "Station: Quarry Bay\n"
        "2026-10-03  01:05  2.44 m\n"
        "2026-10-03  08:57  0.84 m\n"
    )


def test_cli_tide_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"data": [["10", "03", "0105", "2.44", "0857", "0.84", "", ""]]}
        ),
    )
    assert main(["--tide", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Quarry Bay",
        "events": [
            {"date": "2026-10-03", "time": "01:05", "height_m": 2.44},
            {"date": "2026-10-03", "time": "08:57", "height_m": 0.84},
        ],
    }


def test_cli_tide_when_no_readings(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": []}),
    )
    assert main(["--tide"]) == 0
    assert capsys.readouterr().out == "No tide readings are available.\n"
    assert main(["--tide", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No tide readings are available."}


def test_cli_tide_hour_lists_heights(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "fields": ["MM", "DD", "01", "02", "03"],
                "data": [["10", "3", "  2.44  ", "M", "2.29"]],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tide-hour", "--lang", "tc"]) == 0
    assert "dataType=HHOT" in seen["url"]
    assert "station=QUB" in seen["url"]
    assert "year=2026" in seen["url"]
    assert "month=10" in seen["url"]
    assert "day=3" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong hourly tide\n"
        "Station: Quarry Bay\n"
        "2026-10-03  01:00  2.44 m\n"
        "2026-10-03  03:00  2.29 m\n"
    )


def test_cli_tide_hour_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"fields": ["MM", "DD", "01"], "data": [["10", "03", "2.44"]]}
        ),
    )
    assert main(["--tide-hour", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Quarry Bay",
        "date": "2026-10-03",
        "hours": [{"hour": "01:00", "height_m": 2.44}],
    }


def test_cli_tide_hour_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"fields": ["MM", "DD", "01"], "data": [["10", "03", "***"]]}),
    )
    assert main(["--tide-hour"]) == 0
    assert capsys.readouterr().out == "No hourly tide heights are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": []}),
    )
    assert main(["--tide-hour", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No hourly tide heights are available."}


def test_cli_tide_latest_prints_newest_time(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Tide Station,Date,Time,Height(m)\n"
            "Quarry Bay,2026-10-04,03:00,2.10\n"
            "Quarry Bay,2026-10-04,03:15,  2.34  \n"
            "Shek Pik,2026-10-04,03:15,2.31\n"
            "Waglan Island,2026-10-04,03:15,----\n"
            "Tai Po Kau,2026-10-04,02:00,2.00\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tide-latest", "--lang", "tc"]) == 0
    assert seen["url"].endswith("ALL_tc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong latest tide\n"
        "Recorded: 2026-10-04 03:15\n"
        "Quarry Bay  2.34 m\n"
        "Shek Pik  2.31 m\n"
    )


def test_cli_tide_latest_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Tide Station,Date,Time,Height(m)\n"
            "Quarry Bay,2026-10-04,03:15,2.34\n"
        ),
    )
    assert main(["--tide-latest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 03:15",
        "stations": [{"place": "Quarry Bay", "height_m": 2.34}],
    }


def test_cli_tide_latest_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Tide Station,Date,Time,Height(m)\n"
            "Waglan Island,2026-10-04,03:15,----\n"
        ),
    )
    assert main(["--tide-latest"]) == 0
    assert capsys.readouterr().out == "No latest tide heights are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tide-latest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No latest tide heights are available."}


_AQHI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<item><title>Central/Western</title><description><![CDATA[Central/Western - General Stations: 3 Low - Sat, 03 Oct 2026 08:30]]></description></item>
<item><title>Causeway Bay</title><description><![CDATA[Causeway Bay - Roadside Stations: 10+ Serious - Sat, 03 Oct 2026 08:30]]></description></item>
<item><title>Skip</title><description><![CDATA[not a reading]]></description></item>
</channel></rss>
"""


def test_cli_aqhi_lists_stations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(_AQHI_XML)

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-A", "--lang", "tc"]) == 0
    assert seen["url"].endswith("aqhi_ind_rss_ChT.xml")
    assert capsys.readouterr().out == (
        "Hong Kong AQHI\n"
        "Updated: Sat, 03 Oct 2026 08:30\n"
        "Central/Western  General Stations  3  Low\n"
        "Causeway Bay  Roadside Stations  10+  Serious\n"
    )


def test_cli_aqhi_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(_AQHI_XML),
    )
    assert main(["--aqhi", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "updated": "Sat, 03 Oct 2026 08:30",
        "readings": [
            {
                "station": "Central/Western",
                "area": "General Stations",
                "aqhi": "3",
                "health_risk": "Low",
            },
            {
                "station": "Causeway Bay",
                "area": "Roadside Stations",
                "aqhi": "10+",
                "health_risk": "Serious",
            },
        ],
    }


def test_cli_aqhi_when_no_readings(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel></channel></rss>'
        ),
    )
    assert main(["--aqhi"]) == 0
    assert capsys.readouterr().out == "No AQHI readings are available.\n"
    assert main(["--aqhi", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No AQHI readings are available."}


def test_cli_sunrise_prints_times(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "fields": ["YYYY-MM-DD", "RISE", "TRAN.", "SET"],
                "data": [["2026-10-03", "06:15", "12:12", "18:09"], ["", "", "", ""]],
            }
        )

    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda: "2026-10-03")
    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-U", "--lang", "tc"]) == 0
    assert "opendata.php" in seen["url"]
    assert "dataType=SRS" in seen["url"]
    assert "year=2026" in seen["url"]
    assert "month=10" in seen["url"]
    assert "day=3" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong sunrise\n"
        "2026-10-03\n"
        "Rise: 06:15\n"
        "Transit: 12:12\n"
        "Set: 18:09\n"
    )


def test_cli_sunrise_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"data": [["2026-10-03", "06:15", "12:12", "18:09"]]}
        ),
    )
    assert main(["--sunrise", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "date": "2026-10-03",
        "rise": "06:15",
        "transit": "12:12",
        "set": "18:09",
    }


def test_cli_sunrise_when_no_times(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": []}),
    )
    assert main(["--sunrise"]) == 0
    assert capsys.readouterr().out == "No sunrise times are available.\n"
    assert main(["--sunrise", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No sunrise times are available."}


def test_cli_moon_prints_times(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "fields": ["YYYY-MM-DD", "RISE", "TRAN.", "SET"],
                "data": [["2026-10-03", "23:39", "05:42", "12:48"], ["", "", "", ""]],
            }
        )

    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda: "2026-10-03")
    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-M", "--lang", "sc"]) == 0
    assert "opendata.php" in seen["url"]
    assert "dataType=MRS" in seen["url"]
    assert "year=2026" in seen["url"]
    assert "month=10" in seen["url"]
    assert "day=3" in seen["url"]
    assert "lang=sc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong moon\n"
        "2026-10-03\n"
        "Rise: 23:39\n"
        "Transit: 05:42\n"
        "Set: 12:48\n"
    )


def test_cli_moon_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"data": [["2026-10-03", "23:39", "05:42", "12:48"]]}
        ),
    )
    assert main(["--moon", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "date": "2026-10-03",
        "rise": "23:39",
        "transit": "05:42",
        "set": "12:48",
    }


def test_cli_moon_when_no_times(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": []}),
    )
    assert main(["--moon"]) == 0
    assert capsys.readouterr().out == "No moon times are available.\n"
    assert main(["--moon", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No moon times are available."}


def test_cli_lunar_prints_today(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"LunarYear": "  丙午年，馬  ", "LunarDate": "八月廿三"})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lunar", "--lang", "tc"]) == 0
    assert "lunardate.php" in seen["url"]
    assert "date=2026-10-03" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong lunar date\n2026-10-03\n丙午年，馬\n八月廿三\n"


def test_cli_lunar_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"LunarYear": "丙午年，馬", "LunarDate": "八月廿三"}
        ),
    )
    assert main(["--lunar", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "date": "2026-10-03",
        "lunar_year": "丙午年，馬",
        "lunar_date": "八月廿三",
    }


def test_cli_lunar_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"LunarYear": "  ", "LunarDate": ""}),
    )
    assert main(["--lunar"]) == 0
    assert capsys.readouterr().out == "No lunar date is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--lunar", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No lunar date is available."}


def test_cli_visibility_when_none_available(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"data": [["202610030730", "Chek Lap Kok", "N/A"]]}
        ),
    )
    assert main(["--visibility"]) == 0
    assert capsys.readouterr().out == "No visibility readings are available.\n"


def test_cli_reduced_vis_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,3.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--reduced-vis", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_RVIS_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong reduced visibility\n"
        "Station: 香港國際機場\n"
        "2026-08-31  0 hours\n"
    )


def test_cli_reduced_vis_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,0,C\n"
        ),
    )
    assert main(["--reduced-vis", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-08-31",
        "hours": 0.0,
    }


def test_cli_reduced_vis_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--reduced-vis"]) == 0
    assert capsys.readouterr().out == "No reduced visibility is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--reduced-vis", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No reduced visibility is available."
    }


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


def test_cli_fifteen_uv_prints_latest_reading(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,past 15-minute mean UV Index\n"
            "202610040800,0.4\n"
            "202610040815,N/A\n"
            "202610040830,  1.4  \n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--fifteen-uv", "--lang", "tc"]) == 0
    assert seen["url"].endswith("latest_15min_uvindex_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong 15-minute UV index\n"
        "Station: 京士柏\n"
        "2026-10-04 08:30  1.4\n"
    )


def test_cli_fifteen_uv_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,past 15-minute mean UV Index\n"
            "202610040815,1\n"
        ),
    )
    assert main(["--fifteen-uv", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "time": "2026-10-04 08:15",
        "uv_index": 1.0,
    }


def test_cli_fifteen_uv_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,past 15-minute mean UV Index\n"
            "202610040815,N/A\n"
        ),
    )
    assert main(["--fifteen-uv"]) == 0
    assert capsys.readouterr().out == "No 15-minute UV index is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--fifteen-uv", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No 15-minute UV index is available."
    }


def test_cli_icon_time_prints_timestamp(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"iconUpdateTime": "  2026-10-03T09:50:00+08:00  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--icon-time", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong icon update\n2026-10-03T09:50:00+08:00\n"


def test_cli_icon_time_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"iconUpdateTime": "2026-10-03T09:50:00+08:00"}
        ),
    )
    assert main(["-i", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"updated": "2026-10-03T09:50:00+08:00"}


def test_cli_icon_time_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"iconUpdateTime": "   "}),
    )
    assert main(["--icon-time"]) == 0
    assert capsys.readouterr().out == "No icon update time is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--icon-time", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No icon update time is available."
    }


def test_cli_icon_prints_code_and_label(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"icon": [52, True, "no", 65]})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--icon", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong weather icon\n"
        "52  Sunny Intervals\n"
        "65  Thunderstorms\n"
    )


def test_cli_icon_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"icon": 52}),
    )
    assert main(["--icon", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "icons": [{"code": 52, "label": "Sunny Intervals"}]
    }


def test_cli_icon_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"icon": []}),
    )
    assert main(["--icon"]) == 0
    assert capsys.readouterr().out == "No weather icon is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--icon", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No weather icon is available."}


def test_cli_current_updated_prints_timestamp(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"updateTime": "  2026-10-03T16:45:00+08:00  ", "icon": [52]})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--current-updated", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong weather update\n2026-10-03T16:45:00+08:00\n"


def test_cli_current_updated_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"updateTime": "2026-10-03T16:45:00+08:00"}),
    )
    assert main(["--current-updated", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"updated": "2026-10-03T16:45:00+08:00"}


def test_cli_current_updated_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"icon": [52], "updateTime": "  "}),
    )
    assert main(["--current-updated"]) == 0
    assert capsys.readouterr().out == "No weather update time is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--current-updated", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No weather update time is available."}


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


def test_cli_lamppost_prints_experimental_reading(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "PI": "GF3637",
                "BODY": {
                    "HKO": {
                        "RH": "  86.0  ",
                        "T0": "27.1",
                        "TS": "20261004065027",
                        "WS": "4",
                        "WD": "144",
                        "DH": "3",
                    }
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lamppost", "--lang", "tc"]) == 0
    assert "pi=GF3637" in seen["url"]
    assert "di=01" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong smart lamppost\n"
        "Lamppost: GF3637\n"
        "2026-10-04 06:50:27  27.1°C  humidity 86%  wind 4 km/h from 144°\n"
    )


def test_cli_lamppost_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "PI": "GF3637",
                "BODY": {
                    "HKO": {
                        "RH": "////",
                        "T0": "27.1",
                        "TS": "20261004065027",
                        "WS": "4",
                        "WD": "144",
                    }
                },
            }
        ),
    )
    assert main(["--lamppost", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "lamppost": "GF3637",
        "time": "2026-10-04 06:50:27",
        "temperature_c": 27.1,
        "humidity_percent": None,
        "wind_km_h": 4.0,
        "direction_deg": 144.0,
    }


def test_cli_lamppost_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"message": "No record found"}),
    )
    assert main(["--lamppost"]) == 0
    assert capsys.readouterr().out == "No smart lamppost reading is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"PI": "GF3637", "BODY": {"HKO": {"T0": "////", "RH": "////", "WS": "////", "WD": "////"}}}
        ),
    )
    assert main(["--lamppost", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No smart lamppost reading is available."
    }


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
        "🌧️ Rain, 28°C, humidity 85% — "
        "The Thunderstorm Warning has been issued (+1 more)\n"
    )
    assert "Hong Kong weather" not in out


def test_cli_summary_prints_briefing(monkeypatch, capsys):
    seen = []
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen.append(request.full_url)
        url = request.full_url
        if "dataType=warnsum" in url:
            return _json_response(
                {
                    "WTS": {
                        "code": "WTS",
                        "name": "Thunderstorm Warning",
                        "actionCode": "ISSUE",
                    },
                    "WRAIN": {
                        "code": "WRAIN",
                        "name": "Rainstorm Warning Signal",
                        "actionCode": "CANCEL",
                    },
                }
            )
        if "dataType=fnd" in url:
            return _json_response(
                {
                    "updateTime": "2026-10-03T00:00:00+08:00",
                    "weatherForecast": [
                        {
                            "forecastDate": "20261003",
                            "week": "Saturday",
                            "forecastWeather": "Rain.",
                            "forecastMaxtemp": {"value": 30, "unit": "C"},
                            "forecastMintemp": {"value": 26, "unit": "C"},
                            "PSR": "Medium",
                        }
                    ],
                }
            )
        return _json_response(
            {
                "icon": [63],
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
                },
                "humidity": {
                    "data": [{"place": "Hong Kong Observatory", "value": 85, "unit": "percent"}]
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--summary", "--lang", "tc"]) == 0
    assert any("dataType=rhrread" in url and "lang=tc" in url for url in seen)
    assert any("dataType=warnsum" in url and "lang=tc" in url for url in seen)
    assert any("dataType=fnd" in url and "lang=tc" in url for url in seen)
    assert capsys.readouterr().out == (
        "Hong Kong summary\n"
        "🌧️ Rain, 28°C, humidity 85%\n"
        "Warnings:\n"
        "WTS  Thunderstorm Warning\n"
        "Today: 2026-10-03  high 30°C  low 26°C  rain Medium\n"
    )


def test_cli_summary_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        url = request.full_url
        if "dataType=warnsum" in url:
            return _json_response(
                {"WTS": {"code": "WTS", "name": "Thunderstorm Warning", "actionCode": "ISSUE"}}
            )
        if "dataType=fnd" in url:
            return _json_response(
                {
                    "weatherForecast": [
                        {
                            "forecastDate": "20261003",
                            "week": "Saturday",
                            "forecastWeather": "Rain.",
                            "forecastMaxtemp": {"value": 30, "unit": "C"},
                            "forecastMintemp": {"value": 26, "unit": "C"},
                            "PSR": "Medium",
                        }
                    ]
                }
            )
        return _json_response(
            {
                "icon": [63],
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
                },
                "humidity": {
                    "data": [{"place": "Hong Kong Observatory", "value": 85, "unit": "percent"}]
                },
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-S", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "conditions": "Rain, 28°C, humidity 85%",
        "warnings": [{"code": "WTS", "description": "Thunderstorm Warning"}],
        "today": {
            "date": "2026-10-03",
            "high_c": 30.0,
            "low_c": 26.0,
            "rain_chance": "Medium",
        },
    }


def test_cli_summary_when_warnings_and_today_are_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-02")

    def fake_urlopen(request, timeout):
        url = request.full_url
        if "dataType=warnsum" in url:
            return _json_response({})
        if "dataType=fnd" in url:
            return _json_response(
                {
                    "weatherForecast": [
                        {
                            "forecastDate": "20261003",
                            "week": "Saturday",
                            "forecastWeather": "Sunny.",
                        }
                    ]
                }
            )
        return _json_response(
            {
                "icon": [50],
                "temperature": {"data": [{"place": "Chek Lap Kok", "value": 30, "unit": "C"}]},
                "humidity": "",
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--summary"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong summary\n"
        "☀️ Sunny, 30°C, humidity n/a\n"
        "Warnings: none\n"
        "Today: not available\n"
    )
    assert main(["--summary", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "conditions": "Sunny, 30°C, humidity n/a",
        "warnings": [],
        "today": None,
    }


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
    assert capsys.readouterr().out == "☀️ Sunny, 30°C, humidity n/a\n"


def test_cli_report_prefixes_known_icon(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "updateTime": "2026-10-02T23:02:00+08:00",
                "icon": [63, 65],
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
                },
                "humidity": {
                    "data": [{"place": "Hong Kong Observatory", "value": 85, "unit": "percent"}]
                },
            }
        ),
    )
    assert main([]) == 0
    assert "Conditions: 🌧️ Rain, ⛈️ Thunderstorms" in capsys.readouterr().out
    assert main(["--short"]) == 0
    assert capsys.readouterr().out == "🌧️ Rain, ⛈️ Thunderstorms, 28°C, humidity 85%\n"


def test_cli_unmapped_or_missing_icon_stays_plain(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "icon": [999],
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
                },
                "humidity": "",
            }
        ),
    )
    assert main([]) == 0
    report = capsys.readouterr().out
    assert "Conditions: Icon 999\n" in report
    assert "🌧️" not in report
    assert main(["--short"]) == 0
    assert capsys.readouterr().out == "Icon 999, 28°C, humidity n/a\n"

    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "temperature": {
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}]
                },
                "humidity": "",
            }
        ),
    )
    assert main([]) == 0
    report = capsys.readouterr().out
    assert "Conditions: Unknown\n" in report
    assert "☀️" not in report
    assert main(["-s"]) == 0
    assert capsys.readouterr().out == "Unknown, 28°C, humidity n/a\n"


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


def test_cli_rain_period_prints_the_window(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "rainfall": {
                    "startTime": "2026-10-03T15:45:00+08:00",
                    "endTime": "2026-10-03T16:45:00+08:00",
                    "data": [{"place": "Sai Kung", "max": 2, "unit": "mm"}],
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--rain-period", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong rainfall period\n"
        "From: 2026-10-03T15:45:00+08:00\n"
        "To: 2026-10-03T16:45:00+08:00\n"
    )


def test_cli_rain_period_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "rainfall": {
                    "startTime": "2026-10-03T15:45:00+08:00",
                    "endTime": "2026-10-03T16:45:00+08:00",
                }
            }
        ),
    )
    assert main(["--rain-period", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "start": "2026-10-03T15:45:00+08:00",
        "end": "2026-10-03T16:45:00+08:00",
    }


def test_cli_rain_period_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"rainfall": {"data": [{"place": "Sai Kung", "max": 2, "unit": "mm"}]}}
        ),
    )
    assert main(["--rain-period"]) == 0
    assert capsys.readouterr().out == "No rainfall period is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--rain-period", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No rainfall period is available."}


def test_cli_rain_maint_lists_flagged_districts(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "rainfall": {
                    "data": [
                        {"place": "  Sai Kung  ", "max": 1, "main": " TRUE "},
                        {"place": "Yuen Long", "max": 0, "main": "FALSE"},
                        {"place": "Sai Kung", "max": 2, "main": True},
                        {"place": "Islands", "max": 0, "main": "true"},
                    ]
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--rain-maint", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong rainfall maintenance\nSai Kung\nIslands\n"


def test_cli_rain_maint_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"rainfall": {"data": [{"place": "Sai Kung", "main": "TRUE"}]}}
        ),
    )
    assert main(["--rain-maint", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"places": ["Sai Kung"]}


def test_cli_rain_maint_when_none(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"rainfall": {"data": [{"place": "Sai Kung", "max": 1, "main": "FALSE"}]}}
        ),
    )
    assert main(["--rain-maint"]) == 0
    assert capsys.readouterr().out == "No rainfall stations are under maintenance.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--rain-maint", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No rainfall stations are under maintenance."
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


def test_cli_strikes_prints_counts(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "fields": ["DateTime", "Type", "Region", "lightning count"],
                "data": [
                    ["202610031200-202610031259", "Cloud-to-ground", "New Territories West", "3"],
                    ["202610031200-202610031259", "  ", "Skip", "1"],
                    ["202610031200-202610031259", "Cloud-to-cloud", "Hong Kong territory", "12"],
                    ["short"],
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--strikes", "--lang", "tc"]) == 0
    assert "dataType=LHL" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong lightning count\n"
        "2026-10-03 12:00-12:59  Cloud-to-ground  New Territories West  3\n"
        "2026-10-03 12:00-12:59  Cloud-to-cloud  Hong Kong territory  12\n"
    )


def test_cli_strikes_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "data": [
                    ["202610031200-202610031259", "Cloud-to-ground", "Lantau", "0"],
                ]
            }
        ),
    )
    assert main(["-l", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "counts": [
            {
                "start": "2026-10-03 12:00",
                "end": "2026-10-03 12:59",
                "kind": "Cloud-to-ground",
                "region": "Lantau",
                "count": 0,
            }
        ]
    }


def test_cli_strikes_when_none_available(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"data": []}),
    )
    assert main(["--strikes"]) == 0
    assert capsys.readouterr().out == "No lightning counts are available.\n"
    assert main(["--strikes", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No lightning counts are available."
    }


def test_cli_daily_strikes_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,30,0,C\n"
            "2026,8,31,***,\n"
            "2026,8,31,  42  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--daily-strikes"]) == 0
    assert seen["url"].endswith("daily_HK_LGTG_2026.csv")
    assert capsys.readouterr().out == "Hong Kong daily lightning\n2026-08-31  42\n"


def test_cli_daily_strikes_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,30,0,C\n"
        ),
    )
    assert main(["--daily-strikes", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"date": "2026-08-30", "count": 0.0}


def test_cli_daily_strikes_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--daily-strikes"]) == 0
    assert capsys.readouterr().out == "No daily lightning count is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--daily-strikes", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No daily lightning count is available."
    }


def test_cli_cloud_strikes_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,28,80,C\n"
            "2026,8,30,0,C\n"
            "2026,8,31,***,\n"
            "2026,8,31,  158  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cloud-strikes", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HK_LGTC_2026.csv")
    assert capsys.readouterr().out == "Hong Kong cloud-to-cloud lightning\n2026-08-31  158\n"


def test_cli_cloud_strikes_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,158,C\n"
        ),
    )
    assert main(["--cloud-strikes", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "date": "2026-08-31",
        "count": 158.0,
    }


def test_cli_cloud_strikes_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cloud-strikes"]) == 0
    assert capsys.readouterr().out == "No cloud-to-cloud lightning count is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cloud-strikes", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No cloud-to-cloud lightning count is available."
    }


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


def test_cli_minute_temp_prints_latest_stations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Automatic Weather Station,Air Temperature(degree Celsius)\n"
            "202610040130,Chek Lap Kok,  27.9  \n"
            "202610040130,Clear Water Bay,N/A\n"
            "202610040130,HK Observatory,27.7\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--minute-temp", "--lang", "tc"]) == 0
    assert seen["url"].endswith("latest_1min_temperature_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong 1-minute temperature\n"
        "Recorded: 2026-10-04 01:30\n"
        "Chek Lap Kok  27.9°C\n"
        "HK Observatory  27.7°C\n"
    )


def test_cli_minute_temp_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Temperature\n"
            "202610040130,Chek Lap Kok,27.9\n"
        ),
    )
    assert main(["--minute-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 01:30",
        "stations": [{"place": "Chek Lap Kok", "temperature_c": 27.9}],
    }


def test_cli_minute_temp_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Temperature\n"
            "202610040130,Clear Water Bay,N/A\n"
        ),
    )
    assert main(["--minute-temp"]) == 0
    assert capsys.readouterr().out == "No 1-minute temperatures are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--minute-temp", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No 1-minute temperatures are available."
    }


def test_cli_minute_humidity_prints_latest_stations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Automatic Weather Station,Relative Humidity(percent)\n"
            "202610040140,Chek Lap Kok,  74  \n"
            "202610040140,Clear Water Bay,N/A\n"
            "202610040140,Cheung Chau,96\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--minute-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("latest_1min_humidity_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong 1-minute humidity\n"
        "Recorded: 2026-10-04 01:40\n"
        "Chek Lap Kok  74%\n"
        "Cheung Chau  96%\n"
    )


def test_cli_minute_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Humidity\n"
            "202610040140,Chek Lap Kok,74\n"
        ),
    )
    assert main(["--minute-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 01:40",
        "stations": [{"place": "Chek Lap Kok", "humidity_percent": 74}],
    }


def test_cli_minute_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Humidity\n"
            "202610040140,Clear Water Bay,N/A\n"
        ),
    )
    assert main(["--minute-humidity"]) == 0
    assert capsys.readouterr().out == "No 1-minute humidity readings are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--minute-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No 1-minute humidity readings are available."
    }


def test_cli_mean_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,78,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  85  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--mean-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKO_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 香港天文台\n"
        "2026-08-31  85%\n"
    )


def test_cli_mean_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,85,C\n"
        ),
    )
    assert main(["--mean-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Observatory",
        "date": "2026-08-31",
        "humidity_percent": 85.0,
    }


def test_cli_mean_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--mean-humidity"]) == 0
    assert capsys.readouterr().out == "No daily mean humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--mean-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No daily mean humidity is available."
    }


def test_cli_tai_mo_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,94,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  96  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMS_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 大帽山\n"
        "2026-08-31  96%\n"
    )


def test_cli_tai_mo_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,96,C\n"
        ),
    )
    assert main(["--tai-mo-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo Shan",
        "date": "2026-08-31",
        "humidity_percent": 96.0,
    }


def test_cli_tai_mo_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-humidity"]) == 0
    assert capsys.readouterr().out == "No Tai Mo Shan humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo Shan humidity is available."
    }


def test_cli_waglan_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,89,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  91  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--waglan-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WGL_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 橫瀾島\n"
        "2026-08-31  91%\n"
    )


def test_cli_waglan_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,91,C\n"
        ),
    )
    assert main(["--waglan-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Waglan Island",
        "date": "2026-08-31",
        "humidity_percent": 91.0,
    }


def test_cli_waglan_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--waglan-humidity"]) == 0
    assert capsys.readouterr().out == "No Waglan Island humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--waglan-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Waglan Island humidity is available."
    }


def test_cli_tate_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,93,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  95  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tate-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TC_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 大老山\n"
        "2026-08-31  95%\n"
    )


def test_cli_tate_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,95,C\n"
        ),
    )
    assert main(["--tate-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tate's Cairn",
        "date": "2026-08-31",
        "humidity_percent": 95.0,
    }


def test_cli_tate_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tate-humidity"]) == 0
    assert capsys.readouterr().out == "No Tate's Cairn humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tate-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tate's Cairn humidity is available."
    }


def test_cli_ta_kwu_ling_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,85,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  94  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ta-kwu-ling-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TKL_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 打鼓嶺\n"
        "2026-08-31  94%\n"
    )


def test_cli_ta_kwu_ling_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,94,C\n"
        ),
    )
    assert main(["--ta-kwu-ling-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ta Kwu Ling",
        "date": "2026-08-31",
        "humidity_percent": 94.0,
    }


def test_cli_ta_kwu_ling_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ta-kwu-ling-humidity"]) == 0
    assert capsys.readouterr().out == "No Ta Kwu Ling humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ta-kwu-ling-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ta Kwu Ling humidity is available."
    }


def test_cli_wetland_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,90,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  96  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wetland-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WLP_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 濕地公園\n"
        "2026-08-31  96%\n"
    )


def test_cli_wetland_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,96,C\n"
        ),
    )
    assert main(["--wetland-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wetland Park",
        "date": "2026-08-31",
        "humidity_percent": 96.0,
    }


def test_cli_wetland_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wetland-humidity"]) == 0
    assert capsys.readouterr().out == "No Wetland Park humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wetland-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wetland Park humidity is available."
    }


def test_cli_shek_kong_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,90,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  93  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shek-kong-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SEK_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 石崗\n"
        "2026-08-31  93%\n"
    )


def test_cli_shek_kong_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,93,C\n"
        ),
    )
    assert main(["--shek-kong-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shek Kong",
        "date": "2026-08-31",
        "humidity_percent": 93.0,
    }


def test_cli_shek_kong_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shek-kong-humidity"]) == 0
    assert capsys.readouterr().out == "No Shek Kong humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shek-kong-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shek Kong humidity is available."
    }


def test_cli_lau_fau_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,89,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  95  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lau-fau-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_LFS_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 流浮山\n"
        "2026-08-31  95%\n"
    )


def test_cli_lau_fau_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,95,C\n"
        ),
    )
    assert main(["--lau-fau-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Lau Fau Shan",
        "date": "2026-08-31",
        "humidity_percent": 95.0,
    }


def test_cli_lau_fau_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--lau-fau-humidity"]) == 0
    assert capsys.readouterr().out == "No Lau Fau Shan humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--lau-fau-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Lau Fau Shan humidity is available."
    }


def test_cli_park_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,82,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  84  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--park-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 京士柏\n"
        "2026-08-31  84%\n"
    )


def test_cli_park_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,84,C\n"
        ),
    )
    assert main(["--park-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "humidity_percent": 84.0,
    }


def test_cli_park_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--park-humidity"]) == 0
    assert capsys.readouterr().out == "No King's Park humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--park-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park humidity is available."
    }


def test_cli_sai_kung_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,81,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  86  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sai-kung-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKG_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 西貢\n"
        "2026-08-31  86%\n"
    )


def test_cli_sai_kung_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,86,C\n"
        ),
    )
    assert main(["--sai-kung-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sai Kung",
        "date": "2026-08-31",
        "humidity_percent": 86.0,
    }


def test_cli_sai_kung_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sai-kung-humidity"]) == 0
    assert capsys.readouterr().out == "No Sai Kung humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sai-kung-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sai Kung humidity is available."
    }


def test_cli_cheung_chau_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,95,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  92  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cheung-chau-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CCH_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 長洲\n"
        "2026-08-31  92%\n"
    )


def test_cli_cheung_chau_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,92,C\n"
        ),
    )
    assert main(["--cheung-chau-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Cheung Chau",
        "date": "2026-08-31",
        "humidity_percent": 92.0,
    }


def test_cli_cheung_chau_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cheung-chau-humidity"]) == 0
    assert capsys.readouterr().out == "No Cheung Chau humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cheung-chau-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Cheung Chau humidity is available."
    }


def test_cli_sha_tin_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,82,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  88  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-tin-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SHA_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 沙田\n"
        "2026-08-31  88%\n"
    )


def test_cli_sha_tin_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,88,C\n"
        ),
    )
    assert main(["--sha-tin-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Tin",
        "date": "2026-08-31",
        "humidity_percent": 88.0,
    }


def test_cli_sha_tin_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-tin-humidity"]) == 0
    assert capsys.readouterr().out == "No Sha Tin humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-tin-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Tin humidity is available."
    }


def test_cli_sheung_shui_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,79,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  88  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sheung-shui-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSH_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 上水\n"
        "2026-08-31  88%\n"
    )


def test_cli_sheung_shui_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,88,C\n"
        ),
    )
    assert main(["--sheung-shui-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sheung Shui",
        "date": "2026-08-31",
        "humidity_percent": 88.0,
    }


def test_cli_sheung_shui_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sheung-shui-humidity"]) == 0
    assert capsys.readouterr().out == "No Sheung Shui humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sheung-shui-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sheung Shui humidity is available."
    }


def test_cli_wong_chuk_hang_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,88,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  90  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wong-chuk-hang-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKS_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 黃竹坑\n"
        "2026-08-31  90%\n"
    )


def test_cli_wong_chuk_hang_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,90,C\n"
        ),
    )
    assert main(["--wong-chuk-hang-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wong Chuk Hang",
        "date": "2026-08-31",
        "humidity_percent": 90.0,
    }


def test_cli_wong_chuk_hang_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wong-chuk-hang-humidity"]) == 0
    assert capsys.readouterr().out == "No Wong Chuk Hang humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wong-chuk-hang-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wong Chuk Hang humidity is available."
    }


def test_cli_tseung_kwan_o_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,86,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  94  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tseung-kwan-o-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_JKB_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 將軍澳\n"
        "2026-08-31  94%\n"
    )


def test_cli_tseung_kwan_o_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,94,C\n"
        ),
    )
    assert main(["--tseung-kwan-o-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tseung Kwan O",
        "date": "2026-08-31",
        "humidity_percent": 94.0,
    }


def test_cli_tseung_kwan_o_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tseung-kwan-o-humidity"]) == 0
    assert capsys.readouterr().out == "No Tseung Kwan O humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tseung-kwan-o-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tseung Kwan O humidity is available."
    }


def test_cli_peng_chau_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,82,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  84  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--peng-chau-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_PEN_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 坪洲\n"
        "2026-08-31  84%\n"
    )


def test_cli_peng_chau_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,84,C\n"
        ),
    )
    assert main(["--peng-chau-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Peng Chau",
        "date": "2026-08-31",
        "humidity_percent": 84.0,
    }


def test_cli_peng_chau_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--peng-chau-humidity"]) == 0
    assert capsys.readouterr().out == "No Peng Chau humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--peng-chau-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Peng Chau humidity is available."
    }


def test_cli_sha_lo_wan_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,86,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  94  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-lo-wan-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SLW_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 沙螺灣\n"
        "2026-08-31  94%\n"
    )


def test_cli_sha_lo_wan_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,94,C\n"
        ),
    )
    assert main(["--sha-lo-wan-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Lo Wan",
        "date": "2026-08-31",
        "humidity_percent": 94.0,
    }


def test_cli_sha_lo_wan_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-lo-wan-humidity"]) == 0
    assert capsys.readouterr().out == "No Sha Lo Wan humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-lo-wan-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Lo Wan humidity is available."
    }


def test_cli_airport_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,7,29,89,C\n"
            "2026,7,30,***,\n"
            "2026,7,31,  86  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--airport-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 香港國際機場\n"
        "2026-07-31  86%\n"
    )


def test_cli_airport_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,86,C\n"
        ),
    )
    assert main(["--airport-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-07-31",
        "humidity_percent": 86.0,
    }


def test_cli_airport_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,***,\n"
        ),
    )
    assert main(["--airport-humidity"]) == 0
    assert capsys.readouterr().out == "No airport humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--airport-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No airport humidity is available."
    }


def test_cli_tsuen_wan_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,91,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  93  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tsuen-wan-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TWN_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 荃灣\n"
        "2026-08-31  93%\n"
    )
    assert main(["--tsuen-wan-humidity", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 荃湾\n"
        "2026-08-31  93%\n"
    )


def test_cli_tsuen_wan_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,93,C\n"
        ),
    )
    assert main(["--tsuen-wan-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tsuen Wan",
        "date": "2026-08-31",
        "humidity_percent": 93.0,
    }


def test_cli_tsuen_wan_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tsuen-wan-humidity"]) == 0
    assert capsys.readouterr().out == "No Tsuen Wan humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tsuen-wan-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tsuen Wan humidity is available."
    }


def test_cli_hong_kong_park_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,83,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  89  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--hong-kong-park-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKP_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 香港公園\n"
        "2026-08-31  89%\n"
    )
    assert main(["--hong-kong-park-humidity", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 香港公园\n"
        "2026-08-31  89%\n"
    )


def test_cli_hong_kong_park_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,89,C\n"
        ),
    )
    assert main(["--hong-kong-park-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Park",
        "date": "2026-08-31",
        "humidity_percent": 89.0,
    }


def test_cli_hong_kong_park_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--hong-kong-park-humidity"]) == 0
    assert capsys.readouterr().out == "No Hong Kong Park humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--hong-kong-park-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Hong Kong Park humidity is available."
    }


def test_cli_clear_water_bay_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,85,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  89  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--clear-water-bay-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CWB_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 清水灣\n"
        "2026-08-31  89%\n"
    )
    assert main(["--clear-water-bay-humidity", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 清水湾\n"
        "2026-08-31  89%\n"
    )


def test_cli_clear_water_bay_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,89,C\n"
        ),
    )
    assert main(["--clear-water-bay-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Clear Water Bay",
        "date": "2026-08-31",
        "humidity_percent": 89.0,
    }


def test_cli_clear_water_bay_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--clear-water-bay-humidity"]) == 0
    assert capsys.readouterr().out == "No Clear Water Bay humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--clear-water-bay-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Clear Water Bay humidity is available."
    }


def test_cli_shau_kei_wan_humidity_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,88,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  90  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shau-kei-wan-humidity", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKW_RH_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 筲箕灣\n"
        "2026-08-31  90%\n"
    )
    assert main(["--shau-kei-wan-humidity", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong daily mean humidity\n"
        "Station: 筲箕湾\n"
        "2026-08-31  90%\n"
    )


def test_cli_shau_kei_wan_humidity_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,90,C\n"
        ),
    )
    assert main(["--shau-kei-wan-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shau Kei Wan",
        "date": "2026-08-31",
        "humidity_percent": 90.0,
    }


def test_cli_shau_kei_wan_humidity_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shau-kei-wan-humidity"]) == 0
    assert capsys.readouterr().out == "No Shau Kei Wan humidity is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shau-kei-wan-humidity", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shau Kei Wan humidity is available."
    }


def test_cli_since_midnight_prints_high_and_low(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Station,Maximum,Minimum\n"
            "202610040150,Chek Lap Kok,  28.2  ,27.8\n"
            "202610040150,Clear Water Bay,N/A,N/A\n"
            "202610040150,HK Observatory,27.9,27.6\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--since-midnight", "--lang", "tc"]) == 0
    assert seen["url"].endswith("latest_since_midnight_maxmin_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong temperature since midnight\n"
        "Recorded: 2026-10-04 01:50\n"
        "Chek Lap Kok  high 28.2°C  low 27.8°C\n"
        "HK Observatory  high 27.9°C  low 27.6°C\n"
    )


def test_cli_since_midnight_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Maximum,Minimum\n"
            "202610040150,Chek Lap Kok,28.2,27.8\n"
        ),
    )
    assert main(["--since-midnight", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 01:50",
        "stations": [
            {"place": "Chek Lap Kok", "temp_high_c": 28.2, "temp_low_c": 27.8}
        ],
    }


def test_cli_since_midnight_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Maximum,Minimum\n"
            "202610040150,Clear Water Bay,N/A,N/A\n"
        ),
    )
    assert main(["--since-midnight"]) == 0
    assert capsys.readouterr().out == "No temperatures since midnight are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--since-midnight", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No temperatures since midnight are available."
    }


def test_cli_pressure_prints_latest_stations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Automatic Weather Station,Mean Sea Level Pressure(hPa)\n"
            "202610040210,Chek Lap Kok,  1011.9  \n"
            "202610040210,Peng Chau,N/A\n"
            "202610040210,HK Observatory,1011.8\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("latest_1min_pressure_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong sea level pressure\n"
        "Recorded: 2026-10-04 02:10\n"
        "Chek Lap Kok  1011.9 hPa\n"
        "HK Observatory  1011.8 hPa\n"
    )


def test_cli_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Pressure\n"
            "202610040210,Chek Lap Kok,1011.9\n"
        ),
    )
    assert main(["--pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 02:10",
        "stations": [{"place": "Chek Lap Kok", "pressure_hpa": 1011.9}],
    }


def test_cli_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Pressure\n"
            "202610040210,Peng Chau,N/A\n"
        ),
    )
    assert main(["--pressure"]) == 0
    assert capsys.readouterr().out == "No sea level pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No sea level pressure is available."}


def test_cli_mean_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,1001.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  998.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--mean-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKO_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 香港天文台\n"
        "2026-08-31  998.7 hPa\n"
    )


def test_cli_mean_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,998.7,C\n"
        ),
    )
    assert main(["--mean-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Observatory",
        "date": "2026-08-31",
        "pressure_hpa": 998.7,
    }


def test_cli_mean_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--mean-pressure"]) == 0
    assert capsys.readouterr().out == "No daily mean pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--mean-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No daily mean pressure is available."
    }


def test_cli_park_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,999.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  998.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--park-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 京士柏\n"
        "2026-08-31  998.5 hPa\n"
    )


def test_cli_park_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,998.5,C\n"
        ),
    )
    assert main(["--park-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "pressure_hpa": 998.5,
    }


def test_cli_park_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--park-pressure"]) == 0
    assert capsys.readouterr().out == "No King's Park pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--park-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park pressure is available."
    }


def test_cli_sha_tin_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,999.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  999.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-tin-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SHA_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 沙田\n"
        "2026-08-31  999.1 hPa\n"
    )


def test_cli_sha_tin_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,999.1,C\n"
        ),
    )
    assert main(["--sha-tin-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Tin",
        "date": "2026-08-31",
        "pressure_hpa": 999.1,
    }


def test_cli_sha_tin_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-tin-pressure"]) == 0
    assert capsys.readouterr().out == "No Sha Tin pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-tin-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Tin pressure is available."
    }


def test_cli_sheung_shui_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,999.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  998.3  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sheung-shui-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSH_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 上水\n"
        "2026-08-31  998.3 hPa\n"
    )


def test_cli_sheung_shui_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,998.3,C\n"
        ),
    )
    assert main(["--sheung-shui-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sheung Shui",
        "date": "2026-08-31",
        "pressure_hpa": 998.3,
    }


def test_cli_sheung_shui_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sheung-shui-pressure"]) == 0
    assert capsys.readouterr().out == "No Sheung Shui pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sheung-shui-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sheung Shui pressure is available."
    }


def test_cli_waglan_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,999.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  998.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--waglan-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WGL_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 橫瀾島\n"
        "2026-08-31  998.8 hPa\n"
    )


def test_cli_waglan_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,998.8,C\n"
        ),
    )
    assert main(["--waglan-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Waglan Island",
        "date": "2026-08-31",
        "pressure_hpa": 998.8,
    }


def test_cli_waglan_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--waglan-pressure"]) == 0
    assert capsys.readouterr().out == "No Waglan Island pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--waglan-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Waglan Island pressure is available."
    }


def test_cli_cheung_chau_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,999.8,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  998.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cheung-chau-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CCH_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 長洲\n"
        "2026-08-31  998.8 hPa\n"
    )


def test_cli_cheung_chau_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,998.8,C\n"
        ),
    )
    assert main(["--cheung-chau-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Cheung Chau",
        "date": "2026-08-31",
        "pressure_hpa": 998.8,
    }


def test_cli_cheung_chau_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cheung-chau-pressure"]) == 0
    assert capsys.readouterr().out == "No Cheung Chau pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cheung-chau-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Cheung Chau pressure is available."
    }


def test_cli_lau_fau_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,999.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  998.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lau-fau-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_LFS_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 流浮山\n"
        "2026-08-31  998.7 hPa\n"
    )


def test_cli_lau_fau_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,998.7,C\n"
        ),
    )
    assert main(["--lau-fau-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Lau Fau Shan",
        "date": "2026-08-31",
        "pressure_hpa": 998.7,
    }


def test_cli_lau_fau_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--lau-fau-pressure"]) == 0
    assert capsys.readouterr().out == "No Lau Fau Shan pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--lau-fau-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Lau Fau Shan pressure is available."
    }


def test_cli_tate_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,1000.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  999.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tate-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TC_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 大老山\n"
        "2026-08-31  999.7 hPa\n"
    )


def test_cli_tate_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,999.7,C\n"
        ),
    )
    assert main(["--tate-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tate's Cairn",
        "date": "2026-08-31",
        "pressure_hpa": 999.7,
    }


def test_cli_tate_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tate-pressure"]) == 0
    assert capsys.readouterr().out == "No Tate's Cairn pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tate-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tate's Cairn pressure is available."
    }


def test_cli_wetland_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,999.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  998.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wetland-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WLP_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 濕地公園\n"
        "2026-08-31  998.6 hPa\n"
    )


def test_cli_wetland_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,998.6,C\n"
        ),
    )
    assert main(["--wetland-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wetland Park",
        "date": "2026-08-31",
        "pressure_hpa": 998.6,
    }


def test_cli_wetland_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wetland-pressure"]) == 0
    assert capsys.readouterr().out == "No Wetland Park pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wetland-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wetland Park pressure is available."
    }


def test_cli_peng_chau_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,999.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  998.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--peng-chau-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_PEN_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 坪洲\n"
        "2026-08-31  998.7 hPa\n"
    )


def test_cli_peng_chau_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,998.7,C\n"
        ),
    )
    assert main(["--peng-chau-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Peng Chau",
        "date": "2026-08-31",
        "pressure_hpa": 998.7,
    }


def test_cli_peng_chau_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--peng-chau-pressure"]) == 0
    assert capsys.readouterr().out == "No Peng Chau pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--peng-chau-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Peng Chau pressure is available."
    }


def test_cli_tai_mo_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,1001.6,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  1000.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMS_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 大帽山\n"
        "2026-08-31  1000.4 hPa\n"
    )


def test_cli_tai_mo_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,1000.4,C\n"
        ),
    )
    assert main(["--tai-mo-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo Shan",
        "date": "2026-08-31",
        "pressure_hpa": 1000.4,
    }


def test_cli_tai_mo_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-pressure"]) == 0
    assert capsys.readouterr().out == "No Tai Mo Shan pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo Shan pressure is available."
    }


def test_cli_sha_lo_wan_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,1000.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  999.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-lo-wan-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SLW_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 沙螺灣\n"
        "2026-08-31  999.2 hPa\n"
    )


def test_cli_sha_lo_wan_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,999.2,C\n"
        ),
    )
    assert main(["--sha-lo-wan-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Lo Wan",
        "date": "2026-08-31",
        "pressure_hpa": 999.2,
    }


def test_cli_sha_lo_wan_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-lo-wan-pressure"]) == 0
    assert capsys.readouterr().out == "No Sha Lo Wan pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-lo-wan-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Lo Wan pressure is available."
    }


def test_cli_shek_kong_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,999.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  998.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shek-kong-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SEK_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 石崗\n"
        "2026-08-31  998.7 hPa\n"
    )


def test_cli_shek_kong_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,998.7,C\n"
        ),
    )
    assert main(["--shek-kong-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shek Kong",
        "date": "2026-08-31",
        "pressure_hpa": 998.7,
    }


def test_cli_shek_kong_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shek-kong-pressure"]) == 0
    assert capsys.readouterr().out == "No Shek Kong pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shek-kong-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shek Kong pressure is available."
    }


def test_cli_ta_kwu_ling_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,999.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  998.7  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ta-kwu-ling-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TKL_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 打鼓嶺\n"
        "2026-08-31  998.7 hPa\n"
    )


def test_cli_ta_kwu_ling_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,998.7,C\n"
        ),
    )
    assert main(["--ta-kwu-ling-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ta Kwu Ling",
        "date": "2026-08-31",
        "pressure_hpa": 998.7,
    }


def test_cli_ta_kwu_ling_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ta-kwu-ling-pressure"]) == 0
    assert capsys.readouterr().out == "No Ta Kwu Ling pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ta-kwu-ling-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ta Kwu Ling pressure is available."
    }


def test_cli_airport_pressure_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,7,29,1010.5,C\n"
            "2026,7,30,***,\n"
            "2026,7,31,  1009.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--airport-pressure", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_MSLP_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean pressure\n"
        "Station: 香港國際機場\n"
        "2026-07-31  1009.4 hPa\n"
    )


def test_cli_airport_pressure_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,1009.4,C\n"
        ),
    )
    assert main(["--airport-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-07-31",
        "pressure_hpa": 1009.4,
    }


def test_cli_airport_pressure_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,***,\n"
        ),
    )
    assert main(["--airport-pressure"]) == 0
    assert capsys.readouterr().out == "No airport pressure is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--airport-pressure", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No airport pressure is available."
    }


def test_cli_minute_grass_prints_latest_stations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Automatic Weather Station,Grass Temperature(degree Celsius)\n"
            "202610040230,King's Park,  25.9  \n"
            "202610040230,Tai Mo Shan,N/A\n"
            "202610040230,Ta Kwu Ling,26.0\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--minute-grass", "--lang", "tc"]) == 0
    assert seen["url"].endswith("latest_1min_grass_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong 1-minute grass temperature\n"
        "Recorded: 2026-10-04 02:30\n"
        "King's Park  25.9°C\n"
        "Ta Kwu Ling  26°C\n"
    )


def test_cli_minute_grass_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Grass\n"
            "202610040230,Tai Mo Shan,21.5\n"
        ),
    )
    assert main(["--minute-grass", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 02:30",
        "stations": [{"place": "Tai Mo Shan", "grass_c": 21.5}],
    }


def test_cli_minute_grass_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Grass\n"
            "202610040230,Tai Mo Shan,N/A\n"
        ),
    )
    assert main(["--minute-grass"]) == 0
    assert capsys.readouterr().out == "No 1-minute grass temperatures are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--minute-grass", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No 1-minute grass temperatures are available."
    }


def test_cli_daily_grass_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,24.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  23.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--daily-grass", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_GMT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily grass temperature\n"
        "Station: 京士柏\n"
        "2026-08-31  23.9°C\n"
    )


def test_cli_daily_grass_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,23.9,C\n"
        ),
    )
    assert main(["--daily-grass", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "grass_c": 23.9,
    }


def test_cli_daily_grass_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--daily-grass"]) == 0
    assert capsys.readouterr().out == "No daily grass temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--daily-grass", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No daily grass temperature is available."
    }


def test_cli_obs_grass_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,28.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--obs-grass", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKO_GMT_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily grass temperature\n"
        "Station: 香港天文台\n"
        "2026-08-31  26.6°C\n"
    )


def test_cli_obs_grass_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.6,C\n"
        ),
    )
    assert main(["--obs-grass", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Observatory",
        "date": "2026-08-31",
        "grass_c": 26.6,
    }


def test_cli_obs_grass_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--obs-grass"]) == 0
    assert capsys.readouterr().out == "No Observatory grass temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--obs-grass", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Observatory grass temperature is available."
    }


def test_cli_temp_diff_prints_signed_changes(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Station,Past 24-hour Temperature Difference(degree Celsius)\n"
            "202610040240,Chek Lap Kok,  -0.6  \n"
            "202610040240,Clear Water Bay,N/A\n"
            "202610040240,HK Observatory,+0.4\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--temp-diff", "--lang", "tc"]) == 0
    assert seen["url"].endswith("latest_past24_temperature_diff_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong 24-hour temperature change\n"
        "Recorded: 2026-10-04 02:40\n"
        "Chek Lap Kok  -0.6°C\n"
        "HK Observatory  +0.4°C\n"
    )


def test_cli_temp_diff_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Difference\n"
            "202610040240,Chek Lap Kok,-0.6\n"
        ),
    )
    assert main(["--temp-diff", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 02:40",
        "stations": [{"place": "Chek Lap Kok", "change_c": -0.6}],
    }


def test_cli_temp_diff_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Difference\n"
            "202610040240,Clear Water Bay,N/A\n"
        ),
    )
    assert main(["--temp-diff"]) == 0
    assert capsys.readouterr().out == "No 24-hour temperature changes are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--temp-diff", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No 24-hour temperature changes are available."
    }


def test_cli_heat_index_prints_latest_minute(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Automatic Weather Station,10 minute mean Hong Kong Heat Index\n"
            "202610040251,Beas River,23.9\n"
            "202610040300,Happy Valley,  25.8  \n"
            "202610040300,Sha Tin,N/A\n"
            "202610040300,King's Park,25.1\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--heat-index", "--lang", "tc"]) == 0
    assert seen["url"].endswith("recent10_10min_hkhi_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong heat index\n"
        "Recorded: 2026-10-04 03:00\n"
        "Happy Valley  25.8\n"
        "King's Park  25.1\n"
    )


def test_cli_heat_index_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Index\n"
            "202610040300,Happy Valley,25.8\n"
        ),
    )
    assert main(["--heat-index", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 03:00",
        "stations": [{"place": "Happy Valley", "heat_index": 25.8}],
    }


def test_cli_heat_index_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Index\n"
            "202610040300,Sha Tin,N/A\n"
        ),
    )
    assert main(["--heat-index"]) == 0
    assert capsys.readouterr().out == "No heat index is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--heat-index", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No heat index is available."}


def test_cli_daily_heat_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,31.2,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  29.2  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--daily-heat", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_MAXHKHI_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily heat index\n"
        "Station: 京士柏\n"
        "2026-08-31  29.2\n"
    )


def test_cli_daily_heat_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,29.2,C\n"
        ),
    )
    assert main(["--daily-heat", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "heat_index": 29.2,
    }


def test_cli_daily_heat_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--daily-heat"]) == 0
    assert capsys.readouterr().out == "No daily maximum heat index is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--daily-heat", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No daily maximum heat index is available."
    }


def test_cli_mean_heat_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,29.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  26.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--mean-heat", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_MEANHKHI_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily mean heat index\n"
        "Station: 京士柏\n"
        "2026-08-31  26.6\n"
    )


def test_cli_mean_heat_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,26.6,C\n"
        ),
    )
    assert main(["--mean-heat", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "heat_index": 26.6,
    }


def test_cli_mean_heat_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--mean-heat"]) == 0
    assert capsys.readouterr().out == "No daily mean heat index is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--mean-heat", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No daily mean heat index is available."
    }


def test_cli_wbgt_prints_latest_minute(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Automatic Weather Station,60-minute mean Wet Bulb Globe Temperature (WBGT)\n"
            "202610040311,Beas River,23.9\n"
            "202610040320,Happy Valley,  25.8  \n"
            "202610040320,Sha Tin,N/A\n"
            "202610040320,King's Park,25.3\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wbgt", "--lang", "tc"]) == 0
    assert seen["url"].endswith("recent10_60min_wbgt_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong wet bulb globe temperature\n"
        "Recorded: 2026-10-04 03:20\n"
        "Happy Valley  25.8°C\n"
        "King's Park  25.3°C\n"
    )


def test_cli_wbgt_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,WBGT\n"
            "202610040320,Happy Valley,25.8\n"
        ),
    )
    assert main(["--wbgt", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 03:20",
        "stations": [{"place": "Happy Valley", "wbgt_c": 25.8}],
    }


def test_cli_wbgt_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,WBGT\n"
            "202610040320,Sha Tin,N/A\n"
        ),
    )
    assert main(["--wbgt"]) == 0
    assert capsys.readouterr().out == "No wet bulb globe temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wbgt", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No wet bulb globe temperature is available."
    }


def test_cli_wet_bulb_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,27,26.7,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.8  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wet-bulb", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKO_WET_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong wet bulb temperature\n"
        "Station: 香港天文台\n"
        "2026-08-31  25.8°C\n"
    )


def test_cli_wet_bulb_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.8,C\n"
        ),
    )
    assert main(["--wet-bulb", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Observatory",
        "date": "2026-08-31",
        "wet_bulb_c": 25.8,
    }


def test_cli_wet_bulb_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wet-bulb"]) == 0
    assert capsys.readouterr().out == "No wet bulb temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wet-bulb", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No wet bulb temperature is available."
    }


def test_cli_airport_wet_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,7,29,25.6,C\n"
            "2026,7,30,***,\n"
            "2026,7,31,  24.4  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--airport-wet", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_WET_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong wet bulb temperature\n"
        "Station: 香港國際機場\n"
        "2026-07-31  24.4°C\n"
    )


def test_cli_airport_wet_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,24.4,C\n"
        ),
    )
    assert main(["--airport-wet", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-07-31",
        "wet_bulb_c": 24.4,
    }


def test_cli_airport_wet_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,***,\n"
        ),
    )
    assert main(["--airport-wet"]) == 0
    assert capsys.readouterr().out == "No airport wet bulb temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--airport-wet", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No airport wet bulb temperature is available."
    }


def test_cli_park_wet_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,26.1,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--park-wet", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_WET_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong wet bulb temperature\n"
        "Station: 京士柏\n"
        "2026-08-31  25.6°C\n"
    )


def test_cli_park_wet_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.6,C\n"
        ),
    )
    assert main(["--park-wet", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "wet_bulb_c": 25.6,
    }


def test_cli_park_wet_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--park-wet"]) == 0
    assert capsys.readouterr().out == "No King's Park wet bulb temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--park-wet", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park wet bulb temperature is available."
    }


def test_cli_sha_lo_wan_wet_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,27.3,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.9  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-lo-wan-wet", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SLW_WET_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong wet bulb temperature\n"
        "Station: 沙螺灣\n"
        "2026-08-31  25.9°C\n"
    )


def test_cli_sha_lo_wan_wet_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.9,C\n"
        ),
    )
    assert main(["--sha-lo-wan-wet", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Lo Wan",
        "date": "2026-08-31",
        "wet_bulb_c": 25.9,
    }


def test_cli_sha_lo_wan_wet_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-lo-wan-wet"]) == 0
    assert capsys.readouterr().out == "No Sha Lo Wan wet bulb temperature is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-lo-wan-wet", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Lo Wan wet bulb temperature is available."
    }


def test_cli_solar_prints_latest_minute(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Date time,Automatic Weather Station,Global,Direct,Diffuse\n"
            "202610040400,Kau Sai Chau,0.0,0.0,0.0\n"
            "202610040410,Kau Sai Chau,  1.0  ,0.0,1.0\n"
            "202610040410,Sha Tin,N/A,N/A,N/A\n"
            "202610040410,King's Park,0.0,0.0,0.0\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--solar", "--lang", "tc"]) == 0
    assert seen["url"].endswith("latest_1min_solar_uc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong solar radiation\n"
        "Recorded: 2026-10-04 04:10\n"
        "Kau Sai Chau  global 1  direct 0  diffuse 1 W/m²\n"
        "King's Park  global 0  direct 0  diffuse 0 W/m²\n"
    )


def test_cli_solar_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Global,Direct,Diffuse\n"
            "202610040410,Kau Sai Chau,1.0,0.0,1.0\n"
        ),
    )
    assert main(["--solar", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-04 04:10",
        "stations": [
            {
                "place": "Kau Sai Chau",
                "global_w_m2": 1.0,
                "direct_w_m2": 0.0,
                "diffuse_w_m2": 1.0,
            }
        ],
    }


def test_cli_solar_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Date time,Station,Global,Direct,Diffuse\n"
            "202610040410,Sha Tin,N/A,0.0,0.0\n"
        ),
    )
    assert main(["--solar"]) == 0
    assert capsys.readouterr().out == "No solar radiation is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--solar", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No solar radiation is available."}


def test_cli_global_solar_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,21.73,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  8.95  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--global-solar", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_GSR_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong global solar radiation\n"
        "Station: 京士柏\n"
        "2026-08-31  8.95 MJ/m²\n"
    )


def test_cli_global_solar_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,8.95,C\n"
        ),
    )
    assert main(["--global-solar", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "global_solar_mj_m2": 8.95,
    }


def test_cli_global_solar_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--global-solar"]) == 0
    assert capsys.readouterr().out == "No global solar radiation is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--global-solar", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No global solar radiation is available."
    }


def test_cli_temp_time_prints_timestamp(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "temperature": {
                    "recordTime": "  2026-10-03T16:00:00+08:00  ",
                    "data": [{"place": "Hong Kong Observatory", "value": 28, "unit": "C"}],
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--temp-time", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong temperature time\n2026-10-03T16:00:00+08:00\n"


def test_cli_temp_time_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"temperature": {"recordTime": "2026-10-03T16:00:00+08:00", "data": []}}
        ),
    )
    assert main(["--temp-time", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"recorded": "2026-10-03T16:00:00+08:00"}


def test_cli_temp_time_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"temperature": [{"place": "Hong Kong Observatory", "value": 28}]}
        ),
    )
    assert main(["--temp-time"]) == 0
    assert capsys.readouterr().out == "No temperature time is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"temperature": {"recordTime": "  ", "data": []}}),
    )
    assert main(["--temp-time", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No temperature time is available."}


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


def test_cli_coldest_prints_coolest_place(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "temperature": {
                    "recordTime": "2026-10-02T23:00:00+08:00",
                    "data": [
                        {"place": "Hong Kong Observatory", "value": 28, "unit": "C"},
                        {"place": "Tai Mo Shan", "value": 18, "unit": "C"},
                        {"place": "Ngong Ping", "value": 18, "unit": "C"},
                        {"place": "Tai Po", "unit": "C"},
                    ],
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-C", "--lang", "sc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=sc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong coldest\n"
        "Recorded: 2026-10-02T23:00:00+08:00\n"
        "Tai Mo Shan  18°C\n"
    )
    assert "Ngong Ping" not in out
    assert "28°C" not in out


def test_cli_coldest_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "temperature": {
                    "recordTime": "2026-10-02T23:00:00+08:00",
                    "data": [
                        {"place": "King's Park", "value": 31, "unit": "C"},
                        {"place": "Tai Mo Shan", "value": 18, "unit": "C"},
                    ],
                }
            }
        ),
    )
    assert main(["--coldest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "record_time": "2026-10-02T23:00:00+08:00",
        "place": "Tai Mo Shan",
        "temperature_c": 18.0,
    }


def test_cli_overnight_prints_minimum(monkeypatch, capsys):
    seen = {}
    message = (
        "The minimum temperature recorded at the Hong Kong Observatory "
        "between midnight and 9 am today was 25.3 degrees."
    )

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"mintempFrom00To09": f"  {message}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--overnight", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong overnight minimum\n{message}\n"


def test_cli_overnight_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"mintempFrom00To09": "The minimum temperature was 24 degrees."}
        ),
    )
    assert main(["-O", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "report": "The minimum temperature was 24 degrees."
    }


def test_cli_noon_rain_prints_note(monkeypatch, capsys):
    seen = {}
    message = (
        "The rainfall recorded at the Hong Kong Observatory between midnight "
        "and noon today was less than 0.5 millimetres."
    )

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"rainfallFrom00To12": f"  {message}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--noon-rain", "--lang", "sc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=sc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong noon rainfall\n{message}\n"


def test_cli_noon_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"rainfallFrom00To12": "Rainfall between midnight and noon was 12.4 millimetres."}
        ),
    )
    assert main(["-N", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "report": "Rainfall between midnight and noon was 12.4 millimetres."
    }


def test_cli_noon_rain_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"rainfallFrom00To12": "   "}),
    )
    assert main(["--noon-rain"]) == 0
    assert capsys.readouterr().out == "No noon rainfall note is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--noon-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No noon rainfall note is available."
    }


def test_cli_month_rain_prints_note(monkeypatch, capsys):
    seen = {}
    message = (
        "The rainfall recorded at the Hong Kong Observatory in September "
        "was 245.8 millimetres, about 25 percent below the normal of 327.6 millimetres."
    )

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"rainfallLastMonth": f"  {message}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--month-rain", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong last month rainfall\n{message}\n"


def test_cli_month_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"rainfallLastMonth": "September rainfall was 245.8 millimetres."}
        ),
    )
    assert main(["-L", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "report": "September rainfall was 245.8 millimetres."
    }


def test_cli_month_rain_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"rainfallLastMonth": "   "}),
    )
    assert main(["--month-rain"]) == 0
    assert capsys.readouterr().out == "No last-month rainfall note is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--month-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No last-month rainfall note is available."
    }


def test_cli_year_rain_prints_note(monkeypatch, capsys):
    seen = {}
    message = (
        "The accumulated rainfall recorded at the Hong Kong Observatory from January "
        "to September was 1864.3 millimetres, about 25 percent below the normal."
    )

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"rainfallJanuaryToLastMonth": f"  {message}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--year-rain", "--lang", "sc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=sc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong year-to-date rainfall\n{message}\n"


def test_cli_year_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"rainfallJanuaryToLastMonth": "January to September rainfall was 1864.3 millimetres."}
        ),
    )
    assert main(["-y", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "report": "January to September rainfall was 1864.3 millimetres."
    }


def test_cli_year_rain_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"rainfallJanuaryToLastMonth": "   "}),
    )
    assert main(["--year-rain"]) == 0
    assert capsys.readouterr().out == "No year-to-date rainfall note is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--year-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No year-to-date rainfall note is available."
    }


def test_cli_overnight_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"mintempFrom00To09": "   "}),
    )
    assert main(["--overnight"]) == 0
    assert capsys.readouterr().out == "No overnight minimum is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--overnight", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No overnight minimum is available."
    }


def test_cli_coldest_when_no_readings(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"temperature": ""}),
    )
    assert main(["--coldest"]) == 0
    assert capsys.readouterr().out == "No temperature readings are available.\n"
    assert main(["--coldest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No temperature readings are available."
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


def test_cli_humidest_prints_dampest_place(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "humidity": {
                    "recordTime": "2026-10-03T02:00:00+08:00",
                    "data": [
                        {"place": "King's Park", "value": 80, "unit": "percent"},
                        {"place": "Chek Lap Kok", "value": 95, "unit": "percent"},
                        {"place": "Sha Tin", "value": 95, "unit": "percent"},
                        {"place": "Tai Po", "unit": "percent"},
                    ],
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--humidest", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong humidest\n"
        "Recorded: 2026-10-03T02:00:00+08:00\n"
        "Chek Lap Kok  95%\n"
    )
    assert "Sha Tin" not in out
    assert "80%" not in out


def test_cli_humidest_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "humidity": {
                    "recordTime": "2026-10-03T02:00:00+08:00",
                    "data": [
                        {"place": "King's Park", "value": 80, "unit": "percent"},
                        {"place": "Chek Lap Kok", "value": 95, "unit": "percent"},
                    ],
                }
            }
        ),
    )
    assert main(["--humidest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "record_time": "2026-10-03T02:00:00+08:00",
        "place": "Chek Lap Kok",
        "humidity_percent": 95.0,
    }


def test_cli_humidest_when_no_reading(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"humidity": ""}),
    )
    assert main(["--humidest"]) == 0
    assert capsys.readouterr().out == "No humidity reading is available.\n"
    assert main(["--humidest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No humidity reading is available."
    }


def test_cli_least_humid_prints_driest_place(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "humidity": {
                    "recordTime": "2026-10-03T02:00:00+08:00",
                    "data": [
                        {"place": "Chek Lap Kok", "value": 95, "unit": "percent"},
                        {"place": "King's Park", "value": 80, "unit": "percent"},
                        {"place": "Sha Tin", "value": 80, "unit": "percent"},
                        {"place": "Tai Po", "unit": "percent"},
                    ],
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--least-humid", "--lang", "sc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=sc" in seen["url"]
    out = capsys.readouterr().out
    assert out == (
        "Hong Kong least humid\n"
        "Recorded: 2026-10-03T02:00:00+08:00\n"
        "King's Park  80%\n"
    )
    assert "Sha Tin" not in out
    assert "95%" not in out


def test_cli_least_humid_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "humidity": {
                    "recordTime": "2026-10-03T02:00:00+08:00",
                    "data": [
                        {"place": "Chek Lap Kok", "value": 95, "unit": "percent"},
                        {"place": "King's Park", "value": 80, "unit": "percent"},
                    ],
                }
            }
        ),
    )
    assert main(["--least-humid", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "record_time": "2026-10-03T02:00:00+08:00",
        "place": "King's Park",
        "humidity_percent": 80.0,
    }


def test_cli_least_humid_when_no_reading(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"humidity": ""}),
    )
    assert main(["--least-humid"]) == 0
    assert capsys.readouterr().out == "No humidity reading is available.\n"
    assert main(["--least-humid", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No humidity reading is available."
    }


def test_cli_humidity_when_no_reading(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"humidity": ""}),
    )
    assert main(["--humidity"]) == 0
    assert capsys.readouterr().out == "No humidity reading is available.\n"


def test_cli_humidity_time_prints_timestamp(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "humidity": {
                    "recordTime": "  2026-10-03T16:00:00+08:00  ",
                    "data": [{"place": "Hong Kong Observatory", "value": 80, "unit": "percent"}],
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--humidity-time", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == "Hong Kong humidity time\n2026-10-03T16:00:00+08:00\n"


def test_cli_humidity_time_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"humidity": {"recordTime": "2026-10-03T16:00:00+08:00", "data": []}}
        ),
    )
    assert main(["--humidity-time", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"recorded": "2026-10-03T16:00:00+08:00"}


def test_cli_humidity_time_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"humidity": [{"place": "Hong Kong Observatory", "value": 80}]}
        ),
    )
    assert main(["--humidity-time"]) == 0
    assert capsys.readouterr().out == "No humidity time is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"humidity": {"recordTime": "  ", "data": []}}),
    )
    assert main(["--humidity-time", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No humidity time is available."}


def test_cli_wettest_prints_wettest_district(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "rainfall": {
                    "data": [
                        {"place": "Wan Chai", "max": 2, "unit": "mm"},
                        {"place": "Sai Kung", "max": 12, "unit": "mm"},
                        {"place": "North District", "max": 12, "unit": "mm"},
                        {"place": "Islands District", "unit": "mm"},
                    ]
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-R", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    out = capsys.readouterr().out
    assert out == "Hong Kong wettest\nSai Kung  12 mm\n"
    assert "North District" not in out
    assert "Wan Chai" not in out


def test_cli_wettest_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "rainfall": {
                    "data": [
                        {"place": "Wan Chai", "max": 2, "unit": "mm"},
                        {"place": "Sai Kung", "max": 12, "unit": "mm"},
                    ]
                }
            }
        ),
    )
    assert main(["--wettest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "place": "Sai Kung",
        "rainfall_mm": 12.0,
    }


def test_cli_wettest_when_no_readings(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"rainfall": ""}),
    )
    assert main(["--wettest"]) == 0
    assert capsys.readouterr().out == "No rainfall readings are available.\n"
    assert main(["--wettest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No rainfall readings are available."
    }


def test_cli_driest_prints_driest_district(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "rainfall": {
                    "data": [
                        {"place": "Sai Kung", "max": 12, "unit": "mm"},
                        {"place": "Central & Western", "max": 0, "unit": "mm"},
                        {"place": "Wan Chai", "max": 0, "unit": "mm"},
                        {"place": "Islands District", "unit": "mm"},
                    ]
                }
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["-D", "--lang", "sc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=sc" in seen["url"]
    out = capsys.readouterr().out
    assert out == "Hong Kong driest\nCentral & Western  0 mm\n"
    assert "Wan Chai" not in out
    assert "Sai Kung" not in out


def test_cli_driest_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "rainfall": {
                    "data": [
                        {"place": "Sai Kung", "max": 12, "unit": "mm"},
                        {"place": "Central & Western", "max": 0, "unit": "mm"},
                    ]
                }
            }
        ),
    )
    assert main(["--driest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "place": "Central & Western",
        "rainfall_mm": 0.0,
    }


def test_cli_driest_when_no_readings(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"rainfall": ""}),
    )
    assert main(["--driest"]) == 0
    assert capsys.readouterr().out == "No rainfall readings are available.\n"
    assert main(["--driest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No rainfall readings are available."
    }


def test_cli_nowcast_prints_heaviest_cells(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "Updated,Ending,Latitude,Longitude,Rainfall\n"
            "202610040624,202610040654,23.487,112.956,0.00\n"
            "202610040624,202610040724,22.200,114.100,1.50\n"
            "202610040624,202610040724,22.300,114.200,1.20\n"
            "202610040624,202610040824,22.178,115.272,80.44\n"
            "202610040624,202610040824,22.100,115.100,80.44\n"
            "202610040624,202610040824,22.000,115.000,N/A\n"
            "0\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--nowcast", "--lang", "tc"]) == 0
    assert seen["url"].endswith("Gridded_rainfall_nowcast_tc.csv")
    assert capsys.readouterr().out == (
        "Hong Kong rainfall nowcast\n"
        "Updated: 2026-10-04 06:24\n"
        "2026-10-04 06:54  23.487°N  112.956°E  0 mm\n"
        "2026-10-04 07:24  22.2°N  114.1°E  1.5 mm\n"
        "2026-10-04 08:24  22.178°N  115.272°E  80.44 mm\n"
    )


def test_cli_nowcast_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Updated,Ending,Latitude,Longitude,Rainfall\n"
            "202610040624,202610040824,22.178,115.272,80.44\n"
        ),
    )
    assert main(["--nowcast", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "updated": "2026-10-04 06:24",
        "periods": [
            {
                "ending": "2026-10-04 08:24",
                "latitude": 22.178,
                "longitude": 115.272,
                "rainfall_mm": 80.44,
            }
        ],
    }


def test_cli_nowcast_when_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Updated,Ending,Latitude,Longitude,Rainfall\n"
            "202610040624,202610040654,22.178,115.272,N/A\n"
        ),
    )
    assert main(["--nowcast"]) == 0
    assert capsys.readouterr().out == "No rainfall nowcast is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--nowcast", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No rainfall nowcast is available."
    }


def test_cli_daily_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,12.4,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  25.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--daily-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKO_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 香港天文台\n"
        "2026-08-31  25 mm\n"
    )


def test_cli_daily_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,25.0,C\n"
        ),
    )
    assert main(["--daily-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong Observatory",
        "date": "2026-08-31",
        "rainfall_mm": 25.0,
    }


def test_cli_daily_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--daily-rain"]) == 0
    assert capsys.readouterr().out == "No daily rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--daily-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No daily rainfall is available."
    }


def test_cli_lau_fau_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,2.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  40.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--lau-fau-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_LFS_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 流浮山\n"
        "2026-08-31  40 mm\n"
    )


def test_cli_lau_fau_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,40.0,C\n"
        ),
    )
    assert main(["--lau-fau-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Lau Fau Shan",
        "date": "2026-08-31",
        "rainfall_mm": 40.0,
    }


def test_cli_lau_fau_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--lau-fau-rain"]) == 0
    assert capsys.readouterr().out == "No Lau Fau Shan rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--lau-fau-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Lau Fau Shan rainfall is available."
    }


def test_cli_shek_kong_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,1.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  24.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shek-kong-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SEK_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 石崗\n"
        "2026-08-31  24.5 mm\n"
    )


def test_cli_shek_kong_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,24.5,C\n"
        ),
    )
    assert main(["--shek-kong-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shek Kong",
        "date": "2026-08-31",
        "rainfall_mm": 24.5,
    }


def test_cli_shek_kong_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shek-kong-rain"]) == 0
    assert capsys.readouterr().out == "No Shek Kong rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shek-kong-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shek Kong rainfall is available."
    }


def test_cli_wetland_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  55.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--wetland-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WLP_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 濕地公園\n"
        "2026-08-31  55.5 mm\n"
    )


def test_cli_wetland_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,55.5,C\n"
        ),
    )
    assert main(["--wetland-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Wetland Park",
        "date": "2026-08-31",
        "rainfall_mm": 55.5,
    }


def test_cli_wetland_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--wetland-rain"]) == 0
    assert capsys.readouterr().out == "No Wetland Park rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--wetland-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Wetland Park rainfall is available."
    }


def test_cli_sham_shui_po_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  35.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sham-shui-po-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSP_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 深水埗\n"
        "2026-08-31  35 mm\n"
    )


def test_cli_sham_shui_po_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,35.0,C\n"
        ),
    )
    assert main(["--sham-shui-po-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sham Shui Po",
        "date": "2026-08-31",
        "rainfall_mm": 35.0,
    }


def test_cli_sham_shui_po_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sham-shui-po-rain"]) == 0
    assert capsys.readouterr().out == "No Sham Shui Po rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sham-shui-po-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sham Shui Po rainfall is available."
    }


def test_cli_park_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  33.1  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--park-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_KP_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 京士柏\n"
        "2026-08-31  33.1 mm\n"
    )


def test_cli_park_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,33.1,C\n"
        ),
    )
    assert main(["--park-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "King's Park",
        "date": "2026-08-31",
        "rainfall_mm": 33.1,
    }


def test_cli_park_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--park-rain"]) == 0
    assert capsys.readouterr().out == "No King's Park rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--park-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No King's Park rainfall is available."
    }


def test_cli_tseung_kwan_o_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  14.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tseung-kwan-o-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_JKB_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 將軍澳\n"
        "2026-08-31  14.5 mm\n"
    )


def test_cli_tseung_kwan_o_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,14.5,C\n"
        ),
    )
    assert main(["--tseung-kwan-o-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tseung Kwan O",
        "date": "2026-08-31",
        "rainfall_mm": 14.5,
    }


def test_cli_tseung_kwan_o_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tseung-kwan-o-rain"]) == 0
    assert capsys.readouterr().out == "No Tseung Kwan O rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tseung-kwan-o-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tseung Kwan O rainfall is available."
    }


def test_cli_sheung_shui_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,2.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  19.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sheung-shui-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SSH_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 上水\n"
        "2026-08-31  19.5 mm\n"
    )


def test_cli_sheung_shui_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,19.5,C\n"
        ),
    )
    assert main(["--sheung-shui-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sheung Shui",
        "date": "2026-08-31",
        "rainfall_mm": 19.5,
    }


def test_cli_sheung_shui_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sheung-shui-rain"]) == 0
    assert capsys.readouterr().out == "No Sheung Shui rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sheung-shui-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sheung Shui rainfall is available."
    }


def test_cli_sha_tin_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  7.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-tin-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SHA_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 沙田\n"
        "2026-08-31  7 mm\n"
    )


def test_cli_sha_tin_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,7.0,C\n"
        ),
    )
    assert main(["--sha-tin-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Tin",
        "date": "2026-08-31",
        "rainfall_mm": 7.0,
    }


def test_cli_sha_tin_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-tin-rain"]) == 0
    assert capsys.readouterr().out == "No Sha Tin rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-tin-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Tin rainfall is available."
    }


def test_cli_ta_kwu_ling_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,2.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  13.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ta-kwu-ling-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TKL_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 打鼓嶺\n"
        "2026-08-31  13 mm\n"
    )


def test_cli_ta_kwu_ling_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,13.0,C\n"
        ),
    )
    assert main(["--ta-kwu-ling-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ta Kwu Ling",
        "date": "2026-08-31",
        "rainfall_mm": 13.0,
    }


def test_cli_ta_kwu_ling_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ta-kwu-ling-rain"]) == 0
    assert capsys.readouterr().out == "No Ta Kwu Ling rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ta-kwu-ling-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ta Kwu Ling rainfall is available."
    }


def test_cli_cheung_chau_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,15.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  2.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cheung-chau-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CCH_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 長洲\n"
        "2026-08-31  2.5 mm\n"
    )


def test_cli_cheung_chau_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,2.5,C\n"
        ),
    )
    assert main(["--cheung-chau-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Cheung Chau",
        "date": "2026-08-31",
        "rainfall_mm": 2.5,
    }


def test_cli_cheung_chau_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--cheung-chau-rain"]) == 0
    assert capsys.readouterr().out == "No Cheung Chau rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--cheung-chau-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Cheung Chau rainfall is available."
    }


def test_cli_waglan_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  1.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--waglan-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_WGL_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 橫瀾島\n"
        "2026-08-31  1.5 mm\n"
    )


def test_cli_waglan_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,1.5,C\n"
        ),
    )
    assert main(["--waglan-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Waglan Island",
        "date": "2026-08-31",
        "rainfall_mm": 1.5,
    }


def test_cli_waglan_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--waglan-rain"]) == 0
    assert capsys.readouterr().out == "No Waglan Island rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--waglan-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Waglan Island rainfall is available."
    }


def test_cli_tate_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  5.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tate-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TC_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 大老山\n"
        "2026-08-31  5.5 mm\n"
    )


def test_cli_tate_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,5.5,C\n"
        ),
    )
    assert main(["--tate-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tate's Cairn",
        "date": "2026-08-31",
        "rainfall_mm": 5.5,
    }


def test_cli_tate_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tate-rain"]) == 0
    assert capsys.readouterr().out == "No Tate's Cairn rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tate-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tate's Cairn rainfall is available."
    }


def test_cli_peng_chau_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  8.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--peng-chau-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_PEN_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 坪洲\n"
        "2026-08-31  8.5 mm\n"
    )


def test_cli_peng_chau_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,8.5,C\n"
        ),
    )
    assert main(["--peng-chau-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Peng Chau",
        "date": "2026-08-31",
        "rainfall_mm": 8.5,
    }


def test_cli_peng_chau_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--peng-chau-rain"]) == 0
    assert capsys.readouterr().out == "No Peng Chau rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--peng-chau-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Peng Chau rainfall is available."
    }


def test_cli_ping_chau_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,1.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  9.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--ping-chau-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_EPC_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 平洲\n"
        "2026-08-31  9.5 mm\n"
    )


def test_cli_ping_chau_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,9.5,C\n"
        ),
    )
    assert main(["--ping-chau-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Ping Chau",
        "date": "2026-08-31",
        "rainfall_mm": 9.5,
    }


def test_cli_ping_chau_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--ping-chau-rain"]) == 0
    assert capsys.readouterr().out == "No Ping Chau rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--ping-chau-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Ping Chau rainfall is available."
    }


def test_cli_tai_mo_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  15.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mo-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TMS_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 大帽山\n"
        "2026-08-31  15.5 mm\n"
    )


def test_cli_tai_mo_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,15.5,C\n"
        ),
    )
    assert main(["--tai-mo-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mo Shan",
        "date": "2026-08-31",
        "rainfall_mm": 15.5,
    }


def test_cli_tai_mo_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mo-rain"]) == 0
    assert capsys.readouterr().out == "No Tai Mo Shan rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mo-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mo Shan rainfall is available."
    }


def test_cli_sha_lo_wan_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  4.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--sha-lo-wan-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SLW_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 沙螺灣\n"
        "2026-08-31  4 mm\n"
    )


def test_cli_sha_lo_wan_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,4.0,C\n"
        ),
    )
    assert main(["--sha-lo-wan-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Sha Lo Wan",
        "date": "2026-08-31",
        "rainfall_mm": 4.0,
    }


def test_cli_sha_lo_wan_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--sha-lo-wan-rain"]) == 0
    assert capsys.readouterr().out == "No Sha Lo Wan rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--sha-lo-wan-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Sha Lo Wan rainfall is available."
    }


def test_cli_airport_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,7,29,57.7,C\n"
            "2026,7,30,***,\n"
            "2026,7,31,  25.6  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--airport-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HKA_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 香港國際機場\n"
        "2026-07-31  25.6 mm\n"
    )


def test_cli_airport_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,25.6,C\n"
        ),
    )
    assert main(["--airport-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Hong Kong International Airport",
        "date": "2026-07-31",
        "rainfall_mm": 25.6,
    }


def test_cli_airport_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,7,31,***,\n"
        ),
    )
    assert main(["--airport-rain"]) == 0
    assert capsys.readouterr().out == "No airport rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--airport-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No airport rainfall is available."
    }


def test_cli_green_island_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,1.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  31.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--green-island-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_GI_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 青洲\n"
        "2026-08-31  31.5 mm\n"
    )


def test_cli_green_island_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,31.5,C\n"
        ),
    )
    assert main(["--green-island-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Green Island",
        "date": "2026-08-31",
        "rainfall_mm": 31.5,
    }


def test_cli_green_island_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--green-island-rain"]) == 0
    assert capsys.readouterr().out == "No Green Island rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--green-island-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Green Island rainfall is available."
    }


def test_cli_tsuen_wan_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,0.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  22.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tsuen-wan-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TWN_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 荃灣\n"
        "2026-08-31  22 mm\n"
    )


def test_cli_tsuen_wan_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,22.0,C\n"
        ),
    )
    assert main(["--tsuen-wan-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tsuen Wan",
        "date": "2026-08-31",
        "rainfall_mm": 22.0,
    }


def test_cli_tsuen_wan_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tsuen-wan-rain"]) == 0
    assert capsys.readouterr().out == "No Tsuen Wan rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tsuen-wan-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tsuen Wan rainfall is available."
    }


def test_cli_tap_mun_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,1.5,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  4.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tap-mun-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_TAP_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 塔門\n"
        "2026-08-31  4 mm\n"
    )


def test_cli_tap_mun_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,4.0,C\n"
        ),
    )
    assert main(["--tap-mun-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tap Mun",
        "date": "2026-08-31",
        "rainfall_mm": 4.0,
    }


def test_cli_tap_mun_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tap-mun-rain"]) == 0
    assert capsys.readouterr().out == "No Tap Mun rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tap-mun-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tap Mun rainfall is available."
    }


def test_cli_clear_water_bay_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,3.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  7.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--clear-water-bay-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_CWB_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 清水灣\n"
        "2026-08-31  7 mm\n"
    )


def test_cli_clear_water_bay_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,7.0,C\n"
        ),
    )
    assert main(["--clear-water-bay-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Clear Water Bay",
        "date": "2026-08-31",
        "rainfall_mm": 7.0,
    }


def test_cli_clear_water_bay_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--clear-water-bay-rain"]) == 0
    assert capsys.readouterr().out == (
        "No Clear Water Bay rainfall is available.\n"
    )
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--clear-water-bay-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Clear Water Bay rainfall is available."
    }


def test_cli_shau_kei_wan_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,12.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  31.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--shau-kei-wan-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_SKW_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 筲箕灣\n"
        "2026-08-31  31.5 mm\n"
    )
    assert main(["--shau-kei-wan-rain", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 筲箕湾\n"
        "2026-08-31  31.5 mm\n"
    )


def test_cli_shau_kei_wan_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,31.5,C\n"
        ),
    )
    assert main(["--shau-kei-wan-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Shau Kei Wan",
        "date": "2026-08-31",
        "rainfall_mm": 31.5,
    }


def test_cli_shau_kei_wan_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--shau-kei-wan-rain"]) == 0
    assert capsys.readouterr().out == "No Shau Kei Wan rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--shau-kei-wan-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Shau Kei Wan rainfall is available."
    }


def test_cli_happy_valley_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,8.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  14.5  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--happy-valley-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_HPV_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 跑馬地\n"
        "2026-08-31  14.5 mm\n"
    )
    assert main(["--happy-valley-rain", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 跑马地\n"
        "2026-08-31  14.5 mm\n"
    )


def test_cli_happy_valley_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,14.5,C\n"
        ),
    )
    assert main(["--happy-valley-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Happy Valley",
        "date": "2026-08-31",
        "rainfall_mm": 14.5,
    }


def test_cli_happy_valley_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--happy-valley-rain"]) == 0
    assert capsys.readouterr().out == "No Happy Valley rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--happy-valley-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Happy Valley rainfall is available."
    }


def test_cli_tai_mei_tuk_rain_prints_latest_day(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _text_response(
            "年/Year,月/Month,日/Day,數值/Value,數據完整性/data Completeness\n"
            "2026,8,29,4.0,C\n"
            "2026,8,30,***,\n"
            "2026,8,31,  16.0  ,C\n"
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--tai-mei-tuk-rain", "--lang", "tc"]) == 0
    assert seen["url"].endswith("daily_PLC_RF_2026.csv")
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 大美督\n"
        "2026-08-31  16 mm\n"
    )
    assert main(["--tai-mei-tuk-rain", "--lang", "sc"]) == 0
    assert capsys.readouterr().out == (
        "Hong Kong daily rainfall\n"
        "Station: 大美督\n"
        "2026-08-31  16 mm\n"
    )


def test_cli_tai_mei_tuk_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,16.0,C\n"
        ),
    )
    assert main(["--tai-mei-tuk-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "station": "Tai Mei Tuk",
        "date": "2026-08-31",
        "rainfall_mm": 16.0,
    }


def test_cli_tai_mei_tuk_rain_when_missing(monkeypatch, capsys):
    monkeypatch.setattr("hk_weather.hko._hong_kong_today", lambda now=None: "2026-10-03")
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(
            "Year,Month,Day,Value,Completeness\n"
            "2026,8,31,***,\n"
        ),
    )
    assert main(["--tai-mei-tuk-rain"]) == 0
    assert capsys.readouterr().out == "No Tai Mei Tuk rainfall is available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _text_response(""),
    )
    assert main(["--tai-mei-tuk-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No Tai Mei Tuk rainfall is available."
    }


def test_cli_rainstorm_prints_reminder(monkeypatch, capsys):
    seen = {}
    message = (
        "Though the rainstorm warning has been cancelled, showers are still expected."
    )

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"rainstormReminder": f"  {message}  "})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--rainstorm", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == f"Hong Kong rainstorm reminder\n{message}\n"


def test_cli_rainstorm_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"rainstormReminder": "Showers may still be heavy."}
        ),
    )
    assert main(["--rainstorm", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "reminder": "Showers may still be heavy."
    }


def test_cli_cyclone_prints_messages(monkeypatch, capsys):
    seen = {}
    first = "At noon, Typhoon Mangkhut was centred about 510 kilometres southeast of Hong Kong."
    second = "It is forecast to move west-northwest at about 22 kilometres per hour."

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response({"tcmessage": [f"  {first}  ", {"message": second}, ""]})

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--cyclone", "--lang", "tc"]) == 0
    assert "dataType=rhrread" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong tropical cyclone\n"
        f"- {first}\n"
        f"- {second}\n"
    )


def test_cli_cyclone_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {"tcmessage": "  Tropical Cyclone Warning Bulletin.  "}
        ),
    )
    assert main(["-c", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "messages": ["Tropical Cyclone Warning Bulletin."]
    }


def test_cli_cyclone_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"tcmessage": ""}),
    )
    assert main(["--cyclone"]) == 0
    assert capsys.readouterr().out == "No tropical cyclone message.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--cyclone", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No tropical cyclone message."}


def test_cli_rainstorm_when_blank_or_missing(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"rainstormReminder": "   "}),
    )
    assert main(["--rainstorm"]) == 0
    assert capsys.readouterr().out == "No rainstorm reminder.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--rainstorm", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"message": "No rainstorm reminder."}


def test_cli_hour_rain_prints_stations(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "obsTime": "2026-10-03T15:00:00+08:00",
                "hourlyRainfall": [
                    {
                        "automaticWeatherStation": "Lau Fau Shan",
                        "automaticWeatherStationID": "RF001",
                        "value": "0",
                        "unit": "mm",
                    },
                    {
                        "automaticWeatherStation": "Wetland Park",
                        "automaticWeatherStationID": "RF002",
                        "value": "2",
                        "unit": "mm",
                    },
                    {
                        "automaticWeatherStation": "Wetland Park",
                        "automaticWeatherStationID": "DUP",
                        "value": "9",
                        "unit": "mm",
                    },
                    {
                        "automaticWeatherStation": "Shek Kong",
                        "automaticWeatherStationID": "RF003",
                        "value": "M",
                        "unit": "mm",
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--hour-rain", "--lang", "sc"]) == 0
    assert "hourlyRainfall.php" in seen["url"]
    assert "lang=sc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong hourly rainfall\n"
        "Recorded: 2026-10-03T15:00:00+08:00\n"
        "Wetland Park  2 mm\n"
        "Lau Fau Shan  0 mm\n"
    )


def test_cli_hour_rain_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "obsTime": "2026-10-03T15:00:00+08:00",
                "hourlyRainfall": [
                    {
                        "automaticWeatherStation": "Sai Kung",
                        "automaticWeatherStationID": "N15",
                        "value": "1.5",
                        "unit": "mm",
                    }
                ],
            }
        ),
    )
    assert main(["--hour-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-03T15:00:00+08:00",
        "readings": [
            {"place": "Sai Kung", "station_id": "N15", "rainfall_mm": 1.5},
        ],
    }


def test_cli_hour_rain_when_none_available(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "obsTime": "2026-10-03T15:00:00+08:00",
                "hourlyRainfall": [
                    {
                        "automaticWeatherStation": "Shek Kong",
                        "automaticWeatherStationID": "RF003",
                        "value": "M",
                        "unit": "mm",
                    }
                ],
            }
        ),
    )
    assert main(["--hour-rain"]) == 0
    assert capsys.readouterr().out == "No hourly rainfall readings are available.\n"
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({}),
    )
    assert main(["--hour-rain", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No hourly rainfall readings are available."
    }


def test_cli_hour_wettest_prints_top_station(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "obsTime": "2026-10-03T15:00:00+08:00",
                "hourlyRainfall": [
                    {
                        "automaticWeatherStation": "Wetland Park",
                        "automaticWeatherStationID": "RF002",
                        "value": "2",
                        "unit": "mm",
                    },
                    {
                        "automaticWeatherStation": "Lau Fau Shan",
                        "automaticWeatherStationID": "RF001",
                        "value": "2",
                        "unit": "mm",
                    },
                    {
                        "automaticWeatherStation": "Shek Kong",
                        "automaticWeatherStationID": "RF003",
                        "value": "M",
                        "unit": "mm",
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--hour-wettest", "--lang", "tc"]) == 0
    assert "hourlyRainfall.php" in seen["url"]
    assert "lang=tc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong hourly wettest\n"
        "Recorded: 2026-10-03T15:00:00+08:00\n"
        "Wetland Park  2 mm\n"
    )


def test_cli_hour_wettest_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "obsTime": "2026-10-03T15:00:00+08:00",
                "hourlyRainfall": [
                    {
                        "automaticWeatherStation": "Lau Fau Shan",
                        "automaticWeatherStationID": "RF001",
                        "value": "0",
                        "unit": "mm",
                    },
                    {
                        "automaticWeatherStation": "Sai Kung",
                        "automaticWeatherStationID": "N15",
                        "value": "4",
                        "unit": "mm",
                    },
                ],
            }
        ),
    )
    assert main(["--hour-wettest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-03T15:00:00+08:00",
        "place": "Sai Kung",
        "station_id": "N15",
        "rainfall_mm": 4.0,
    }


def test_cli_hour_wettest_when_none_available(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"hourlyRainfall": []}),
    )
    assert main(["--hour-wettest"]) == 0
    assert capsys.readouterr().out == "No hourly rainfall readings are available.\n"
    assert main(["--hour-wettest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No hourly rainfall readings are available."
    }


def test_cli_hour_driest_prints_lowest_station(monkeypatch, capsys):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return _json_response(
            {
                "obsTime": "2026-10-03T15:00:00+08:00",
                "hourlyRainfall": [
                    {
                        "automaticWeatherStation": "Wetland Park",
                        "automaticWeatherStationID": "RF002",
                        "value": "2",
                        "unit": "mm",
                    },
                    {
                        "automaticWeatherStation": "Lau Fau Shan",
                        "automaticWeatherStationID": "RF001",
                        "value": "0",
                        "unit": "mm",
                    },
                    {
                        "automaticWeatherStation": "Cheung Chau",
                        "automaticWeatherStationID": "RF011",
                        "value": "0",
                        "unit": "mm",
                    },
                    {
                        "automaticWeatherStation": "Shek Kong",
                        "automaticWeatherStationID": "RF003",
                        "value": "M",
                        "unit": "mm",
                    },
                ],
            }
        )

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", fake_urlopen)
    assert main(["--hour-driest", "--lang", "sc"]) == 0
    assert "hourlyRainfall.php" in seen["url"]
    assert "lang=sc" in seen["url"]
    assert capsys.readouterr().out == (
        "Hong Kong hourly driest\n"
        "Recorded: 2026-10-03T15:00:00+08:00\n"
        "Lau Fau Shan  0 mm\n"
    )


def test_cli_hour_driest_json_is_one_object(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response(
            {
                "obsTime": "2026-10-03T15:00:00+08:00",
                "hourlyRainfall": [
                    {
                        "automaticWeatherStation": "Sai Kung",
                        "automaticWeatherStationID": "N15",
                        "value": "4",
                        "unit": "mm",
                    },
                    {
                        "automaticWeatherStation": "Lau Fau Shan",
                        "automaticWeatherStationID": "RF001",
                        "value": "0",
                        "unit": "mm",
                    },
                ],
            }
        ),
    )
    assert main(["--hour-driest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "obs_time": "2026-10-03T15:00:00+08:00",
        "place": "Lau Fau Shan",
        "station_id": "RF001",
        "rainfall_mm": 0.0,
    }


def test_cli_hour_driest_when_none_available(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.hko.urllib.request.urlopen",
        lambda request, timeout: _json_response({"hourlyRainfall": []}),
    )
    assert main(["--hour-driest"]) == 0
    assert capsys.readouterr().out == "No hourly rainfall readings are available.\n"
    assert main(["--hour-driest", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "message": "No hourly rainfall readings are available."
    }


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
