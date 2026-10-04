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
hk-weather --outlook
hk-weather --outlook --json
hk-weather --coastal
hk-weather --coastal --json
hk-weather --coast-report
hk-weather --coast-report --json
hk-weather --forecast-period
hk-weather --forecast-period --json
hk-weather --forecast-desc
hk-weather --forecast-desc --json
hk-weather --forecast-updated
hk-weather --forecast-updated --json
hk-weather --situation
hk-weather --situation --json
hk-weather --fire-danger
hk-weather --fire-danger --json
hk-weather --tc-info
hk-weather --tc-info --json
hk-weather --nine-day
hk-weather --nine-day --json
hk-weather --sea-temp
hk-weather --sea-temp --json
hk-weather --soil-temp
hk-weather --soil-temp --json
hk-weather --nine-situation
hk-weather --nine-situation --json
hk-weather --nine-updated
hk-weather --nine-updated --json
hk-weather --nine-weather
hk-weather --nine-weather --json
hk-weather --nine-temp
hk-weather --nine-temp --json
hk-weather --nine-humidity
hk-weather --nine-humidity --json
hk-weather --today
hk-weather -Y --json
hk-weather --yesterday
hk-weather --yesterday --json
hk-weather --mean-temp
hk-weather --mean-temp --json
hk-weather --tai-mo-temp
hk-weather --tai-mo-temp --json
hk-weather --tate-temp
hk-weather --tate-temp --json
hk-weather --sai-kung-temp
hk-weather --sai-kung-temp --json
hk-weather --max-temp
hk-weather --max-temp --json
hk-weather --min-temp
hk-weather --min-temp --json
hk-weather --tai-mo-min
hk-weather --tai-mo-min --json
hk-weather --tate-min
hk-weather --tate-min --json
hk-weather --tai-mo-max
hk-weather --tai-mo-max --json
hk-weather --tseung-kwan-o-max
hk-weather --tseung-kwan-o-max --json
hk-weather --sheung-shui-max
hk-weather --sheung-shui-max --json
hk-weather --waglan-max
hk-weather --waglan-max --json
hk-weather --dew-point
hk-weather --dew-point --json
hk-weather --park-dew
hk-weather --park-dew --json
hk-weather --cheung-dew
hk-weather --cheung-dew --json
hk-weather --wong-chuk-hang-dew
hk-weather --wong-chuk-hang-dew --json
hk-weather --sai-kung-dew
hk-weather --sai-kung-dew --json
hk-weather --sha-tin-dew
hk-weather --sha-tin-dew --json
hk-weather --cloud
hk-weather --cloud --json
hk-weather --evaporation
hk-weather --evaporation --json
hk-weather --evapotranspiration
hk-weather --evapotranspiration --json
hk-weather --grass
hk-weather --grass --json
hk-weather --sunshine
hk-weather --sunshine --json
hk-weather --daily-sun
hk-weather --daily-sun --json
hk-weather --max-uv
hk-weather --max-uv --json
hk-weather --uv-peak
hk-weather --uv-peak --json
hk-weather --mean-uv
hk-weather --mean-uv --json
hk-weather --daily-uv
hk-weather --daily-uv --json
hk-weather --dose
hk-weather --dose --json
hk-weather --hourly-dose
hk-weather --hourly-dose --json
hk-weather --accum-rain
hk-weather --accum-rain --json
hk-weather --avg-rain
hk-weather --avg-rain --json
hk-weather --radiation
hk-weather --radiation --json
hk-weather --bulletin
hk-weather --bulletin --json
hk-weather --radiation-note
hk-weather --radiation-note --json
hk-weather --radiation-weather
hk-weather --radiation-weather --json
hk-weather --radiation-ground
hk-weather --radiation-ground --json
hk-weather --radiation-provisional
hk-weather --radiation-provisional --json
hk-weather --tomorrow
hk-weather -T --json
hk-weather --weekend
hk-weather -E --json
hk-weather --day 1
hk-weather --psr
hk-weather --psr --json
hk-weather --wind
hk-weather --wind --json
hk-weather --gust
hk-weather --gust --json
hk-weather --prevailing
hk-weather --prevailing --json
hk-weather --cheung-prevailing
hk-weather --cheung-prevailing --json
hk-weather --ping-chau-prevailing
hk-weather --ping-chau-prevailing --json
hk-weather --tai-mo-to-prevailing
hk-weather --tai-mo-to-prevailing --json
hk-weather --tai-po-kau-prevailing
hk-weather --tai-po-kau-prevailing --json
hk-weather --mean-wind
hk-weather --mean-wind --json
hk-weather --cheung-wind
hk-weather --cheung-wind --json
hk-weather --lau-fau-wind
hk-weather --lau-fau-wind --json
hk-weather --peng-chau-wind
hk-weather --peng-chau-wind --json
hk-weather --tai-po-kau-wind
hk-weather --tai-po-kau-wind --json
hk-weather --forecast-icon
hk-weather --forecast-icon --json
hk-weather --quake
hk-weather --quake --json
hk-weather --felt
hk-weather --felt --json
hk-weather --visibility
hk-weather --visibility --json
hk-weather --reduced-vis
hk-weather --reduced-vis --json
hk-weather --tide
hk-weather --tide --json
hk-weather --tide-hour
hk-weather --tide-hour --json
hk-weather --tide-latest
hk-weather --tide-latest --json
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
hk-weather --warning-time
hk-weather --warning-time --json
hk-weather --warning-info
hk-weather --uv
hk-weather --uv --json
hk-weather --fifteen-uv
hk-weather --fifteen-uv --json
hk-weather --icon-time
hk-weather --icon-time --json
hk-weather --icon
hk-weather --icon --json
hk-weather --current-updated
hk-weather --current-updated --json
hk-weather --lang tc
hk-weather --forecast --lang sc
hk-weather --tips
hk-weather --tips --json
hk-weather --lamppost
hk-weather --lamppost --json
hk-weather --rain
hk-weather --rain --json
hk-weather --rain-period
hk-weather --rain-period --json
hk-weather --rain-maint
hk-weather --rain-maint --json
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
hk-weather --nowcast
hk-weather --nowcast --json
hk-weather --daily-rain
hk-weather --daily-rain --json
hk-weather --lau-fau-rain
hk-weather --lau-fau-rain --json
hk-weather --shek-kong-rain
hk-weather --shek-kong-rain --json
hk-weather --wetland-rain
hk-weather --wetland-rain --json
hk-weather --sham-shui-po-rain
hk-weather --sham-shui-po-rain --json
hk-weather --park-rain
hk-weather --park-rain --json
hk-weather --tseung-kwan-o-rain
hk-weather --tseung-kwan-o-rain --json
hk-weather --rainstorm
hk-weather --rainstorm --json
hk-weather --cyclone
hk-weather --cyclone --json
hk-weather --lightning
hk-weather --lightning --json
hk-weather --strikes
hk-weather --strikes --json
hk-weather --daily-strikes
hk-weather --daily-strikes --json
hk-weather --cloud-strikes
hk-weather --cloud-strikes --json
hk-weather --humidity
hk-weather --humidity --json
hk-weather --humidity-time
hk-weather --humidity-time --json
hk-weather --minute-humidity
hk-weather --minute-humidity --json
hk-weather --humidest
hk-weather --humidest --json
hk-weather --least-humid
hk-weather --least-humid --json
hk-weather --mean-humidity
hk-weather --mean-humidity --json
hk-weather --tai-mo-humidity
hk-weather --tai-mo-humidity --json
hk-weather --waglan-humidity
hk-weather --waglan-humidity --json
hk-weather --tate-humidity
hk-weather --tate-humidity --json
hk-weather --ta-kwu-ling-humidity
hk-weather --ta-kwu-ling-humidity --json
hk-weather --wetland-humidity
hk-weather --wetland-humidity --json
hk-weather --shek-kong-humidity
hk-weather --shek-kong-humidity --json
hk-weather --temps
hk-weather --temps --json
hk-weather --temp-time
hk-weather --temp-time --json
hk-weather --minute-temp
hk-weather --minute-temp --json
hk-weather --since-midnight
hk-weather --since-midnight --json
hk-weather --pressure
hk-weather --pressure --json
hk-weather --mean-pressure
hk-weather --mean-pressure --json
hk-weather --park-pressure
hk-weather --park-pressure --json
hk-weather --sha-tin-pressure
hk-weather --sha-tin-pressure --json
hk-weather --sheung-shui-pressure
hk-weather --sheung-shui-pressure --json
hk-weather --minute-grass
hk-weather --minute-grass --json
hk-weather --daily-grass
hk-weather --daily-grass --json
hk-weather --obs-grass
hk-weather --obs-grass --json
hk-weather --temp-diff
hk-weather --temp-diff --json
hk-weather --heat-index
hk-weather --heat-index --json
hk-weather --daily-heat
hk-weather --daily-heat --json
hk-weather --mean-heat
hk-weather --mean-heat --json
hk-weather --wbgt
hk-weather --wbgt --json
hk-weather --wet-bulb
hk-weather --wet-bulb --json
hk-weather --airport-wet
hk-weather --airport-wet --json
hk-weather --park-wet
hk-weather --park-wet --json
hk-weather --sha-lo-wan-wet
hk-weather --sha-lo-wan-wet --json
hk-weather --solar
hk-weather --solar --json
hk-weather --global-solar
hk-weather --global-solar --json
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

