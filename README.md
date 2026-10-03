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
hk-weather --summary
hk-weather --summary --json
hk-weather --json
hk-weather --forecast
hk-weather --forecast --json
hk-weather --situation
hk-weather --situation --json
hk-weather --fire-danger
hk-weather --fire-danger --json
hk-weather --tc-info
hk-weather --tc-info --json
hk-weather --nine-day
hk-weather --nine-day --json
hk-weather --today
hk-weather -Y --json
hk-weather --yesterday
hk-weather --yesterday --json
hk-weather --grass
hk-weather --grass --json
hk-weather --accum-rain
hk-weather --accum-rain --json
hk-weather --avg-rain
hk-weather --avg-rain --json
hk-weather --radiation
hk-weather --radiation --json
hk-weather --tomorrow
hk-weather -T --json
hk-weather --weekend
hk-weather -E --json
hk-weather --day 1
hk-weather --psr
hk-weather --psr --json
hk-weather --wind
hk-weather --wind --json
hk-weather --quake
hk-weather --quake --json
hk-weather --felt
hk-weather --felt --json
hk-weather --visibility
hk-weather --visibility --json
hk-weather --tide
hk-weather --tide --json
hk-weather --aqhi
hk-weather --aqhi --json
hk-weather --sunrise
hk-weather --sunrise --json
hk-weather --moon
hk-weather --moon --json
hk-weather --lunar
hk-weather --lunar --json
hk-weather --warnings
hk-weather --warnings --json
hk-weather --warning-info
hk-weather --uv
hk-weather --uv --json
hk-weather --icon-time
hk-weather --icon-time --json
hk-weather --lang tc
hk-weather --forecast --lang sc
hk-weather --tips
hk-weather --tips --json
hk-weather --rain
hk-weather --rain --json
hk-weather --rain-period
hk-weather --rain-period --json
hk-weather --hour-rain
hk-weather --hour-rain --json
hk-weather --hour-wettest
hk-weather --hour-wettest --json
hk-weather --hour-driest
hk-weather --hour-driest --json
hk-weather --wettest
hk-weather --wettest --json
hk-weather --driest
hk-weather --driest --json
hk-weather --rainstorm
hk-weather --rainstorm --json
hk-weather --cyclone
hk-weather --cyclone --json
hk-weather --lightning
hk-weather --lightning --json
hk-weather --strikes
hk-weather --strikes --json
hk-weather --humidity
hk-weather --humidity --json
hk-weather --humidest
hk-weather --humidest --json
hk-weather --least-humid
hk-weather --least-humid --json
hk-weather --temps
hk-weather --temps --json
hk-weather --hottest
hk-weather --hottest --json
hk-weather --coldest
hk-weather --coldest --json
hk-weather --overnight
hk-weather --overnight --json
hk-weather --noon-rain
hk-weather --noon-rain --json
hk-weather --month-rain
hk-weather --month-rain --json
hk-weather --year-rain
hk-weather --year-rain --json
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
Conditions: 🌧️ Rain
Temperature: 28°C (Hong Kong Observatory)
Humidity: 85%
Rainfall (past hour, highest district): 2 mm (Sai Kung)
Lightning: Lantau
Warnings:
- The Thunderstorm Warning has been issued.
```

The temperature and humidity lines use the Hong Kong Observatory station when that reading is present.

`hk-weather --short` (or `-s`) prints current conditions on one line, for example: `🌧️ Rain, 28°C, humidity 85% — The Thunderstorm Warning has been issued`. A known Observatory icon prefixes that line and the default report's conditions line. A missing or unmapped icon stays plain text.

`hk-weather --summary` (or `-S`) prints a short briefing: that same conditions line, active warnings (or `Warnings: none`), and today's high, low, and rain chance from the 9-day forecast. `--summary --json` prints the briefing as one JSON object. `--lang` applies. If today's forecast is missing, the today line says `not available`.

`hk-weather --forecast` prints the local forecast period, description, and outlook. With `--json`, that same forecast is one JSON object. Current conditions stay the default.

`hk-weather --situation` (or `-g`) prints the general situation from that forecast (`generalSituation`). `--situation --json` prints that paragraph as one JSON object. `--lang` applies. If the field is missing or blank, it says `No general situation is available.`

`hk-weather --fire-danger` (or `-f`) prints the fire danger warning from that forecast (`fireDangerWarning`). `--fire-danger --json` prints that sentence as one JSON object. `--lang` applies. If the field is missing or blank, it says `No fire danger warning is available.`

`hk-weather --tc-info` prints tropical cyclone information from that forecast (`tcInfo`). `--tc-info --json` prints that paragraph as one JSON object. `--lang` applies. If the field is missing or blank, it says `No tropical cyclone information is available.`

`hk-weather --nine-day` (or `-n`) prints each day with the date, weather, high and low temperature, humidity range, and chance of rain when the Observatory includes them. `--nine-day --json` prints that same forecast as one JSON object.

`hk-weather --today` (or `-Y`) prints only today's day from that forecast, using the Hong Kong calendar date. It includes weather, high and low, humidity, chance of rain, and wind when the Observatory sends them. `--today --json` prints that day as one JSON object. `--lang` applies. For example: `2026-10-03 Saturday  high 31°C  low 27°C  humidity 75-95%  rain Medium High`. If that day is missing, it says so.

`hk-weather --yesterday` prints yesterday's Observatory summary (`dataType=RYES`, station HKO): high, low, rainfall, and humidity. `--yesterday --json` prints that summary as one JSON object. `--lang` applies. If the summary is missing, it says `Yesterday's Observatory summary is not available.`

