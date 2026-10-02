# hk-weather

Small Python CLI that prints the current weather in Hong Kong. This repository is a **Cursor cloud-agent demo**: an agent started from an almost empty public repo and added the package, tests, and CI.

Data comes from the [Hong Kong Observatory Open Data API](https://www.hko.gov.hk/en/abouthko/opendata_intro.htm) current weather report (`dataType=rhrread`). No API key or account is required.

## Run

```bash
pip install -e .
hk-weather
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

## Test

Tests mock HTTP, so they do not call the Observatory.

```bash
pip install -e ".[dev]"
pytest
```

GitHub Actions runs the same install and `pytest` on pushes and pull requests to `main`.