`hk-weather --outlook` prints only the outlook paragraph from that forecast (`outlook`). `--forecast` still prints the full local forecast. `--outlook --json` prints that paragraph as one JSON object. `--lang` applies. If the field is missing or blank, it says `No outlook is available.`

`hk-weather --coastal` prints the South China coastal waters area forecast, for example `Hong Kong Adjacent Waters  East force 4, becoming north force 5 later.  Scattered showers and squally thunderstorms.  Moderate seas.` `--outlook` still prints the local-forecast outlook. `--coastal --json` prints those areas as one JSON object. `--lang` selects the bulletin language. An area is omitted when its name or all of its details are blank. If none remain, it says `No coastal waters forecast is available.`

`hk-weather --coast-report` prints the latest observations from South China coastal stations, for example `Waglan Island  Wind east force 1  visibility 44 km`. `--coastal` still prints the area forecast. `--coast-report --json` prints those stations as one JSON object. `--lang` selects the bulletin language. A station is omitted when its name is blank or it has no wind, weather, or visibility. If none remain, it says `No coastal station reports are available.`

`hk-weather --forecast-period` prints the period that forecast covers (`forecastPeriod`), for example `Weather forecast for tonight and tomorrow`. `--forecast` still prints the full local forecast. `--forecast-period --json` prints that line as one JSON object. `--lang` applies. If the field is missing or blank, it says `No forecast period is available.`

`hk-weather --forecast-desc` prints the description from that forecast (`forecastDesc`). `--forecast` still prints the full local forecast. `--forecast-desc --json` prints that paragraph as one JSON object. `--lang` applies. If the field is missing or blank, it says `No forecast description is available.`

`hk-weather --forecast-updated` prints when that forecast was last updated (`updateTime`). `--forecast` still prints the full local forecast. `--forecast-updated --json` prints that timestamp as one JSON object. `--lang` applies. If the field is missing or blank, it says `No forecast update time is available.`

`hk-weather --situation` (or `-g`) prints the general situation from that forecast (`generalSituation`). `--situation --json` prints that paragraph as one JSON object. `--lang` applies. If the field is missing or blank, it says `No general situation is available.`

`hk-weather --fire-danger` (or `-f`) prints the fire danger warning from that forecast (`fireDangerWarning`). `--fire-danger --json` prints that sentence as one JSON object. `--lang` applies. If the field is missing or blank, it says `No fire danger warning is available.`

`hk-weather --tc-info` prints tropical cyclone information from that forecast (`tcInfo`). `--tc-info --json` prints that paragraph as one JSON object. `--lang` applies. If the field is missing or blank, it says `No tropical cyclone information is available.`

`hk-weather --nine-day` (or `-n`) prints each day with the date, weather, high and low temperature, humidity range, and chance of rain when the Observatory includes them. `--nine-day --json` prints that same forecast as one JSON object.

`hk-weather --sea-temp` prints the sea temperature from that forecast (`seaTemp`), for example `North Point  29°C`. `--nine-day` still prints the daily forecast. `--sea-temp --json` prints the reading as one JSON object. `--lang` applies. If the reading is missing, it says `No sea temperature is available.`

`hk-weather --soil-temp` prints soil temperatures from that forecast (`soilTemp`), one line per depth, for example `Hong Kong Observatory  0.5 m  30.6°C`. `--sea-temp` still prints the sea temperature. `--soil-temp --json` prints those readings as one JSON object. `--lang` applies. If none are present, it says `No soil temperature is available.`

`hk-weather --nine-situation` prints the general situation from the 9-day forecast (`generalSituation` on `dataType=fnd`). `--situation` still prints the local-forecast paragraph. `--nine-situation --json` prints that paragraph as one JSON object. `--lang` applies. If the field is missing or blank, it says `No 9-day situation is available.`

`hk-weather --nine-updated` prints when that 9-day forecast was last updated (`updateTime`). `--nine-day` still prints the daily forecast. `--forecast-updated` still prints the local-forecast time. `--nine-updated --json` prints that timestamp as one JSON object. `--lang` applies. If the field is missing or blank, it says `No 9-day update time is available.`