`hk-weather --grass` prints yesterday's grass minimum from that same summary (`HKOReadingsMinGrassTemp`). `--yesterday` still prints the air-temperature summary. `--grass --json` prints the grass minimum as one JSON object. `--lang` applies. If the reading is missing, it says `No grass minimum is available.`

`hk-weather --accum-rain` prints accumulated rainfall at the Observatory from 1 January through yesterday (`HKOReadingsAccumRainfall` on that same summary). `--year-rain` still prints the January-to-last-month note. `--accum-rain --json` prints the total as one JSON object. `--lang` applies. If the reading is missing, it says `No accumulated rainfall is available.`

`hk-weather --avg-rain` prints the climatological normal of that accumulated total (`HKOReadingsAvgRainfall`). `--accum-rain` still prints the recorded total. `--avg-rain --json` prints the normal as one JSON object. `--lang` applies. If the reading is missing, it says `No average rainfall is available.`

`hk-weather --radiation` prints yesterday's outdoor gamma radiation report from that same summary (`HongKongDesc`). `--radiation --json` prints that paragraph as one JSON object. `--lang` applies. If the report is missing, it says `No radiation report is available.`

`hk-weather --tomorrow` (or `-T`) prints only tomorrow's day from that forecast, including wind when the Observatory sends it. `--tomorrow --json` prints that day as one JSON object. `--lang` applies. If that day is missing, it says so.

`hk-weather --weekend` (or `-E`) prints only Saturday and Sunday from that forecast, with weather, high and low, humidity, chance of rain, and wind when the Observatory includes them. `--weekend --json` prints those days as one JSON object. If the 9-day window has no weekend day, it says so.

`hk-weather --day 1` prints the first day in that same list (array index 0). `--day` takes 1 through 9. `--tomorrow` is the next Hong Kong calendar day, which is often a later entry.

`hk-weather --psr` (or `-P`) prints the chance of significant rain for each day of that forecast, for example `2026-10-03 Saturday  High`. `--psr --json` prints those days as one JSON object. `--lang` applies. A day with no PSR value shows `n/a`.

`hk-weather --wind` prints the forecast wind for each day from that same 9-day forecast. `--wind --json` prints those days as one JSON object. If no wind text is present, it says so.

`hk-weather --quake` lists the latest quick earthquake message from the Observatory earthquake feed (`earthquake.php`, `dataType=qem`), for example `2026-10-03T00:34:00+08:00  M6  off east coast of Kamchatka (51.79, 159.6)`. `--quake --json` prints that list as one JSON object. `--lang` applies. If none is reported, it says so.

`hk-weather --felt` (or `-q`) prints the latest locally felt earth tremor (`dataType=feltearthquake`), including time, magnitude, place, and intensity when the Observatory sends them. `--felt --json` prints that report as one JSON object. `--lang` applies. If none is reported, it says `No locally felt earth tremor is reported.`

