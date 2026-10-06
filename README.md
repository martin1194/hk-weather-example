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
hk-weather --north-point-am-sea
hk-weather --north-point-am-sea --json
hk-weather --north-point-pm-sea
hk-weather --north-point-pm-sea --json
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
hk-weather --sha-tin-temp
hk-weather --sha-tin-temp --json
hk-weather --sheung-shui-temp
hk-weather --sheung-shui-temp --json
hk-weather --wong-chuk-hang-temp
hk-weather --wong-chuk-hang-temp --json
hk-weather --lau-fau-temp
hk-weather --lau-fau-temp --json
hk-weather --tseung-kwan-o-temp
hk-weather --tseung-kwan-o-temp --json
hk-weather --sham-shui-po-temp
hk-weather --sham-shui-po-temp --json
hk-weather --shek-kong-temp
hk-weather --shek-kong-temp --json
hk-weather --wetland-temp
hk-weather --wetland-temp --json
hk-weather --ta-kwu-ling-temp
hk-weather --ta-kwu-ling-temp --json
hk-weather --peng-chau-temp
hk-weather --peng-chau-temp --json
hk-weather --park-temp
hk-weather --park-temp --json
hk-weather --cheung-chau-temp
hk-weather --cheung-chau-temp --json
hk-weather --waglan-temp
hk-weather --waglan-temp --json
hk-weather --ping-chau-temp
hk-weather --ping-chau-temp --json
hk-weather --sha-lo-wan-temp
hk-weather --sha-lo-wan-temp --json
hk-weather --airport-temp
hk-weather --airport-temp --json
hk-weather --clear-water-bay-temp
hk-weather --clear-water-bay-temp --json
hk-weather --hong-kong-park-temp
hk-weather --hong-kong-park-temp --json
hk-weather --ngong-ping-temp
hk-weather --ngong-ping-temp --json
hk-weather --kwun-tong-temp
hk-weather --kwun-tong-temp --json
hk-weather --wong-tai-sin-temp
hk-weather --wong-tai-sin-temp --json
hk-weather --tsuen-wan-temp
hk-weather --tsuen-wan-temp --json
hk-weather --yuen-long-park-temp
hk-weather --yuen-long-park-temp --json
hk-weather --tap-mun-temp
hk-weather --tap-mun-temp --json
hk-weather --shau-kei-wan-temp
hk-weather --shau-kei-wan-temp --json
hk-weather --happy-valley-temp
hk-weather --happy-valley-temp --json
hk-weather --tai-mei-tuk-temp
hk-weather --tai-mei-tuk-temp --json
hk-weather --kau-sai-chau-temp
hk-weather --kau-sai-chau-temp --json
hk-weather --kadoorie-farm-temp
hk-weather --kadoorie-farm-temp --json
hk-weather --the-peak-temp
hk-weather --the-peak-temp --json
hk-weather --kat-o-temp
hk-weather --kat-o-temp --json
hk-weather --pak-tam-chung-temp
hk-weather --pak-tam-chung-temp --json
hk-weather --beas-river-temp
hk-weather --beas-river-temp --json
hk-weather --bluff-head-temp
hk-weather --bluff-head-temp --json
hk-weather --runway-park-temp
hk-weather --runway-park-temp --json
hk-weather --kowloon-city-temp
hk-weather --kowloon-city-temp --json
hk-weather --nei-lak-shan-temp
hk-weather --nei-lak-shan-temp --json
hk-weather --new-tsing-yi-temp
hk-weather --new-tsing-yi-temp --json
hk-weather --stanley-temp
hk-weather --stanley-temp --json
hk-weather --shing-mun-valley-temp
hk-weather --shing-mun-valley-temp --json
hk-weather --tuen-mun-home-temp
hk-weather --tuen-mun-home-temp --json
hk-weather --buoy-2-temp
hk-weather --buoy-2-temp --json
hk-weather --buoy-8-temp
hk-weather --buoy-8-temp --json
hk-weather --max-temp
hk-weather --max-temp --json
hk-weather --min-temp
hk-weather --min-temp --json
hk-weather --tai-mo-min
hk-weather --tai-mo-min --json
hk-weather --tate-min
hk-weather --tate-min --json
hk-weather --sai-kung-min
hk-weather --sai-kung-min --json
hk-weather --wong-chuk-hang-min
hk-weather --wong-chuk-hang-min --json
hk-weather --waglan-min
hk-weather --waglan-min --json
hk-weather --sha-tin-min
hk-weather --sha-tin-min --json
hk-weather --cheung-chau-min
hk-weather --cheung-chau-min --json
hk-weather --park-min
hk-weather --park-min --json
hk-weather --lau-fau-min
hk-weather --lau-fau-min --json
hk-weather --sheung-shui-min
hk-weather --sheung-shui-min --json
hk-weather --tseung-kwan-o-min
hk-weather --tseung-kwan-o-min --json
hk-weather --sham-shui-po-min
hk-weather --sham-shui-po-min --json
hk-weather --shek-kong-min
hk-weather --shek-kong-min --json
hk-weather --wetland-min
hk-weather --wetland-min --json
hk-weather --ta-kwu-ling-min
hk-weather --ta-kwu-ling-min --json
hk-weather --sha-lo-wan-min
hk-weather --sha-lo-wan-min --json
hk-weather --airport-min
hk-weather --airport-min --json
hk-weather --yuen-long-park-min
hk-weather --yuen-long-park-min --json
hk-weather --clear-water-bay-min
hk-weather --clear-water-bay-min --json
hk-weather --tap-mun-min
hk-weather --tap-mun-min --json
hk-weather --hong-kong-park-min
hk-weather --hong-kong-park-min --json
hk-weather --ngong-ping-min
hk-weather --ngong-ping-min --json
hk-weather --kwun-tong-min
hk-weather --kwun-tong-min --json
hk-weather --wong-tai-sin-min
hk-weather --wong-tai-sin-min --json
hk-weather --tsuen-wan-min
hk-weather --tsuen-wan-min --json
hk-weather --kau-sai-chau-min
hk-weather --kau-sai-chau-min --json
hk-weather --kadoorie-farm-min
hk-weather --kadoorie-farm-min --json
hk-weather --the-peak-min
hk-weather --the-peak-min --json
hk-weather --kat-o-min
hk-weather --kat-o-min --json
hk-weather --pak-tam-chung-min
hk-weather --pak-tam-chung-min --json
hk-weather --beas-river-min
hk-weather --beas-river-min --json
hk-weather --kowloon-city-min
hk-weather --kowloon-city-min --json
hk-weather --new-tsing-yi-min
hk-weather --new-tsing-yi-min --json
hk-weather --stanley-min
hk-weather --stanley-min --json
hk-weather --shing-mun-valley-min
hk-weather --shing-mun-valley-min --json
hk-weather --tuen-mun-home-min
hk-weather --tuen-mun-home-min --json
hk-weather --buoy-2-min
hk-weather --buoy-2-min --json
hk-weather --tai-mo-max
hk-weather --tai-mo-max --json
hk-weather --tseung-kwan-o-max
hk-weather --tseung-kwan-o-max --json
hk-weather --sheung-shui-max
hk-weather --sheung-shui-max --json
hk-weather --waglan-max
hk-weather --waglan-max --json
hk-weather --shek-kong-max
hk-weather --shek-kong-max --json
hk-weather --cheung-chau-max
hk-weather --cheung-chau-max --json
hk-weather --park-max
hk-weather --park-max --json
hk-weather --lau-fau-max
hk-weather --lau-fau-max --json
hk-weather --sai-kung-max
hk-weather --sai-kung-max --json
hk-weather --sha-tin-max
hk-weather --sha-tin-max --json
hk-weather --tate-max
hk-weather --tate-max --json
hk-weather --wong-chuk-hang-max
hk-weather --wong-chuk-hang-max --json
hk-weather --sham-shui-po-max
hk-weather --sham-shui-po-max --json
hk-weather --wetland-max
hk-weather --wetland-max --json
hk-weather --ta-kwu-ling-max
hk-weather --ta-kwu-ling-max --json
hk-weather --sha-lo-wan-max
hk-weather --sha-lo-wan-max --json
hk-weather --airport-max
hk-weather --airport-max --json
hk-weather --yuen-long-park-max
hk-weather --yuen-long-park-max --json
hk-weather --clear-water-bay-max
hk-weather --clear-water-bay-max --json
hk-weather --tap-mun-max
hk-weather --tap-mun-max --json
hk-weather --hong-kong-park-max
hk-weather --hong-kong-park-max --json
hk-weather --ngong-ping-max
hk-weather --ngong-ping-max --json
hk-weather --kwun-tong-max
hk-weather --kwun-tong-max --json
hk-weather --wong-tai-sin-max
hk-weather --wong-tai-sin-max --json
hk-weather --tsuen-wan-max
hk-weather --tsuen-wan-max --json
hk-weather --kau-sai-chau-max
hk-weather --kau-sai-chau-max --json
hk-weather --kadoorie-farm-max
hk-weather --kadoorie-farm-max --json
hk-weather --the-peak-max
hk-weather --the-peak-max --json
hk-weather --kat-o-max
hk-weather --kat-o-max --json
hk-weather --pak-tam-chung-max
hk-weather --pak-tam-chung-max --json
hk-weather --beas-river-max
hk-weather --beas-river-max --json
hk-weather --kowloon-city-max
hk-weather --kowloon-city-max --json
hk-weather --new-tsing-yi-max
hk-weather --new-tsing-yi-max --json
hk-weather --stanley-max
hk-weather --stanley-max --json
hk-weather --shing-mun-valley-max
hk-weather --shing-mun-valley-max --json
hk-weather --tuen-mun-home-max
hk-weather --tuen-mun-home-max --json
hk-weather --buoy-2-max
hk-weather --buoy-2-max --json
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
hk-weather --sheung-shui-dew
hk-weather --sheung-shui-dew --json
hk-weather --waglan-dew
hk-weather --waglan-dew --json
hk-weather --lau-fau-dew
hk-weather --lau-fau-dew --json
hk-weather --wetland-dew
hk-weather --wetland-dew --json
hk-weather --ta-kwu-ling-dew
hk-weather --ta-kwu-ling-dew --json
hk-weather --shek-kong-dew
hk-weather --shek-kong-dew --json
hk-weather --tseung-kwan-o-dew
hk-weather --tseung-kwan-o-dew --json
hk-weather --tai-mo-dew
hk-weather --tai-mo-dew --json
hk-weather --peng-chau-dew
hk-weather --peng-chau-dew --json
hk-weather --sha-lo-wan-dew
hk-weather --sha-lo-wan-dew --json
hk-weather --airport-dew
hk-weather --airport-dew --json
hk-weather --clear-water-bay-dew
hk-weather --clear-water-bay-dew --json
hk-weather --hong-kong-park-dew
hk-weather --hong-kong-park-dew --json
hk-weather --tsuen-wan-dew
hk-weather --tsuen-wan-dew --json
hk-weather --shau-kei-wan-dew
hk-weather --shau-kei-wan-dew --json
hk-weather --kau-sai-chau-dew
hk-weather --kau-sai-chau-dew --json
hk-weather --pak-tam-chung-dew
hk-weather --pak-tam-chung-dew --json
hk-weather --beas-river-dew
hk-weather --beas-river-dew --json
hk-weather --runway-park-dew
hk-weather --runway-park-dew --json
hk-weather --kowloon-city-dew
hk-weather --kowloon-city-dew --json
hk-weather --nei-lak-shan-dew
hk-weather --nei-lak-shan-dew --json
hk-weather --new-tsing-yi-dew
hk-weather --new-tsing-yi-dew --json
hk-weather --tate-dew
hk-weather --tate-dew --json
hk-weather --shing-mun-valley-dew
hk-weather --shing-mun-valley-dew --json
hk-weather --tuen-mun-home-dew
hk-weather --tuen-mun-home-dew --json
hk-weather --buoy-2-dew
hk-weather --buoy-2-dew --json
hk-weather --buoy-8-dew
hk-weather --buoy-8-dew --json
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
hk-weather --park-prevailing
hk-weather --park-prevailing --json
hk-weather --lau-fau-prevailing
hk-weather --lau-fau-prevailing --json
hk-weather --sha-lo-wan-prevailing
hk-weather --sha-lo-wan-prevailing --json
hk-weather --wong-chuk-hang-prevailing
hk-weather --wong-chuk-hang-prevailing --json
hk-weather --sai-kung-prevailing
hk-weather --sai-kung-prevailing --json
hk-weather --tseung-kwan-o-prevailing
hk-weather --tseung-kwan-o-prevailing --json
hk-weather --shek-kong-prevailing
hk-weather --shek-kong-prevailing --json
hk-weather --sha-tin-prevailing
hk-weather --sha-tin-prevailing --json
hk-weather --ta-kwu-ling-prevailing
hk-weather --ta-kwu-ling-prevailing --json
hk-weather --wetland-prevailing
hk-weather --wetland-prevailing --json
hk-weather --tai-mo-prevailing
hk-weather --tai-mo-prevailing --json
hk-weather --airport-prevailing
hk-weather --airport-prevailing --json
hk-weather --kai-tak-prevailing
hk-weather --kai-tak-prevailing --json
hk-weather --green-island-prevailing
hk-weather --green-island-prevailing --json
hk-weather --ngong-ping-prevailing
hk-weather --ngong-ping-prevailing --json
hk-weather --tai-mei-tuk-prevailing
hk-weather --tai-mei-tuk-prevailing --json
hk-weather --central-pier-prevailing
hk-weather --central-pier-prevailing --json
hk-weather --nei-lak-shan-prevailing
hk-weather --nei-lak-shan-prevailing --json
hk-weather --buoy-2-prevailing
hk-weather --buoy-2-prevailing --json
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
hk-weather --tai-mo-to-wind
hk-weather --tai-mo-to-wind --json
hk-weather --tai-mo-wind
hk-weather --tai-mo-wind --json
hk-weather --tate-wind
hk-weather --tate-wind --json
hk-weather --shek-kong-wind
hk-weather --shek-kong-wind --json
hk-weather --sai-kung-wind
hk-weather --sai-kung-wind --json
hk-weather --sha-tin-wind
hk-weather --sha-tin-wind --json
hk-weather --wong-chuk-hang-wind
hk-weather --wong-chuk-hang-wind --json
hk-weather --park-wind
hk-weather --park-wind --json
hk-weather --wetland-wind
hk-weather --wetland-wind --json
hk-weather --tseung-kwan-o-wind
hk-weather --tseung-kwan-o-wind --json
hk-weather --ta-kwu-ling-wind
hk-weather --ta-kwu-ling-wind --json
hk-weather --sha-lo-wan-wind
hk-weather --sha-lo-wan-wind --json
hk-weather --ping-chau-wind
hk-weather --ping-chau-wind --json
hk-weather --airport-wind
hk-weather --airport-wind --json
hk-weather --green-island-wind
hk-weather --green-island-wind --json
hk-weather --ngong-ping-wind
hk-weather --ngong-ping-wind --json
hk-weather --tai-mei-tuk-wind
hk-weather --tai-mei-tuk-wind --json
hk-weather --lamma-island-wind
hk-weather --lamma-island-wind --json
hk-weather --kai-tak-wind
hk-weather --kai-tak-wind --json
hk-weather --central-pier-wind
hk-weather --central-pier-wind --json
hk-weather --nei-lak-shan-wind
hk-weather --nei-lak-shan-wind --json
hk-weather --buoy-2-wind
hk-weather --buoy-2-wind --json
hk-weather --buoy-8-wind
hk-weather --buoy-8-wind --json
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
hk-weather --sheung-shui-rain
hk-weather --sheung-shui-rain --json
hk-weather --sha-tin-rain
hk-weather --sha-tin-rain --json
hk-weather --ta-kwu-ling-rain
hk-weather --ta-kwu-ling-rain --json
hk-weather --cheung-chau-rain
hk-weather --cheung-chau-rain --json
hk-weather --waglan-rain
hk-weather --waglan-rain --json
hk-weather --tate-rain
hk-weather --tate-rain --json
hk-weather --peng-chau-rain
hk-weather --peng-chau-rain --json
hk-weather --ping-chau-rain
hk-weather --ping-chau-rain --json
hk-weather --tai-mo-rain
hk-weather --tai-mo-rain --json
hk-weather --sha-lo-wan-rain
hk-weather --sha-lo-wan-rain --json
hk-weather --airport-rain
hk-weather --airport-rain --json
hk-weather --green-island-rain
hk-weather --green-island-rain --json
hk-weather --tsuen-wan-rain
hk-weather --tsuen-wan-rain --json
hk-weather --tap-mun-rain
hk-weather --tap-mun-rain --json
hk-weather --clear-water-bay-rain
hk-weather --clear-water-bay-rain --json
hk-weather --shau-kei-wan-rain
hk-weather --shau-kei-wan-rain --json
hk-weather --happy-valley-rain
hk-weather --happy-valley-rain --json
hk-weather --tai-mei-tuk-rain
hk-weather --tai-mei-tuk-rain --json
hk-weather --kadoorie-farm-rain
hk-weather --kadoorie-farm-rain --json
hk-weather --the-peak-rain
hk-weather --the-peak-rain --json
hk-weather --pak-tam-chung-rain
hk-weather --pak-tam-chung-rain --json
hk-weather --ching-pak-house-rain
hk-weather --ching-pak-house-rain --json
hk-weather --kau-sai-chau-rain
hk-weather --kau-sai-chau-rain --json
hk-weather --kai-tak-rain
hk-weather --kai-tak-rain --json
hk-weather --sha-tau-kok-rain
hk-weather --sha-tau-kok-rain --json
hk-weather --beas-river-rain
hk-weather --beas-river-rain --json
hk-weather --kat-o-rain
hk-weather --kat-o-rain --json
hk-weather --tap-shek-kok-rain
hk-weather --tap-shek-kok-rain --json
hk-weather --tsim-bei-tsui-rain
hk-weather --tsim-bei-tsui-rain --json
hk-weather --tai-mei-tuk-pump-rain
hk-weather --tai-mei-tuk-pump-rain --json
hk-weather --ngong-ping-reservoir-rain
hk-weather --ngong-ping-reservoir-rain --json
hk-weather --discovery-bay-rain
hk-weather --discovery-bay-rain --json
hk-weather --adventist-college-rain
hk-weather --adventist-college-rain --json
hk-weather --wong-shiu-chi-rain
hk-weather --wong-shiu-chi-rain --json
hk-weather --au-tau-rain
hk-weather --au-tau-rain --json
hk-weather --lok-ma-chau-rain
hk-weather --lok-ma-chau-rain --json
hk-weather --lamma-island-rain
hk-weather --lamma-island-rain --json
hk-weather --tuen-mun-home-rain
hk-weather --tuen-mun-home-rain --json
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
hk-weather --lau-fau-humidity
hk-weather --lau-fau-humidity --json
hk-weather --park-humidity
hk-weather --park-humidity --json
hk-weather --sai-kung-humidity
hk-weather --sai-kung-humidity --json
hk-weather --cheung-chau-humidity
hk-weather --cheung-chau-humidity --json
hk-weather --sha-tin-humidity
hk-weather --sha-tin-humidity --json
hk-weather --sheung-shui-humidity
hk-weather --sheung-shui-humidity --json
hk-weather --wong-chuk-hang-humidity
hk-weather --wong-chuk-hang-humidity --json
hk-weather --tseung-kwan-o-humidity
hk-weather --tseung-kwan-o-humidity --json
hk-weather --peng-chau-humidity
hk-weather --peng-chau-humidity --json
hk-weather --sha-lo-wan-humidity
hk-weather --sha-lo-wan-humidity --json
hk-weather --airport-humidity
hk-weather --airport-humidity --json
hk-weather --tsuen-wan-humidity
hk-weather --tsuen-wan-humidity --json
hk-weather --hong-kong-park-humidity
hk-weather --hong-kong-park-humidity --json
hk-weather --clear-water-bay-humidity
hk-weather --clear-water-bay-humidity --json
hk-weather --shau-kei-wan-humidity
hk-weather --shau-kei-wan-humidity --json
hk-weather --kau-sai-chau-humidity
hk-weather --kau-sai-chau-humidity --json
hk-weather --pak-tam-chung-humidity
hk-weather --pak-tam-chung-humidity --json
hk-weather --beas-river-humidity
hk-weather --beas-river-humidity --json
hk-weather --runway-park-humidity
hk-weather --runway-park-humidity --json
hk-weather --kowloon-city-humidity
hk-weather --kowloon-city-humidity --json
hk-weather --nei-lak-shan-humidity
hk-weather --nei-lak-shan-humidity --json
hk-weather --new-tsing-yi-humidity
hk-weather --new-tsing-yi-humidity --json
hk-weather --shing-mun-valley-humidity
hk-weather --shing-mun-valley-humidity --json
hk-weather --tuen-mun-home-humidity
hk-weather --tuen-mun-home-humidity --json
hk-weather --buoy-2-humidity
hk-weather --buoy-2-humidity --json
hk-weather --buoy-8-humidity
hk-weather --buoy-8-humidity --json
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
hk-weather --waglan-pressure
hk-weather --waglan-pressure --json
hk-weather --cheung-chau-pressure
hk-weather --cheung-chau-pressure --json
hk-weather --lau-fau-pressure
hk-weather --lau-fau-pressure --json
hk-weather --tate-pressure
hk-weather --tate-pressure --json
hk-weather --wetland-pressure
hk-weather --wetland-pressure --json
hk-weather --peng-chau-pressure
hk-weather --peng-chau-pressure --json
hk-weather --tai-mo-pressure
hk-weather --tai-mo-pressure --json
hk-weather --sha-lo-wan-pressure
hk-weather --sha-lo-wan-pressure --json
hk-weather --shek-kong-pressure
hk-weather --shek-kong-pressure --json
hk-weather --ta-kwu-ling-pressure
hk-weather --ta-kwu-ling-pressure --json
hk-weather --airport-pressure
hk-weather --airport-pressure --json
hk-weather --nei-lak-shan-pressure
hk-weather --nei-lak-shan-pressure --json
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
hk-weather --kau-sai-chau-solar
hk-weather --kau-sai-chau-solar --json
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