`hk-weather --nine-weather` prints each day's weather sentence from that forecast (`forecastWeather`), for example `2026-10-04 Sunday  Mainly cloudy with a few showers`. `--nine-day` still prints the full daily forecast. `--wind` still prints the wind. `--nine-weather --json` prints those days as one JSON object. `--lang` applies. If no weather text is present, it says `No 9-day weather is available.`

`hk-weather --nine-temp` prints each day's high and low from that forecast (`forecastMaxtemp` and `forecastMintemp`), for example `2026-10-04 Sunday  high 31°C  low 26°C`. `--temps` still prints the current station temperatures. `--nine-temp --json` prints those days as one JSON object. `--lang` applies. If no temperature is present, it says `No 9-day temperatures are available.`

`hk-weather --nine-humidity` prints each day's humidity range from that forecast (`forecastMaxrh` and `forecastMinrh`), for example `2026-10-04 Sunday  humidity 65-95%`. `--humidity` still prints the current station readings. `--nine-humidity --json` prints those days as one JSON object. `--lang` applies. If no humidity is present, it says `No 9-day humidity is available.`

`hk-weather --today` (or `-Y`) prints only today's day from that forecast, using the Hong Kong calendar date. It includes weather, high and low, humidity, chance of rain, and wind when the Observatory sends them. `--today --json` prints that day as one JSON object. `--lang` applies. For example: `2026-10-03 Saturday  high 31°C  low 27°C  humidity 75-95%  rain Medium High`. If that day is missing, it says so.

`hk-weather --yesterday` prints yesterday's Observatory summary (`dataType=RYES`, station HKO): high, low, rainfall, and humidity. `--yesterday --json` prints that summary as one JSON object. `--lang` applies. If the summary is missing, it says `Yesterday's Observatory summary is not available.`

`hk-weather --mean-temp` prints the latest daily mean temperature at the Observatory for the current Hong Kong year (`dataType=CLMTEMP`, station HKO), for example `2026-08-31  27.7°C`. `--yesterday` still prints yesterday's high and low. `--mean-temp --json` prints that day as one JSON object. `--lang` applies. If no numeric day is present, it says `No daily mean temperature is available.`

`hk-weather --tai-mo-temp` prints the latest daily mean temperature at Tai Mo Shan, for example `2026-08-31  21.7°C`. `--mean-temp` still prints the Observatory reading. `--tai-mo-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan temperature is available.`

`hk-weather --tate-temp` prints the latest daily mean temperature at Tate's Cairn, for example `2026-08-31  24.2°C`. `--mean-temp` still prints the Observatory reading, and `--tai-mo-temp` still prints Tai Mo Shan. `--tate-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tate's Cairn temperature is available.`

`hk-weather --sai-kung-temp` prints the latest daily mean temperature at Sai Kung, for example `2026-08-31  27.7°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, and `--tate-temp` still prints Tate's Cairn. `--sai-kung-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sai Kung temperature is available.`

`hk-weather --max-temp` prints the latest daily maximum temperature at the Observatory for that same year (`dataType=CLMMAXT`, station HKO), for example `2026-08-31  29.5°C`. `--mean-temp` still prints the daily mean. `--hottest` still prints the current warmest place. `--max-temp --json` prints that day as one JSON object. `--lang` applies. If no numeric day is present, it says `No daily maximum temperature is available.`

`hk-weather --min-temp` prints the latest daily minimum temperature at the Observatory for that same year (`dataType=CLMMINT`, station HKO), for example `2026-08-31  26.2°C`. `--max-temp` still prints the daily maximum. `--coldest` still prints the current coolest place. `--min-temp --json` prints that day as one JSON object. `--lang` applies. If no numeric day is present, it says `No daily minimum temperature is available.`

`hk-weather --tai-mo-min` prints the latest daily minimum temperature at Tai Mo Shan, for example `2026-08-31  19.5°C`. `--min-temp` still prints the Observatory minimum, and `--tai-mo-temp` still prints the peak's daily mean. `--tai-mo-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan minimum temperature is available.`

`hk-weather --tate-min` prints the latest daily minimum temperature at Tate's Cairn, for example `2026-08-31  22.1°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, and `--tate-temp` still prints Tate's Cairn's daily mean. `--tate-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tate's Cairn minimum temperature is available.`

`hk-weather --tai-mo-max` prints the latest daily maximum temperature at Tai Mo Shan, for example `2026-08-31  24.1°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-temp` still prints the peak's daily mean, and `--tai-mo-min` still prints the peak's daily minimum. `--tai-mo-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan maximum temperature is available.`

`hk-weather --tseung-kwan-o-max` prints the latest daily maximum temperature at Tseung Kwan O, for example `2026-08-31  31.2°C`. `--max-temp` still prints the Observatory maximum, and `--tai-mo-max` still prints Tai Mo Shan. `--tseung-kwan-o-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tseung Kwan O maximum temperature is available.`

`hk-weather --sheung-shui-max` prints the latest daily maximum temperature at Sheung Shui, for example `2026-08-31  30.9°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, and `--tseung-kwan-o-max` still prints Tseung Kwan O. `--sheung-shui-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sheung Shui maximum temperature is available.`

`hk-weather --waglan-max` prints the latest daily maximum temperature at Waglan Island, for example `2026-08-31  31.7°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, and `--sheung-shui-max` still prints Sheung Shui. `--mean-wind` still prints Waglan Island's wind speed, and `--waglan-humidity` still prints its humidity. `--waglan-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Waglan Island maximum temperature is available.`

`hk-weather --dew-point` prints the latest daily mean dew point at the Observatory for the current Hong Kong year, for example `2026-08-31  25°C`. `--mean-temp` still prints the daily mean air temperature. `--dew-point --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No dew point is available.`

`hk-weather --park-dew` prints the latest daily mean dew point at King's Park, for example `2026-08-31  24.7°C`. `--dew-point` still prints the Observatory reading. `--park-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park dew point is available.`

`hk-weather --cheung-dew` prints the latest daily mean dew point at Cheung Chau, for example `2026-08-31  25.6°C`. `--dew-point` still prints the Observatory reading, and `--park-dew` still prints King's Park. `--cheung-wind` still prints Cheung Chau's daily mean wind speed. `--cheung-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau dew point is available.`

`hk-weather --wong-chuk-hang-dew` prints the latest daily mean dew point at Wong Chuk Hang, for example `2026-08-31  25.9°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, and `--cheung-dew` still prints Cheung Chau. `--wong-chuk-hang-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Chuk Hang dew point is available.`

`hk-weather --sai-kung-dew` prints the latest daily mean dew point at Sai Kung, for example `2026-08-31  25.2°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, and `--sai-kung-temp` still prints Sai Kung's daily mean temperature. `--sai-kung-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sai Kung dew point is available.`