`hk-weather --visibility` (or `-V`) prints the latest 10-minute mean visibility (`opendata.php`, `dataType=LTMV`), for example `2026-10-03 07:30  Central  14 km`. `--visibility --json` prints those stations as one JSON object. `--lang` applies. Stations marked `N/A` are omitted. If none remain, it says so.

`hk-weather --tide` (or `-I`) prints today's astronomical high and low tides at Quarry Bay (`opendata.php`, `dataType=HLT`), for example `2026-10-03  01:05  2.44 m`. `--tide --json` prints that list as one JSON object. `--lang` applies. If none are present, it says so.

`hk-weather --aqhi` (or `-A`) prints the current Air Quality Health Index at each monitoring station, for example `Central/Western  General Stations  3  Low`. `--aqhi --json` prints that list as one JSON object. `--lang` chooses the English, Traditional Chinese, or Simplified Chinese feed. If none are present, it says so.

`hk-weather --sunrise` (or `-U`) prints today's sunrise, sun transit, and sunset (`opendata.php`, `dataType=SRS`), for example `Rise: 06:15` and `Set: 18:09`. `--sunrise --json` prints that day as one JSON object. `--lang` applies. If the times are missing, it says so.

`hk-weather --moon` (or `-M`) prints today's moonrise, moon transit, and moonset (`opendata.php`, `dataType=MRS`), for example `Rise: 23:39` and `Set: 12:48`. `--moon --json` prints that day as one JSON object. `--lang` applies. If the times are missing, it says so.

`hk-weather --lunar` prints today's lunar date from the Observatory calendar, for example `丙午年，馬` and `八月廿三`. `--lunar --json` prints that date as one JSON object. `--lang` is sent on the request; the Observatory still returns the lunar labels in Chinese. If the date is missing, it says `No lunar date is available.`

`hk-weather --warnings` (or `-w`) prints each active warning as a code and description. `--warnings --json` prints them as one JSON object. If none are in force, it says so.

`hk-weather --warning-info` (or `-W`) prints each detailed warning message from `dataType=warningInfo`. `--json` and `--lang` apply. If none are present, it says so.

`hk-weather --uv` (or `-u`) prints the Observatory UV index (place, value, and description). `--uv --json` prints that same reading as one JSON object. When the Observatory has no UV reading, it says so. Current conditions stay the default.

`hk-weather --icon-time` (or `-i`) prints when the current weather icon was last updated (`iconUpdateTime`). `--icon-time --json` prints that timestamp as one JSON object. `--lang` applies. If the field is missing or blank, it says `No icon update time is available.`

`--lang` chooses the Observatory response language: `en` (default), `tc`, or `sc`. It is sent as the `lang` query parameter on every fetch.

`hk-weather --tips` (or `-t`) prints each special weather tip. `--tips --json` prints them as one JSON object. `--lang` applies. Current conditions stay the default.

`hk-weather --rain` (or `-r`) prints rainfall by district from the current report, one line per place. `--rain --json` prints that list as one JSON object. If no readings are present, it says so.

`hk-weather --rain-period` prints the observation window for that district rainfall (`rainfall.startTime` and `rainfall.endTime`). `--rain` still prints the amounts. `--rain-period --json` prints the window as one JSON object. `--lang` applies. If the window is missing, it says `No rainfall period is available.`

`hk-weather --hour-rain` prints past-hour rainfall from automatic weather stations (`hourlyRainfall.php`), wettest first. `--hour-rain --json` prints that list as one JSON object. `--lang` applies. A station marked under maintenance is skipped. If no readings are present, it says `No hourly rainfall readings are available.`

`hk-weather --hour-wettest` prints the wettest station from that list, for example `Wetland Park  2 mm`. `--hour-wettest --json` prints that station as one JSON object. `--lang` applies. If no readings are present, it says so.

`hk-weather --hour-driest` prints the driest station from that list, for example `Lau Fau Shan  0 mm`. `--hour-driest --json` prints that station as one JSON object. `--lang` applies. If no readings are present, it says so.

