import json
from urllib.error import URLError

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


def test_cli_prints_report(monkeypatch, capsys):
    monkeypatch.setattr(
        "hk_weather.cli.fetch_current",
        lambda timeout: SAMPLE_WEATHER,
    )
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Temperature: 28°C" in out


def test_cli_reports_fetch_errors(monkeypatch, capsys):
    def boom(timeout):
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


def test_cli_json_fetch_error_stays_on_stderr(monkeypatch, capsys):
    def boom(request, timeout):
        raise URLError("down")

    monkeypatch.setattr("hk_weather.hko.urllib.request.urlopen", boom)
    assert main(["--json"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "could not reach Hong Kong Observatory" in captured.err
