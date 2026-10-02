# hk-weather

Small Python CLI that prints the current weather in Hong Kong. This repository is a **Cursor cloud-agent demo**: an agent started from an almost empty public repo and added the package, tests, and CI.

Data comes from the [Hong Kong Observatory Open Data API](https://www.hko.gov.hk/en/abouthko/opendata_intro.htm). The default is the current weather report (`dataType=rhrread`). `--forecast` prints the local weather forecast (`dataType=flw`). `--nine-day` prints the 9-day forecast (`dataType=fnd`). `--warnings` lists active warnings (`dataType=warnsum`). `--uv` prints the UV index from the current report (`dataType=rhrread`). `--tips` prints special weather tips (`dataType=swt`). No API key or account is required.

## Run

```bash
pip install -e .
hk-weather
hk-weather --json
hk-weather --forecast
hk-weather --forecast --json
hk-weather --nine-day
hk-weather --nine-day --json
hk-weather --warnings
hk-weather --uv
hk-weather --uv --json
hk-weather --lang tc
hk-weather --forecast --lang sc
hk-weather --tips
hk-weather --tips --json
```

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

`hk-weather --forecast` prints the local forecast period, description, and outlook. With `--json`, that same forecast is one JSON object. Current conditions stay the default.

`hk-weather --nine-day` (or `-n`) prints each day with the date, weather, high and low temperature, and chance of rain when the Observatory includes it. `--nine-day --json` prints that same forecast as one JSON object.

`hk-weather --warnings` (or `-w`) prints each active warning as a code and description. If none are in force, it says so.

`hk-weather --uv` (or `-u`) prints the Observatory UV index (place, value, and description). `--uv --json` prints that same reading as one JSON object. When the Observatory has no UV reading, it says so. Current conditions stay the default.

`--lang` chooses the Observatory response language: `en` (default), `tc`, or `sc`. It is sent as the `lang` query parameter on every fetch.

`hk-weather --tips` (or `-t`) prints each special weather tip. `--tips --json` prints them as one JSON object. `--lang` applies. Current conditions stay the default.

## Test

Tests mock HTTP, so they do not call the Observatory.

```bash
pip install -e ".[dev]"
pytest
```

GitHub Actions runs the same install and `pytest` on pushes and pull requests to `main`.