`hk-weather --rainstorm` prints the rainstorm reminder from the current report (`rainstormReminder`). `--rainstorm --json` prints that message as one JSON object. `--lang` applies. If the field is missing or blank, it says `No rainstorm reminder.`

`hk-weather --cyclone` (or `-c`) prints the tropical cyclone message from the current report (`tcmessage`). `--cyclone --json` prints those lines as one JSON object. `--lang` applies. If the field is missing or blank, it says `No tropical cyclone message.`

`hk-weather --wettest` (or `-R`) prints the wettest district from that list, for example `Sai Kung  12 mm`. `--wettest --json` prints that reading as one JSON object. `--lang` applies. If no readings are present, it says so.

`hk-weather --driest` (or `-D`) prints the driest district from that list, for example `Central & Western  0 mm`. `--driest --json` prints that reading as one JSON object. `--lang` applies. If no readings are present, it says so.

`hk-weather --lightning` lists places where the current report shows lightning. `--lightning --json` prints those places as one JSON object. If none are reported, it says so.

`hk-weather --strikes` (or `-l`) prints hourly cloud-to-ground and cloud-to-cloud lightning counts by region (`dataType=LHL`). `--strikes --json` prints those counts as one JSON object. `--lang` applies. If none are available, it says `No lightning counts are available.`

`hk-weather --humidity` prints humidity by place from the current report, with the record time when the Observatory includes it. `--humidity --json` prints that list as one JSON object. If no reading is present, it says so.

`hk-weather --humidest` prints the most humid place from the current report, for example `Chek Lap Kok  95%`. `--humidest --json` prints that reading as one JSON object. `--lang` applies. If no reading is present, it says so.

`hk-weather --least-humid` prints the least humid place from the current report, for example `King's Park  80%`. `--least-humid --json` prints that reading as one JSON object. `--lang` applies. If no reading is present, it says so.

`hk-weather --temps` prints temperature by place from the current report, with the record time when the Observatory includes it. `--temps --json` prints that list as one JSON object. If no readings are present, it says so.

`hk-weather --hottest` (or `-H`) prints the warmest place from the current report, for example `King's Park  31°C`. `--hottest --json` prints that reading as one JSON object. `--lang` applies. If no readings are present, it says so.

`hk-weather --coldest` (or `-C`) prints the coolest place from the current report, for example `Tai Mo Shan  18°C`. `--coldest --json` prints that reading as one JSON object. `--lang` applies. If no readings are present, it says so.

`hk-weather --overnight` (or `-O`) prints the Observatory's midnight-to-9am minimum temperature note (`mintempFrom00To09`). `--overnight --json` prints that sentence as one JSON object. `--lang` applies. If the field is missing or blank, it says `No overnight minimum is available.`

`hk-weather --noon-rain` (or `-N`) prints the Observatory's midnight-to-noon rainfall note (`rainfallFrom00To12`). `--noon-rain --json` prints that sentence as one JSON object. `--lang` applies. If the field is missing or blank, it says `No noon rainfall note is available.`

`hk-weather --month-rain` (or `-L`) prints the Observatory's last-month rainfall note (`rainfallLastMonth`). `--month-rain --json` prints that sentence as one JSON object. `--lang` applies. If the field is missing or blank, it says `No last-month rainfall note is available.`

`hk-weather --year-rain` (or `-y`) prints the Observatory's January-to-last-month rainfall note (`rainfallJanuaryToLastMonth`). `--year-rain --json` prints that sentence as one JSON object. `--lang` applies. If the field is missing or blank, it says `No year-to-date rainfall note is available.`

`hk-weather --stations` lists each place in the current report with its temperature and, when the Observatory includes it, humidity.

`hk-weather --list-places` prints the station names from the current report (temperature and humidity), so you can see what to pass to `--place`.

`hk-weather --place NAME` prints the same readings for stations whose name contains NAME (case-insensitive). `--json` and `--lang` apply. If nothing matches, it says so.

## Test

Tests mock HTTP, so they do not call the Observatory.

```bash
pip install -e ".[dev]"
ruff check
pytest
```

GitHub Actions runs the same install, `ruff check`, and `pytest` on Python 3.11, 3.12, and 3.13 for pushes and pull requests to `main`. Pip downloads are cached from `pyproject.toml` so later installs are faster.