`hk-weather --north-point-am-sea` prints the latest daily mean morning sea temperature at North Point, for example `2026-08-31  25°C`. `--sea-temp` still prints the sea temperature from the 9-day forecast. `--north-point-am-sea --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `北角` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No North Point morning sea temperature is available.`

`hk-weather --north-point-pm-sea` prints the latest daily mean afternoon sea temperature at North Point, for example `2026-08-31  25°C`. `--north-point-am-sea` still prints the morning reading, and `--sea-temp` still prints the sea temperature from the 9-day forecast. `--north-point-pm-sea --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `北角` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No North Point afternoon sea temperature is available.`

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

`hk-weather --sha-tin-temp` prints the latest daily mean temperature at Sha Tin, for example `2026-08-31  27.5°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, and `--sai-kung-temp` still prints Sai Kung. `--sha-tin-min` still prints Sha Tin's minimum, `--sha-tin-max` still prints its maximum, `--sha-tin-humidity` still prints its humidity, `--sha-tin-dew` still prints its dew point, `--sha-tin-pressure` still prints its pressure, and `--sha-tin-rain` still prints its rainfall. `--sha-tin-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin temperature is available.`

`hk-weather --sheung-shui-temp` prints the latest daily mean temperature at Sheung Shui, for example `2026-08-31  27.1°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, and `--sha-tin-temp` still prints Sha Tin. `--sheung-shui-min` still prints Sheung Shui's minimum, `--sheung-shui-max` still prints its maximum, `--sheung-shui-dew` still prints its dew point, `--sheung-shui-pressure` still prints its pressure, `--sheung-shui-rain` still prints its rainfall, and `--sheung-shui-humidity` still prints its humidity. `--sheung-shui-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sheung Shui temperature is available.`

`hk-weather --wong-chuk-hang-temp` prints the latest daily mean temperature at Wong Chuk Hang, for example `2026-08-31  27.7°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, and `--sheung-shui-temp` still prints Sheung Shui. `--wong-chuk-hang-min` still prints Wong Chuk Hang's minimum, `--wong-chuk-hang-max` still prints its maximum, `--wong-chuk-hang-dew` still prints its dew point, and `--wong-chuk-hang-humidity` still prints its humidity. `--wong-chuk-hang-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Chuk Hang temperature is available.`

`hk-weather --lau-fau-temp` prints the latest daily mean temperature at Lau Fau Shan, for example `2026-08-31  26.6°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, and `--wong-chuk-hang-temp` still prints Wong Chuk Hang. `--lau-fau-max` still prints Lau Fau Shan's maximum, `--lau-fau-min` still prints its minimum, `--lau-fau-dew` still prints its dew point, `--lau-fau-rain` still prints its rainfall, `--lau-fau-wind` still prints its wind speed, `--lau-fau-humidity` still prints its humidity, and `--lau-fau-pressure` still prints its pressure. `--lau-fau-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Lau Fau Shan temperature is available.`

`hk-weather --tseung-kwan-o-temp` prints the latest daily mean temperature at Tseung Kwan O, for example `2026-08-31  26.7°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, and `--lau-fau-temp` still prints Lau Fau Shan. `--tseung-kwan-o-max` still prints Tseung Kwan O's maximum, `--tseung-kwan-o-min` still prints its minimum, and `--tseung-kwan-o-rain` still prints its rainfall. `--tseung-kwan-o-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tseung Kwan O temperature is available.`

`hk-weather --sham-shui-po-temp` prints the latest daily mean temperature at Sham Shui Po, for example `2026-08-31  27.5°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, `--lau-fau-temp` still prints Lau Fau Shan, and `--tseung-kwan-o-temp` still prints Tseung Kwan O. `--sham-shui-po-min` still prints Sham Shui Po's minimum, and `--sham-shui-po-rain` still prints its rainfall. `--sham-shui-po-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sham Shui Po temperature is available.`

`hk-weather --shek-kong-temp` prints the latest daily mean temperature at Shek Kong, for example `2026-08-31  27.1°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, `--lau-fau-temp` still prints Lau Fau Shan, `--tseung-kwan-o-temp` still prints Tseung Kwan O, and `--sham-shui-po-temp` still prints Sham Shui Po. `--shek-kong-max` still prints Shek Kong's maximum, `--shek-kong-min` still prints its minimum, `--shek-kong-dew` still prints its dew point, `--shek-kong-humidity` still prints its humidity, and `--shek-kong-rain` still prints its rainfall. `--shek-kong-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shek Kong temperature is available.`

`hk-weather --wetland-temp` prints the latest daily mean temperature at Wetland Park, for example `2026-08-31  26.6°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, `--lau-fau-temp` still prints Lau Fau Shan, `--tseung-kwan-o-temp` still prints Tseung Kwan O, `--sham-shui-po-temp` still prints Sham Shui Po, and `--shek-kong-temp` still prints Shek Kong. `--wetland-min` still prints Wetland Park's minimum, `--wetland-dew` still prints its dew point, `--wetland-humidity` still prints its humidity, `--wetland-pressure` still prints its pressure, and `--wetland-rain` still prints its rainfall. `--wetland-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wetland Park temperature is available.`

`hk-weather --ta-kwu-ling-temp` prints the latest daily mean temperature at Ta Kwu Ling, for example `2026-08-31  26.8°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, `--lau-fau-temp` still prints Lau Fau Shan, `--tseung-kwan-o-temp` still prints Tseung Kwan O, `--sham-shui-po-temp` still prints Sham Shui Po, `--shek-kong-temp` still prints Shek Kong, and `--wetland-temp` still prints Wetland Park. `--ta-kwu-ling-min` still prints Ta Kwu Ling's minimum, `--ta-kwu-ling-dew` still prints its dew point, `--ta-kwu-ling-humidity` still prints its humidity, and `--ta-kwu-ling-rain` still prints its rainfall. `--ta-kwu-ling-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ta Kwu Ling temperature is available.`

`hk-weather --peng-chau-temp` prints the latest daily mean temperature at Peng Chau, for example `2026-08-31  27.6°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, `--lau-fau-temp` still prints Lau Fau Shan, `--tseung-kwan-o-temp` still prints Tseung Kwan O, `--sham-shui-po-temp` still prints Sham Shui Po, `--shek-kong-temp` still prints Shek Kong, `--wetland-temp` still prints Wetland Park, and `--ta-kwu-ling-temp` still prints Ta Kwu Ling. `--peng-chau-wind` still prints Peng Chau's wind speed, and `--peng-chau-rain` still prints its rainfall. `--peng-chau-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Peng Chau temperature is available.`

`hk-weather --park-temp` prints the latest daily mean temperature at King's Park, for example `2026-08-31  27.6°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, `--lau-fau-temp` still prints Lau Fau Shan, `--tseung-kwan-o-temp` still prints Tseung Kwan O, `--sham-shui-po-temp` still prints Sham Shui Po, `--shek-kong-temp` still prints Shek Kong, `--wetland-temp` still prints Wetland Park, `--ta-kwu-ling-temp` still prints Ta Kwu Ling, and `--peng-chau-temp` still prints Peng Chau. `--park-max` still prints King's Park's maximum, `--park-min` still prints its minimum, `--park-dew` still prints its dew point, `--park-humidity` still prints its humidity, `--park-pressure` still prints its pressure, `--park-wet` still prints its wet-bulb temperature, and `--park-rain` still prints its rainfall. `--park-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park temperature is available.`

`hk-weather --cheung-chau-temp` prints the latest daily mean temperature at Cheung Chau, for example `2026-08-31  27°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, `--lau-fau-temp` still prints Lau Fau Shan, `--tseung-kwan-o-temp` still prints Tseung Kwan O, `--sham-shui-po-temp` still prints Sham Shui Po, `--shek-kong-temp` still prints Shek Kong, `--wetland-temp` still prints Wetland Park, `--ta-kwu-ling-temp` still prints Ta Kwu Ling, `--peng-chau-temp` still prints Peng Chau, and `--park-temp` still prints King's Park. `--cheung-chau-max` still prints Cheung Chau's maximum, `--cheung-chau-min` still prints its minimum, `--cheung-chau-humidity` still prints its humidity, `--cheung-wind` still prints its wind speed, `--cheung-prevailing` still prints its prevailing direction, `--cheung-dew` still prints its dew point, and `--cheung-chau-rain` still prints its rainfall. `--cheung-chau-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau temperature is available.`

`hk-weather --waglan-temp` prints the latest daily mean temperature at Waglan Island, for example `2026-08-31  27.6°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, `--lau-fau-temp` still prints Lau Fau Shan, `--tseung-kwan-o-temp` still prints Tseung Kwan O, `--sham-shui-po-temp` still prints Sham Shui Po, `--shek-kong-temp` still prints Shek Kong, `--wetland-temp` still prints Wetland Park, `--ta-kwu-ling-temp` still prints Ta Kwu Ling, `--peng-chau-temp` still prints Peng Chau, `--park-temp` still prints King's Park, and `--cheung-chau-temp` still prints Cheung Chau. `--waglan-max` still prints Waglan Island's maximum, `--waglan-min` still prints its minimum, `--waglan-dew` still prints its dew point, `--waglan-humidity` still prints its humidity, `--waglan-pressure` still prints its pressure, `--waglan-rain` still prints its rainfall, and `--mean-wind` still prints its wind speed. `--waglan-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Waglan Island temperature is available.`

`hk-weather --ping-chau-temp` prints the latest daily mean temperature at Ping Chau, for example `2026-08-31  26°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, `--lau-fau-temp` still prints Lau Fau Shan, `--tseung-kwan-o-temp` still prints Tseung Kwan O, `--sham-shui-po-temp` still prints Sham Shui Po, `--shek-kong-temp` still prints Shek Kong, `--wetland-temp` still prints Wetland Park, `--ta-kwu-ling-temp` still prints Ta Kwu Ling, `--peng-chau-temp` still prints Peng Chau, `--park-temp` still prints King's Park, `--cheung-chau-temp` still prints Cheung Chau, and `--waglan-temp` still prints Waglan Island. `--ping-chau-prevailing` still prints Ping Chau's prevailing wind direction. `--ping-chau-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ping Chau temperature is available.`

`hk-weather --sha-lo-wan-temp` prints the latest daily mean temperature at Sha Lo Wan, for example `2026-08-31  26.6°C`. `--mean-temp` still prints the Observatory reading, `--tai-mo-temp` still prints Tai Mo Shan, `--tate-temp` still prints Tate's Cairn, `--sai-kung-temp` still prints Sai Kung, `--sha-tin-temp` still prints Sha Tin, `--sheung-shui-temp` still prints Sheung Shui, `--wong-chuk-hang-temp` still prints Wong Chuk Hang, `--lau-fau-temp` still prints Lau Fau Shan, `--tseung-kwan-o-temp` still prints Tseung Kwan O, `--sham-shui-po-temp` still prints Sham Shui Po, `--shek-kong-temp` still prints Shek Kong, `--wetland-temp` still prints Wetland Park, `--ta-kwu-ling-temp` still prints Ta Kwu Ling, `--peng-chau-temp` still prints Peng Chau, `--park-temp` still prints King's Park, `--cheung-chau-temp` still prints Cheung Chau, `--waglan-temp` still prints Waglan Island, and `--ping-chau-temp` still prints Ping Chau. `--sha-lo-wan-wet` still prints Sha Lo Wan's wet-bulb temperature. `--sha-lo-wan-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Lo Wan temperature is available.`

`hk-weather --airport-temp` prints the latest daily mean temperature at Hong Kong International Airport, for example `2026-07-31  26.2°C`. The published airport series currently ends in July. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--airport-wet` still prints the airport wet-bulb temperature. `--airport-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No airport temperature is available.`

`hk-weather --clear-water-bay-temp` prints the latest daily mean temperature at Clear Water Bay, for example `2026-08-31  27°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--clear-water-bay-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Clear Water Bay temperature is available.`

`hk-weather --hong-kong-park-temp` prints the latest daily mean temperature at Hong Kong Park, for example `2026-08-31  27.1°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--hong-kong-park-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Hong Kong Park temperature is available.`

`hk-weather --ngong-ping-temp` prints the latest daily mean temperature at Ngong Ping, for example `2026-08-31  23.7°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--ngong-ping-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ngong Ping temperature is available.`

`hk-weather --kwun-tong-temp` prints the latest daily mean temperature at Kwun Tong, for example `2026-08-31  27.4°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--kwun-tong-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Kwun Tong temperature is available.`

`hk-weather --wong-tai-sin-temp` prints the latest daily mean temperature at Wong Tai Sin, for example `2026-08-31  27.7°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--wong-tai-sin-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Tai Sin temperature is available.`

`hk-weather --tsuen-wan-temp` prints the latest daily mean temperature at Tsuen Wan, for example `2026-08-31  26°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--tsuen-wan-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan temperature is available.`

`hk-weather --yuen-long-park-temp` prints the latest daily mean temperature at Yuen Long Park, for example `2026-08-31  27.3°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--yuen-long-park-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Yuen Long Park temperature is available.`

`hk-weather --tap-mun-temp` prints the latest daily mean temperature at Tap Mun, for example `2026-08-31  26.7°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--tap-mun-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tap Mun temperature is available.`

`hk-weather --shau-kei-wan-temp` prints the latest daily mean temperature at Shau Kei Wan, for example `2026-08-31  27.1°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--shau-kei-wan-humidity` still prints Shau Kei Wan's humidity, `--shau-kei-wan-dew` still prints its dew point, and `--shau-kei-wan-rain` still prints its rainfall. `--shau-kei-wan-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shau Kei Wan temperature is available.`

`hk-weather --happy-valley-temp` prints the latest daily mean temperature at Happy Valley, for example `2026-08-31  28.4°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--heat-index` still prints the Hong Kong Heat Index, which can include Happy Valley. `--happy-valley-temp --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Happy Valley temperature is available.`

`hk-weather --tai-mei-tuk-temp` prints the latest daily mean temperature at Tai Mei Tuk, for example `2026-08-31  26.1°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--happy-valley-temp` still prints Happy Valley's mean temperature. `--tai-mei-tuk-temp --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `大美督` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Tai Mei Tuk temperature is available.`

`hk-weather --kau-sai-chau-temp` prints the latest daily mean temperature at Kau Sai Chau, for example `2026-08-31  26.9°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--kau-sai-chau-humidity` still prints Kau Sai Chau's humidity, `--kau-sai-chau-dew` still prints its dew point, and `--kau-sai-chau-rain` still prints its rainfall. `--kau-sai-chau-temp --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `滘西洲` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Kau Sai Chau temperature is available.`

`hk-weather --kadoorie-farm-temp` prints the latest daily mean temperature at Kadoorie Farm and Botanic Garden, for example `2026-08-31  25.1°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--kadoorie-farm-rain` still prints its rainfall. `--kadoorie-farm-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `嘉道理農場暨植物園` and simplified text uses `嘉道理农场暨植物园`. Days marked `***` are omitted. If none remain, it says `No Kadoorie Farm and Botanic Garden temperature is available.`

`hk-weather --the-peak-temp` prints the latest daily mean temperature at The Peak, for example `2026-08-31  25.4°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--the-peak-rain` still prints The Peak's rainfall. `--the-peak-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `山頂` and simplified text uses `山顶`. Days marked `***` are omitted. If none remain, it says `No The Peak temperature is available.`

`hk-weather --kat-o-temp` prints the latest daily mean temperature at Kat O, for example `2026-08-31  26.8°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--kat-o-rain` still prints Kat O's rainfall. `--kat-o-temp --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `吉澳` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Kat O temperature is available.`

`hk-weather --pak-tam-chung-temp` prints the latest daily mean temperature at Pak Tam Chung (Tsak Yue Wu), for example `2026-08-31  26.8°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--pak-tam-chung-rain` still prints its rainfall. `--pak-tam-chung-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `北潭涌(鯽魚湖)` and simplified text uses `北潭涌(鲫鱼湖)`. Days marked `***` are omitted. If none remain, it says `No Pak Tam Chung (Tsak Yue Wu) temperature is available.`

`hk-weather --beas-river-temp` prints the latest daily mean temperature at Beas River, for example `2026-08-31  26.6°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--beas-river-rain` still prints its rainfall. `--beas-river-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `上水雙魚河` and simplified text uses `上水双鱼河`. Days marked `***` are omitted. If none remain, it says `No Beas River temperature is available.`

`hk-weather --bluff-head-temp` prints the latest daily mean temperature at Bluff Head, for example `2026-08-31  27.3°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--bluff-head-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `黃麻角` and simplified text uses `黄麻角`. Days marked `***` are omitted. If none remain, it says `No Bluff Head temperature is available.`

`hk-weather --runway-park-temp` prints the latest daily mean temperature at Kai Tak Runway Park, for example `2026-08-31  27.5°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--runway-park-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `啟德跑道公園` and simplified text uses `启德跑道公园`. Days marked `***` are omitted. If none remain, it says `No Kai Tak Runway Park temperature is available.`

`hk-weather --kowloon-city-temp` prints the latest daily mean temperature at Kowloon City, for example `2026-08-31  27.4°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--kowloon-city-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `九龍城` and simplified text uses `九龙城`. Days marked `***` are omitted. If none remain, it says `No Kowloon City temperature is available.`

`hk-weather --nei-lak-shan-temp` prints the latest daily mean temperature at Nei Lak Shan, for example `2026-08-31  22.8°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--nei-lak-shan-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `彌勒山` and simplified text uses `弥勒山`. Days marked `***` are omitted. If none remain, it says `No Nei Lak Shan temperature is available.`

`hk-weather --new-tsing-yi-temp` prints the latest daily mean temperature at New Tsing Yi Station, for example `2026-08-31  27°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--new-tsing-yi-temp --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `新青衣站` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No New Tsing Yi Station temperature is available.`

`hk-weather --stanley-temp` prints the latest daily mean temperature at Stanley, for example `2026-08-31  27.3°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--stanley-temp --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `赤柱` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Stanley temperature is available.`

`hk-weather --shing-mun-valley-temp` prints the latest daily mean temperature at Tsuen Wan Shing Mun Valley, for example `2026-08-31  26.7°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--tsuen-wan-temp` still prints Tsuen Wan. `--shing-mun-valley-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `荃灣城門谷` and simplified text uses `荃湾城门谷`. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan Shing Mun Valley temperature is available.`

