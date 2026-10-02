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