`hk-weather --sha-tin-dew` prints the latest daily mean dew point at Sha Tin, for example `2026-08-31  25.4°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, and `--sha-tin-pressure` still prints Sha Tin's daily mean pressure. `--sha-tin-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin dew point is available.`

`hk-weather --cloud` prints the latest daily mean cloud amount at the Observatory for the current Hong Kong year, for example `2026-08-31  88%`. `--dew-point` still prints the dew point. `--cloud --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No cloud amount is available.`

`hk-weather --evaporation` prints the latest daily total evaporation at King's Park for the current Hong Kong year, for example `2026-08-31  2.5 mm`. `--cloud` still prints the cloud amount. `--evaporation --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No evaporation is available.`

`hk-weather --evapotranspiration` prints the latest monthly potential evapotranspiration at King's Park, for example `2026-08  43.6 mm`. `--evaporation` still prints the daily total. `--evapotranspiration --json` prints that month as one JSON object. `--lang` selects the station name. Months marked `***` are omitted. If none remain, it says `No potential evapotranspiration is available.`

`hk-weather --grass` prints yesterday's grass minimum from that same summary (`HKOReadingsMinGrassTemp`). `--yesterday` still prints the air-temperature summary. `--grass --json` prints the grass minimum as one JSON object. `--lang` applies. If the reading is missing, it says `No grass minimum is available.`

`hk-weather --sunshine` prints yesterday's sunshine duration at King's Park (`dataType=RYES`, station KP, `KingsParkReadingsSunShine`), for example `2026-10-02  4.7 hours`. `--grass` still prints yesterday's grass minimum. `--uv` still prints the current UV index. `--sunshine --json` prints that day as one JSON object. `--lang` applies. If the reading is missing, it says `No sunshine duration is available.`

`hk-weather --daily-sun` prints the latest daily bright sunshine total at King's Park, for example `2026-08-31  2.2 hours`. `--sunshine` still prints yesterday's duration. A total of zero is kept. `--daily-sun --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No daily sunshine is available.`

`hk-weather --max-uv` prints yesterday's maximum UV index at King's Park (`KingsParkReadingsMaxUVIndex` on that same report), for example `2026-10-02  6`. `--uv` still prints the current UV index. `--sunshine` still prints the sunshine duration. `--max-uv --json` prints that day as one JSON object. `--lang` applies. If the reading is missing, it says `No maximum UV index is available.`

`hk-weather --uv-peak` prints the latest daily maximum UV index at King's Park and the 15-minute period when it occurred, for example `2026-08-31  5  10:00-10:15`. `--max-uv` still prints yesterday's index, and `--fifteen-uv` still prints the latest 15-minute mean. A reading of zero is kept. `--uv-peak --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No daily maximum UV index is available.`

`hk-weather --mean-uv` prints yesterday's mean UV index at King's Park (`KingsParkReadingsMeanUVIndex` on that same report), for example `2026-10-02  2`. `--max-uv` still prints the maximum. `--uv` still prints the current UV index. `--mean-uv --json` prints that day as one JSON object. `--lang` applies. If the reading is missing, it says `No mean UV index is available.`

`hk-weather --daily-uv` prints the latest daily mean UV index at King's Park for 7 a.m. to 6 p.m., for example `2026-08-31  2`. `--mean-uv` still prints yesterday's index, `--uv-peak` still prints that day's maximum and its period, and `--max-uv` still prints yesterday's maximum. `--daily-uv --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park daily mean UV index is available.`

`hk-weather --dose` prints yesterday's average ambient gamma dose rate at King's Park (`KingsParkMicrosieverts` on that same report), for example `2026-10-02  0.15 µSv/h`. `--radiation` still prints the outdoor radiation paragraph. `--dose --json` prints that day as one JSON object. `--lang` applies. If the reading is missing, it says `No gamma dose rate is available.`

`hk-weather --hourly-dose` prints the latest hourly mean ambient gamma dose rate, for example `King's Park  0.14 µSv/h`. `--dose` still prints yesterday's King's Park average. Earlier hours in the file are omitted. `--hourly-dose --json` prints that hour as one JSON object. `--lang` selects the station names. Stations marked `N/A` are omitted. If none remain, it says `No hourly gamma dose rate is available.`

`hk-weather --accum-rain` prints accumulated rainfall at the Observatory from 1 January through yesterday (`HKOReadingsAccumRainfall` on that same summary). `--year-rain` still prints the January-to-last-month note. `--accum-rain --json` prints the total as one JSON object. `--lang` applies. If the reading is missing, it says `No accumulated rainfall is available.`

`hk-weather --avg-rain` prints the climatological normal of that accumulated total (`HKOReadingsAvgRainfall`). `--accum-rain` still prints the recorded total. `--avg-rain --json` prints the normal as one JSON object. `--lang` applies. If the reading is missing, it says `No average rainfall is available.`

`hk-weather --radiation` prints yesterday's outdoor gamma radiation report from that same summary (`HongKongDesc`). `--radiation --json` prints that paragraph as one JSON object. `--lang` applies. If the report is missing, it says `No radiation report is available.`

`hk-weather --bulletin` prints when that summary was issued (`BulletinDate` and `BulletinTime`), for example `2026-10-03 00:15`. `--yesterday` still prints the temperature and rainfall summary. `--bulletin --json` prints the issue time as one JSON object. `--lang` applies. If the time is missing, it says `No weather bulletin time is available.`

`hk-weather --radiation-note` prints the note on the normal outdoor radiation range from that same summary (`NoteDesc`). `--radiation` still prints yesterday's dose-rate report. `--radiation-note --json` prints the note as one JSON object. `--lang` applies. If the note is missing, it says `No radiation note is available.`

`hk-weather --radiation-weather` prints how that dose rate varies with the weather (`NoteDesc1`). `--radiation-note` still prints the normal range. `--radiation-weather --json` prints the note as one JSON object. `--lang` applies. If the note is missing, it says `No radiation weather note is available.`

`hk-weather --radiation-ground` prints how that dose rate varies with the ground (`NoteDesc2`). `--radiation-weather` still prints the weather note. `--radiation-ground --json` prints the note as one JSON object. `--lang` applies. If the note is missing, it says `No radiation ground note is available.`

`hk-weather --radiation-provisional` prints the provisional-data note on that report (`NoteDesc3`). `--radiation-ground` still prints the ground note. `--radiation-provisional --json` prints the note as one JSON object. `--lang` applies. If the note is missing, it says `No radiation provisional note is available.`

`hk-weather --tomorrow` (or `-T`) prints only tomorrow's day from that forecast, including wind when the Observatory sends it. `--tomorrow --json` prints that day as one JSON object. `--lang` applies. If that day is missing, it says so.

