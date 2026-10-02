# hk-weather

[![CI](https://github.com/martin1194/hk-weather-example/actions/workflows/ci.yml/badge.svg)](https://github.com/martin1194/hk-weather-example/actions/workflows/ci.yml)

Small Python CLI that prints the current weather in Hong Kong. This repository is a **Cursor cloud-agent demo**: an agent started from an almost empty public repo and added the package, tests, and CI.

Data comes from the [Hong Kong Observatory Open Data API](https://www.hko.gov.hk/en/abouthko/opendata_intro.htm). The default is the current weather report (`dataType=rhrread`). `--forecast` prints the local weather forecast (`dataType=flw`). `--nine-day` prints the 9-day forecast (`dataType=fnd`). `--warnings` lists active warnings (`dataType=warnsum`). `--uv` prints the UV index from the current report (`dataType=rhrread`). `--tips` prints special weather tips (`dataType=swt`). `--stations` lists each station in the current report. `--place` filters that list by name. No API key or account is required.

## Run

```bash
pip install -e .
hk-weather
hk-weather --version
hk-weather --short
hk-weather --json
hk-weather --forecast
hk-weather --forecast --json
hk-weather --nine-day
hk-weather --nine-day --json
hk-weather --wind
hk-weather --wind --json
hk-weather --warnings
hk-weather --warnings --json
hk-weather --uv
hk-weather --uv --json
hk-weather --lang tc
hk-weather --forecast --lang sc
hk-weather --tips
hk-weather --tips --json
hk-weather --rain
hk-weather --rain --json
hk-weather --lightning
hk-weather --lightning --json
hk-weather --humidity
hk-weather --humidity --json
hk-weather --temps
hk-weather --temps --json
hk-weather --stations
hk-weather --list-places
hk-weather --place "King's Park"
hk-weather --place park --json
```

`hk-weather --version` prints the installed package version and exits.

Or without installing the script:

```bash
pip install -e .
python -m hk_weather
```

Example:

```text
Hong Kong weather
Source: Hong Kong Observatory open data
Updated: 2026-10-02T23:02:00+08:00
Conditions: Rain
Temperature: 28°C (Hong Kong Observatory)
Humidity: 85%
Rainfall (past hour, highest district): 2 mm (Sai Kung)
Lightning: Lantau
Warnings:
- The Thunderstorm Warning has been issued.
```

The temperature and humidity lines use the Hong Kong Observatory station when that reading is present.

`hk-weather --short` (or `-s`) prints current conditions on one line, for example: `Rain, 28°C, humidity 85% — The Thunderstorm Warning has been issued`. The default multi-line report is unchanged.

`hk-weather --forecast` prints the local forecast period, description, and outlook. With `--json`, that same forecast is one JSON object. Current conditions stay the default.

`hk-weather --nine-day` (or `-n`) prints each day with the date, weather, high and low temperature, humidity range, and chance of rain when the Observatory includes them. `--nine-day --json` prints that same forecast as one JSON object.

`hk-weather --wind` prints the forecast wind for each day from that same 9-day forecast. `--wind --json` prints those days as one JSON object. If no wind text is present, it says so.

`hk-weather --warnings` (or `-w`) prints each active warning as a code and description. `--warnings --json` prints them as one JSON object. If none are in force, it says so.

`hk-weather --uv` (or `-u`) prints the Observatory UV index (place, value, and description). `--uv --json` prints that same reading as one JSON object. When the Observatory has no UV reading, it says so. Current conditions stay the default.

`--lang` chooses the Observatory response language: `en` (default), `tc`, or `sc`. It is sent as the `lang` query parameter on every fetch.

`hk-weather --tips` (or `-t`) prints each special weather tip. `--tips --json` prints them as one JSON object. `--lang` applies. Current conditions stay the default.

`hk-weather --rain` (or `-r`) prints rainfall by district from the current report, one line per place. `--rain --json` prints that list as one JSON object. If no readings are present, it says so.

`hk-weather --lightning` lists places where the current report shows lightning. `--lightning --json` prints those places as one JSON object. If none are reported, it says so.

`hk-weather --humidity` prints humidity by place from the current report, with the record time when the Observatory includes it. `--humidity --json` prints that list as one JSON object. If no reading is present, it says so.

`hk-weather --temps` prints temperature by place from the current report, with the record time when the Observatory includes it. `--temps --json` prints that list as one JSON object. If no readings are present, it says so.

`hk-weather --stations` lists each place in the current report with its temperature and, when the Observatory includes it, humidity.

`hk-weather --list-places` prints the station names from the current report (temperature and humidity), so you can see what to pass to `--place`.

`hk-weather --place NAME` prints the same readings for stations whose name contains NAME (case-insensitive). `--json` and `--lang` apply. If nothing matches, it says so.

## Test

Tests mock HTTP, so they do not call the Observatory.

```bash
pip install -e ".[dev]"
pytest
```

GitHub Actions runs the same install and `pytest` on Python 3.11, 3.12, and 3.13 for pushes and pull requests to `main`.