`hk-weather --tuen-mun-home-temp` prints the latest daily mean temperature at Tuen Mun Children and Juvenile Home, for example `2026-08-31  27°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--tuen-mun-home-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `屯門兒童及青少年院` and simplified text uses `屯门儿童及青少年院`. Days marked `***` are omitted. If none remain, it says `No Tuen Mun Children and Juvenile Home temperature is available.`

`hk-weather --buoy-2-temp` prints the latest daily mean temperature at Automatic Weather Buoy No.2 (Hong Kong International Airport, West), for example `2026-08-31  27.6°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--buoy-2-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標2號 (香港國際機場西面)` and simplified text uses `自动气象浮标2号 (香港国际机场西面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) temperature is available.`

`hk-weather --buoy-8-temp` prints the latest daily mean temperature at Automatic Weather Buoy No.8 (Hong Kong International Airport, East), for example `2026-08-31  27.4°C`. `--mean-temp` still prints the Observatory reading, and the other station temperature flags still print their own stations. `--buoy-2-temp` still prints Automatic Weather Buoy No.2. `--buoy-8-temp --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標8號 (香港國際機場東面)` and simplified text uses `自动气象浮标8号 (香港国际机场东面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.8 (Hong Kong International Airport, East) temperature is available.`

`hk-weather --max-temp` prints the latest daily maximum temperature at the Observatory for that same year (`dataType=CLMMAXT`, station HKO), for example `2026-08-31  29.5°C`. `--mean-temp` still prints the daily mean. `--hottest` still prints the current warmest place. `--max-temp --json` prints that day as one JSON object. `--lang` applies. If no numeric day is present, it says `No daily maximum temperature is available.`

`hk-weather --min-temp` prints the latest daily minimum temperature at the Observatory for that same year (`dataType=CLMMINT`, station HKO), for example `2026-08-31  26.2°C`. `--max-temp` still prints the daily maximum. `--coldest` still prints the current coolest place. `--min-temp --json` prints that day as one JSON object. `--lang` applies. If no numeric day is present, it says `No daily minimum temperature is available.`

`hk-weather --tai-mo-min` prints the latest daily minimum temperature at Tai Mo Shan, for example `2026-08-31  19.5°C`. `--min-temp` still prints the Observatory minimum, and `--tai-mo-temp` still prints the peak's daily mean. `--tai-mo-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan minimum temperature is available.`

`hk-weather --tate-min` prints the latest daily minimum temperature at Tate's Cairn, for example `2026-08-31  22.1°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, and `--tate-temp` still prints Tate's Cairn's daily mean. `--tate-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tate's Cairn minimum temperature is available.`

`hk-weather --sai-kung-min` prints the latest daily minimum temperature at Sai Kung, for example `2026-08-31  26.9°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, and `--tate-min` still prints Tate's Cairn. `--sai-kung-temp` still prints Sai Kung's daily mean, and `--sai-kung-dew` still prints its dew point. `--sai-kung-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sai Kung minimum temperature is available.`

`hk-weather --wong-chuk-hang-min` prints the latest daily minimum temperature at Wong Chuk Hang, for example `2026-08-31  26.6°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, and `--sai-kung-min` still prints Sai Kung. `--wong-chuk-hang-dew` still prints Wong Chuk Hang's dew point. `--wong-chuk-hang-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Chuk Hang minimum temperature is available.`

`hk-weather --waglan-min` prints the latest daily minimum temperature at Waglan Island, for example `2026-08-31  26°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, and `--wong-chuk-hang-min` still prints Wong Chuk Hang. `--waglan-max` still prints Waglan Island's maximum, `--waglan-humidity` still prints its humidity, and `--waglan-pressure` still prints its pressure. `--waglan-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Waglan Island minimum temperature is available.`

`hk-weather --sha-tin-min` prints the latest daily minimum temperature at Sha Tin, for example `2026-08-31  26.1°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, and `--waglan-min` still prints Waglan Island. `--sha-tin-humidity` still prints Sha Tin's humidity, `--sha-tin-dew` still prints its dew point, `--sha-tin-pressure` still prints its pressure, and `--sha-tin-rain` still prints its rainfall. `--sha-tin-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin minimum temperature is available.`

`hk-weather --cheung-chau-min` prints the latest daily minimum temperature at Cheung Chau, for example `2026-08-31  25.9°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, `--waglan-min` still prints Waglan Island, and `--sha-tin-min` still prints Sha Tin. `--cheung-chau-max` still prints Cheung Chau's maximum, `--cheung-chau-humidity` still prints its humidity, `--cheung-wind` still prints its wind speed, `--cheung-prevailing` still prints its prevailing direction, `--cheung-dew` still prints its dew point, and `--cheung-chau-rain` still prints its rainfall. `--cheung-chau-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau minimum temperature is available.`

`hk-weather --park-min` prints the latest daily minimum temperature at King's Park, for example `2026-08-31  25.7°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, `--waglan-min` still prints Waglan Island, `--sha-tin-min` still prints Sha Tin, and `--cheung-chau-min` still prints Cheung Chau. `--park-max` still prints King's Park's maximum, `--park-dew` still prints its dew point, `--park-pressure` still prints its pressure, `--park-wet` still prints its wet-bulb temperature, `--park-rain` still prints its rainfall, and `--park-humidity` still prints its humidity. `--park-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park minimum temperature is available.`

`hk-weather --lau-fau-min` prints the latest daily minimum temperature at Lau Fau Shan, for example `2026-08-31  25.2°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, `--waglan-min` still prints Waglan Island, `--sha-tin-min` still prints Sha Tin, `--cheung-chau-min` still prints Cheung Chau, and `--park-min` still prints King's Park. `--lau-fau-max` still prints Lau Fau Shan's maximum, `--lau-fau-rain` still prints its rainfall, `--lau-fau-wind` still prints its wind speed, and `--lau-fau-humidity` still prints its humidity. `--lau-fau-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Lau Fau Shan minimum temperature is available.`

`hk-weather --sheung-shui-min` prints the latest daily minimum temperature at Sheung Shui, for example `2026-08-31  25.4°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, `--waglan-min` still prints Waglan Island, `--sha-tin-min` still prints Sha Tin, `--cheung-chau-min` still prints Cheung Chau, `--park-min` still prints King's Park, and `--lau-fau-min` still prints Lau Fau Shan. `--sheung-shui-max` still prints Sheung Shui's maximum, `--sheung-shui-dew` still prints its dew point, `--sheung-shui-pressure` still prints its pressure, `--sheung-shui-rain` still prints its rainfall, and `--sheung-shui-humidity` still prints its humidity. `--sheung-shui-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sheung Shui minimum temperature is available.`

`hk-weather --tseung-kwan-o-min` prints the latest daily minimum temperature at Tseung Kwan O, for example `2026-08-31  25.1°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, `--waglan-min` still prints Waglan Island, `--sha-tin-min` still prints Sha Tin, `--cheung-chau-min` still prints Cheung Chau, `--park-min` still prints King's Park, `--lau-fau-min` still prints Lau Fau Shan, and `--sheung-shui-min` still prints Sheung Shui. `--tseung-kwan-o-max` still prints Tseung Kwan O's maximum, and `--tseung-kwan-o-rain` still prints its rainfall. `--tseung-kwan-o-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tseung Kwan O minimum temperature is available.`

`hk-weather --sham-shui-po-min` prints the latest daily minimum temperature at Sham Shui Po, for example `2026-08-31  25.7°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, `--waglan-min` still prints Waglan Island, `--sha-tin-min` still prints Sha Tin, `--cheung-chau-min` still prints Cheung Chau, `--park-min` still prints King's Park, `--lau-fau-min` still prints Lau Fau Shan, `--sheung-shui-min` still prints Sheung Shui, and `--tseung-kwan-o-min` still prints Tseung Kwan O. `--sham-shui-po-rain` still prints Sham Shui Po's rainfall. `--sham-shui-po-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sham Shui Po minimum temperature is available.`

`hk-weather --shek-kong-min` prints the latest daily minimum temperature at Shek Kong, for example `2026-08-31  25.2°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, `--waglan-min` still prints Waglan Island, `--sha-tin-min` still prints Sha Tin, `--cheung-chau-min` still prints Cheung Chau, `--park-min` still prints King's Park, `--lau-fau-min` still prints Lau Fau Shan, `--sheung-shui-min` still prints Sheung Shui, `--tseung-kwan-o-min` still prints Tseung Kwan O, and `--sham-shui-po-min` still prints Sham Shui Po. `--shek-kong-max` still prints Shek Kong's maximum, `--shek-kong-humidity` still prints its humidity, and `--shek-kong-rain` still prints its rainfall. `--shek-kong-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shek Kong minimum temperature is available.`

`hk-weather --wetland-min` prints the latest daily minimum temperature at Wetland Park, for example `2026-08-31  25.2°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, `--waglan-min` still prints Waglan Island, `--sha-tin-min` still prints Sha Tin, `--cheung-chau-min` still prints Cheung Chau, `--park-min` still prints King's Park, `--lau-fau-min` still prints Lau Fau Shan, `--sheung-shui-min` still prints Sheung Shui, `--tseung-kwan-o-min` still prints Tseung Kwan O, `--sham-shui-po-min` still prints Sham Shui Po, and `--shek-kong-min` still prints Shek Kong. `--wetland-rain` still prints Wetland Park's rainfall, `--wetland-humidity` still prints its humidity, `--wetland-dew` still prints its dew point, and `--wetland-pressure` still prints its pressure. `--wetland-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wetland Park minimum temperature is available.`

`hk-weather --ta-kwu-ling-min` prints the latest daily minimum temperature at Ta Kwu Ling, for example `2026-08-31  25.1°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, `--waglan-min` still prints Waglan Island, `--sha-tin-min` still prints Sha Tin, `--cheung-chau-min` still prints Cheung Chau, `--park-min` still prints King's Park, `--lau-fau-min` still prints Lau Fau Shan, `--sheung-shui-min` still prints Sheung Shui, `--tseung-kwan-o-min` still prints Tseung Kwan O, `--sham-shui-po-min` still prints Sham Shui Po, `--shek-kong-min` still prints Shek Kong, and `--wetland-min` still prints Wetland Park. `--ta-kwu-ling-humidity` still prints Ta Kwu Ling's humidity, `--ta-kwu-ling-rain` still prints its rainfall, and `--ta-kwu-ling-dew` still prints its dew point. `--ta-kwu-ling-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ta Kwu Ling minimum temperature is available.`

`hk-weather --sha-lo-wan-min` prints the latest daily minimum temperature at Sha Lo Wan, for example `2026-08-31  25.4°C`. `--min-temp` still prints the Observatory minimum, `--tai-mo-min` still prints Tai Mo Shan, `--tate-min` still prints Tate's Cairn, `--sai-kung-min` still prints Sai Kung, `--wong-chuk-hang-min` still prints Wong Chuk Hang, `--waglan-min` still prints Waglan Island, `--sha-tin-min` still prints Sha Tin, `--cheung-chau-min` still prints Cheung Chau, `--park-min` still prints King's Park, `--lau-fau-min` still prints Lau Fau Shan, `--sheung-shui-min` still prints Sheung Shui, `--tseung-kwan-o-min` still prints Tseung Kwan O, `--sham-shui-po-min` still prints Sham Shui Po, `--shek-kong-min` still prints Shek Kong, `--wetland-min` still prints Wetland Park, and `--ta-kwu-ling-min` still prints Ta Kwu Ling. `--sha-lo-wan-temp` still prints Sha Lo Wan's mean temperature, `--sha-lo-wan-humidity` still prints its humidity, and `--sha-lo-wan-wet` still prints its wet-bulb temperature. `--sha-lo-wan-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Lo Wan minimum temperature is available.`

`hk-weather --airport-min` prints the latest daily minimum temperature at Hong Kong International Airport, for example `2026-07-31  24.2°C`. The published airport series currently ends in July. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--airport-temp` still prints the airport mean temperature, `--airport-max` still prints its maximum, `--airport-humidity` still prints its humidity, and `--airport-wet` still prints its wet-bulb temperature. `--airport-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No airport minimum temperature is available.`

`hk-weather --yuen-long-park-min` prints the latest daily minimum temperature at Yuen Long Park, for example `2026-08-31  25.6°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--yuen-long-park-temp` still prints Yuen Long Park's mean temperature, and `--yuen-long-park-max` still prints its maximum. `--yuen-long-park-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Yuen Long Park minimum temperature is available.`

`hk-weather --clear-water-bay-min` prints the latest daily minimum temperature at Clear Water Bay, for example `2026-08-31  25.9°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--clear-water-bay-temp` still prints Clear Water Bay's mean temperature, and `--clear-water-bay-max` still prints its maximum. `--clear-water-bay-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Clear Water Bay minimum temperature is available.`

`hk-weather --tap-mun-min` prints the latest daily minimum temperature at Tap Mun, for example `2026-08-31  25.8°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--tap-mun-temp` still prints Tap Mun's mean temperature, and `--tap-mun-max` still prints its maximum. `--tap-mun-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tap Mun minimum temperature is available.`

`hk-weather --hong-kong-park-min` prints the latest daily minimum temperature at Hong Kong Park, for example `2026-08-31  25.8°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--hong-kong-park-temp` still prints Hong Kong Park's mean temperature, and `--hong-kong-park-max` still prints its maximum. `--hong-kong-park-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Hong Kong Park minimum temperature is available.`

`hk-weather --ngong-ping-min` prints the latest daily minimum temperature at Ngong Ping, for example `2026-08-31  22.4°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--ngong-ping-temp` still prints Ngong Ping's mean temperature, and `--ngong-ping-max` still prints its maximum. `--ngong-ping-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ngong Ping minimum temperature is available.`

`hk-weather --kwun-tong-min` prints the latest daily minimum temperature at Kwun Tong, for example `2026-08-31  25°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--kwun-tong-temp` still prints Kwun Tong's mean temperature, and `--kwun-tong-max` still prints its maximum. `--kwun-tong-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Kwun Tong minimum temperature is available.`

`hk-weather --wong-tai-sin-min` prints the latest daily minimum temperature at Wong Tai Sin, for example `2026-08-31  25.5°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--wong-tai-sin-temp` still prints Wong Tai Sin's mean temperature, and `--wong-tai-sin-max` still prints its maximum. `--wong-tai-sin-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Tai Sin minimum temperature is available.`

`hk-weather --tsuen-wan-min` prints the latest daily minimum temperature at Tsuen Wan, for example `2026-08-31  24.8°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--tsuen-wan-temp` still prints Tsuen Wan's mean temperature, and `--tsuen-wan-max` still prints its maximum. `--tsuen-wan-min --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan minimum temperature is available.`

`hk-weather --kau-sai-chau-min` prints the latest daily minimum temperature at Kau Sai Chau, for example `2026-08-31  25.8°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--kau-sai-chau-temp` still prints Kau Sai Chau's mean temperature, and `--kau-sai-chau-max` still prints its maximum. `--kau-sai-chau-min --json` prints that day as one JSON object. `--lang` selects the station name. Traditional and simplified text both use `滘西洲`. Days marked `***` are omitted. If none remain, it says `No Kau Sai Chau minimum temperature is available.`

`hk-weather --kadoorie-farm-min` prints the latest daily minimum temperature at Kadoorie Farm and Botanic Garden, for example `2026-08-31  23.6°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--kadoorie-farm-temp` still prints Kadoorie Farm's mean temperature, and `--kadoorie-farm-max` still prints its maximum. `--kadoorie-farm-min --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `嘉道理農場暨植物園` and simplified text uses `嘉道理农场暨植物园`. Days marked `***` are omitted. If none remain, it says `No Kadoorie Farm and Botanic Garden minimum temperature is available.`

`hk-weather --the-peak-min` prints the latest daily minimum temperature at The Peak, for example `2026-08-31  24°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--the-peak-temp` still prints The Peak's mean temperature, and `--the-peak-max` still prints its maximum. `--the-peak-min --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `山頂` and simplified text uses `山顶`. Days marked `***` are omitted. If none remain, it says `No The Peak minimum temperature is available.`

`hk-weather --kat-o-min` prints the latest daily minimum temperature at Kat O, for example `2026-08-31  25.9°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--kat-o-temp` still prints Kat O's mean temperature, and `--kat-o-max` still prints its maximum. `--kat-o-min --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `吉澳` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Kat O minimum temperature is available.`

`hk-weather --pak-tam-chung-min` prints the latest daily minimum temperature at Pak Tam Chung (Tsak Yue Wu), for example `2026-08-31  25°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--pak-tam-chung-temp` still prints Pak Tam Chung's mean temperature, and `--pak-tam-chung-max` still prints its maximum. `--pak-tam-chung-min --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `北潭涌(鯽魚湖)` and simplified text uses `北潭涌(鲫鱼湖)`. Days marked `***` are omitted. If none remain, it says `No Pak Tam Chung (Tsak Yue Wu) minimum temperature is available.`

`hk-weather --beas-river-min` prints the latest daily minimum temperature at Beas River, for example `2026-08-31  24.7°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--beas-river-temp` still prints Beas River's mean temperature, and `--beas-river-max` still prints its maximum. `--beas-river-min --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `上水雙魚河` and simplified text uses `上水双鱼河`. Days marked `***` are omitted. If none remain, it says `No Beas River minimum temperature is available.`

`hk-weather --kowloon-city-min` prints the latest daily minimum temperature at Kowloon City, for example `2026-08-31  25.7°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--kowloon-city-temp` still prints Kowloon City's mean temperature, and `--kowloon-city-max` still prints its maximum. `--kowloon-city-min --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `九龍城` and simplified text uses `九龙城`. Days marked `***` are omitted. If none remain, it says `No Kowloon City minimum temperature is available.`

`hk-weather --new-tsing-yi-min` prints the latest daily minimum temperature at New Tsing Yi Station, for example `2026-08-31  25.6°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--new-tsing-yi-temp` still prints New Tsing Yi Station's mean temperature, and `--new-tsing-yi-max` still prints its maximum. `--new-tsing-yi-min --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `新青衣站` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No New Tsing Yi Station minimum temperature is available.`

`hk-weather --stanley-min` prints the latest daily minimum temperature at Stanley, for example `2026-08-31  26°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--stanley-temp` still prints Stanley's mean temperature, and `--stanley-max` still prints its maximum. `--stanley-min --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `赤柱` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Stanley minimum temperature is available.`

`hk-weather --shing-mun-valley-min` prints the latest daily minimum temperature at Tsuen Wan Shing Mun Valley, for example `2026-08-31  25°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--shing-mun-valley-temp` still prints the valley's mean temperature, `--shing-mun-valley-max` still prints its maximum, and `--tsuen-wan-min` still prints Tsuen Wan. `--shing-mun-valley-min --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `荃灣城門谷` and simplified text uses `荃湾城门谷`. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan Shing Mun Valley minimum temperature is available.`

`hk-weather --tuen-mun-home-min` prints the latest daily minimum temperature at Tuen Mun Children and Juvenile Home, for example `2026-08-31  25.7°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--tuen-mun-home-temp` still prints the home's mean temperature, and `--tuen-mun-home-max` still prints its maximum. `--tuen-mun-home-min --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `屯門兒童及青少年院` and simplified text uses `屯门儿童及青少年院`. Days marked `***` are omitted. If none remain, it says `No Tuen Mun Children and Juvenile Home minimum temperature is available.`

`hk-weather --buoy-2-min` prints the latest daily minimum temperature at Automatic Weather Buoy No.2 (Hong Kong International Airport, West), for example `2026-08-31  26.1°C`. `--min-temp` still prints the Observatory minimum, and the other station minimum flags still print their own stations. `--buoy-2-temp` still prints the buoy's mean temperature, and `--buoy-2-max` still prints its maximum. `--buoy-2-min --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標2號 (香港國際機場西面)` and simplified text uses `自动气象浮标2号 (香港国际机场西面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) minimum temperature is available.`

`hk-weather --tai-mo-max` prints the latest daily maximum temperature at Tai Mo Shan, for example `2026-08-31  24.1°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-temp` still prints the peak's daily mean, and `--tai-mo-min` still prints the peak's daily minimum. `--tai-mo-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan maximum temperature is available.`

`hk-weather --tseung-kwan-o-max` prints the latest daily maximum temperature at Tseung Kwan O, for example `2026-08-31  31.2°C`. `--max-temp` still prints the Observatory maximum, and `--tai-mo-max` still prints Tai Mo Shan. `--tseung-kwan-o-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tseung Kwan O maximum temperature is available.`

`hk-weather --sheung-shui-max` prints the latest daily maximum temperature at Sheung Shui, for example `2026-08-31  30.9°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, and `--tseung-kwan-o-max` still prints Tseung Kwan O. `--sheung-shui-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sheung Shui maximum temperature is available.`

`hk-weather --waglan-max` prints the latest daily maximum temperature at Waglan Island, for example `2026-08-31  31.7°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, and `--sheung-shui-max` still prints Sheung Shui. `--mean-wind` still prints Waglan Island's wind speed, and `--waglan-humidity` still prints its humidity. `--waglan-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Waglan Island maximum temperature is available.`

`hk-weather --shek-kong-max` prints the latest daily maximum temperature at Shek Kong, for example `2026-08-31  30.5°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, and `--waglan-max` still prints Waglan Island. `--shek-kong-humidity` still prints Shek Kong's humidity, and `--shek-kong-rain` still prints its rainfall. `--shek-kong-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shek Kong maximum temperature is available.`

`hk-weather --cheung-chau-max` prints the latest daily maximum temperature at Cheung Chau, for example `2026-08-31  30.7°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, and `--shek-kong-max` still prints Shek Kong. `--cheung-wind` still prints Cheung Chau's wind speed, `--cheung-prevailing` still prints its prevailing direction, and `--cheung-dew` still prints its dew point. `--cheung-chau-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau maximum temperature is available.`

`hk-weather --park-max` prints the latest daily maximum temperature at King's Park, for example `2026-08-31  30.4°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, `--shek-kong-max` still prints Shek Kong, and `--cheung-chau-max` still prints Cheung Chau. `--park-dew`, `--park-pressure`, `--park-wet`, `--park-rain`, and `--park-humidity` still print King's Park's other daily readings. `--park-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park maximum temperature is available.`

`hk-weather --lau-fau-max` prints the latest daily maximum temperature at Lau Fau Shan, for example `2026-08-31  29.4°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, `--shek-kong-max` still prints Shek Kong, `--cheung-chau-max` still prints Cheung Chau, and `--park-max` still prints King's Park. `--lau-fau-rain` still prints Lau Fau Shan's rainfall, `--lau-fau-wind` still prints its wind speed, and `--lau-fau-humidity` still prints its humidity. `--lau-fau-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Lau Fau Shan maximum temperature is available.`

`hk-weather --sai-kung-max` prints the latest daily maximum temperature at Sai Kung, for example `2026-08-31  29.9°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, `--shek-kong-max` still prints Shek Kong, `--cheung-chau-max` still prints Cheung Chau, `--park-max` still prints King's Park, and `--lau-fau-max` still prints Lau Fau Shan. `--sai-kung-temp` still prints Sai Kung's daily mean, `--sai-kung-min` still prints its minimum, `--sai-kung-dew` still prints its dew point, and `--sai-kung-humidity` still prints its humidity. `--sai-kung-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sai Kung maximum temperature is available.`

`hk-weather --sha-tin-max` prints the latest daily maximum temperature at Sha Tin, for example `2026-08-31  30.4°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, `--shek-kong-max` still prints Shek Kong, `--cheung-chau-max` still prints Cheung Chau, `--park-max` still prints King's Park, `--lau-fau-max` still prints Lau Fau Shan, and `--sai-kung-max` still prints Sai Kung. `--sha-tin-min` still prints Sha Tin's minimum, `--sha-tin-humidity` still prints its humidity, `--sha-tin-dew` still prints its dew point, `--sha-tin-pressure` still prints its pressure, and `--sha-tin-rain` still prints its rainfall. `--sha-tin-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin maximum temperature is available.`

`hk-weather --tate-max` prints the latest daily maximum temperature at Tate's Cairn, for example `2026-08-31  29.4°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, `--shek-kong-max` still prints Shek Kong, `--cheung-chau-max` still prints Cheung Chau, `--park-max` still prints King's Park, `--lau-fau-max` still prints Lau Fau Shan, `--sai-kung-max` still prints Sai Kung, and `--sha-tin-max` still prints Sha Tin. `--tate-temp` still prints Tate's Cairn's daily mean, `--tate-min` still prints its minimum, and `--tate-humidity` still prints its humidity. `--tate-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tate's Cairn maximum temperature is available.`

`hk-weather --wong-chuk-hang-max` prints the latest daily maximum temperature at Wong Chuk Hang, for example `2026-08-31  29.9°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, `--shek-kong-max` still prints Shek Kong, `--cheung-chau-max` still prints Cheung Chau, `--park-max` still prints King's Park, `--lau-fau-max` still prints Lau Fau Shan, `--sai-kung-max` still prints Sai Kung, `--sha-tin-max` still prints Sha Tin, and `--tate-max` still prints Tate's Cairn. `--wong-chuk-hang-min` still prints Wong Chuk Hang's minimum, `--wong-chuk-hang-dew` still prints its dew point, and `--wong-chuk-hang-humidity` still prints its humidity. `--wong-chuk-hang-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Chuk Hang maximum temperature is available.`

`hk-weather --sham-shui-po-max` prints the latest daily maximum temperature at Sham Shui Po, for example `2026-08-31  31.3°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, `--shek-kong-max` still prints Shek Kong, `--cheung-chau-max` still prints Cheung Chau, `--park-max` still prints King's Park, `--lau-fau-max` still prints Lau Fau Shan, `--sai-kung-max` still prints Sai Kung, `--sha-tin-max` still prints Sha Tin, `--tate-max` still prints Tate's Cairn, and `--wong-chuk-hang-max` still prints Wong Chuk Hang. `--sham-shui-po-min` still prints Sham Shui Po's minimum, `--sham-shui-po-temp` still prints its mean temperature, and `--sham-shui-po-rain` still prints its rainfall. `--sham-shui-po-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sham Shui Po maximum temperature is available.`

`hk-weather --wetland-max` prints the latest daily maximum temperature at Wetland Park, for example `2026-08-31  29.9°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, `--shek-kong-max` still prints Shek Kong, `--cheung-chau-max` still prints Cheung Chau, `--park-max` still prints King's Park, `--lau-fau-max` still prints Lau Fau Shan, `--sai-kung-max` still prints Sai Kung, `--sha-tin-max` still prints Sha Tin, `--tate-max` still prints Tate's Cairn, `--wong-chuk-hang-max` still prints Wong Chuk Hang, and `--sham-shui-po-max` still prints Sham Shui Po. `--wetland-temp` still prints Wetland Park's mean temperature, `--wetland-min` still prints its minimum, `--wetland-dew` still prints its dew point, `--wetland-rain` still prints its rainfall, `--wetland-humidity` still prints its humidity, and `--wetland-pressure` still prints its pressure. `--wetland-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wetland Park maximum temperature is available.`

`hk-weather --ta-kwu-ling-max` prints the latest daily maximum temperature at Ta Kwu Ling, for example `2026-08-31  30.2°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, `--shek-kong-max` still prints Shek Kong, `--cheung-chau-max` still prints Cheung Chau, `--park-max` still prints King's Park, `--lau-fau-max` still prints Lau Fau Shan, `--sai-kung-max` still prints Sai Kung, `--sha-tin-max` still prints Sha Tin, `--tate-max` still prints Tate's Cairn, `--wong-chuk-hang-max` still prints Wong Chuk Hang, `--sham-shui-po-max` still prints Sham Shui Po, and `--wetland-max` still prints Wetland Park. `--ta-kwu-ling-temp` still prints Ta Kwu Ling's mean temperature, `--ta-kwu-ling-min` still prints its minimum, `--ta-kwu-ling-dew` still prints its dew point, `--ta-kwu-ling-rain` still prints its rainfall, and `--ta-kwu-ling-humidity` still prints its humidity. `--ta-kwu-ling-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ta Kwu Ling maximum temperature is available.`

`hk-weather --sha-lo-wan-max` prints the latest daily maximum temperature at Sha Lo Wan, for example `2026-08-31  30.3°C`. `--max-temp` still prints the Observatory maximum, `--tai-mo-max` still prints Tai Mo Shan, `--tseung-kwan-o-max` still prints Tseung Kwan O, `--sheung-shui-max` still prints Sheung Shui, `--waglan-max` still prints Waglan Island, `--shek-kong-max` still prints Shek Kong, `--cheung-chau-max` still prints Cheung Chau, `--park-max` still prints King's Park, `--lau-fau-max` still prints Lau Fau Shan, `--sai-kung-max` still prints Sai Kung, `--sha-tin-max` still prints Sha Tin, `--tate-max` still prints Tate's Cairn, `--wong-chuk-hang-max` still prints Wong Chuk Hang, `--sham-shui-po-max` still prints Sham Shui Po, `--wetland-max` still prints Wetland Park, and `--ta-kwu-ling-max` still prints Ta Kwu Ling. `--sha-lo-wan-min` still prints Sha Lo Wan's minimum, `--sha-lo-wan-temp` still prints its mean temperature, and `--sha-lo-wan-humidity` still prints its humidity. `--sha-lo-wan-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Lo Wan maximum temperature is available.`

`hk-weather --airport-max` prints the latest daily maximum temperature at Hong Kong International Airport, for example `2026-07-31  28.2°C`. The published airport series currently ends in July. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--airport-temp` still prints the airport mean temperature, `--airport-humidity` still prints its humidity, and `--airport-wet` still prints its wet-bulb temperature. `--airport-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No airport maximum temperature is available.`

`hk-weather --yuen-long-park-max` prints the latest daily maximum temperature at Yuen Long Park, for example `2026-08-31  31.4°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--yuen-long-park-temp` still prints Yuen Long Park's mean temperature. `--yuen-long-park-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Yuen Long Park maximum temperature is available.`

`hk-weather --clear-water-bay-max` prints the latest daily maximum temperature at Clear Water Bay, for example `2026-08-31  31.1°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--clear-water-bay-temp` still prints Clear Water Bay's mean temperature. `--clear-water-bay-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Clear Water Bay maximum temperature is available.`

`hk-weather --tap-mun-max` prints the latest daily maximum temperature at Tap Mun, for example `2026-08-31  29.4°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--tap-mun-temp` still prints Tap Mun's mean temperature. `--tap-mun-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tap Mun maximum temperature is available.`

`hk-weather --hong-kong-park-max` prints the latest daily maximum temperature at Hong Kong Park, for example `2026-08-31  29.5°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--hong-kong-park-temp` still prints Hong Kong Park's mean temperature. `--hong-kong-park-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Hong Kong Park maximum temperature is available.`

`hk-weather --ngong-ping-max` prints the latest daily maximum temperature at Ngong Ping, for example `2026-08-31  27.1°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--ngong-ping-temp` still prints Ngong Ping's mean temperature. `--ngong-ping-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ngong Ping maximum temperature is available.`

`hk-weather --kwun-tong-max` prints the latest daily maximum temperature at Kwun Tong, for example `2026-08-31  31°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--kwun-tong-temp` still prints Kwun Tong's mean temperature. `--kwun-tong-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Kwun Tong maximum temperature is available.`

`hk-weather --wong-tai-sin-max` prints the latest daily maximum temperature at Wong Tai Sin, for example `2026-08-31  32.4°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--wong-tai-sin-temp` still prints Wong Tai Sin's mean temperature. `--wong-tai-sin-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Tai Sin maximum temperature is available.`

`hk-weather --tsuen-wan-max` prints the latest daily maximum temperature at Tsuen Wan, for example `2026-08-31  28.8°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--tsuen-wan-temp` still prints Tsuen Wan's mean temperature. `--tsuen-wan-max --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan maximum temperature is available.`

`hk-weather --kau-sai-chau-max` prints the latest daily maximum temperature at Kau Sai Chau, for example `2026-08-31  29.7°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--kau-sai-chau-temp` still prints Kau Sai Chau's mean temperature. `--kau-sai-chau-max --json` prints that day as one JSON object. `--lang` selects the station name. Traditional and simplified text both use `滘西洲`. Days marked `***` are omitted. If none remain, it says `No Kau Sai Chau maximum temperature is available.`

`hk-weather --kadoorie-farm-max` prints the latest daily maximum temperature at Kadoorie Farm and Botanic Garden, for example `2026-08-31  27.7°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--kadoorie-farm-temp` still prints Kadoorie Farm's mean temperature. `--kadoorie-farm-max --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `嘉道理農場暨植物園` and simplified text uses `嘉道理农场暨植物园`. Days marked `***` are omitted. If none remain, it says `No Kadoorie Farm and Botanic Garden maximum temperature is available.`

`hk-weather --the-peak-max` prints the latest daily maximum temperature at The Peak, for example `2026-08-31  28.2°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--the-peak-temp` still prints The Peak's mean temperature. `--the-peak-max --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `山頂` and simplified text uses `山顶`. Days marked `***` are omitted. If none remain, it says `No The Peak maximum temperature is available.`

`hk-weather --kat-o-max` prints the latest daily maximum temperature at Kat O, for example `2026-08-31  29.7°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--kat-o-temp` still prints Kat O's mean temperature. `--kat-o-max --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `吉澳` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Kat O maximum temperature is available.`

`hk-weather --pak-tam-chung-max` prints the latest daily maximum temperature at Pak Tam Chung (Tsak Yue Wu), for example `2026-08-31  30.2°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--pak-tam-chung-temp` still prints Pak Tam Chung's mean temperature. `--pak-tam-chung-max --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `北潭涌(鯽魚湖)` and simplified text uses `北潭涌(鲫鱼湖)`. Days marked `***` are omitted. If none remain, it says `No Pak Tam Chung (Tsak Yue Wu) maximum temperature is available.`

`hk-weather --beas-river-max` prints the latest daily maximum temperature at Beas River, for example `2026-08-31  30.7°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--beas-river-temp` still prints Beas River's mean temperature. `--beas-river-max --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `上水雙魚河` and simplified text uses `上水双鱼河`. Days marked `***` are omitted. If none remain, it says `No Beas River maximum temperature is available.`

`hk-weather --kowloon-city-max` prints the latest daily maximum temperature at Kowloon City, for example `2026-08-31  31.4°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--kowloon-city-temp` still prints Kowloon City's mean temperature. `--kowloon-city-max --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `九龍城` and simplified text uses `九龙城`. Days marked `***` are omitted. If none remain, it says `No Kowloon City maximum temperature is available.`

`hk-weather --new-tsing-yi-max` prints the latest daily maximum temperature at New Tsing Yi Station, for example `2026-08-31  31.3°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--new-tsing-yi-temp` still prints New Tsing Yi Station's mean temperature. `--new-tsing-yi-max --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `新青衣站` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No New Tsing Yi Station maximum temperature is available.`

`hk-weather --stanley-max` prints the latest daily maximum temperature at Stanley, for example `2026-08-31  31.1°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--stanley-temp` still prints Stanley's mean temperature. `--stanley-max --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `赤柱` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Stanley maximum temperature is available.`

`hk-weather --shing-mun-valley-max` prints the latest daily maximum temperature at Tsuen Wan Shing Mun Valley, for example `2026-08-31  31°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--shing-mun-valley-temp` still prints the valley's mean temperature, and `--tsuen-wan-max` still prints Tsuen Wan. `--shing-mun-valley-max --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `荃灣城門谷` and simplified text uses `荃湾城门谷`. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan Shing Mun Valley maximum temperature is available.`

`hk-weather --tuen-mun-home-max` prints the latest daily maximum temperature at Tuen Mun Children and Juvenile Home, for example `2026-08-31  30.9°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--tuen-mun-home-temp` still prints the home's mean temperature. `--tuen-mun-home-max --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `屯門兒童及青少年院` and simplified text uses `屯门儿童及青少年院`. Days marked `***` are omitted. If none remain, it says `No Tuen Mun Children and Juvenile Home maximum temperature is available.`

`hk-weather --buoy-2-max` prints the latest daily maximum temperature at Automatic Weather Buoy No.2 (Hong Kong International Airport, West), for example `2026-08-31  28.7°C`. `--max-temp` still prints the Observatory maximum, and the other station maximum flags still print their own stations. `--buoy-2-temp` still prints the buoy's mean temperature. `--buoy-2-max --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標2號 (香港國際機場西面)` and simplified text uses `自动气象浮标2号 (香港国际机场西面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) maximum temperature is available.`

`hk-weather --dew-point` prints the latest daily mean dew point at the Observatory for the current Hong Kong year, for example `2026-08-31  25°C`. `--mean-temp` still prints the daily mean air temperature. `--dew-point --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No dew point is available.`

`hk-weather --park-dew` prints the latest daily mean dew point at King's Park, for example `2026-08-31  24.7°C`. `--dew-point` still prints the Observatory reading. `--park-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park dew point is available.`

`hk-weather --cheung-dew` prints the latest daily mean dew point at Cheung Chau, for example `2026-08-31  25.6°C`. `--dew-point` still prints the Observatory reading, and `--park-dew` still prints King's Park. `--cheung-wind` still prints Cheung Chau's daily mean wind speed. `--cheung-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau dew point is available.`

`hk-weather --wong-chuk-hang-dew` prints the latest daily mean dew point at Wong Chuk Hang, for example `2026-08-31  25.9°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, and `--cheung-dew` still prints Cheung Chau. `--wong-chuk-hang-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Chuk Hang dew point is available.`

`hk-weather --sai-kung-dew` prints the latest daily mean dew point at Sai Kung, for example `2026-08-31  25.2°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, and `--sai-kung-temp` still prints Sai Kung's daily mean temperature. `--sai-kung-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sai Kung dew point is available.`

`hk-weather --sha-tin-dew` prints the latest daily mean dew point at Sha Tin, for example `2026-08-31  25.4°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, and `--sha-tin-pressure` still prints Sha Tin's daily mean pressure. `--sha-tin-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin dew point is available.`

`hk-weather --sheung-shui-dew` prints the latest daily mean dew point at Sheung Shui, for example `2026-08-31  24.8°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, and `--sha-tin-dew` still prints Sha Tin. `--sheung-shui-max` still prints Sheung Shui's maximum temperature, `--sheung-shui-pressure` still prints its pressure, `--sheung-shui-rain` still prints its rainfall, and `--sheung-shui-humidity` still prints its humidity. `--sheung-shui-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sheung Shui dew point is available.`

`hk-weather --waglan-dew` prints the latest daily mean dew point at Waglan Island, for example `2026-08-31  26°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, `--sha-tin-dew` still prints Sha Tin, and `--sheung-shui-dew` still prints Sheung Shui. `--waglan-max` still prints Waglan Island's maximum, `--waglan-min` still prints its minimum, `--waglan-humidity` still prints its humidity, `--waglan-pressure` still prints its pressure, and `--waglan-rain` still prints its rainfall. `--waglan-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Waglan Island dew point is available.`

`hk-weather --lau-fau-dew` prints the latest daily mean dew point at Lau Fau Shan, for example `2026-08-31  25.7°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, `--sha-tin-dew` still prints Sha Tin, `--sheung-shui-dew` still prints Sheung Shui, and `--waglan-dew` still prints Waglan Island. `--lau-fau-max` still prints Lau Fau Shan's maximum, `--lau-fau-min` still prints its minimum, `--lau-fau-rain` still prints its rainfall, `--lau-fau-wind` still prints its wind speed, `--lau-fau-humidity` still prints its humidity, and `--lau-fau-pressure` still prints its pressure. `--lau-fau-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Lau Fau Shan dew point is available.`

`hk-weather --wetland-dew` prints the latest daily mean dew point at Wetland Park, for example `2026-08-31  25.9°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, `--sha-tin-dew` still prints Sha Tin, `--sheung-shui-dew` still prints Sheung Shui, `--waglan-dew` still prints Waglan Island, and `--lau-fau-dew` still prints Lau Fau Shan. `--wetland-rain` still prints Wetland Park's rainfall, and `--wetland-humidity` still prints its humidity. `--wetland-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wetland Park dew point is available.`

`hk-weather --ta-kwu-ling-dew` prints the latest daily mean dew point at Ta Kwu Ling, for example `2026-08-31  25.7°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, `--sha-tin-dew` still prints Sha Tin, `--sheung-shui-dew` still prints Sheung Shui, `--waglan-dew` still prints Waglan Island, `--lau-fau-dew` still prints Lau Fau Shan, and `--wetland-dew` still prints Wetland Park. `--ta-kwu-ling-humidity` still prints Ta Kwu Ling's humidity, and `--ta-kwu-ling-rain` still prints its rainfall. `--ta-kwu-ling-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ta Kwu Ling dew point is available.`

`hk-weather --shek-kong-dew` prints the latest daily mean dew point at Shek Kong, for example `2026-08-31  25.8°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, `--sha-tin-dew` still prints Sha Tin, `--sheung-shui-dew` still prints Sheung Shui, `--waglan-dew` still prints Waglan Island, `--lau-fau-dew` still prints Lau Fau Shan, `--wetland-dew` still prints Wetland Park, and `--ta-kwu-ling-dew` still prints Ta Kwu Ling. `--shek-kong-max` still prints Shek Kong's maximum, `--shek-kong-min` still prints its minimum, `--shek-kong-humidity` still prints its humidity, and `--shek-kong-rain` still prints its rainfall. `--shek-kong-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shek Kong dew point is available.`

`hk-weather --tseung-kwan-o-dew` prints the latest daily mean dew point at Tseung Kwan O, for example `2026-08-31  25.6°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, `--sha-tin-dew` still prints Sha Tin, `--sheung-shui-dew` still prints Sheung Shui, `--waglan-dew` still prints Waglan Island, `--lau-fau-dew` still prints Lau Fau Shan, `--wetland-dew` still prints Wetland Park, `--ta-kwu-ling-dew` still prints Ta Kwu Ling, and `--shek-kong-dew` still prints Shek Kong. `--tseung-kwan-o-max` still prints Tseung Kwan O's maximum, `--tseung-kwan-o-min` still prints its minimum, `--tseung-kwan-o-temp` still prints its daily mean, and `--tseung-kwan-o-rain` still prints its rainfall. `--tseung-kwan-o-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tseung Kwan O dew point is available.`

`hk-weather --tai-mo-dew` prints the latest daily mean dew point at Tai Mo Shan, for example `2026-08-31  21.1°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, `--sha-tin-dew` still prints Sha Tin, `--sheung-shui-dew` still prints Sheung Shui, `--waglan-dew` still prints Waglan Island, `--lau-fau-dew` still prints Lau Fau Shan, `--wetland-dew` still prints Wetland Park, `--ta-kwu-ling-dew` still prints Ta Kwu Ling, `--shek-kong-dew` still prints Shek Kong, and `--tseung-kwan-o-dew` still prints Tseung Kwan O. `--tai-mo-temp` still prints Tai Mo Shan's mean temperature, `--tai-mo-min` still prints its minimum, `--tai-mo-max` still prints its maximum, and `--tai-mo-humidity` still prints its humidity. `--tai-mo-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan dew point is available.`

`hk-weather --peng-chau-dew` prints the latest daily mean dew point at Peng Chau, for example `2026-08-31  24.7°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, `--sha-tin-dew` still prints Sha Tin, `--sheung-shui-dew` still prints Sheung Shui, `--waglan-dew` still prints Waglan Island, `--lau-fau-dew` still prints Lau Fau Shan, `--wetland-dew` still prints Wetland Park, `--ta-kwu-ling-dew` still prints Ta Kwu Ling, `--shek-kong-dew` still prints Shek Kong, `--tseung-kwan-o-dew` still prints Tseung Kwan O, and `--tai-mo-dew` still prints Tai Mo Shan. `--peng-chau-temp` still prints Peng Chau's mean temperature, `--peng-chau-humidity` still prints its humidity, `--peng-chau-pressure` still prints its pressure, `--peng-chau-wind` still prints its wind speed, and `--peng-chau-rain` still prints its rainfall. `--peng-chau-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Peng Chau dew point is available.`

`hk-weather --sha-lo-wan-dew` prints the latest daily mean dew point at Sha Lo Wan, for example `2026-08-31  25.6°C`. `--dew-point` still prints the Observatory reading, `--park-dew` still prints King's Park, `--cheung-dew` still prints Cheung Chau, `--wong-chuk-hang-dew` still prints Wong Chuk Hang, `--sai-kung-dew` still prints Sai Kung, `--sha-tin-dew` still prints Sha Tin, `--sheung-shui-dew` still prints Sheung Shui, `--waglan-dew` still prints Waglan Island, `--lau-fau-dew` still prints Lau Fau Shan, `--wetland-dew` still prints Wetland Park, `--ta-kwu-ling-dew` still prints Ta Kwu Ling, `--shek-kong-dew` still prints Shek Kong, `--tseung-kwan-o-dew` still prints Tseung Kwan O, `--tai-mo-dew` still prints Tai Mo Shan, and `--peng-chau-dew` still prints Peng Chau. `--sha-lo-wan-temp` still prints Sha Lo Wan's mean temperature, `--sha-lo-wan-humidity` still prints its humidity, `--sha-lo-wan-wind` still prints its wind speed, and `--sha-lo-wan-prevailing` still prints its prevailing wind. `--sha-lo-wan-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Lo Wan dew point is available.`

`hk-weather --airport-dew` prints the latest daily mean dew point at Hong Kong International Airport, for example `2026-07-31  23.7°C`. The published airport series currently ends in July. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--airport-temp` still prints the airport mean temperature, `--airport-max` still prints its maximum, `--airport-min` still prints its minimum, `--airport-humidity` still prints its humidity, `--airport-rain` still prints its rainfall, `--airport-pressure` still prints its pressure, and `--airport-wet` still prints its wet-bulb temperature. `--airport-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No airport dew point is available.`

`hk-weather --clear-water-bay-dew` prints the latest daily mean dew point at Clear Water Bay, for example `2026-08-31  25°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--clear-water-bay-temp` still prints Clear Water Bay's mean temperature, `--clear-water-bay-max` still prints its maximum, `--clear-water-bay-min` still prints its minimum, and `--clear-water-bay-rain` still prints its rainfall. `--clear-water-bay-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Clear Water Bay dew point is available.`

`hk-weather --hong-kong-park-dew` prints the latest daily mean dew point at Hong Kong Park, for example `2026-08-31  25.1°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--hong-kong-park-temp` still prints Hong Kong Park's mean temperature, `--hong-kong-park-max` still prints its maximum, and `--hong-kong-park-min` still prints its minimum. `--hong-kong-park-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Hong Kong Park dew point is available.`

`hk-weather --tsuen-wan-dew` prints the latest daily mean dew point at Tsuen Wan, for example `2026-08-31  24.8°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--tsuen-wan-temp` still prints Tsuen Wan's mean temperature, `--tsuen-wan-max` still prints its maximum, `--tsuen-wan-min` still prints its minimum, and `--tsuen-wan-rain` still prints its rainfall. `--tsuen-wan-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan dew point is available.`

`hk-weather --shau-kei-wan-dew` prints the latest daily mean dew point at Shau Kei Wan, for example `2026-08-31  25.2°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--shau-kei-wan-humidity` still prints Shau Kei Wan's humidity. `--shau-kei-wan-dew --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shau Kei Wan dew point is available.`

`hk-weather --kau-sai-chau-dew` prints the latest daily mean dew point at Kau Sai Chau, for example `2026-08-31  25°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--kau-sai-chau-rain` still prints Kau Sai Chau's rainfall. `--kau-sai-chau-dew --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `滘西洲` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Kau Sai Chau dew point is available.`

`hk-weather --pak-tam-chung-dew` prints the latest daily mean dew point at Pak Tam Chung (Tsak Yue Wu), for example `2026-08-31  25.6°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--pak-tam-chung-temp` still prints Pak Tam Chung's mean temperature, `--pak-tam-chung-max` still prints its maximum, and `--pak-tam-chung-min` still prints its minimum. `--pak-tam-chung-dew --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `北潭涌(鯽魚湖)` and simplified text uses `北潭涌(鲫鱼湖)`. Days marked `***` are omitted. If none remain, it says `No Pak Tam Chung (Tsak Yue Wu) dew point is available.`

`hk-weather --beas-river-dew` prints the latest daily mean dew point at Beas River, for example `2026-08-31  25.4°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--beas-river-temp` still prints Beas River's mean temperature, `--beas-river-max` still prints its maximum, and `--beas-river-min` still prints its minimum. `--beas-river-dew --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `上水雙魚河` and simplified text uses `上水双鱼河`. Days marked `***` are omitted. If none remain, it says `No Beas River dew point is available.`

`hk-weather --runway-park-dew` prints the latest daily mean dew point at Kai Tak Runway Park, for example `2026-08-31  24.7°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--runway-park-temp` still prints Kai Tak Runway Park's mean temperature. `--runway-park-dew --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `啟德跑道公園` and simplified text uses `启德跑道公园`. Days marked `***` are omitted. If none remain, it says `No Kai Tak Runway Park dew point is available.`

`hk-weather --kowloon-city-dew` prints the latest daily mean dew point at Kowloon City, for example `2026-08-31  25°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--kowloon-city-temp` still prints Kowloon City's mean temperature, `--kowloon-city-max` still prints its maximum, and `--kowloon-city-min` still prints its minimum. `--kowloon-city-dew --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `九龍城` and simplified text uses `九龙城`. Days marked `***` are omitted. If none remain, it says `No Kowloon City dew point is available.`

`hk-weather --nei-lak-shan-dew` prints the latest daily mean dew point at Nei Lak Shan, for example `2026-08-31  22.2°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--nei-lak-shan-temp` still prints Nei Lak Shan's mean temperature. `--nei-lak-shan-dew --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `彌勒山` and simplified text uses `弥勒山`. Days marked `***` are omitted. If none remain, it says `No Nei Lak Shan dew point is available.`

`hk-weather --new-tsing-yi-dew` prints the latest daily mean dew point at New Tsing Yi Station, for example `2026-08-31  25.1°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--new-tsing-yi-temp` still prints New Tsing Yi Station's mean temperature, `--new-tsing-yi-max` still prints its maximum, and `--new-tsing-yi-min` still prints its minimum. `--new-tsing-yi-dew --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `新青衣站` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No New Tsing Yi Station dew point is available.`

`hk-weather --tate-dew` prints the latest daily mean dew point at Tate's Cairn, for example `2026-08-31  23.3°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--tate-temp` still prints Tate's Cairn's mean temperature, `--tate-max` still prints its maximum, and `--tate-min` still prints its minimum. `--tate-dew --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `大老山` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Tate's Cairn dew point is available.`

`hk-weather --shing-mun-valley-dew` prints the latest daily mean dew point at Tsuen Wan Shing Mun Valley, for example `2026-08-31  24.6°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--shing-mun-valley-temp` still prints the valley's mean temperature, `--shing-mun-valley-max` still prints its maximum, `--shing-mun-valley-min` still prints its minimum, and `--tsuen-wan-dew` still prints Tsuen Wan. `--shing-mun-valley-dew --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `荃灣城門谷` and simplified text uses `荃湾城门谷`. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan Shing Mun Valley dew point is available.`

`hk-weather --tuen-mun-home-dew` prints the latest daily mean dew point at Tuen Mun Children and Juvenile Home, for example `2026-08-31  25.4°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--tuen-mun-home-temp` still prints the home's mean temperature, `--tuen-mun-home-max` still prints its maximum, and `--tuen-mun-home-min` still prints its minimum. `--tuen-mun-home-dew --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `屯門兒童及青少年院` and simplified text uses `屯门儿童及青少年院`. Days marked `***` are omitted. If none remain, it says `No Tuen Mun Children and Juvenile Home dew point is available.`

`hk-weather --buoy-2-dew` prints the latest daily mean dew point at Automatic Weather Buoy No.2 (Hong Kong International Airport, West), for example `2026-08-31  24.7°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--buoy-2-temp` still prints the buoy's mean temperature, `--buoy-2-max` still prints its maximum, and `--buoy-2-min` still prints its minimum. `--buoy-2-dew --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標2號 (香港國際機場西面)` and simplified text uses `自动气象浮标2号 (香港国际机场西面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) dew point is available.`

`hk-weather --buoy-8-dew` prints the latest daily mean dew point at Automatic Weather Buoy No.8 (Hong Kong International Airport, East), for example `2026-08-31  24.1°C`. `--dew-point` still prints the Observatory reading, and the other station dew-point flags still print their own stations. `--buoy-8-temp` still prints the buoy's mean temperature, and `--buoy-2-dew` still prints Automatic Weather Buoy No.2. `--buoy-8-dew --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標8號 (香港國際機場東面)` and simplified text uses `自动气象浮标8号 (香港国际机场东面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.8 (Hong Kong International Airport, East) dew point is available.`

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

`hk-weather --park-prevailing` prints the latest daily prevailing wind direction at King's Park, for example `2026-08-31  270°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, and `--park-wind` still prints King's Park's mean wind speed. `--park-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park prevailing wind is available.`

`hk-weather --lau-fau-prevailing` prints the latest daily prevailing wind direction at Lau Fau Shan, for example `2026-08-31  360°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, `--park-prevailing` still prints King's Park, and `--lau-fau-wind` still prints Lau Fau Shan's mean wind speed. `--lau-fau-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Lau Fau Shan prevailing wind is available.`

`hk-weather --sha-lo-wan-prevailing` prints the latest daily prevailing wind direction at Sha Lo Wan, for example `2026-08-31  260°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, `--park-prevailing` still prints King's Park, `--lau-fau-prevailing` still prints Lau Fau Shan, and `--sha-lo-wan-wind` still prints Sha Lo Wan's mean wind speed. `--sha-lo-wan-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Lo Wan prevailing wind is available.`

`hk-weather --wong-chuk-hang-prevailing` prints the latest daily prevailing wind direction at Wong Chuk Hang, for example `2026-08-31  130°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, `--park-prevailing` still prints King's Park, `--lau-fau-prevailing` still prints Lau Fau Shan, `--sha-lo-wan-prevailing` still prints Sha Lo Wan, and `--wong-chuk-hang-wind` still prints Wong Chuk Hang's mean wind speed. `--wong-chuk-hang-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Chuk Hang prevailing wind is available.`

`hk-weather --sai-kung-prevailing` prints the latest daily prevailing wind direction at Sai Kung, for example `2026-08-31  30°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, `--park-prevailing` still prints King's Park, `--lau-fau-prevailing` still prints Lau Fau Shan, `--sha-lo-wan-prevailing` still prints Sha Lo Wan, `--wong-chuk-hang-prevailing` still prints Wong Chuk Hang, and `--sai-kung-wind` still prints Sai Kung's mean wind speed. `--sai-kung-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sai Kung prevailing wind is available.`

`hk-weather --tseung-kwan-o-prevailing` prints the latest daily prevailing wind direction at Tseung Kwan O, for example `2026-08-31  90°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, `--park-prevailing` still prints King's Park, `--lau-fau-prevailing` still prints Lau Fau Shan, `--sha-lo-wan-prevailing` still prints Sha Lo Wan, `--wong-chuk-hang-prevailing` still prints Wong Chuk Hang, `--sai-kung-prevailing` still prints Sai Kung, and `--tseung-kwan-o-wind` still prints Tseung Kwan O's mean wind speed. `--tseung-kwan-o-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tseung Kwan O prevailing wind is available.`

`hk-weather --shek-kong-prevailing` prints the latest daily prevailing wind direction at Shek Kong, for example `2026-08-31  60°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, `--park-prevailing` still prints King's Park, `--lau-fau-prevailing` still prints Lau Fau Shan, `--sha-lo-wan-prevailing` still prints Sha Lo Wan, `--wong-chuk-hang-prevailing` still prints Wong Chuk Hang, `--sai-kung-prevailing` still prints Sai Kung, `--tseung-kwan-o-prevailing` still prints Tseung Kwan O, and `--shek-kong-wind` still prints Shek Kong's mean wind speed. `--shek-kong-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shek Kong prevailing wind is available.`

`hk-weather --sha-tin-prevailing` prints the latest daily prevailing wind direction at Sha Tin, for example `2026-08-31  10°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, `--park-prevailing` still prints King's Park, `--lau-fau-prevailing` still prints Lau Fau Shan, `--sha-lo-wan-prevailing` still prints Sha Lo Wan, `--wong-chuk-hang-prevailing` still prints Wong Chuk Hang, `--sai-kung-prevailing` still prints Sai Kung, `--tseung-kwan-o-prevailing` still prints Tseung Kwan O, `--shek-kong-prevailing` still prints Shek Kong, and `--sha-tin-wind` still prints Sha Tin's mean wind speed. `--sha-tin-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin prevailing wind is available.`

`hk-weather --ta-kwu-ling-prevailing` prints the latest daily prevailing wind direction at Ta Kwu Ling, for example `2026-08-31  100°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, `--park-prevailing` still prints King's Park, `--lau-fau-prevailing` still prints Lau Fau Shan, `--sha-lo-wan-prevailing` still prints Sha Lo Wan, `--wong-chuk-hang-prevailing` still prints Wong Chuk Hang, `--sai-kung-prevailing` still prints Sai Kung, `--tseung-kwan-o-prevailing` still prints Tseung Kwan O, `--shek-kong-prevailing` still prints Shek Kong, `--sha-tin-prevailing` still prints Sha Tin, and `--ta-kwu-ling-wind` still prints Ta Kwu Ling's mean wind speed. `--ta-kwu-ling-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ta Kwu Ling prevailing wind is available.`

`hk-weather --wetland-prevailing` prints the latest daily prevailing wind direction at Wetland Park, for example `2026-08-31  320°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, `--park-prevailing` still prints King's Park, `--lau-fau-prevailing` still prints Lau Fau Shan, `--sha-lo-wan-prevailing` still prints Sha Lo Wan, `--wong-chuk-hang-prevailing` still prints Wong Chuk Hang, `--sai-kung-prevailing` still prints Sai Kung, `--tseung-kwan-o-prevailing` still prints Tseung Kwan O, `--shek-kong-prevailing` still prints Shek Kong, `--sha-tin-prevailing` still prints Sha Tin, `--ta-kwu-ling-prevailing` still prints Ta Kwu Ling, and `--wetland-wind` still prints Wetland Park's mean wind speed. `--wetland-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wetland Park prevailing wind is available.`

`hk-weather --tai-mo-prevailing` prints the latest daily prevailing wind direction at Tai Mo Shan, for example `2026-08-31  20°`. `--prevailing` still prints Waglan Island, `--cheung-prevailing` still prints Cheung Chau, `--ping-chau-prevailing` still prints Ping Chau, `--tai-mo-to-prevailing` still prints Tai Mo To, `--tai-po-kau-prevailing` still prints Tai Po Kau, `--park-prevailing` still prints King's Park, `--lau-fau-prevailing` still prints Lau Fau Shan, `--sha-lo-wan-prevailing` still prints Sha Lo Wan, `--wong-chuk-hang-prevailing` still prints Wong Chuk Hang, `--sai-kung-prevailing` still prints Sai Kung, `--tseung-kwan-o-prevailing` still prints Tseung Kwan O, `--shek-kong-prevailing` still prints Shek Kong, `--sha-tin-prevailing` still prints Sha Tin, `--ta-kwu-ling-prevailing` still prints Ta Kwu Ling, `--wetland-prevailing` still prints Wetland Park, and `--tai-mo-wind` still prints Tai Mo Shan's mean wind speed. `--tai-mo-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan prevailing wind is available.`

`hk-weather --airport-prevailing` prints the latest daily prevailing wind direction at Hong Kong International Airport, for example `2026-07-31  90°`. The published airport series currently ends in July. `--prevailing` still prints Waglan Island, and the other station prevailing-wind flags still print their own stations. `--airport-wind` still prints the airport mean wind speed, `--airport-temp` still prints its mean temperature, `--airport-dew` still prints its dew point, `--airport-humidity` still prints its humidity, `--airport-rain` still prints its rainfall, `--airport-pressure` still prints its pressure, and `--airport-wet` still prints its wet-bulb temperature. `--airport-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No airport prevailing wind is available.`

`hk-weather --kai-tak-prevailing` prints the latest daily prevailing wind direction at Kai Tak, for example `2026-08-31  140°`. `--prevailing` still prints Waglan Island, and the other station prevailing-wind flags still print their own stations. `--kai-tak-wind` still prints Kai Tak's mean wind speed, and `--kai-tak-rain` still prints its rainfall. `--kai-tak-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `啟德` and simplified text uses `启德`. Days marked `***` are omitted. If none remain, it says `No Kai Tak prevailing wind is available.`

`hk-weather --green-island-prevailing` prints the latest daily prevailing wind direction at Green Island, for example `2026-08-31  350°`. `--prevailing` still prints Waglan Island, and the other station prevailing-wind flags still print their own stations. `--green-island-wind` still prints Green Island's mean wind speed, and `--green-island-rain` still prints its rainfall. `--green-island-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `青洲` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Green Island prevailing wind is available.`

`hk-weather --ngong-ping-prevailing` prints the latest daily prevailing wind direction at Ngong Ping, for example `2026-08-31  50°`. `--prevailing` still prints Waglan Island, and the other station prevailing-wind flags still print their own stations. `--ngong-ping-wind` still prints Ngong Ping's mean wind speed, `--ngong-ping-temp` still prints its mean temperature, `--ngong-ping-max` still prints its maximum, and `--ngong-ping-min` still prints its minimum. `--ngong-ping-reservoir-rain` still prints Ngong Ping Fresh Water Reservoir's rainfall. `--ngong-ping-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `昂坪` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Ngong Ping prevailing wind is available.`

`hk-weather --tai-mei-tuk-prevailing` prints the latest daily prevailing wind direction at Tai Mei Tuk, for example `2026-08-31  280°`. `--prevailing` still prints Waglan Island, and the other station prevailing-wind flags still print their own stations. `--tai-mei-tuk-wind` still prints Tai Mei Tuk's mean wind speed, `--tai-mei-tuk-temp` still prints its mean temperature, and `--tai-mei-tuk-rain` still prints its rainfall. `--tai-mei-tuk-pump-rain` still prints Tai Mei Tuk Pumping Station's rainfall. `--tai-mei-tuk-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `大美督` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Tai Mei Tuk prevailing wind is available.`

`hk-weather --central-pier-prevailing` prints the latest daily prevailing wind direction at Central Pier, for example `2026-08-31  290°`. `--prevailing` still prints Waglan Island, and the other station prevailing-wind flags still print their own stations. `--central-pier-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `中環碼頭` and simplified text uses `中环码头`. Days marked `***` are omitted. If none remain, it says `No Central Pier prevailing wind is available.`

`hk-weather --nei-lak-shan-prevailing` prints the latest daily prevailing wind direction at Nei Lak Shan, for example `2026-08-31  20°`. `--prevailing` still prints Waglan Island, and the other station prevailing-wind flags still print their own stations. `--nei-lak-shan-wind` still prints Nei Lak Shan's mean wind speed, `--nei-lak-shan-temp` still prints its mean temperature, `--nei-lak-shan-dew` still prints its dew point, and `--nei-lak-shan-humidity` still prints its humidity. `--nei-lak-shan-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `彌勒山` and simplified text uses `弥勒山`. Days marked `***` are omitted. If none remain, it says `No Nei Lak Shan prevailing wind is available.`

`hk-weather --buoy-2-prevailing` prints the latest daily prevailing wind direction at Automatic Weather Buoy No.2 (Hong Kong International Airport, West), for example `2026-08-31  350°`. `--prevailing` still prints Waglan Island, and the other station prevailing-wind flags still print their own stations. `--buoy-2-wind` still prints the buoy's mean wind speed. `--buoy-2-prevailing --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標2號 (香港國際機場西面)` and simplified text uses `自动气象浮标2号 (香港国际机场西面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) prevailing wind is available.`

`hk-weather --mean-wind` prints the latest daily mean wind speed at Waglan Island, for example `2026-08-31  5.9 km/h`. `--prevailing` still prints the wind direction, and `--gust` still prints the latest gusts. `--mean-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No mean wind speed is available.`

`hk-weather --cheung-wind` prints the latest daily mean wind speed at Cheung Chau, for example `2026-08-31  9.2 km/h`. `--mean-wind` still prints Waglan Island, and `--cheung-prevailing` still prints the wind direction. `--cheung-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau mean wind speed is available.`

`hk-weather --lau-fau-wind` prints the latest daily mean wind speed at Lau Fau Shan, for example `2026-08-31  6.8 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, and `--lau-fau-rain` still prints Lau Fau Shan's rainfall. `--lau-fau-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Lau Fau Shan mean wind speed is available.`

`hk-weather --peng-chau-wind` prints the latest daily mean wind speed at Peng Chau, for example `2026-08-31  9.7 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, and `--lau-fau-wind` still prints Lau Fau Shan. A speed of zero is kept. `--peng-chau-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Peng Chau mean wind speed is available.`

`hk-weather --tai-po-kau-wind` prints the latest daily mean wind speed at Tai Po Kau, for example `2026-08-31  4.8 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, and `--peng-chau-wind` still prints Peng Chau. A speed of zero is kept. `--tai-po-kau-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Po Kau mean wind speed is available.`

`hk-weather --tai-mo-to-wind` prints the latest daily mean wind speed at Tai Mo To, for example `2026-08-31  7.4 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, and `--tai-po-kau-wind` still prints Tai Po Kau. `--tai-mo-to-prevailing` still prints Tai Mo To's prevailing wind direction. A speed of zero is kept. `--tai-mo-to-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo To mean wind speed is available.`

`hk-weather --tai-mo-wind` prints the latest daily mean wind speed at Tai Mo Shan, for example `2026-08-31  10.9 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, and `--tai-mo-to-wind` still prints Tai Mo To. `--tai-mo-temp` still prints Tai Mo Shan's mean temperature, `--tai-mo-max` still prints its maximum, `--tai-mo-min` still prints its minimum, `--tai-mo-dew` still prints its dew point, `--tai-mo-rain` still prints its rainfall, `--tai-mo-humidity` still prints its humidity, and `--tai-mo-pressure` still prints its pressure. A speed of zero is kept. `--tai-mo-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan mean wind speed is available.`

`hk-weather --tate-wind` prints the latest daily mean wind speed at Tate's Cairn, for example `2026-08-31  9.8 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, and `--tai-mo-wind` still prints Tai Mo Shan. `--tate-temp` still prints Tate's Cairn's mean temperature, `--tate-max` still prints its maximum, `--tate-min` still prints its minimum, `--tate-humidity` still prints its humidity, `--tate-pressure` still prints its pressure, and `--tate-rain` still prints its rainfall. A speed of zero is kept. `--tate-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tate's Cairn mean wind speed is available.`

`hk-weather --shek-kong-wind` prints the latest daily mean wind speed at Shek Kong, for example `2026-08-31  3.1 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, `--tai-mo-wind` still prints Tai Mo Shan, and `--tate-wind` still prints Tate's Cairn. `--shek-kong-temp` still prints Shek Kong's mean temperature, `--shek-kong-max` still prints its maximum, `--shek-kong-min` still prints its minimum, `--shek-kong-dew` still prints its dew point, `--shek-kong-rain` still prints its rainfall, and `--shek-kong-humidity` still prints its humidity. A speed of zero is kept. `--shek-kong-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shek Kong mean wind speed is available.`

`hk-weather --sai-kung-wind` prints the latest daily mean wind speed at Sai Kung, for example `2026-08-31  6.6 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, `--tai-mo-wind` still prints Tai Mo Shan, `--tate-wind` still prints Tate's Cairn, and `--shek-kong-wind` still prints Shek Kong. `--sai-kung-temp` still prints Sai Kung's mean temperature, `--sai-kung-max` still prints its maximum, `--sai-kung-min` still prints its minimum, `--sai-kung-dew` still prints its dew point, and `--sai-kung-humidity` still prints its humidity. A speed of zero is kept. `--sai-kung-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sai Kung mean wind speed is available.`

`hk-weather --sha-tin-wind` prints the latest daily mean wind speed at Sha Tin, for example `2026-08-31  3.9 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, `--tai-mo-wind` still prints Tai Mo Shan, `--tate-wind` still prints Tate's Cairn, `--shek-kong-wind` still prints Shek Kong, and `--sai-kung-wind` still prints Sai Kung. `--sha-tin-temp` still prints Sha Tin's mean temperature, `--sha-tin-max` still prints its maximum, `--sha-tin-min` still prints its minimum, `--sha-tin-dew` still prints its dew point, `--sha-tin-rain` still prints its rainfall, `--sha-tin-humidity` still prints its humidity, and `--sha-tin-pressure` still prints its pressure. A speed of zero is kept. `--sha-tin-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin mean wind speed is available.`

`hk-weather --wong-chuk-hang-wind` prints the latest daily mean wind speed at Wong Chuk Hang, for example `2026-08-31  2.1 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, `--tai-mo-wind` still prints Tai Mo Shan, `--tate-wind` still prints Tate's Cairn, `--shek-kong-wind` still prints Shek Kong, `--sai-kung-wind` still prints Sai Kung, and `--sha-tin-wind` still prints Sha Tin. `--wong-chuk-hang-temp` still prints Wong Chuk Hang's mean temperature, `--wong-chuk-hang-max` still prints its maximum, `--wong-chuk-hang-min` still prints its minimum, `--wong-chuk-hang-dew` still prints its dew point, and `--wong-chuk-hang-humidity` still prints its humidity. A speed of zero is kept. `--wong-chuk-hang-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Chuk Hang mean wind speed is available.`

`hk-weather --park-wind` prints the latest daily mean wind speed at King's Park, for example `2026-08-31  4.8 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, `--tai-mo-wind` still prints Tai Mo Shan, `--tate-wind` still prints Tate's Cairn, `--shek-kong-wind` still prints Shek Kong, `--sai-kung-wind` still prints Sai Kung, `--sha-tin-wind` still prints Sha Tin, and `--wong-chuk-hang-wind` still prints Wong Chuk Hang. `--park-temp` still prints King's Park's mean temperature, `--park-max` still prints its maximum, `--park-min` still prints its minimum, `--park-dew` still prints its dew point, `--park-rain` still prints its rainfall, `--park-humidity` still prints its humidity, `--park-pressure` still prints its pressure, and `--park-wet` still prints its wet-bulb temperature. A speed of zero is kept. `--park-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park mean wind speed is available.`

`hk-weather --wetland-wind` prints the latest daily mean wind speed at Wetland Park, for example `2026-08-31  0.2 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, `--tai-mo-wind` still prints Tai Mo Shan, `--tate-wind` still prints Tate's Cairn, `--shek-kong-wind` still prints Shek Kong, `--sai-kung-wind` still prints Sai Kung, `--sha-tin-wind` still prints Sha Tin, `--wong-chuk-hang-wind` still prints Wong Chuk Hang, and `--park-wind` still prints King's Park. `--wetland-temp` still prints Wetland Park's mean temperature, `--wetland-max` still prints its maximum, `--wetland-min` still prints its minimum, `--wetland-dew` still prints its dew point, `--wetland-rain` still prints its rainfall, `--wetland-humidity` still prints its humidity, and `--wetland-pressure` still prints its pressure. A speed of zero is kept. `--wetland-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wetland Park mean wind speed is available.`

`hk-weather --tseung-kwan-o-wind` prints the latest daily mean wind speed at Tseung Kwan O, for example `2026-08-31  3.4 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, `--tai-mo-wind` still prints Tai Mo Shan, `--tate-wind` still prints Tate's Cairn, `--shek-kong-wind` still prints Shek Kong, `--sai-kung-wind` still prints Sai Kung, `--sha-tin-wind` still prints Sha Tin, `--wong-chuk-hang-wind` still prints Wong Chuk Hang, `--park-wind` still prints King's Park, and `--wetland-wind` still prints Wetland Park. `--tseung-kwan-o-temp` still prints Tseung Kwan O's mean temperature, `--tseung-kwan-o-max` still prints its maximum, `--tseung-kwan-o-min` still prints its minimum, `--tseung-kwan-o-dew` still prints its dew point, `--tseung-kwan-o-rain` still prints its rainfall, and `--tseung-kwan-o-humidity` still prints its humidity. A speed of zero is kept. `--tseung-kwan-o-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tseung Kwan O mean wind speed is available.`

`hk-weather --ta-kwu-ling-wind` prints the latest daily mean wind speed at Ta Kwu Ling, for example `2026-08-31  2.9 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, `--tai-mo-wind` still prints Tai Mo Shan, `--tate-wind` still prints Tate's Cairn, `--shek-kong-wind` still prints Shek Kong, `--sai-kung-wind` still prints Sai Kung, `--sha-tin-wind` still prints Sha Tin, `--wong-chuk-hang-wind` still prints Wong Chuk Hang, `--park-wind` still prints King's Park, `--wetland-wind` still prints Wetland Park, and `--tseung-kwan-o-wind` still prints Tseung Kwan O. `--ta-kwu-ling-temp` still prints Ta Kwu Ling's mean temperature, `--ta-kwu-ling-max` still prints its maximum, `--ta-kwu-ling-min` still prints its minimum, `--ta-kwu-ling-dew` still prints its dew point, `--ta-kwu-ling-rain` still prints its rainfall, and `--ta-kwu-ling-humidity` still prints its humidity. A speed of zero is kept. `--ta-kwu-ling-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ta Kwu Ling mean wind speed is available.`

`hk-weather --sha-lo-wan-wind` prints the latest daily mean wind speed at Sha Lo Wan, for example `2026-08-31  4.5 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, `--tai-mo-wind` still prints Tai Mo Shan, `--tate-wind` still prints Tate's Cairn, `--shek-kong-wind` still prints Shek Kong, `--sai-kung-wind` still prints Sai Kung, `--sha-tin-wind` still prints Sha Tin, `--wong-chuk-hang-wind` still prints Wong Chuk Hang, `--park-wind` still prints King's Park, `--wetland-wind` still prints Wetland Park, `--tseung-kwan-o-wind` still prints Tseung Kwan O, and `--ta-kwu-ling-wind` still prints Ta Kwu Ling. `--sha-lo-wan-temp` still prints Sha Lo Wan's mean temperature, `--sha-lo-wan-max` still prints its maximum, `--sha-lo-wan-min` still prints its minimum, `--sha-lo-wan-humidity` still prints its humidity, and `--sha-lo-wan-wet` still prints its wet-bulb temperature. A speed of zero is kept. `--sha-lo-wan-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Lo Wan mean wind speed is available.`

`hk-weather --ping-chau-wind` prints the latest daily mean wind speed at Ping Chau, for example `2026-08-31  1.5 km/h`. `--mean-wind` still prints Waglan Island, `--cheung-wind` still prints Cheung Chau, `--lau-fau-wind` still prints Lau Fau Shan, `--peng-chau-wind` still prints Peng Chau, `--tai-po-kau-wind` still prints Tai Po Kau, `--tai-mo-to-wind` still prints Tai Mo To, `--tai-mo-wind` still prints Tai Mo Shan, `--tate-wind` still prints Tate's Cairn, `--shek-kong-wind` still prints Shek Kong, `--sai-kung-wind` still prints Sai Kung, `--sha-tin-wind` still prints Sha Tin, `--wong-chuk-hang-wind` still prints Wong Chuk Hang, `--park-wind` still prints King's Park, `--wetland-wind` still prints Wetland Park, `--tseung-kwan-o-wind` still prints Tseung Kwan O, `--ta-kwu-ling-wind` still prints Ta Kwu Ling, and `--sha-lo-wan-wind` still prints Sha Lo Wan. `--ping-chau-temp` still prints Ping Chau's mean temperature, `--ping-chau-rain` still prints its rainfall, and `--ping-chau-prevailing` still prints its prevailing wind direction. A speed of zero is kept. `--ping-chau-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ping Chau mean wind speed is available.`

`hk-weather --airport-wind` prints the latest daily mean wind speed at Hong Kong International Airport, for example `2026-07-31  14 km/h`. The published airport series currently ends in July. `--mean-wind` still prints Waglan Island, and the other station wind flags still print their own stations. `--airport-temp` still prints the airport mean temperature, `--airport-max` still prints its maximum, `--airport-min` still prints its minimum, `--airport-humidity` still prints its humidity, `--airport-dew` still prints its dew point, `--airport-rain` still prints its rainfall, `--airport-pressure` still prints its pressure, and `--airport-wet` still prints its wet-bulb temperature. A speed of zero is kept. `--airport-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No airport mean wind speed is available.`

`hk-weather --green-island-wind` prints the latest daily mean wind speed at Green Island, for example `2026-08-31  9.3 km/h`. `--mean-wind` still prints Waglan Island, and the other station wind flags still print their own stations. `--green-island-rain` still prints Green Island's rainfall. A speed of zero is kept. `--green-island-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Green Island mean wind speed is available.`

`hk-weather --ngong-ping-wind` prints the latest daily mean wind speed at Ngong Ping, for example `2026-08-31  12.5 km/h`. `--mean-wind` still prints Waglan Island, and the other station wind flags still print their own stations. `--ngong-ping-temp` still prints Ngong Ping's mean temperature, `--ngong-ping-max` still prints its maximum, and `--ngong-ping-min` still prints its minimum. A speed of zero is kept. `--ngong-ping-wind --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ngong Ping mean wind speed is available.`

`hk-weather --tai-mei-tuk-wind` prints the latest daily mean wind speed at Tai Mei Tuk, for example `2026-08-31  5.7 km/h`. `--mean-wind` still prints Waglan Island, and the other station wind flags still print their own stations. `--tai-mei-tuk-temp` still prints Tai Mei Tuk's mean temperature, and `--tai-mei-tuk-rain` still prints its rainfall. A speed of zero is kept. `--tai-mei-tuk-wind --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `大美督` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Tai Mei Tuk mean wind speed is available.`

`hk-weather --lamma-island-wind` prints the latest daily mean wind speed at Lamma Island, for example `2026-08-31  6 km/h`. `--mean-wind` still prints Waglan Island, and the other station wind flags still print their own stations. `--lamma-island-rain` still prints Lamma Island's rainfall. A speed of zero is kept. `--lamma-island-wind --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `南丫島` and simplified text uses `南丫岛`. Days marked `***` are omitted. If none remain, it says `No Lamma Island mean wind speed is available.`

`hk-weather --kai-tak-wind` prints the latest daily mean wind speed at Kai Tak, for example `2026-08-31  4.7 km/h`. `--mean-wind` still prints Waglan Island, and the other station wind flags still print their own stations. `--kai-tak-rain` still prints Kai Tak's rainfall. A speed of zero is kept. `--kai-tak-wind --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `啟德` and simplified text uses `启德`. Days marked `***` are omitted. If none remain, it says `No Kai Tak mean wind speed is available.`

`hk-weather --central-pier-wind` prints the latest daily mean wind speed at Central Pier, for example `2026-08-31  8.2 km/h`. `--mean-wind` still prints Waglan Island, and the other station wind flags still print their own stations. `--central-pier-prevailing` still prints Central Pier's prevailing wind direction. A speed of zero is kept. `--central-pier-wind --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `中環碼頭` and simplified text uses `中环码头`. Days marked `***` are omitted. If none remain, it says `No Central Pier mean wind speed is available.`

`hk-weather --nei-lak-shan-wind` prints the latest daily mean wind speed at Nei Lak Shan, for example `2026-08-31  14.1 km/h`. `--mean-wind` still prints Waglan Island, and the other station wind flags still print their own stations. `--nei-lak-shan-temp` still prints Nei Lak Shan's mean temperature, `--nei-lak-shan-dew` still prints its dew point, and `--nei-lak-shan-humidity` still prints its humidity. A speed of zero is kept. `--nei-lak-shan-wind --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `彌勒山` and simplified text uses `弥勒山`. Days marked `***` are omitted. If none remain, it says `No Nei Lak Shan mean wind speed is available.`

`hk-weather --buoy-2-wind` prints the latest daily mean wind speed at Automatic Weather Buoy No.2 (Hong Kong International Airport, West), for example `2026-08-31  9.8 km/h`. `--mean-wind` still prints Waglan Island, and the other station wind flags still print their own stations. `--buoy-2-temp` still prints the buoy's mean temperature, `--buoy-2-max` still prints its maximum, `--buoy-2-min` still prints its minimum, `--buoy-2-dew` still prints its dew point, and `--buoy-2-humidity` still prints its humidity. A speed of zero is kept. `--buoy-2-wind --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標2號 (香港國際機場西面)` and simplified text uses `自动气象浮标2号 (香港国际机场西面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) mean wind speed is available.`

`hk-weather --buoy-8-wind` prints the latest daily mean wind speed at Automatic Weather Buoy No.8 (Hong Kong International Airport, East), for example `2026-08-31  5.2 km/h`. `--mean-wind` still prints Waglan Island, and the other station wind flags still print their own stations. `--buoy-8-temp` still prints the buoy's mean temperature, `--buoy-8-dew` still prints its dew point, `--buoy-8-humidity` still prints its humidity, and `--buoy-2-wind` still prints Automatic Weather Buoy No.2. A speed of zero is kept. `--buoy-8-wind --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標8號 (香港國際機場東面)` and simplified text uses `自动气象浮标8号 (香港国际机场东面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.8 (Hong Kong International Airport, East) mean wind speed is available.`

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

`hk-weather --sheung-shui-rain` prints the latest daily total rainfall at Sheung Shui, for example `2026-08-31  19.5 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, `--park-rain` still prints King's Park, and `--tseung-kwan-o-rain` still prints Tseung Kwan O. `--sheung-shui-max` still prints Sheung Shui's daily maximum, and `--sheung-shui-pressure` still prints its pressure. A total of zero is kept. `--sheung-shui-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sheung Shui rainfall is available.`

`hk-weather --sha-tin-rain` prints the latest daily total rainfall at Sha Tin, for example `2026-08-31  7 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, `--park-rain` still prints King's Park, `--tseung-kwan-o-rain` still prints Tseung Kwan O, and `--sheung-shui-rain` still prints Sheung Shui. `--sha-tin-pressure` still prints Sha Tin's pressure, and `--sha-tin-dew` still prints its dew point. A total of zero is kept. `--sha-tin-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin rainfall is available.`

`hk-weather --ta-kwu-ling-rain` prints the latest daily total rainfall at Ta Kwu Ling, for example `2026-08-31  13 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, `--park-rain` still prints King's Park, `--tseung-kwan-o-rain` still prints Tseung Kwan O, `--sheung-shui-rain` still prints Sheung Shui, and `--sha-tin-rain` still prints Sha Tin. `--ta-kwu-ling-humidity` still prints Ta Kwu Ling's humidity. A total of zero is kept. `--ta-kwu-ling-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ta Kwu Ling rainfall is available.`

`hk-weather --cheung-chau-rain` prints the latest daily total rainfall at Cheung Chau, for example `2026-08-31  2.5 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, `--park-rain` still prints King's Park, `--tseung-kwan-o-rain` still prints Tseung Kwan O, `--sheung-shui-rain` still prints Sheung Shui, `--sha-tin-rain` still prints Sha Tin, and `--ta-kwu-ling-rain` still prints Ta Kwu Ling. `--cheung-chau-max` still prints Cheung Chau's maximum temperature, `--cheung-chau-humidity` still prints its humidity, `--cheung-wind` still prints its wind speed, `--cheung-prevailing` still prints its prevailing direction, and `--cheung-dew` still prints its dew point. A total of zero is kept. `--cheung-chau-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau rainfall is available.`

`hk-weather --waglan-rain` prints the latest daily total rainfall at Waglan Island, for example `2026-08-31  1.5 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, `--park-rain` still prints King's Park, `--tseung-kwan-o-rain` still prints Tseung Kwan O, `--sheung-shui-rain` still prints Sheung Shui, `--sha-tin-rain` still prints Sha Tin, `--ta-kwu-ling-rain` still prints Ta Kwu Ling, and `--cheung-chau-rain` still prints Cheung Chau. `--waglan-max` still prints Waglan Island's maximum temperature, `--waglan-min` still prints its minimum, `--waglan-humidity` still prints its humidity, and `--waglan-pressure` still prints its pressure. A total of zero is kept. `--waglan-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Waglan Island rainfall is available.`

`hk-weather --tate-rain` prints the latest daily total rainfall at Tate's Cairn, for example `2026-08-31  5.5 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, `--park-rain` still prints King's Park, `--tseung-kwan-o-rain` still prints Tseung Kwan O, `--sheung-shui-rain` still prints Sheung Shui, `--sha-tin-rain` still prints Sha Tin, `--ta-kwu-ling-rain` still prints Ta Kwu Ling, `--cheung-chau-rain` still prints Cheung Chau, and `--waglan-rain` still prints Waglan Island. `--tate-max` still prints Tate's Cairn's maximum temperature, `--tate-min` still prints its minimum, `--tate-temp` still prints its daily mean, and `--tate-humidity` still prints its humidity. A total of zero is kept. `--tate-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tate's Cairn rainfall is available.`

`hk-weather --peng-chau-rain` prints the latest daily total rainfall at Peng Chau, for example `2026-08-31  8.5 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, `--park-rain` still prints King's Park, `--tseung-kwan-o-rain` still prints Tseung Kwan O, `--sheung-shui-rain` still prints Sheung Shui, `--sha-tin-rain` still prints Sha Tin, `--ta-kwu-ling-rain` still prints Ta Kwu Ling, `--cheung-chau-rain` still prints Cheung Chau, `--waglan-rain` still prints Waglan Island, and `--tate-rain` still prints Tate's Cairn. `--peng-chau-wind` still prints Peng Chau's wind speed. A total of zero is kept. `--peng-chau-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Peng Chau rainfall is available.`

`hk-weather --ping-chau-rain` prints the latest daily total rainfall at Ping Chau, for example `2026-08-31  9.5 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, `--park-rain` still prints King's Park, `--tseung-kwan-o-rain` still prints Tseung Kwan O, `--sheung-shui-rain` still prints Sheung Shui, `--sha-tin-rain` still prints Sha Tin, `--ta-kwu-ling-rain` still prints Ta Kwu Ling, `--cheung-chau-rain` still prints Cheung Chau, `--waglan-rain` still prints Waglan Island, `--tate-rain` still prints Tate's Cairn, and `--peng-chau-rain` still prints Peng Chau. `--ping-chau-temp` still prints Ping Chau's mean temperature, and `--ping-chau-prevailing` still prints its prevailing wind direction. A total of zero is kept. `--ping-chau-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ping Chau rainfall is available.`

`hk-weather --tai-mo-rain` prints the latest daily total rainfall at Tai Mo Shan, for example `2026-08-31  15.5 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, `--park-rain` still prints King's Park, `--tseung-kwan-o-rain` still prints Tseung Kwan O, `--sheung-shui-rain` still prints Sheung Shui, `--sha-tin-rain` still prints Sha Tin, `--ta-kwu-ling-rain` still prints Ta Kwu Ling, `--cheung-chau-rain` still prints Cheung Chau, `--waglan-rain` still prints Waglan Island, `--tate-rain` still prints Tate's Cairn, `--peng-chau-rain` still prints Peng Chau, and `--ping-chau-rain` still prints Ping Chau. `--tai-mo-temp` still prints Tai Mo Shan's mean temperature, `--tai-mo-min` still prints its minimum, `--tai-mo-max` still prints its maximum, `--tai-mo-humidity` still prints its humidity, and `--tai-mo-dew` still prints its dew point. A total of zero is kept. `--tai-mo-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan rainfall is available.`

`hk-weather --sha-lo-wan-rain` prints the latest daily total rainfall at Sha Lo Wan, for example `2026-08-31  4 mm`. `--daily-rain` still prints the Observatory total, `--lau-fau-rain` still prints Lau Fau Shan, `--shek-kong-rain` still prints Shek Kong, `--wetland-rain` still prints Wetland Park, `--sham-shui-po-rain` still prints Sham Shui Po, `--park-rain` still prints King's Park, `--tseung-kwan-o-rain` still prints Tseung Kwan O, `--sheung-shui-rain` still prints Sheung Shui, `--sha-tin-rain` still prints Sha Tin, `--ta-kwu-ling-rain` still prints Ta Kwu Ling, `--cheung-chau-rain` still prints Cheung Chau, `--waglan-rain` still prints Waglan Island, `--tate-rain` still prints Tate's Cairn, `--peng-chau-rain` still prints Peng Chau, `--ping-chau-rain` still prints Ping Chau, and `--tai-mo-rain` still prints Tai Mo Shan. `--sha-lo-wan-temp` still prints Sha Lo Wan's mean temperature, `--sha-lo-wan-humidity` still prints its humidity, `--sha-lo-wan-dew` still prints its dew point, `--sha-lo-wan-pressure` still prints its pressure, and `--sha-lo-wan-wind` still prints its wind speed. A total of zero is kept. `--sha-lo-wan-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Lo Wan rainfall is available.`

`hk-weather --airport-rain` prints the latest daily total rainfall at Hong Kong International Airport, for example `2026-07-31  25.6 mm`. The published airport series currently ends in July. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--airport-temp` still prints the airport mean temperature, `--airport-max` still prints its maximum, `--airport-min` still prints its minimum, and `--airport-humidity` still prints its humidity. A total of zero is kept. `--airport-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No airport rainfall is available.`

`hk-weather --green-island-rain` prints the latest daily total rainfall at Green Island, for example `2026-08-31  31.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--green-island-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Green Island rainfall is available.`

`hk-weather --tsuen-wan-rain` prints the latest daily total rainfall at Tsuen Wan, for example `2026-08-31  22 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--tsuen-wan-temp` still prints Tsuen Wan's mean temperature, `--tsuen-wan-max` still prints its maximum, and `--tsuen-wan-min` still prints its minimum. A total of zero is kept. `--tsuen-wan-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan rainfall is available.`

`hk-weather --tap-mun-rain` prints the latest daily total rainfall at Tap Mun, for example `2026-08-31  4 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--tap-mun-temp` still prints Tap Mun's mean temperature, `--tap-mun-max` still prints its maximum, and `--tap-mun-min` still prints its minimum. A total of zero is kept. `--tap-mun-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tap Mun rainfall is available.`

`hk-weather --clear-water-bay-rain` prints the latest daily total rainfall at Clear Water Bay, for example `2026-08-31  7 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--clear-water-bay-temp` still prints Clear Water Bay's mean temperature, `--clear-water-bay-max` still prints its maximum, and `--clear-water-bay-min` still prints its minimum. A total of zero is kept. `--clear-water-bay-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Clear Water Bay rainfall is available.`

`hk-weather --shau-kei-wan-rain` prints the latest daily total rainfall at Shau Kei Wan, for example `2026-08-31  31.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--shau-kei-wan-humidity` still prints Shau Kei Wan's humidity, and `--shau-kei-wan-dew` still prints its dew point. A total of zero is kept. `--shau-kei-wan-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shau Kei Wan rainfall is available.`

`hk-weather --happy-valley-rain` prints the latest daily total rainfall at Happy Valley, for example `2026-08-31  14.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--heat-index` still prints the Hong Kong Heat Index, which can include Happy Valley. A total of zero is kept. `--happy-valley-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Happy Valley rainfall is available.`

`hk-weather --tai-mei-tuk-rain` prints the latest daily total rainfall at Tai Mei Tuk, for example `2026-08-31  16 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--tai-mei-tuk-temp` still prints Tai Mei Tuk's mean temperature. A total of zero is kept. `--tai-mei-tuk-rain --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `大美督` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Tai Mei Tuk rainfall is available.`

`hk-weather --kadoorie-farm-rain` prints the latest daily total rainfall at Kadoorie Farm and Botanic Garden, for example `2026-08-31  20.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--tai-mei-tuk-rain` still prints Tai Mei Tuk's rainfall. A total of zero is kept. `--kadoorie-farm-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Kadoorie Farm and Botanic Garden rainfall is available.`

`hk-weather --the-peak-rain` prints the latest daily total rainfall at The Peak, for example `2026-08-31  10.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--the-peak-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No The Peak rainfall is available.`

`hk-weather --pak-tam-chung-rain` prints the latest daily total rainfall at Pak Tam Chung (Tsak Yue Wu), for example `2026-08-31  4 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--pak-tam-chung-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Pak Tam Chung (Tsak Yue Wu) rainfall is available.`

`hk-weather --ching-pak-house-rain` prints the latest daily total rainfall at Ching Pak House(Tsing Yi), for example `2026-08-31  50.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--ching-pak-house-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ching Pak House(Tsing Yi) rainfall is available.`

`hk-weather --kau-sai-chau-rain` prints the latest daily total rainfall at Kau Sai Chau, for example `2026-08-31  1.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--kau-sai-chau-rain --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `滘西洲` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Kau Sai Chau rainfall is available.`

`hk-weather --kai-tak-rain` prints the latest daily total rainfall at Kai Tak, for example `2026-08-31  28 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--kai-tak-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Kai Tak rainfall is available.`

`hk-weather --sha-tau-kok-rain` prints the latest daily total rainfall at Sha Tau Kok, for example `2026-08-31  13.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--sha-tau-kok-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tau Kok rainfall is available.`

`hk-weather --beas-river-rain` prints the latest daily total rainfall at Beas River, for example `2026-08-31  24.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--beas-river-rain --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Beas River rainfall is available.`

`hk-weather --kat-o-rain` prints the latest daily total rainfall at Kat O, for example `2026-08-31  16 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--kat-o-rain --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `吉澳` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Kat O rainfall is available.`

`hk-weather --tap-shek-kok-rain` prints the latest daily total rainfall at Tap Shek Kok, for example `2026-08-31  22.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--tap-shek-kok-rain --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `踏石角` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Tap Shek Kok rainfall is available.`

`hk-weather --tsim-bei-tsui-rain` prints the latest daily total rainfall at Tsim Bei Tsui, for example `2026-08-31  49 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--tsim-bei-tsui-rain --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `尖鼻咀` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Tsim Bei Tsui rainfall is available.`

`hk-weather --tai-mei-tuk-pump-rain` prints the latest daily total rainfall at Tai Mei Tuk Pumping Station, for example `2026-08-31  16.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--tai-mei-tuk-rain` still prints Tai Mei Tuk. A total of zero is kept. `--tai-mei-tuk-pump-rain --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `大美督抽水站` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Tai Mei Tuk Pumping Station rainfall is available.`

`hk-weather --ngong-ping-reservoir-rain` prints the latest daily total rainfall at Ngong Ping Fresh Water Reservoir, for example `2026-08-31  3.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--ngong-ping-wind` still prints Ngong Ping. A total of zero is kept. `--ngong-ping-reservoir-rain --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `昂坪食水配水庫` and simplified text uses `昂坪食水配水库`. Days marked `***` are omitted. If none remain, it says `No Ngong Ping Fresh Water Reservoir rainfall is available.`

`hk-weather --discovery-bay-rain` prints the latest daily total rainfall at Discovery Bay, for example `2026-08-31  7 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--discovery-bay-rain --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `愉景灣` and simplified text uses `愉景湾`. Days marked `***` are omitted. If none remain, it says `No Discovery Bay rainfall is available.`

`hk-weather --adventist-college-rain` prints the latest daily total rainfall at Hong Kong Adventist College(Sai Kung), for example `2026-08-31  11.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--sai-kung-temp` still prints Sai Kung. A total of zero is kept. `--adventist-college-rain --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `西貢(香港三育書院)` and simplified text uses `西贡(香港三育书院)`. Days marked `***` are omitted. If none remain, it says `No Hong Kong Adventist College(Sai Kung) rainfall is available.`

`hk-weather --wong-shiu-chi-rain` prints the latest daily total rainfall at Tai Po Wong Shiu Chi Secondary School, for example `2026-08-31  12.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--tai-po-kau-wind` still prints Tai Po Kau. A total of zero is kept. `--wong-shiu-chi-rain --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `大埔王肇枝中學` and simplified text uses `大埔王肇枝中学`. Days marked `***` are omitted. If none remain, it says `No Tai Po Wong Shiu Chi Secondary School rainfall is available.`

`hk-weather --au-tau-rain` prints the latest daily total rainfall at Au Tau, for example `2026-08-31  29.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--au-tau-rain --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `凹頭` and simplified text uses `凹头`. Days marked `***` are omitted. If none remain, it says `No Au Tau rainfall is available.`

`hk-weather --lok-ma-chau-rain` prints the latest daily total rainfall at Lok Ma Chau, for example `2026-08-31  38.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--lok-ma-chau-rain --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `落馬洲` and simplified text uses `落马洲`. Days marked `***` are omitted. If none remain, it says `No Lok Ma Chau rainfall is available.`

`hk-weather --lamma-island-rain` prints the latest daily total rainfall at Lamma Island, for example `2026-08-31  18 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. A total of zero is kept. `--lamma-island-rain --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `南丫島` and simplified text uses `南丫岛`. Days marked `***` are omitted. If none remain, it says `No Lamma Island rainfall is available.`

`hk-weather --tuen-mun-home-rain` prints the latest daily total rainfall at Tuen Mun Children and Juvenile Home, for example `2026-08-31  27.5 mm`. `--daily-rain` still prints the Observatory total, and the other station rainfall flags still print their own stations. `--tuen-mun-home-temp` still prints the home's mean temperature, `--tuen-mun-home-max` still prints its maximum, `--tuen-mun-home-min` still prints its minimum, `--tuen-mun-home-dew` still prints its dew point, and `--tuen-mun-home-humidity` still prints its humidity. A total of zero is kept. `--tuen-mun-home-rain --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `屯門兒童及青少年院` and simplified text uses `屯门儿童及青少年院`. Days marked `***` are omitted. If none remain, it says `No Tuen Mun Children and Juvenile Home rainfall is available.`

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

`hk-weather --lau-fau-humidity` prints the latest daily mean relative humidity at Lau Fau Shan, for example `2026-08-31  95%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, and `--shek-kong-humidity` still prints Shek Kong. `--lau-fau-rain` still prints Lau Fau Shan's rainfall, and `--lau-fau-wind` still prints its wind speed. `--lau-fau-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Lau Fau Shan humidity is available.`

`hk-weather --park-humidity` prints the latest daily mean relative humidity at King's Park, for example `2026-08-31  84%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, `--shek-kong-humidity` still prints Shek Kong, and `--lau-fau-humidity` still prints Lau Fau Shan. `--park-dew`, `--park-pressure`, `--park-wet`, and `--park-rain` still print King's Park's other daily readings. `--park-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park humidity is available.`

`hk-weather --sai-kung-humidity` prints the latest daily mean relative humidity at Sai Kung, for example `2026-08-31  86%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, `--shek-kong-humidity` still prints Shek Kong, `--lau-fau-humidity` still prints Lau Fau Shan, and `--park-humidity` still prints King's Park. `--sai-kung-temp`, `--sai-kung-min`, and `--sai-kung-dew` still print Sai Kung's other daily readings. `--sai-kung-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sai Kung humidity is available.`

`hk-weather --cheung-chau-humidity` prints the latest daily mean relative humidity at Cheung Chau, for example `2026-08-31  92%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, `--shek-kong-humidity` still prints Shek Kong, `--lau-fau-humidity` still prints Lau Fau Shan, `--park-humidity` still prints King's Park, and `--sai-kung-humidity` still prints Sai Kung. `--cheung-chau-max` still prints Cheung Chau's maximum temperature, `--cheung-wind` still prints its wind speed, `--cheung-prevailing` still prints its prevailing direction, and `--cheung-dew` still prints its dew point. `--cheung-chau-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau humidity is available.`

`hk-weather --sha-tin-humidity` prints the latest daily mean relative humidity at Sha Tin, for example `2026-08-31  88%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, `--shek-kong-humidity` still prints Shek Kong, `--lau-fau-humidity` still prints Lau Fau Shan, `--park-humidity` still prints King's Park, `--sai-kung-humidity` still prints Sai Kung, and `--cheung-chau-humidity` still prints Cheung Chau. `--sha-tin-pressure` still prints Sha Tin's pressure, `--sha-tin-dew` still prints its dew point, and `--sha-tin-rain` still prints its rainfall. `--sha-tin-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin humidity is available.`

`hk-weather --sheung-shui-humidity` prints the latest daily mean relative humidity at Sheung Shui, for example `2026-08-31  88%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, `--shek-kong-humidity` still prints Shek Kong, `--lau-fau-humidity` still prints Lau Fau Shan, `--park-humidity` still prints King's Park, `--sai-kung-humidity` still prints Sai Kung, `--cheung-chau-humidity` still prints Cheung Chau, and `--sha-tin-humidity` still prints Sha Tin. `--sheung-shui-max` still prints Sheung Shui's maximum temperature, `--sheung-shui-pressure` still prints its pressure, and `--sheung-shui-rain` still prints its rainfall. `--sheung-shui-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sheung Shui humidity is available.`

`hk-weather --wong-chuk-hang-humidity` prints the latest daily mean relative humidity at Wong Chuk Hang, for example `2026-08-31  90%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, `--shek-kong-humidity` still prints Shek Kong, `--lau-fau-humidity` still prints Lau Fau Shan, `--park-humidity` still prints King's Park, `--sai-kung-humidity` still prints Sai Kung, `--cheung-chau-humidity` still prints Cheung Chau, `--sha-tin-humidity` still prints Sha Tin, and `--sheung-shui-humidity` still prints Sheung Shui. `--wong-chuk-hang-min` still prints Wong Chuk Hang's minimum temperature, and `--wong-chuk-hang-dew` still prints its dew point. `--wong-chuk-hang-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wong Chuk Hang humidity is available.`

`hk-weather --tseung-kwan-o-humidity` prints the latest daily mean relative humidity at Tseung Kwan O, for example `2026-08-31  94%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, `--shek-kong-humidity` still prints Shek Kong, `--lau-fau-humidity` still prints Lau Fau Shan, `--park-humidity` still prints King's Park, `--sai-kung-humidity` still prints Sai Kung, `--cheung-chau-humidity` still prints Cheung Chau, `--sha-tin-humidity` still prints Sha Tin, `--sheung-shui-humidity` still prints Sheung Shui, and `--wong-chuk-hang-humidity` still prints Wong Chuk Hang. `--tseung-kwan-o-max` still prints Tseung Kwan O's maximum, `--tseung-kwan-o-min` still prints its minimum, `--tseung-kwan-o-temp` still prints its mean temperature, `--tseung-kwan-o-dew` still prints its dew point, and `--tseung-kwan-o-rain` still prints its rainfall. `--tseung-kwan-o-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tseung Kwan O humidity is available.`

`hk-weather --peng-chau-humidity` prints the latest daily mean relative humidity at Peng Chau, for example `2026-08-31  84%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, `--shek-kong-humidity` still prints Shek Kong, `--lau-fau-humidity` still prints Lau Fau Shan, `--park-humidity` still prints King's Park, `--sai-kung-humidity` still prints Sai Kung, `--cheung-chau-humidity` still prints Cheung Chau, `--sha-tin-humidity` still prints Sha Tin, `--sheung-shui-humidity` still prints Sheung Shui, `--wong-chuk-hang-humidity` still prints Wong Chuk Hang, and `--tseung-kwan-o-humidity` still prints Tseung Kwan O. `--peng-chau-temp` still prints Peng Chau's mean temperature, `--peng-chau-wind` still prints its wind speed, and `--peng-chau-rain` still prints its rainfall. `--peng-chau-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Peng Chau humidity is available.`

`hk-weather --sha-lo-wan-humidity` prints the latest daily mean relative humidity at Sha Lo Wan, for example `2026-08-31  94%`. `--mean-humidity` still prints the Observatory reading, `--tai-mo-humidity` still prints Tai Mo Shan, `--waglan-humidity` still prints Waglan Island, `--tate-humidity` still prints Tate's Cairn, `--ta-kwu-ling-humidity` still prints Ta Kwu Ling, `--wetland-humidity` still prints Wetland Park, `--shek-kong-humidity` still prints Shek Kong, `--lau-fau-humidity` still prints Lau Fau Shan, `--park-humidity` still prints King's Park, `--sai-kung-humidity` still prints Sai Kung, `--cheung-chau-humidity` still prints Cheung Chau, `--sha-tin-humidity` still prints Sha Tin, `--sheung-shui-humidity` still prints Sheung Shui, `--wong-chuk-hang-humidity` still prints Wong Chuk Hang, `--tseung-kwan-o-humidity` still prints Tseung Kwan O, and `--peng-chau-humidity` still prints Peng Chau. `--sha-lo-wan-temp` still prints Sha Lo Wan's mean temperature, and `--sha-lo-wan-wet` still prints its wet-bulb temperature. `--sha-lo-wan-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Lo Wan humidity is available.`

`hk-weather --airport-humidity` prints the latest daily mean relative humidity at Hong Kong International Airport, for example `2026-07-31  86%`. The published airport series currently ends in July. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--airport-temp` still prints the airport mean temperature, and `--airport-wet` still prints its wet-bulb temperature. `--airport-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No airport humidity is available.`

`hk-weather --tsuen-wan-humidity` prints the latest daily mean relative humidity at Tsuen Wan, for example `2026-08-31  93%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--tsuen-wan-temp` still prints Tsuen Wan's mean temperature, `--tsuen-wan-max` still prints its maximum, `--tsuen-wan-min` still prints its minimum, `--tsuen-wan-rain` still prints its rainfall, and `--tsuen-wan-dew` still prints its dew point. `--tsuen-wan-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan humidity is available.`

`hk-weather --hong-kong-park-humidity` prints the latest daily mean relative humidity at Hong Kong Park, for example `2026-08-31  89%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--hong-kong-park-temp` still prints Hong Kong Park's mean temperature, `--hong-kong-park-max` still prints its maximum, `--hong-kong-park-min` still prints its minimum, and `--hong-kong-park-dew` still prints its dew point. `--hong-kong-park-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Hong Kong Park humidity is available.`

`hk-weather --clear-water-bay-humidity` prints the latest daily mean relative humidity at Clear Water Bay, for example `2026-08-31  89%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--clear-water-bay-temp` still prints Clear Water Bay's mean temperature, `--clear-water-bay-max` still prints its maximum, `--clear-water-bay-min` still prints its minimum, `--clear-water-bay-rain` still prints its rainfall, and `--clear-water-bay-dew` still prints its dew point. `--clear-water-bay-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Clear Water Bay humidity is available.`

`hk-weather --shau-kei-wan-humidity` prints the latest daily mean relative humidity at Shau Kei Wan, for example `2026-08-31  90%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--shau-kei-wan-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shau Kei Wan humidity is available.`

`hk-weather --kau-sai-chau-humidity` prints the latest daily mean relative humidity at Kau Sai Chau, for example `2026-08-31  89%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--kau-sai-chau-dew` still prints Kau Sai Chau's dew point, and `--kau-sai-chau-rain` still prints its rainfall. `--kau-sai-chau-humidity --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `滘西洲` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Kau Sai Chau humidity is available.`

`hk-weather --pak-tam-chung-humidity` prints the latest daily mean relative humidity at Pak Tam Chung (Tsak Yue Wu), for example `2026-08-31  93%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--pak-tam-chung-dew` still prints Pak Tam Chung's dew point, and `--pak-tam-chung-rain` still prints its rainfall. `--pak-tam-chung-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `北潭涌(鯽魚湖)` and simplified text uses `北潭涌(鲫鱼湖)`. Days marked `***` are omitted. If none remain, it says `No Pak Tam Chung (Tsak Yue Wu) humidity is available.`

`hk-weather --beas-river-humidity` prints the latest daily mean relative humidity at Beas River, for example `2026-08-31  93%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--beas-river-dew` still prints Beas River's dew point, and `--beas-river-rain` still prints its rainfall. `--beas-river-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `上水雙魚河` and simplified text uses `上水双鱼河`. Days marked `***` are omitted. If none remain, it says `No Beas River humidity is available.`

`hk-weather --runway-park-humidity` prints the latest daily mean relative humidity at Kai Tak Runway Park, for example `2026-08-31  85%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--runway-park-temp` still prints Kai Tak Runway Park's mean temperature, and `--runway-park-dew` still prints its dew point. `--runway-park-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `啟德跑道公園` and simplified text uses `启德跑道公园`. Days marked `***` are omitted. If none remain, it says `No Kai Tak Runway Park humidity is available.`

`hk-weather --kowloon-city-humidity` prints the latest daily mean relative humidity at Kowloon City, for example `2026-08-31  87%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--kowloon-city-dew` still prints Kowloon City's dew point, `--kowloon-city-temp` still prints its mean temperature, `--kowloon-city-max` still prints its maximum, and `--kowloon-city-min` still prints its minimum. `--kowloon-city-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `九龍城` and simplified text uses `九龙城`. Days marked `***` are omitted. If none remain, it says `No Kowloon City humidity is available.`

`hk-weather --nei-lak-shan-humidity` prints the latest daily mean relative humidity at Nei Lak Shan, for example `2026-08-31  96%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--nei-lak-shan-temp` still prints Nei Lak Shan's mean temperature, and `--nei-lak-shan-dew` still prints its dew point. `--nei-lak-shan-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `彌勒山` and simplified text uses `弥勒山`. Days marked `***` are omitted. If none remain, it says `No Nei Lak Shan humidity is available.`

`hk-weather --new-tsing-yi-humidity` prints the latest daily mean relative humidity at New Tsing Yi Station, for example `2026-08-31  90%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--new-tsing-yi-temp` still prints New Tsing Yi Station's mean temperature, `--new-tsing-yi-max` still prints its maximum, `--new-tsing-yi-min` still prints its minimum, and `--new-tsing-yi-dew` still prints its dew point. `--new-tsing-yi-humidity --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `新青衣站` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No New Tsing Yi Station humidity is available.`

`hk-weather --shing-mun-valley-humidity` prints the latest daily mean relative humidity at Tsuen Wan Shing Mun Valley, for example `2026-08-31  89%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--shing-mun-valley-temp` still prints the valley's mean temperature, `--shing-mun-valley-max` still prints its maximum, `--shing-mun-valley-min` still prints its minimum, `--shing-mun-valley-dew` still prints its dew point, and `--tsuen-wan-humidity` still prints Tsuen Wan. `--shing-mun-valley-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `荃灣城門谷` and simplified text uses `荃湾城门谷`. Days marked `***` are omitted. If none remain, it says `No Tsuen Wan Shing Mun Valley humidity is available.`

`hk-weather --tuen-mun-home-humidity` prints the latest daily mean relative humidity at Tuen Mun Children and Juvenile Home, for example `2026-08-31  91%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--tuen-mun-home-temp` still prints the home's mean temperature, `--tuen-mun-home-max` still prints its maximum, `--tuen-mun-home-min` still prints its minimum, and `--tuen-mun-home-dew` still prints its dew point. `--tuen-mun-home-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `屯門兒童及青少年院` and simplified text uses `屯门儿童及青少年院`. Days marked `***` are omitted. If none remain, it says `No Tuen Mun Children and Juvenile Home humidity is available.`

`hk-weather --buoy-2-humidity` prints the latest daily mean relative humidity at Automatic Weather Buoy No.2 (Hong Kong International Airport, West), for example `2026-08-31  85%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--buoy-2-temp` still prints the buoy's mean temperature, `--buoy-2-max` still prints its maximum, `--buoy-2-min` still prints its minimum, and `--buoy-2-dew` still prints its dew point. `--buoy-2-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標2號 (香港國際機場西面)` and simplified text uses `自动气象浮标2号 (香港国际机场西面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.2 (Hong Kong International Airport, West) humidity is available.`

`hk-weather --buoy-8-humidity` prints the latest daily mean relative humidity at Automatic Weather Buoy No.8 (Hong Kong International Airport, East), for example `2026-08-31  83%`. `--mean-humidity` still prints the Observatory reading, and the other station humidity flags still print their own stations. `--buoy-8-temp` still prints the buoy's mean temperature, `--buoy-8-dew` still prints its dew point, and `--buoy-2-humidity` still prints Automatic Weather Buoy No.2. `--buoy-8-humidity --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `自動氣象浮標8號 (香港國際機場東面)` and simplified text uses `自动气象浮标8号 (香港国际机场东面)`. Days marked `***` are omitted. If none remain, it says `No Automatic Weather Buoy No.8 (Hong Kong International Airport, East) humidity is available.`

`hk-weather --temps` prints temperature by place from the current report, with the record time when the Observatory includes it. `--temps --json` prints that list as one JSON object. If no readings are present, it says so.

`hk-weather --temp-time` prints when those temperatures were recorded (`temperature.recordTime`). `--temps` still prints the readings. `--current-updated` still prints when the whole report was updated. `--temp-time --json` prints that timestamp as one JSON object. `--lang` applies. If the field is missing or blank, it says `No temperature time is available.`

`hk-weather --minute-temp` prints the latest 1-minute mean air temperature at automatic stations, for example `Chek Lap Kok  27.9°C`. `--temps` still prints temperatures from the current weather report. `--minute-temp --json` prints those stations as one JSON object. `--lang` selects the English, Traditional Chinese, or Simplified Chinese station names. Stations marked `N/A` are omitted. If none remain, it says `No 1-minute temperatures are available.`

`hk-weather --since-midnight` prints each automatic station's maximum and minimum air temperature since midnight, for example `Chek Lap Kok  high 28.2°C  low 27.8°C`. `--minute-temp` still prints the latest 1-minute temperature. `--max-temp` and `--min-temp` still print the Observatory daily climate series. `--since-midnight --json` prints those stations as one JSON object. `--lang` selects the station names. A station is omitted when both readings are missing. If none remain, it says `No temperatures since midnight are available.`

`hk-weather --pressure` prints the latest 1-minute mean sea level pressure at automatic stations, for example `Chek Lap Kok  1011.9 hPa`. `--pressure --json` prints those stations as one JSON object. `--lang` selects the English, Traditional Chinese, or Simplified Chinese station names. Stations marked `N/A` are omitted. If none remain, it says `No sea level pressure is available.`

`hk-weather --mean-pressure` prints the latest daily mean pressure at the Observatory, for example `2026-08-31  998.7 hPa`. `--pressure` still prints the latest 1-minute station readings. `--mean-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No daily mean pressure is available.`

`hk-weather --park-pressure` prints the latest daily mean pressure at King's Park, for example `2026-08-31  998.5 hPa`. `--mean-pressure` still prints the Observatory reading, and `--pressure` still prints the latest 1-minute station readings. `--park-dew` still prints King's Park's dew point. `--park-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No King's Park pressure is available.`

`hk-weather --sha-tin-pressure` prints the latest daily mean pressure at Sha Tin, for example `2026-08-31  999.1 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, and `--pressure` still prints the latest 1-minute station readings. `--sha-tin-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Tin pressure is available.`

`hk-weather --sheung-shui-pressure` prints the latest daily mean pressure at Sheung Shui, for example `2026-08-31  998.3 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, and `--sheung-shui-max` still prints Sheung Shui's daily maximum. `--sheung-shui-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sheung Shui pressure is available.`

`hk-weather --waglan-pressure` prints the latest daily mean pressure at Waglan Island, for example `2026-08-31  998.8 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, and `--sheung-shui-pressure` still prints Sheung Shui. `--waglan-max` still prints Waglan Island's daily maximum, `--waglan-humidity` still prints its humidity, and `--mean-wind` still prints its wind speed. `--waglan-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Waglan Island pressure is available.`

`hk-weather --cheung-chau-pressure` prints the latest daily mean pressure at Cheung Chau, for example `2026-08-31  998.8 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, `--sheung-shui-pressure` still prints Sheung Shui, and `--waglan-pressure` still prints Waglan Island. `--cheung-chau-max` still prints Cheung Chau's maximum temperature, `--cheung-chau-min` still prints its minimum, `--cheung-chau-humidity` still prints its humidity, `--cheung-wind` still prints its wind speed, `--cheung-prevailing` still prints its prevailing direction, `--cheung-dew` still prints its dew point, and `--cheung-chau-rain` still prints its rainfall. `--cheung-chau-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Cheung Chau pressure is available.`

`hk-weather --lau-fau-pressure` prints the latest daily mean pressure at Lau Fau Shan, for example `2026-08-31  998.7 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, `--sheung-shui-pressure` still prints Sheung Shui, `--waglan-pressure` still prints Waglan Island, and `--cheung-chau-pressure` still prints Cheung Chau. `--lau-fau-max` still prints Lau Fau Shan's maximum, `--lau-fau-min` still prints its minimum, `--lau-fau-rain` still prints its rainfall, `--lau-fau-wind` still prints its wind speed, and `--lau-fau-humidity` still prints its humidity. `--lau-fau-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Lau Fau Shan pressure is available.`

`hk-weather --tate-pressure` prints the latest daily mean pressure at Tate's Cairn, for example `2026-08-31  999.7 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, `--sheung-shui-pressure` still prints Sheung Shui, `--waglan-pressure` still prints Waglan Island, `--cheung-chau-pressure` still prints Cheung Chau, and `--lau-fau-pressure` still prints Lau Fau Shan. `--tate-max` still prints Tate's Cairn's maximum, `--tate-min` still prints its minimum, `--tate-temp` still prints its daily mean, `--tate-humidity` still prints its humidity, and `--tate-rain` still prints its rainfall. `--tate-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tate's Cairn pressure is available.`

`hk-weather --wetland-pressure` prints the latest daily mean pressure at Wetland Park, for example `2026-08-31  998.6 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, `--sheung-shui-pressure` still prints Sheung Shui, `--waglan-pressure` still prints Waglan Island, `--cheung-chau-pressure` still prints Cheung Chau, `--lau-fau-pressure` still prints Lau Fau Shan, and `--tate-pressure` still prints Tate's Cairn. `--wetland-rain` still prints Wetland Park's rainfall, `--wetland-humidity` still prints its humidity, and `--wetland-dew` still prints its dew point. `--wetland-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Wetland Park pressure is available.`

`hk-weather --peng-chau-pressure` prints the latest daily mean pressure at Peng Chau, for example `2026-08-31  998.7 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, `--sheung-shui-pressure` still prints Sheung Shui, `--waglan-pressure` still prints Waglan Island, `--cheung-chau-pressure` still prints Cheung Chau, `--lau-fau-pressure` still prints Lau Fau Shan, `--tate-pressure` still prints Tate's Cairn, and `--wetland-pressure` still prints Wetland Park. `--peng-chau-humidity` still prints Peng Chau's humidity, `--peng-chau-temp` still prints its mean temperature, `--peng-chau-wind` still prints its wind speed, and `--peng-chau-rain` still prints its rainfall. `--peng-chau-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Peng Chau pressure is available.`

`hk-weather --tai-mo-pressure` prints the latest daily mean pressure at Tai Mo Shan, for example `2026-08-31  1000.4 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, `--sheung-shui-pressure` still prints Sheung Shui, `--waglan-pressure` still prints Waglan Island, `--cheung-chau-pressure` still prints Cheung Chau, `--lau-fau-pressure` still prints Lau Fau Shan, `--tate-pressure` still prints Tate's Cairn, `--wetland-pressure` still prints Wetland Park, and `--peng-chau-pressure` still prints Peng Chau. `--tai-mo-temp` still prints Tai Mo Shan's mean temperature, `--tai-mo-min` still prints its minimum, `--tai-mo-max` still prints its maximum, `--tai-mo-humidity` still prints its humidity, `--tai-mo-dew` still prints its dew point, and `--tai-mo-rain` still prints its rainfall. `--tai-mo-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Tai Mo Shan pressure is available.`

`hk-weather --sha-lo-wan-pressure` prints the latest daily mean pressure at Sha Lo Wan, for example `2026-08-31  999.2 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, `--sheung-shui-pressure` still prints Sheung Shui, `--waglan-pressure` still prints Waglan Island, `--cheung-chau-pressure` still prints Cheung Chau, `--lau-fau-pressure` still prints Lau Fau Shan, `--tate-pressure` still prints Tate's Cairn, `--wetland-pressure` still prints Wetland Park, `--peng-chau-pressure` still prints Peng Chau, and `--tai-mo-pressure` still prints Tai Mo Shan. `--sha-lo-wan-temp` still prints Sha Lo Wan's mean temperature, `--sha-lo-wan-min` still prints its minimum, `--sha-lo-wan-max` still prints its maximum, `--sha-lo-wan-humidity` still prints its humidity, `--sha-lo-wan-dew` still prints its dew point, `--sha-lo-wan-wind` still prints its wind speed, and `--sha-lo-wan-prevailing` still prints its prevailing wind. `--sha-lo-wan-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Sha Lo Wan pressure is available.`

`hk-weather --shek-kong-pressure` prints the latest daily mean pressure at Shek Kong, for example `2026-08-31  998.7 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, `--sheung-shui-pressure` still prints Sheung Shui, `--waglan-pressure` still prints Waglan Island, `--cheung-chau-pressure` still prints Cheung Chau, `--lau-fau-pressure` still prints Lau Fau Shan, `--tate-pressure` still prints Tate's Cairn, `--wetland-pressure` still prints Wetland Park, `--peng-chau-pressure` still prints Peng Chau, `--tai-mo-pressure` still prints Tai Mo Shan, and `--sha-lo-wan-pressure` still prints Sha Lo Wan. `--shek-kong-temp` still prints Shek Kong's mean temperature, `--shek-kong-min` still prints its minimum, `--shek-kong-max` still prints its maximum, `--shek-kong-humidity` still prints its humidity, `--shek-kong-dew` still prints its dew point, `--shek-kong-rain` still prints its rainfall, and `--shek-kong-wind` still prints its wind speed. `--shek-kong-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Shek Kong pressure is available.`

`hk-weather --ta-kwu-ling-pressure` prints the latest daily mean pressure at Ta Kwu Ling, for example `2026-08-31  998.7 hPa`. `--mean-pressure` still prints the Observatory reading, `--park-pressure` still prints King's Park, `--sha-tin-pressure` still prints Sha Tin, `--sheung-shui-pressure` still prints Sheung Shui, `--waglan-pressure` still prints Waglan Island, `--cheung-chau-pressure` still prints Cheung Chau, `--lau-fau-pressure` still prints Lau Fau Shan, `--tate-pressure` still prints Tate's Cairn, `--wetland-pressure` still prints Wetland Park, `--peng-chau-pressure` still prints Peng Chau, `--tai-mo-pressure` still prints Tai Mo Shan, `--sha-lo-wan-pressure` still prints Sha Lo Wan, and `--shek-kong-pressure` still prints Shek Kong. `--ta-kwu-ling-temp` still prints Ta Kwu Ling's mean temperature, `--ta-kwu-ling-min` still prints its minimum, `--ta-kwu-ling-max` still prints its maximum, `--ta-kwu-ling-humidity` still prints its humidity, `--ta-kwu-ling-dew` still prints its dew point, `--ta-kwu-ling-rain` still prints its rainfall, and `--ta-kwu-ling-wind` still prints its wind speed. `--ta-kwu-ling-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No Ta Kwu Ling pressure is available.`

`hk-weather --airport-pressure` prints the latest daily mean pressure at Hong Kong International Airport, for example `2026-07-31  1009.4 hPa`. The published airport series currently ends in July. `--mean-pressure` still prints the Observatory reading, and the other station pressure flags still print their own stations. `--airport-temp` still prints the airport mean temperature, `--airport-max` still prints its maximum, `--airport-min` still prints its minimum, `--airport-humidity` still prints its humidity, `--airport-rain` still prints its rainfall, and `--airport-wet` still prints its wet-bulb temperature. `--airport-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Days marked `***` are omitted. If none remain, it says `No airport pressure is available.`

`hk-weather --nei-lak-shan-pressure` prints the latest daily mean pressure at Nei Lak Shan, for example `2026-08-31  1000.5 hPa`. `--mean-pressure` still prints the Observatory reading, and the other station pressure flags still print their own stations. `--nei-lak-shan-temp` still prints Nei Lak Shan's mean temperature, `--nei-lak-shan-dew` still prints its dew point, `--nei-lak-shan-humidity` still prints its humidity, `--nei-lak-shan-wind` still prints its wind speed, and `--nei-lak-shan-prevailing` still prints its prevailing wind. `--nei-lak-shan-pressure --json` prints that day as one JSON object. `--lang` selects the station name. Traditional text uses `彌勒山` and simplified text uses `弥勒山`. Days marked `***` are omitted. If none remain, it says `No Nei Lak Shan pressure is available.`

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

`hk-weather --kau-sai-chau-solar` prints the latest daily global solar radiation at Kau Sai Chau, for example `2026-08-31  11.13 MJ/m²`. `--global-solar` still prints the King's Park reading, and `--solar` still prints the latest 1-minute readings. `--kau-sai-chau-humidity` still prints Kau Sai Chau's humidity, and `--kau-sai-chau-rain` still prints its rainfall. `--kau-sai-chau-solar --json` prints that day as one JSON object. `--lang` selects the station name. The Chinese name is `滘西洲` in both traditional and simplified text. Days marked `***` are omitted. If none remain, it says `No Kau Sai Chau global solar radiation is available.`

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