`hk-weather --weekend` (or `-E`) prints only Saturday and Sunday from that forecast, with weather, high and low, humidity, chance of rain, and wind when the Observatory includes them. `--weekend --json` prints those days as one JSON object. If the 9-day window has no weekend day, it says so.

`hk-weather --day 1` prints the first day in that same list (array index 0). `--day` takes 1 through 9. `--tomorrow` is the next Hong Kong calendar day, which is often a later entry.

`hk-weather --psr` (or `-P`) prints the chance of significant rain for each day of that forecast, for example `2026-10-03 Saturday  High`. `--psr --json` prints those days as one JSON object. `--lang` applies. A day with no PSR value shows `n/a`.

`hk-weather --wind` prints the forecast wind for each day from that same 9-day forecast. `--wind --json` prints those days as one JSON object. If no wind text is present, it says so.

`hk-weather --gust` prints the latest 10-minute mean wind and maximum gust at automatic stations, for example `Central Pier  East  5 km/h  gust 9 km/h`. `--wind` still prints the forecast wind. `--gust --json` prints those stations as one JSON object. `--lang` selects the English, Traditional Chinese, or Simplified Chinese station names. If no numeric wind remains, it says `No wind gusts are available.`

`hk-weather --prevailing` prints the latest daily prevailing wind direction at Waglan Island, for example `2026-08-31  360°`. `--wind` still prints the forecast wind, and `--gust` still prints the latest gusts. `--prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No prevailing wind is available.`

`hk-weather --cheung-prevailing` prints the latest daily prevailing wind direction at Cheung Chau, for example `2026-08-31  360°`. `--prevailing` still prints Waglan Island. `--cheung-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau prevailing wind is available.`

`hk-weather --ping-chau-prevailing` prints the latest daily prevailing wind direction at Ping Chau, for example `2026-08-31  330°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, and `--peng-chau-wind` still prints Peng Chau's mean wind speed. `--ping-chau-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ping Chau prevailing wind is available.`

`hk-weather --tai-mo-to-prevailing` prints the latest daily prevailing wind direction at Tai Mo To, for example `2026-08-31  310°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, and `--ping-chau-prevailing` still prints Ping Chau. `--tai-mo-to-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo To prevailing wind is available.`

`hk-weather --tai-po-kau-prevailing` prints the latest daily prevailing wind direction at Tai Po Kau, for example `2026-08-31  260°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, and `--tai-po-kau-wind` still prints Tai Po Kau's mean wind speed. `--tai-po-kau-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Po Kau prevailing wind is available.`

`hk-weather --mean-wind` prints the latest daily mean wind speed at Waglan Island, for example `2026-08-31  5.9 km/h`. `--prevailing` still prints the wind direction, and `--gust` still prints the latest gusts. `--mean-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No mean wind speed is available.`

`hk-weather --cheung-wind` prints the latest daily mean wind speed at Cheung Chau, for example `2026-08-31  9.2 km/h`. `--mean-wind` still prints Waglan Island, and `--cheung-prevailing` still prints the wind direction. `--cheung-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau mean wind speed is available.`

`hk-weather --lau-fau-wind` prints the latest daily mean wind speed at Lau Fau Shan, for example `2026-08-31  6.8 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, and `--lau-fau-rain` still prints Lau Fau Shan's rainfall. `--lau-fau-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Lau Fau Shan mean wind speed is available.`

`hk-weather --peng-chau-wind` prints the latest daily mean wind speed at Peng Chau, for example `2026-08-31  9.7 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, and `--lau-fau-wind` still prints Lau Fau Shan. A speed of zero is kept. `--peng-chau-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Peng Chau mean wind speed is available.`

`hk-weather --tai-po-kau-wind` prints the latest daily mean wind speed at Tai Po Kau, for example `2026-08-31  4.8 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, and `--peng-chau-wind` still prints Peng Chau. A speed of zero is kept. `--tai-po-kau-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Po Kau mean wind speed is available.`

`hk-weather --forecast-icon` prints each day's weather icon from that forecast (`ForecastIcon`), for example `2026-10-04 Sunday  54  Sunny Intervals with Showers`. `--wind` still prints the wind. `--forecast-icon --json` prints those days as one JSON object. `--lang` applies. If no icon is present, it says `No forecast icons are available.`

`hk-weather --quake` lists the latest quick earthquake message from the Observatory earthquake feed (`earthquake.php`, `dataType=qem`), for example `2026-10-03T00:34:00+08:00  M6  off east coast of Kamchatka (51.79, 159.6)`. `--quake --json` prints that list as one JSON object. `--lang` applies. If none is reported, it says so.

`hk-weather --felt` (or `-q`) prints the latest locally felt earth tremor (`dataType=feltearthquake`), including time, magnitude, place, and intensity when the Observatory sends them. `--felt --json` prints that report as one JSON object. `--lang` applies. If none is reported, it says `No locally felt earth tremor is reported.`

`hk-weather --visibility` (or `-V`) prints the latest 10-minute mean visibility (`opendata.php`, `dataType=LTMV`), for example `2026-10-03 07:30  Central  14 km`. `--visibility --json` prints those stations as one JSON object. `--lang` applies. Stations marked `N/A` are omitted. If none remain, it says so.

`hk-weather --reduced-vis` prints the latest daily hours of reduced visibility at Hong Kong International Airport, for example `2026-08-31  0 hours`. `--visibility` still prints the latest 10-minute station readings. A total of zero is kept. `--reduced-vis --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No reduced visibility is available.`

`hk-weather --tide` (or `-I`) prints today's astronomical high and low tides at Quarry Bay (`opendata.php`, `dataType=HLT`), for example `2026-10-03  01:05  2.44 m`. `--tide --json` prints that list as one JSON object. `--lang` applies. If none are present, it says so.

`hk-weather --tide-hour` prints today's hourly astronomical tide heights at Quarry Bay (`dataType=HHOT`), for example `2026-10-03  01:00  2.44 m`. `--tide` still prints the high and low times. `--tide-hour --json` prints those hours as one JSON object. `--lang` applies. Hours without a numeric height are omitted. If none remain, it says `No hourly tide heights are available.`

`hk-weather --tide-latest` prints the latest observed tide height at each tide station, for example `Quarry Bay  2.34 m`. `--tide` still prints today's high and low times, and `--tide-hour` still prints today's hourly forecast heights. Earlier times in the file are omitted. `--tide-latest --json` prints that time as one JSON object. `--lang` selects the station names. Stations marked `----` are omitted. If none remain, it says `No latest tide heights are available.`

`hk-weather --aqhi` (or `-A`) prints the current Air Quality Health Index at each monitoring station, for example `Central/Western  General Stations  3  Low`. `--aqhi --json` prints that list as one JSON object. `--lang` chooses the English, Traditional Chinese, or Simplified Chinese feed. If none are present, it says so.

`hk-weather --sunrise` (or `-U`) prints today's sunrise, sun transit, and sunset (`opendata.php`, `dataType=SRS`), for example `Rise: 06:15` and `Set: 18:09`. `--sunrise --json` prints that day as one JSON object. `--lang` applies. If the times are missing, it says so.

`hk-weather --moon` (or `-M`) prints today's moonrise, moon transit, and moonset (`opendata.php`, `dataType=MRS`), for example `Rise: 23:39` and `Set: 12:48`. `--moon --json` prints that day as one JSON object. `--lang` applies. If the times are missing, it says so.

`hk-weather --lunar` prints today's lunar date from the Observatory calendar, for example `丙午年，馬` and `八月廿三`. `--lunar --json` prints that date as one JSON object. `--lang` is sent on the request; the Observatory still returns the lunar labels in Chinese. If the date is missing, it says `No lunar date is available.`

`hk-weather --warnings` (or `-w`) prints each active warning as a code and description. `--warnings --json` prints them as one JSON object. If none are in force, it says so.

`hk-weather --warning-time` prints the issue, update, and expiry times for those active warnings (`issueTime`, `updateTime`, and `expireTime` on `dataType=warnsum`). `--warnings` still prints the codes and names. `--warning-time --json` prints those times as one JSON object. `--lang` applies. Cancelled warnings are omitted. If none are in force, it says `No weather warnings are in force.`

`hk-weather --warning-info` (or `-W`) prints each detailed warning message from `dataType=warningInfo`. `--json` and `--lang` apply. If none are present, it says so.

`hk-weather --uv` (or `-u`) prints the Observatory UV index (place, value, and description). `--uv --json` prints that same reading as one JSON object. When the Observatory has no UV reading, it says so. Current conditions stay the default.

`hk-weather --fifteen-uv` prints the latest 15-minute mean UV index at King's Park, for example `2026-10-04 08:15  1`. `--uv` still prints the hourly index from the current report. A reading of zero is kept. `--fifteen-uv --json` prints that reading as one JSON object. `--lang` selects the station name. Rows that are not numeric are omitted. If none remain, it says `No 15-minute UV index is available.`

`hk-weather --icon-time` (or `-i`) prints when the current weather icon was last updated (`iconUpdateTime`). `--icon-time --json` prints that timestamp as one JSON object. `--lang` applies. If the field is missing or blank, it says `No icon update time is available.`

`hk-weather --icon` prints the current weather icon number and label from that report (`icon`), for example `52  Sunny Intervals`. `--icon-time` still prints when the icon changed. `--forecast-icon` still prints each day's forecast icon. `--icon --json` prints the current icons as one JSON object. `--lang` applies. If no icon is present, it says `No weather icon is available.`

`hk-weather --current-updated` prints when that current report was last updated (`updateTime` on `dataType=rhrread`). The default report still prints current conditions. `--forecast-updated` still prints the local-forecast time. `--icon-time` still prints when the icon changed. `--current-updated --json` prints that timestamp as one JSON object. `--lang` applies. If the field is missing or blank, it says `No weather update time is available.`

`--lang` chooses the Observatory response language: `en` (default), `tc`, or `sc`. It is sent as the `lang` query parameter on every fetch.

`hk-weather --tips` (or `-t`) prints each special weather tip. `--tips --json` prints them as one JSON object. `--lang` applies. Current conditions stay the default.

`hk-weather --lamppost` prints the latest experimental reading from smart lamppost GF3637, for example `2026-10-04 06:50:27  27.1°C  humidity 86%  wind 4 km/h from 144°`. `--tips` still prints special weather tips. `--lamppost --json` prints that reading as one JSON object. A value marked `////` is omitted. If the lamppost has no numeric reading, it says `No smart lamppost reading is available.`

`hk-weather --rain` (or `-r`) prints rainfall by district from the current report, one line per place. `--rain --json` prints that list as one JSON object. If no readings are present, it says so.

`hk-weather --rain-period` prints the observation window for that district rainfall (`rainfall.startTime` and `rainfall.endTime`). `--rain` still prints the amounts. `--rain-period --json` prints the window as one JSON object. `--lang` applies. If the window is missing, it says `No rainfall period is available.`

`hk-weather --rain-maint` lists districts whose rainfall gauge is under maintenance (`main` on each rainfall reading). `--rain` still prints the amounts. `--rain-maint --json` prints those places as one JSON object. `--lang` applies. If none are flagged, it says `No rainfall stations are under maintenance.`

`hk-weather --hour-rain` prints past-hour rainfall from automatic weather stations (`hourlyRainfall.php`), wettest first. `--hour-rain --json` prints that list as one JSON object. `--lang` applies. A station marked under maintenance is skipped. If no readings are present, it says `No hourly rainfall readings are available.`

`hk-weather --hour-wettest` prints the wettest station from that list, for example `Wetland Park  2 mm`. `--hour-wettest --json` prints that station as one JSON object. `--lang` applies. If no readings are present, it says so.

`hk-weather --hour-driest` prints the driest station from that list, for example `Lau Fau Shan  0 mm`. `--hour-driest --json` prints that station as one JSON object. `--lang` applies. If no readings are present, it says so.

`hk-weather --rainstorm` prints the rainstorm reminder from the current report (`rainstormReminder`). `--rainstorm --json` prints that message as one JSON object. `--lang` applies. If the field is missing or blank, it says `No rainstorm reminder.`

`hk-weather --cyclone` (or `-c`) prints the tropical cyclone message from the current report (`tcmessage`). `--cyclone --json` prints those lines as one JSON object. `--lang` applies. If the field is missing or blank, it says `No tropical cyclone message.`

`hk-weather --wettest` (or `-R`) prints the wettest district from that list, for example `Sai Kung  12 mm`. `--wettest --json` prints that reading as one JSON object. `--lang` applies. If no readings are present, it says so.

`hk-weather --driest` (or `-D`) prints the driest district from that list, for example `Central & Western  0 mm`. `--driest --json` prints that reading as one JSON object. `--lang` applies. If no readings are present, it says so.

`hk-weather --nowcast` prints the heaviest grid cell in each half-hour of the rainfall nowcast, for example `2026-10-04 08:24  22.178°N  115.272°E  80.44 mm`. `--rain` still prints observed district rainfall. `--nowcast --json` prints those half-hours as one JSON object. `--lang` selects the bulletin language. A cell is omitted when its rainfall is not numeric. If none remain, it says `No rainfall nowcast is available.`

`hk-weather --daily-rain` prints the latest daily total rainfall at the Observatory, for example `2026-08-31  25 mm`. `--rain` still prints district rainfall, and `--nowcast` still prints the nowcast peaks. A total of zero is kept. `--daily-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No daily rainfall is available.`

`hk-weather --lau-fau-rain` prints the latest daily total rainfall at Lau Fau Shan, for example `2026-08-31  40 mm`. `--daily-rain` still prints the Observatory total. A total of zero is kept. `--lau-fau-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Lau Fau Shan rainfall is available.`

`hk-weather --shek-kong-rain` prints the latest daily total rainfall at Shek Kong, for example `2026-08-31  24.5 mm`. `--daily-rain` still prints the Observatory total, and `--lau-fau-rain` still prints Lau Fau Shan. A total of zero is kept. `--shek-kong-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shek Kong rainfall is available.`

`hk-weather --wetland-rain` prints the latest daily total rainfall at Wetland Park, for example `2026-08-31  55.5 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, and `--shek-kong-rain` still prints Shek Kong. A total of zero is kept. `--wetland-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wetland Park rainfall is available.`

`hk-weather --sham-shui-po-rain` prints the latest daily total rainfall at Sham Shui Po, for example `2026-08-31  35 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, and `--wetland-rain` still prints Wetland Park. A total of zero is kept. `--sham-shui-po-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sham Shui Po rainfall is available.`

`hk-weather --park-rain` prints the latest daily total rainfall at King's Park, for example `2026-08-31  33.1 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, and `--sham-shui-po-rain` still prints Sham Shui Po. `--park-dew`, `--park-pressure`, and `--park-wet` still print King's Park's other daily readings. A total of zero is kept. `--park-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park rainfall is available.`

`hk-weather --tseung-kwan-o-rain` prints the latest daily total rainfall at Tseung Kwan O, for example `2026-08-31  14.5 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, and `--park-rain` still prints King's Park. `--tseung-kwan-o-max` still prints Tseung Kwan O's daily maximum temperature. A total of zero is kept. `--tseung-kwan-o-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tseung Kwan O rainfall is available.`

`hk-weather --lightning` lists places where the current report shows lightning. `--lightning --json` prints those places as one JSON object. If none are reported, it says so.

`hk-weather --strikes` (or `-l`) prints hourly cloud-to-ground and cloud-to-cloud lightning counts by region (`dataType=LHL`). `--strikes --json` prints those counts as one JSON object. `--lang` applies. If none are available, it says `No lightning counts are available.`

`hk-weather --daily-strikes` prints the latest daily cloud-to-ground lightning count over Hong Kong, for example `2026-08-31  42`. `--strikes` still prints the hourly counts. A count of zero is kept. `--daily-strikes --json` prints that day as one JSON object. Days marked `***` are omitted. If none remain, it says `No daily lightning count is available.`

`hk-weather --cloud-strikes` prints the latest daily cloud-to-cloud lightning count over Hong Kong, for example `2026-08-31  158`. `--daily-strikes` still prints the cloud-to-ground count. A count of zero is kept. `--cloud-strikes --json` prints that day as one JSON object. Days marked `***` are omitted. If none remain, it says `No cloud-to-cloud lightning count is available.`

`hk-weather --humidity` prints humidity by place from the current report, with the record time when the Observatory includes it. `--humidity --json` prints that list as one JSON object. If no reading is present, it says so.

`hk-weather --humidity-time` prints when those humidity readings were recorded (`humidity.recordTime`). `--humidity` still prints the readings. `--temp-time` still prints when the temperatures were recorded. `--humidity-time --json` prints that timestamp as one JSON object. `--lang` applies. If the field is missing or blank, it says `No humidity time is available.`

`hk-weather --minute-humidity` prints the latest 1-minute mean relative humidity at automatic stations, for example `Chek Lap Kok  74%`. `--humidity` still prints humidity from the current weather report. `--minute-humidity --json` prints those stations as one JSON object. `--lang` selects the English, Traditional Chinese, or Simplified Chinese station names. Stations marked `N/A` are omitted. If none remain, it says `No 1-minute humidity readings are available.`

`hk-weather --humidest` prints the most humid place from the current report, for example `Chek Lap Kok  95%`. `--humidest --json` prints that reading as one JSON object. `--lang` applies. If no reading is present, it says so.

`hk-weather --least-humid` prints the least humid place from the current report, for example `King's Park  80%`. `--least-humid --json` prints that reading as one JSON object. `--lang` applies. If no reading is present, it says so.

`hk-weather --mean-humidity` prints the latest daily mean relative humidity at the Observatory, for example `2026-08-31  85%`. `--humidity` still prints the current station readings. `--mean-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No daily mean humidity is available.`

`hk-weather --tai-mo-humidity` prints the latest daily mean relative humidity at Tai Mo Shan, for example `2026-08-31  96%`. `--mean-humidity` still prints the Observatory reading. `--tai-mo-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan humidity is available.`

`hk-weather --waglan-humidity` prints the latest daily mean relative humidity at Waglan Island, for example `2026-08-31  91%`. `--mean-humidity` still prints the Observatory reading, and `--tai-mo-humidity` still prints Tai Mo Shan. `--mean-wind` still prints Waglan Island's daily mean wind speed. `--waglan-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Waglan Island humidity is available.`

`hk-weather --tate-humidity` prints the latest daily mean relative humidity at Tate's Cairn, for example `2026-08-31  95%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, and `--tate-temp` still prints Tate's Cairn's daily mean temperature. `--tate-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tate's Cairn humidity is available.`

`hk-weather --ta-kwu-ling-humidity` prints the latest daily mean relative humidity at Ta Kwu Ling, for example `2026-08-31  94%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, and `--tate-humidity` still prints Tate's Cairn. `--ta-kwu-ling-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ta Kwu Ling humidity is available.`

`hk-weather --wetland-humidity` prints the latest daily mean relative humidity at Wetland Park, for example `2026-08-31  96%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, and `--wetland-rain` still prints Wetland Park's rainfall. `--wetland-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wetland Park humidity is available.`

`hk-weather --shek-kong-humidity` prints the latest daily mean relative humidity at Shek Kong, for example `2026-08-31  93%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, and `--shek-kong-rain` still prints Shek Kong's rainfall. `--shek-kong-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shek Kong humidity is available.`

`hk-weather --temps` prints temperature by place from the current report, with the record time when the Observatory includes it. `--temps --json` prints that list as one JSON object. If no readings are present, it says so.

`hk-weather --temp-time` prints when those temperatures were recorded (`temperature.recordTime`). `--temps` still prints the readings. `--current-updated` still prints when the whole report was updated. `--temp-time --json` prints that timestamp as one JSON object. `--lang` applies. If the field is missing or blank, it says `No temperature time is available.`

`hk-weather --minute-temp` prints the latest 1-minute mean air temperature at automatic stations, for example `Chek Lap Kok  27.9°C`. `--temps` still prints temperatures from the current weather report. `--minute-temp --json` prints those stations as one JSON object. `--lang` selects the English, Traditional Chinese, or Simplified Chinese station names. Stations marked `N/A` are omitted. If none remain, it says `No 1-minute temperatures are available.`

`hk-weather --since-midnight` prints each automatic station's maximum and minimum air temperature since midnight, for example `Chek Lap Kok  high 28.2°C  low 27.8°C`. `--minute-temp` still prints the latest 1-minute temperature. `--max-temp` and `--min-temp` still print the Observatory daily climate series. `--since-midnight --json` prints those stations as one JSON object. `--lang` selects the station names. A station is omitted when both readings are missing. If none remain, it says `No temperatures since midnight are available.`

`hk-weather --pressure` prints the latest 1-minute mean sea level pressure at automatic stations, for example `Chek Lap Kok  1011.9 hPa`. `--pressure --json` prints those stations as one JSON object. `--lang` selects the English, Traditional Chinese, or Simplified Chinese station names. Stations marked `N/A` are omitted. If none remain, it says `No sea level pressure is available.`

`hk-weather --mean-pressure` prints the latest daily mean pressure at the Observatory, for example `2026-08-31  998.7 hPa`. `--pressure` still prints the latest 1-minute station readings. `--mean-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No daily mean pressure is available.`

`hk-weather --park-pressure` prints the latest daily mean pressure at King's Park, for example `2026-08-31  998.5 hPa`. `--mean-pressure` still prints the Observatory reading, and `--pressure` still prints the latest 1-minute station readings. `--park-dew` still prints King's Park's dew point. `--park-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park pressure is available.`

`hk-weather --sha-tin-pressure` prints the latest daily mean pressure at Sha Tin, for example `2026-08-31  999.1 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, and `--pressure` still prints the latest 1-minute station readings. `--sha-tin-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin pressure is available.`

`hk-weather --sheung-shui-pressure` prints the latest daily mean pressure at Sheung Shui, for example `2026-08-31  998.3 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, and `--sheung-shui-max` still prints Sheung Shui's daily maximum. `--sheung-shui-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sheung Shui pressure is available.`

`hk-weather --minute-grass` prints the latest 1-minute mean grass temperature at automatic stations, for example `King's Park  25.9°C`. `--grass` still prints yesterday's grass minimum at the Observatory. `--minute-grass --json` prints those stations as one JSON object. `--lang` selects the station names. Stations marked `N/A` are omitted. If none remain, it says `No 1-minute grass temperatures are available.`

`hk-weather --daily-grass` prints the latest daily grass minimum at King's Park, for example `2026-08-31  23.9°C`. `--grass` still prints yesterday's Observatory minimum, and `--minute-grass` still prints the 1-minute readings. A reading of zero is kept. `--daily-grass --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No daily grass temperature is available.`

`hk-weather --obs-grass` prints the latest daily grass minimum at the Observatory, for example `2026-08-31  26.6°C`. `--daily-grass` still prints the King's Park reading. `--obs-grass --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Observatory grass temperature is available.`

`hk-weather --temp-diff` prints the past 24-hour air-temperature change at automatic stations, for example `Chek Lap Kok  -0.6°C` and `HK Observatory  +0.4°C`. `--minute-temp` still prints the latest 1-minute temperature. `--temp-diff --json` prints those stations as one JSON object. `--lang` selects the station names. Stations marked `N/A` are omitted. If none remain, it says `No 24-hour temperature changes are available.`

`hk-weather --heat-index` prints the latest 10-minute mean Hong Kong Heat Index at automatic stations, for example `Happy Valley  25.8`. Earlier minutes in the file are omitted. `--heat-index --json` prints that minute as one JSON object. `--lang` selects the station names. Stations marked `N/A` are omitted. If none remain, it says `No heat index is available.`

`hk-weather --daily-heat` prints the latest daily maximum Hong Kong Heat Index at King's Park, for example `2026-08-31  29.2`. `--heat-index` still prints the latest 10-minute readings. `--daily-heat --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No daily maximum heat index is available.`

`hk-weather --mean-heat` prints the latest daily mean Hong Kong Heat Index at King's Park, for example `2026-08-31  26.6`. `--daily-heat` still prints that day's maximum, and `--heat-index` still prints the latest 10-minute readings. `--mean-heat --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No daily mean heat index is available.`

`hk-weather --wbgt` prints the latest 60-minute mean Wet Bulb Globe Temperature at automatic stations, for example `Happy Valley  25.8°C`. `--heat-index` still prints the Hong Kong Heat Index. Earlier minutes in the file are omitted. `--wbgt --json` prints that minute as one JSON object. `--lang` selects the station names. Stations marked `N/A` are omitted. If none remain, it says `No wet bulb globe temperature is available.`

`hk-weather --wet-bulb` prints the latest daily mean wet-bulb temperature at the Observatory, for example `2026-08-31  25.8°C`. `--wbgt` still prints the current Wet Bulb Globe Temperature. `--dew-point` still prints the dew point. `--wet-bulb --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No wet bulb temperature is available.`

`hk-weather --airport-wet` prints the latest daily mean wet-bulb temperature at Hong Kong International Airport, for example `2026-07-31  24.4°C`. `--wet-bulb` still prints the Observatory reading. `--airport-wet --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No airport wet bulb temperature is available.`

`hk-weather --park-wet` prints the latest daily mean wet-bulb temperature at King's Park, for example `2026-08-31  25.6°C`. `--wet-bulb` still prints the Observatory reading, and `--airport-wet` still prints the airport. `--park-dew` still prints King's Park's dew point. `--park-wet --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park wet bulb temperature is available.`

`hk-weather --sha-lo-wan-wet` prints the latest daily mean wet-bulb temperature at Sha Lo Wan, for example `2026-08-31  25.9°C`. `--wet-bulb` still prints the Observatory reading, `--airport-wet` still prints the airport, and `--park-wet` still prints King's Park. `--sha-lo-wan-wet --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Lo Wan wet bulb temperature is available.`

`hk-weather --solar` prints the latest 1-minute global, direct, and diffuse solar radiation, for example `Kau Sai Chau  global 1  direct 0  diffuse 1 W/m²`. Earlier minutes in the file are omitted. `--solar --json` prints that minute as one JSON object. `--lang` selects the station names. A station is omitted when any component is `N/A`. If none remain, it says `No solar radiation is available.`

`hk-weather --global-solar` prints the latest daily global solar radiation at King's Park, for example `2026-08-31  8.95 MJ/m²`. `--solar` still prints the latest 1-minute readings. `--global-solar --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No global solar radiation is available.`

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
