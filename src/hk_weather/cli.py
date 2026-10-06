"""Command-line entrypoint for current Hong Kong weather."""

from __future__ import annotations

import argparse
import sys

from hk_weather.hko import (
    WeatherError,
    fetch_aqhi,
    fetch_current,
    fetch_driest,
    fetch_nowcast,
    fetch_daily_rain,
    fetch_lau_fau_rain,
    fetch_shek_kong_rain,
    fetch_wetland_rain,
    fetch_sham_shui_po_rain,
    fetch_park_rain,
    fetch_tseung_kwan_o_rain,
    fetch_sheung_shui_rain,
    fetch_sha_tin_rain,
    fetch_ta_kwu_ling_rain,
    fetch_cheung_chau_rain,
    fetch_waglan_rain,
    fetch_tate_rain,
    fetch_peng_chau_rain,
    fetch_ping_chau_rain,
    fetch_tai_mo_rain,
    fetch_sha_lo_wan_rain,
    fetch_airport_rain,
    fetch_green_island_rain,
    fetch_tsuen_wan_rain,
    fetch_tap_mun_rain,
    fetch_clear_water_bay_rain,
    fetch_shau_kei_wan_rain,
    fetch_happy_valley_rain,
    fetch_tai_mei_tuk_rain,
    fetch_kadoorie_farm_rain,
    fetch_the_peak_rain,
    fetch_pak_tam_chung_rain,
    fetch_ching_pak_house_rain,
    fetch_kau_sai_chau_rain,
    fetch_kai_tak_rain,
    fetch_sha_tau_kok_rain,
    fetch_beas_river_rain,
    fetch_kat_o_rain,
    fetch_tap_shek_kok_rain,
    fetch_tsim_bei_tsui_rain,
    fetch_tai_mei_tuk_pump_rain,
    fetch_ngong_ping_reservoir_rain,
    fetch_discovery_bay_rain,
    fetch_adventist_college_rain,
    fetch_wong_shiu_chi_rain,
    fetch_au_tau_rain,
    fetch_lok_ma_chau_rain,
    fetch_lamma_island_rain,
    fetch_tuen_mun_home_rain,
    fetch_forecast,
    fetch_outlook,
    fetch_coastal,
    fetch_coast_report,
    fetch_forecast_period,
    fetch_forecast_desc,
    fetch_forecast_updated,
    fetch_forecast_day,
    fetch_hour_rain,
    fetch_hour_wettest,
    fetch_hour_driest,
    fetch_felt,
    fetch_fire_danger,
    fetch_grass,
    fetch_sunshine,
    fetch_daily_sun,
    fetch_max_uv,
    fetch_uv_peak,
    fetch_mean_uv,
    fetch_daily_uv,
    fetch_dose,
    fetch_hourly_dose,
    fetch_accum_rain,
    fetch_avg_rain,
    fetch_radiation,
    fetch_bulletin,
    fetch_radiation_note,
    fetch_radiation_weather,
    fetch_radiation_ground,
    fetch_radiation_provisional,
    fetch_coldest,
    fetch_cyclone,
    fetch_hottest,
    fetch_humidest,
    fetch_humidity,
    fetch_humidity_time,
    fetch_minute_humidity,
    fetch_mean_humidity,
    fetch_tai_mo_humidity,
    fetch_waglan_humidity,
    fetch_tate_humidity,
    fetch_ta_kwu_ling_humidity,
    fetch_wetland_humidity,
    fetch_shek_kong_humidity,
    fetch_lau_fau_humidity,
    fetch_park_humidity,
    fetch_sai_kung_humidity,
    fetch_cheung_chau_humidity,
    fetch_sha_tin_humidity,
    fetch_sheung_shui_humidity,
    fetch_wong_chuk_hang_humidity,
    fetch_tseung_kwan_o_humidity,
    fetch_peng_chau_humidity,
    fetch_sha_lo_wan_humidity,
    fetch_airport_humidity,
    fetch_tsuen_wan_humidity,
    fetch_hong_kong_park_humidity,
    fetch_clear_water_bay_humidity,
    fetch_shau_kei_wan_humidity,
    fetch_kau_sai_chau_humidity,
    fetch_pak_tam_chung_humidity,
    fetch_beas_river_humidity,
    fetch_runway_park_humidity,
    fetch_kowloon_city_humidity,
    fetch_nei_lak_shan_humidity,
    fetch_new_tsing_yi_humidity,
    fetch_shing_mun_valley_humidity,
    fetch_tuen_mun_home_humidity,
    fetch_buoy_2_humidity,
    fetch_icon_time,
    fetch_icon,
    fetch_current_updated,
    fetch_least_humid,
    fetch_lightning,
    fetch_lunar,
    fetch_moon,
    fetch_month_rain,
    fetch_nine_day,
    fetch_nine_situation,
    fetch_nine_updated,
    fetch_nine_weather,
    fetch_nine_temp,
    fetch_nine_humidity,
    fetch_sea_temp,
    fetch_north_point_am_sea,
    fetch_north_point_pm_sea,
    fetch_soil_temp,
    fetch_year_rain,
    fetch_noon_rain,
    fetch_overnight,
    fetch_psr,
    fetch_quakes,
    fetch_rain,
    fetch_rain_period,
    fetch_rain_maint,
    fetch_rainstorm,
    fetch_stations,
    fetch_strikes,
    fetch_daily_strikes,
    fetch_cloud_strikes,
    fetch_summary,
    fetch_situation,
    fetch_sunrise,
    fetch_wettest,
    fetch_temps,
    fetch_temp_time,
    fetch_minute_temp,
    fetch_since_midnight,
    fetch_pressure,
    fetch_mean_pressure,
    fetch_park_pressure,
    fetch_sha_tin_pressure,
    fetch_sheung_shui_pressure,
    fetch_waglan_pressure,
    fetch_cheung_chau_pressure,
    fetch_lau_fau_pressure,
    fetch_tate_pressure,
    fetch_wetland_pressure,
    fetch_peng_chau_pressure,
    fetch_tai_mo_pressure,
    fetch_sha_lo_wan_pressure,
    fetch_shek_kong_pressure,
    fetch_ta_kwu_ling_pressure,
    fetch_airport_pressure,
    fetch_nei_lak_shan_pressure,
    fetch_minute_grass,
    fetch_daily_grass,
    fetch_obs_grass,
    fetch_temp_diff,
    fetch_heat_index,
    fetch_daily_heat,
    fetch_mean_heat,
    fetch_wbgt,
    fetch_wet_bulb,
    fetch_airport_wet,
    fetch_park_wet,
    fetch_sha_lo_wan_wet,
    fetch_solar,
    fetch_global_solar,
    fetch_kau_sai_chau_solar,
    fetch_tc_info,
    fetch_tide,
    fetch_tide_hour,
    fetch_tide_latest,
    fetch_tips,
    fetch_lamppost,
    fetch_today,
    fetch_tomorrow,
    fetch_uv,
    fetch_fifteen_uv,
    fetch_visibility,
    fetch_reduced_vis,
    fetch_warning_info,
    fetch_warnings,
    fetch_warning_time,
    fetch_weekend,
    fetch_wind,
    fetch_gust,
    fetch_prevailing,
    fetch_cheung_prevailing,
    fetch_ping_chau_prevailing,
    fetch_tai_mo_to_prevailing,
    fetch_tai_po_kau_prevailing,
    fetch_park_prevailing,
    fetch_lau_fau_prevailing,
    fetch_sha_lo_wan_prevailing,
    fetch_wong_chuk_hang_prevailing,
    fetch_sai_kung_prevailing,
    fetch_tseung_kwan_o_prevailing,
    fetch_shek_kong_prevailing,
    fetch_sha_tin_prevailing,
    fetch_ta_kwu_ling_prevailing,
    fetch_wetland_prevailing,
    fetch_tai_mo_prevailing,
    fetch_airport_prevailing,
    fetch_kai_tak_prevailing,
    fetch_green_island_prevailing,
    fetch_ngong_ping_prevailing,
    fetch_tai_mei_tuk_prevailing,
    fetch_central_pier_prevailing,
    fetch_nei_lak_shan_prevailing,
    fetch_buoy_2_prevailing,
    fetch_mean_wind,
    fetch_cheung_wind,
    fetch_lau_fau_wind,
    fetch_peng_chau_wind,
    fetch_tai_po_kau_wind,
    fetch_tai_mo_to_wind,
    fetch_tai_mo_wind,
    fetch_tate_wind,
    fetch_shek_kong_wind,
    fetch_sai_kung_wind,
    fetch_sha_tin_wind,
    fetch_wong_chuk_hang_wind,
    fetch_park_wind,
    fetch_wetland_wind,
    fetch_tseung_kwan_o_wind,
    fetch_ta_kwu_ling_wind,
    fetch_sha_lo_wan_wind,
    fetch_ping_chau_wind,
    fetch_airport_wind,
    fetch_green_island_wind,
    fetch_ngong_ping_wind,
    fetch_tai_mei_tuk_wind,
    fetch_lamma_island_wind,
    fetch_kai_tak_wind,
    fetch_central_pier_wind,
    fetch_nei_lak_shan_wind,
    fetch_buoy_2_wind,
    fetch_forecast_icon,
    fetch_yesterday,
    fetch_mean_temp,
    fetch_tai_mo_temp,
    fetch_tate_temp,
    fetch_sai_kung_temp,
    fetch_sha_tin_temp,
    fetch_sheung_shui_temp,
    fetch_wong_chuk_hang_temp,
    fetch_lau_fau_temp,
    fetch_tseung_kwan_o_temp,
    fetch_sham_shui_po_temp,
    fetch_shek_kong_temp,
    fetch_wetland_temp,
    fetch_ta_kwu_ling_temp,
    fetch_peng_chau_temp,
    fetch_park_temp,
    fetch_cheung_chau_temp,
    fetch_waglan_temp,
    fetch_ping_chau_temp,
    fetch_sha_lo_wan_temp,
    fetch_airport_temp,
    fetch_clear_water_bay_temp,
    fetch_hong_kong_park_temp,
    fetch_ngong_ping_temp,
    fetch_kwun_tong_temp,
    fetch_wong_tai_sin_temp,
    fetch_tsuen_wan_temp,
    fetch_yuen_long_park_temp,
    fetch_tap_mun_temp,
    fetch_shau_kei_wan_temp,
    fetch_happy_valley_temp,
    fetch_tai_mei_tuk_temp,
    fetch_kau_sai_chau_temp,
    fetch_kadoorie_farm_temp,
    fetch_the_peak_temp,
    fetch_kat_o_temp,
    fetch_pak_tam_chung_temp,
    fetch_beas_river_temp,
    fetch_bluff_head_temp,
    fetch_runway_park_temp,
    fetch_kowloon_city_temp,
    fetch_nei_lak_shan_temp,
    fetch_new_tsing_yi_temp,
    fetch_stanley_temp,
    fetch_shing_mun_valley_temp,
    fetch_tuen_mun_home_temp,
    fetch_buoy_2_temp,
    fetch_buoy_8_temp,
    fetch_tai_mo_min,
    fetch_tate_min,
    fetch_sai_kung_min,
    fetch_wong_chuk_hang_min,
    fetch_waglan_min,
    fetch_sha_tin_min,
    fetch_cheung_chau_min,
    fetch_park_min,
    fetch_lau_fau_min,
    fetch_sheung_shui_min,
    fetch_tseung_kwan_o_min,
    fetch_sham_shui_po_min,
    fetch_shek_kong_min,
    fetch_wetland_min,
    fetch_ta_kwu_ling_min,
    fetch_sha_lo_wan_min,
    fetch_airport_min,
    fetch_yuen_long_park_min,
    fetch_clear_water_bay_min,
    fetch_tap_mun_min,
    fetch_hong_kong_park_min,
    fetch_ngong_ping_min,
    fetch_kwun_tong_min,
    fetch_wong_tai_sin_min,
    fetch_tsuen_wan_min,
    fetch_kau_sai_chau_min,
    fetch_kadoorie_farm_min,
    fetch_the_peak_min,
    fetch_kat_o_min,
    fetch_pak_tam_chung_min,
    fetch_beas_river_min,
    fetch_kowloon_city_min,
    fetch_new_tsing_yi_min,
    fetch_stanley_min,
    fetch_shing_mun_valley_min,
    fetch_tuen_mun_home_min,
    fetch_buoy_2_min,
    fetch_tai_mo_max,
    fetch_tseung_kwan_o_max,
    fetch_sheung_shui_max,
    fetch_waglan_max,
    fetch_shek_kong_max,
    fetch_cheung_chau_max,
    fetch_park_max,
    fetch_lau_fau_max,
    fetch_sai_kung_max,
    fetch_sha_tin_max,
    fetch_tate_max,
    fetch_wong_chuk_hang_max,
    fetch_sham_shui_po_max,
    fetch_wetland_max,
    fetch_ta_kwu_ling_max,
    fetch_sha_lo_wan_max,
    fetch_airport_max,
    fetch_yuen_long_park_max,
    fetch_clear_water_bay_max,
    fetch_tap_mun_max,
    fetch_hong_kong_park_max,
    fetch_ngong_ping_max,
    fetch_kwun_tong_max,
    fetch_wong_tai_sin_max,
    fetch_tsuen_wan_max,
    fetch_kau_sai_chau_max,
    fetch_kadoorie_farm_max,
    fetch_the_peak_max,
    fetch_kat_o_max,
    fetch_pak_tam_chung_max,
    fetch_beas_river_max,
    fetch_kowloon_city_max,
    fetch_new_tsing_yi_max,
    fetch_stanley_max,
    fetch_shing_mun_valley_max,
    fetch_tuen_mun_home_max,
    fetch_buoy_2_max,
    fetch_max_temp,
    fetch_min_temp,
    fetch_dew_point,
    fetch_park_dew,
    fetch_cheung_dew,
    fetch_wong_chuk_hang_dew,
    fetch_sai_kung_dew,
    fetch_sha_tin_dew,
    fetch_sheung_shui_dew,
    fetch_waglan_dew,
    fetch_lau_fau_dew,
    fetch_wetland_dew,
    fetch_ta_kwu_ling_dew,
    fetch_shek_kong_dew,
    fetch_tseung_kwan_o_dew,
    fetch_tai_mo_dew,
    fetch_peng_chau_dew,
    fetch_sha_lo_wan_dew,
    fetch_airport_dew,
    fetch_clear_water_bay_dew,
    fetch_hong_kong_park_dew,
    fetch_tsuen_wan_dew,
    fetch_shau_kei_wan_dew,
    fetch_kau_sai_chau_dew,
    fetch_pak_tam_chung_dew,
    fetch_beas_river_dew,
    fetch_runway_park_dew,
    fetch_kowloon_city_dew,
    fetch_nei_lak_shan_dew,
    fetch_new_tsing_yi_dew,
    fetch_tate_dew,
    fetch_shing_mun_valley_dew,
    fetch_tuen_mun_home_dew,
    fetch_buoy_2_dew,
    fetch_cloud,
    fetch_evaporation,
    fetch_evapotranspiration,
    filter_stations,
    format_aqhi,
    format_aqhi_miss,
    format_day_miss,
    format_driest,
    format_driest_miss,
    format_nowcast,
    format_nowcast_miss,
    format_daily_rain,
    format_daily_rain_miss,
    format_lau_fau_rain_miss,
    format_shek_kong_rain_miss,
    format_wetland_rain_miss,
    format_sham_shui_po_rain_miss,
    format_park_rain_miss,
    format_tseung_kwan_o_rain_miss,
    format_sheung_shui_rain_miss,
    format_sha_tin_rain_miss,
    format_ta_kwu_ling_rain_miss,
    format_cheung_chau_rain_miss,
    format_waglan_rain_miss,
    format_tate_rain_miss,
    format_peng_chau_rain_miss,
    format_ping_chau_rain_miss,
    format_tai_mo_rain_miss,
    format_sha_lo_wan_rain_miss,
    format_airport_rain_miss,
    format_green_island_rain_miss,
    format_tsuen_wan_rain_miss,
    format_tap_mun_rain_miss,
    format_clear_water_bay_rain_miss,
    format_shau_kei_wan_rain_miss,
    format_happy_valley_rain_miss,
    format_tai_mei_tuk_rain_miss,
    format_kadoorie_farm_rain_miss,
    format_the_peak_rain_miss,
    format_pak_tam_chung_rain_miss,
    format_ching_pak_house_rain_miss,
    format_kau_sai_chau_rain_miss,
    format_kai_tak_rain_miss,
    format_sha_tau_kok_rain_miss,
    format_beas_river_rain_miss,
    format_kat_o_rain_miss,
    format_tap_shek_kok_rain_miss,
    format_tsim_bei_tsui_rain_miss,
    format_tai_mei_tuk_pump_rain_miss,
    format_ngong_ping_reservoir_rain_miss,
    format_discovery_bay_rain_miss,
    format_adventist_college_rain_miss,
    format_wong_shiu_chi_rain_miss,
    format_au_tau_rain_miss,
    format_lok_ma_chau_rain_miss,
    format_lamma_island_rain_miss,
    format_tuen_mun_home_rain_miss,
    format_forecast,
    format_outlook,
    format_outlook_miss,
    format_coastal,
    format_coastal_miss,
    format_coast_report,
    format_coast_report_miss,
    format_forecast_period,
    format_forecast_period_miss,
    format_forecast_desc,
    format_forecast_desc_miss,
    format_forecast_updated,
    format_forecast_updated_miss,
    format_grass,
    format_grass_miss,
    format_sunshine,
    format_sunshine_miss,
    format_daily_sun,
    format_daily_sun_miss,
    format_max_uv,
    format_max_uv_miss,
    format_uv_peak,
    format_uv_peak_miss,
    format_mean_uv,
    format_mean_uv_miss,
    format_daily_uv_miss,
    format_dose,
    format_dose_miss,
    format_hourly_dose,
    format_hourly_dose_miss,
    format_accum_rain,
    format_accum_rain_miss,
    format_avg_rain,
    format_avg_rain_miss,
    format_radiation,
    format_radiation_miss,
    format_bulletin,
    format_bulletin_miss,
    format_radiation_note,
    format_radiation_note_miss,
    format_radiation_weather,
    format_radiation_weather_miss,
    format_radiation_ground,
    format_radiation_ground_miss,
    format_radiation_provisional,
    format_radiation_provisional_miss,
    format_felt,
    format_felt_miss,
    format_fire_danger,
    format_fire_danger_miss,
    format_coldest,
    format_coldest_miss,
    format_cyclone,
    format_cyclone_miss,
    format_hottest,
    format_hottest_miss,
    format_humidest,
    format_humidest_miss,
    format_humidity,
    format_humidity_time,
    format_humidity_time_miss,
    format_minute_humidity,
    format_minute_humidity_miss,
    format_mean_humidity,
    format_mean_humidity_miss,
    format_tai_mo_humidity_miss,
    format_waglan_humidity_miss,
    format_tate_humidity_miss,
    format_ta_kwu_ling_humidity_miss,
    format_wetland_humidity_miss,
    format_shek_kong_humidity_miss,
    format_lau_fau_humidity_miss,
    format_park_humidity_miss,
    format_sai_kung_humidity_miss,
    format_cheung_chau_humidity_miss,
    format_sha_tin_humidity_miss,
    format_sheung_shui_humidity_miss,
    format_wong_chuk_hang_humidity_miss,
    format_tseung_kwan_o_humidity_miss,
    format_peng_chau_humidity_miss,
    format_sha_lo_wan_humidity_miss,
    format_airport_humidity_miss,
    format_tsuen_wan_humidity_miss,
    format_hong_kong_park_humidity_miss,
    format_clear_water_bay_humidity_miss,
    format_shau_kei_wan_humidity_miss,
    format_kau_sai_chau_humidity_miss,
    format_pak_tam_chung_humidity_miss,
    format_beas_river_humidity_miss,
    format_runway_park_humidity_miss,
    format_kowloon_city_humidity_miss,
    format_nei_lak_shan_humidity_miss,
    format_new_tsing_yi_humidity_miss,
    format_shing_mun_valley_humidity_miss,
    format_tuen_mun_home_humidity_miss,
    format_buoy_2_humidity_miss,
    format_hour_rain,
    format_hour_rain_miss,
    format_hour_wettest,
    format_hour_driest,
    format_icon_time,
    format_icon_time_miss,
    format_icon,
    format_icon_miss,
    format_current_updated,
    format_current_updated_miss,
    format_least_humid,
    format_least_humid_miss,
    format_json,
    format_lightning,
    format_lunar,
    format_lunar_miss,
    format_moon,
    format_moon_miss,
    format_month_rain,
    format_month_rain_miss,
    format_year_rain,
    format_year_rain_miss,
    format_place_miss,
    format_nine_day,
    format_nine_situation,
    format_nine_situation_miss,
    format_nine_updated,
    format_nine_updated_miss,
    format_nine_weather,
    format_nine_weather_miss,
    format_nine_temp,
    format_nine_temp_miss,
    format_nine_humidity,
    format_nine_humidity_miss,
    format_sea_temp,
    format_sea_temp_miss,
    format_morning_sea,
    format_north_point_am_sea_miss,
    format_afternoon_sea,
    format_north_point_pm_sea_miss,
    format_soil_temp,
    format_soil_temp_miss,
    format_noon_rain,
    format_noon_rain_miss,
    format_overnight,
    format_overnight_miss,
    format_places,
    format_psr,
    format_quakes,
    format_rain,
    format_rain_period,
    format_rain_period_miss,
    format_rain_maint,
    format_rain_maint_miss,
    format_rainstorm,
    format_rainstorm_miss,
    format_short,
    format_situation,
    format_situation_miss,
    format_summary,
    format_report,
    format_stations,
    format_strikes,
    format_strikes_miss,
    format_daily_strikes,
    format_daily_strikes_miss,
    format_cloud_strikes,
    format_cloud_strikes_miss,
    format_sunrise,
    format_sunrise_miss,
    format_temps,
    format_temp_time,
    format_temp_time_miss,
    format_minute_temp,
    format_minute_temp_miss,
    format_since_midnight,
    format_since_midnight_miss,
    format_pressure,
    format_pressure_miss,
    format_mean_pressure,
    format_mean_pressure_miss,
    format_park_pressure_miss,
    format_sha_tin_pressure_miss,
    format_sheung_shui_pressure_miss,
    format_waglan_pressure_miss,
    format_cheung_chau_pressure_miss,
    format_lau_fau_pressure_miss,
    format_tate_pressure_miss,
    format_wetland_pressure_miss,
    format_peng_chau_pressure_miss,
    format_tai_mo_pressure_miss,
    format_sha_lo_wan_pressure_miss,
    format_shek_kong_pressure_miss,
    format_ta_kwu_ling_pressure_miss,
    format_airport_pressure_miss,
    format_nei_lak_shan_pressure_miss,
    format_minute_grass,
    format_minute_grass_miss,
    format_daily_grass,
    format_daily_grass_miss,
    format_obs_grass_miss,
    format_temp_diff,
    format_temp_diff_miss,
    format_heat_index,
    format_heat_index_miss,
    format_daily_heat,
    format_daily_heat_miss,
    format_mean_heat,
    format_mean_heat_miss,
    format_wbgt,
    format_wbgt_miss,
    format_wet_bulb,
    format_wet_bulb_miss,
    format_airport_wet_miss,
    format_park_wet_miss,
    format_sha_lo_wan_wet_miss,
    format_solar,
    format_solar_miss,
    format_global_solar,
    format_global_solar_miss,
    format_kau_sai_chau_solar_miss,
    format_tide,
    format_tide_miss,
    format_tide_hour,
    format_tide_hour_miss,
    format_tide_latest,
    format_tide_latest_miss,
    format_tc_info,
    format_tc_info_miss,
    format_tips,
    format_lamppost,
    format_lamppost_miss,
    format_today_miss,
    format_tomorrow,
    format_tomorrow_miss,
    format_uv,
    format_fifteen_uv,
    format_fifteen_uv_miss,
    format_visibility,
    format_reduced_vis,
    format_reduced_vis_miss,
    format_warning_info,
    format_wettest,
    format_wettest_miss,
    format_warnings,
    format_warning_time,
    format_warning_time_miss,
    format_weekend,
    format_weekend_miss,
    format_wind,
    format_gust,
    format_gust_miss,
    format_prevailing,
    format_prevailing_miss,
    format_cheung_prevailing_miss,
    format_ping_chau_prevailing_miss,
    format_tai_mo_to_prevailing_miss,
    format_tai_po_kau_prevailing_miss,
    format_park_prevailing_miss,
    format_lau_fau_prevailing_miss,
    format_sha_lo_wan_prevailing_miss,
    format_wong_chuk_hang_prevailing_miss,
    format_sai_kung_prevailing_miss,
    format_tseung_kwan_o_prevailing_miss,
    format_shek_kong_prevailing_miss,
    format_sha_tin_prevailing_miss,
    format_ta_kwu_ling_prevailing_miss,
    format_wetland_prevailing_miss,
    format_tai_mo_prevailing_miss,
    format_airport_prevailing_miss,
    format_kai_tak_prevailing_miss,
    format_green_island_prevailing_miss,
    format_ngong_ping_prevailing_miss,
    format_tai_mei_tuk_prevailing_miss,
    format_central_pier_prevailing_miss,
    format_nei_lak_shan_prevailing_miss,
    format_buoy_2_prevailing_miss,
    format_mean_wind,
    format_mean_wind_miss,
    format_cheung_wind_miss,
    format_lau_fau_wind_miss,
    format_peng_chau_wind_miss,
    format_tai_po_kau_wind_miss,
    format_tai_mo_to_wind_miss,
    format_tai_mo_wind_miss,
    format_tate_wind_miss,
    format_shek_kong_wind_miss,
    format_sai_kung_wind_miss,
    format_sha_tin_wind_miss,
    format_wong_chuk_hang_wind_miss,
    format_park_wind_miss,
    format_wetland_wind_miss,
    format_tseung_kwan_o_wind_miss,
    format_ta_kwu_ling_wind_miss,
    format_sha_lo_wan_wind_miss,
    format_ping_chau_wind_miss,
    format_airport_wind_miss,
    format_green_island_wind_miss,
    format_ngong_ping_wind_miss,
    format_tai_mei_tuk_wind_miss,
    format_lamma_island_wind_miss,
    format_kai_tak_wind_miss,
    format_central_pier_wind_miss,
    format_nei_lak_shan_wind_miss,
    format_buoy_2_wind_miss,
    format_forecast_icon,
    format_forecast_icon_miss,
    format_yesterday,
    format_yesterday_miss,
    format_mean_temp,
    format_mean_temp_miss,
    format_tai_mo_temp,
    format_tai_mo_temp_miss,
    format_tate_temp_miss,
    format_sai_kung_temp_miss,
    format_sha_tin_temp_miss,
    format_sheung_shui_temp_miss,
    format_wong_chuk_hang_temp_miss,
    format_lau_fau_temp_miss,
    format_tseung_kwan_o_temp_miss,
    format_sham_shui_po_temp_miss,
    format_shek_kong_temp_miss,
    format_wetland_temp_miss,
    format_ta_kwu_ling_temp_miss,
    format_peng_chau_temp_miss,
    format_park_temp_miss,
    format_cheung_chau_temp_miss,
    format_waglan_temp_miss,
    format_ping_chau_temp_miss,
    format_sha_lo_wan_temp_miss,
    format_airport_temp_miss,
    format_clear_water_bay_temp_miss,
    format_hong_kong_park_temp_miss,
    format_ngong_ping_temp_miss,
    format_kwun_tong_temp_miss,
    format_wong_tai_sin_temp_miss,
    format_tsuen_wan_temp_miss,
    format_yuen_long_park_temp_miss,
    format_tap_mun_temp_miss,
    format_shau_kei_wan_temp_miss,
    format_happy_valley_temp_miss,
    format_tai_mei_tuk_temp_miss,
    format_kau_sai_chau_temp_miss,
    format_kadoorie_farm_temp_miss,
    format_the_peak_temp_miss,
    format_kat_o_temp_miss,
    format_pak_tam_chung_temp_miss,
    format_beas_river_temp_miss,
    format_bluff_head_temp_miss,
    format_runway_park_temp_miss,
    format_kowloon_city_temp_miss,
    format_nei_lak_shan_temp_miss,
    format_new_tsing_yi_temp_miss,
    format_stanley_temp_miss,
    format_shing_mun_valley_temp_miss,
    format_tuen_mun_home_temp_miss,
    format_buoy_2_temp_miss,
    format_buoy_8_temp_miss,
    format_tai_mo_min,
    format_tai_mo_min_miss,
    format_tate_min_miss,
    format_sai_kung_min_miss,
    format_wong_chuk_hang_min_miss,
    format_waglan_min_miss,
    format_sha_tin_min_miss,
    format_cheung_chau_min_miss,
    format_park_min_miss,
    format_lau_fau_min_miss,
    format_sheung_shui_min_miss,
    format_tseung_kwan_o_min_miss,
    format_sham_shui_po_min_miss,
    format_shek_kong_min_miss,
    format_wetland_min_miss,
    format_ta_kwu_ling_min_miss,
    format_sha_lo_wan_min_miss,
    format_airport_min_miss,
    format_yuen_long_park_min_miss,
    format_clear_water_bay_min_miss,
    format_tap_mun_min_miss,
    format_hong_kong_park_min_miss,
    format_ngong_ping_min_miss,
    format_kwun_tong_min_miss,
    format_wong_tai_sin_min_miss,
    format_tsuen_wan_min_miss,
    format_kau_sai_chau_min_miss,
    format_kadoorie_farm_min_miss,
    format_the_peak_min_miss,
    format_kat_o_min_miss,
    format_pak_tam_chung_min_miss,
    format_beas_river_min_miss,
    format_kowloon_city_min_miss,
    format_new_tsing_yi_min_miss,
    format_stanley_min_miss,
    format_shing_mun_valley_min_miss,
    format_tuen_mun_home_min_miss,
    format_buoy_2_min_miss,
    format_tai_mo_max,
    format_tai_mo_max_miss,
    format_tseung_kwan_o_max_miss,
    format_sheung_shui_max_miss,
    format_waglan_max_miss,
    format_shek_kong_max_miss,
    format_cheung_chau_max_miss,
    format_park_max_miss,
    format_lau_fau_max_miss,
    format_sai_kung_max_miss,
    format_sha_tin_max_miss,
    format_tate_max_miss,
    format_wong_chuk_hang_max_miss,
    format_sham_shui_po_max_miss,
    format_wetland_max_miss,
    format_ta_kwu_ling_max_miss,
    format_sha_lo_wan_max_miss,
    format_airport_max_miss,
    format_yuen_long_park_max_miss,
    format_clear_water_bay_max_miss,
    format_tap_mun_max_miss,
    format_hong_kong_park_max_miss,
    format_ngong_ping_max_miss,
    format_kwun_tong_max_miss,
    format_wong_tai_sin_max_miss,
    format_tsuen_wan_max_miss,
    format_kau_sai_chau_max_miss,
    format_kadoorie_farm_max_miss,
    format_the_peak_max_miss,
    format_kat_o_max_miss,
    format_pak_tam_chung_max_miss,
    format_beas_river_max_miss,
    format_kowloon_city_max_miss,
    format_new_tsing_yi_max_miss,
    format_stanley_max_miss,
    format_shing_mun_valley_max_miss,
    format_tuen_mun_home_max_miss,
    format_buoy_2_max_miss,
    format_max_temp,
    format_max_temp_miss,
    format_min_temp,
    format_min_temp_miss,
    format_dew_point,
    format_dew_point_miss,
    format_park_dew_miss,
    format_cheung_dew_miss,
    format_wong_chuk_hang_dew_miss,
    format_sai_kung_dew_miss,
    format_sha_tin_dew_miss,
    format_sheung_shui_dew_miss,
    format_waglan_dew_miss,
    format_lau_fau_dew_miss,
    format_wetland_dew_miss,
    format_ta_kwu_ling_dew_miss,
    format_shek_kong_dew_miss,
    format_tseung_kwan_o_dew_miss,
    format_tai_mo_dew_miss,
    format_peng_chau_dew_miss,
    format_sha_lo_wan_dew_miss,
    format_airport_dew_miss,
    format_clear_water_bay_dew_miss,
    format_hong_kong_park_dew_miss,
    format_tsuen_wan_dew_miss,
    format_shau_kei_wan_dew_miss,
    format_kau_sai_chau_dew_miss,
    format_pak_tam_chung_dew_miss,
    format_beas_river_dew_miss,
    format_runway_park_dew_miss,
    format_kowloon_city_dew_miss,
    format_nei_lak_shan_dew_miss,
    format_new_tsing_yi_dew_miss,
    format_tate_dew_miss,
    format_shing_mun_valley_dew_miss,
    format_tuen_mun_home_dew_miss,
    format_buoy_2_dew_miss,
    format_cloud,
    format_cloud_miss,
    format_evaporation,
    format_evaporation_miss,
    format_evapotranspiration,
    format_evapotranspiration_miss,
)


def _day_number(value: str) -> int:
    """Argparse type: forecast day 1–9, where 1 is the first list entry."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("day must be an integer from 1 to 9") from None
    if number < 1 or number > 9:
        raise argparse.ArgumentTypeError("day must be an integer from 1 to 9")
    return number


def package_version() -> str:
    """Return the installed hk-weather version from package metadata."""
    from importlib.metadata import version

    return version("hk-weather")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hk-weather",
        description=(
            "Print Hong Kong weather from Hong Kong Observatory open data. "
            "Current conditions by default; --summary prints a short briefing; "
            "--forecast prints the local forecast; "
            "--outlook prints the local-forecast outlook; "
            "--coastal prints the South China coastal waters forecast; "
            "--coast-report prints the latest coastal station reports; "
            "--forecast-period prints the forecast period; "
            "--forecast-desc prints the forecast description; "
            "--forecast-updated prints when the local forecast was updated; "
            "--situation prints the general situation; "
            "--fire-danger prints the fire danger warning; "
            "--tc-info prints tropical cyclone information from the local forecast; "
            "--nine-day prints the 9-day forecast; --sea-temp prints the sea temperature; "
            "--north-point-am-sea prints the latest daily morning sea temperature at North Point; "
            "--north-point-pm-sea prints the latest daily afternoon sea temperature "
            "at North Point; "
            "--soil-temp prints soil temperatures; "
            "--nine-situation prints the 9-day general situation; "
            "--nine-updated prints when the 9-day forecast was updated; "
            "--nine-weather prints each day's weather from the 9-day forecast; "
            "--nine-temp prints each day's high and low from the 9-day forecast; "
            "--nine-humidity prints each day's humidity from the 9-day forecast; "
            "--warnings lists active warnings; "
            "--warning-time prints when active warnings were issued; "
            "--uv prints the UV index; "
            "--fifteen-uv prints the latest 15-minute mean UV index; "
            "--icon-time prints when the weather icon changed; "
            "--icon prints the current weather icon; "
            "--current-updated prints when the current weather report was updated; "
            "--tips prints special weather tips; "
            "--lamppost prints the experimental smart-lamppost reading; "
            "--stations lists each station; --list-places lists their names; "
            "--place NAME filters those stations; --rain lists district rainfall; "
            "--rain-period prints the district rainfall window; "
            "--rain-maint lists districts whose rainfall gauge is under maintenance; "
            "--hour-rain lists past-hour rainfall at automatic stations; "
            "--hour-wettest prints the wettest of those stations; "
            "--hour-driest prints the driest of those stations; "
            "--lightning lists lightning locations; --strikes lists hourly lightning counts; "
            "--daily-strikes prints the latest daily cloud-to-ground count; "
            "--cloud-strikes prints the latest daily cloud-to-cloud count; "
            "--humidity lists humidity readings; "
            "--humidity-time prints when those readings were recorded; "
            "--minute-humidity prints the latest 1-minute mean humidity; "
            "--mean-humidity prints the latest daily mean humidity; "
            "--tai-mo-humidity prints the latest daily mean humidity at Tai Mo Shan; "
            "--waglan-humidity prints the latest daily mean humidity at Waglan Island; "
            "--tate-humidity prints the latest daily mean humidity at Tate's Cairn; "
            "--ta-kwu-ling-humidity prints the latest daily mean humidity at Ta Kwu Ling; "
            "--wetland-humidity prints the latest daily mean humidity at Wetland Park; "
            "--shek-kong-humidity prints the latest daily mean humidity at Shek Kong; "
            "--lau-fau-humidity prints the latest daily mean humidity at Lau Fau Shan; "
            "--park-humidity prints the latest daily mean humidity at King's Park; "
            "--sai-kung-humidity prints the latest daily mean humidity at Sai Kung; "
            "--cheung-chau-humidity prints the latest daily mean humidity at Cheung Chau; "
            "--sha-tin-humidity prints the latest daily mean humidity at Sha Tin; "
            "--sheung-shui-humidity prints the latest daily mean humidity at Sheung Shui; "
            "--wong-chuk-hang-humidity prints the latest daily mean humidity at Wong Chuk Hang; "
            "--tseung-kwan-o-humidity prints the latest daily mean humidity at Tseung Kwan O; "
            "--peng-chau-humidity prints the latest daily mean humidity at Peng Chau; "
            "--sha-lo-wan-humidity prints the latest daily mean humidity at Sha Lo Wan; "
            "--airport-humidity prints the latest daily mean humidity at the airport; "
            "--tsuen-wan-humidity prints the latest daily mean humidity at Tsuen Wan; "
            "--hong-kong-park-humidity prints the latest daily mean humidity at Hong Kong Park; "
            "--clear-water-bay-humidity prints the latest daily mean humidity at Clear Water Bay; "
            "--shau-kei-wan-humidity prints the latest daily mean humidity at Shau Kei Wan; "
            "--kau-sai-chau-humidity prints the latest daily mean humidity at Kau Sai Chau; "
            "--pak-tam-chung-humidity prints the latest daily mean humidity at Pak Tam Chung (Tsak Yue Wu); "
            "--beas-river-humidity prints the latest daily mean humidity at Beas River; "
            "--runway-park-humidity prints the latest daily mean humidity at Kai Tak Runway Park; "
            "--kowloon-city-humidity prints the latest daily mean humidity at Kowloon City; "
            "--nei-lak-shan-humidity prints the latest daily mean humidity at Nei Lak Shan; "
            "--new-tsing-yi-humidity prints the latest daily mean humidity at New Tsing Yi Station; "
            "--shing-mun-valley-humidity prints the latest daily mean humidity at Tsuen Wan Shing Mun Valley; "
            "--tuen-mun-home-humidity prints the latest daily mean humidity at Tuen Mun Children and Juvenile Home; "
            "--buoy-2-humidity prints the latest daily mean humidity at Automatic Weather Buoy No.2; "
            "--temps lists temperatures by place; "
            "--temp-time prints when those temperatures were recorded; "
            "--minute-temp prints the latest 1-minute mean temperature; "
            "--since-midnight prints each station's high and low since midnight; "
            "--pressure prints the latest 1-minute sea level pressure; "
            "--mean-pressure prints the latest daily mean pressure; "
            "--park-pressure prints the latest daily mean pressure at King's Park; "
            "--sha-tin-pressure prints the latest daily mean pressure at Sha Tin; "
            "--sheung-shui-pressure prints the latest daily mean pressure at Sheung Shui; "
            "--waglan-pressure prints the latest daily mean pressure at Waglan Island; "
            "--cheung-chau-pressure prints the latest daily mean pressure at Cheung Chau; "
            "--lau-fau-pressure prints the latest daily mean pressure at Lau Fau Shan; "
            "--tate-pressure prints the latest daily mean pressure at Tate's Cairn; "
            "--wetland-pressure prints the latest daily mean pressure at Wetland Park; "
            "--peng-chau-pressure prints the latest daily mean pressure at Peng Chau; "
            "--tai-mo-pressure prints the latest daily mean pressure at Tai Mo Shan; "
            "--sha-lo-wan-pressure prints the latest daily mean pressure at Sha Lo Wan; "
            "--shek-kong-pressure prints the latest daily mean pressure at Shek Kong; "
            "--ta-kwu-ling-pressure prints the latest daily mean pressure at Ta Kwu Ling; "
            "--airport-pressure prints the latest daily mean pressure at the airport; "
            "--nei-lak-shan-pressure prints the latest daily mean pressure at Nei Lak Shan; "
            "--minute-grass prints the latest 1-minute grass temperature; "
            "--daily-grass prints the latest daily grass minimum; "
            "--obs-grass prints the latest daily grass minimum at the Observatory; "
            "--temp-diff prints the past 24-hour temperature change; "
            "--heat-index prints the latest Hong Kong Heat Index; "
            "--daily-heat prints the latest daily maximum heat index at King's Park; "
            "--mean-heat prints the latest daily mean heat index at King's Park; "
            "--wbgt prints the latest Wet Bulb Globe Temperature; "
            "--wet-bulb prints the latest daily wet-bulb temperature; "
            "--airport-wet prints the latest daily wet-bulb temperature at the airport; "
            "--park-wet prints the latest daily wet-bulb temperature at King's Park; "
            "--sha-lo-wan-wet prints the latest daily wet-bulb temperature at Sha Lo Wan; "
            "--solar prints the latest solar radiation; "
            "--global-solar prints the latest daily global solar radiation; "
            "--kau-sai-chau-solar prints the latest daily global solar radiation at Kau Sai Chau; "
            "--wind lists the forecast wind; "
            "--gust prints the latest 10-minute wind and gust; "
            "--prevailing prints the latest prevailing wind direction; "
            "--cheung-prevailing prints the latest prevailing wind at Cheung Chau; "
            "--ping-chau-prevailing prints the latest prevailing wind at Ping Chau; "
            "--tai-mo-to-prevailing prints the latest prevailing wind at Tai Mo To; "
            "--tai-po-kau-prevailing prints the latest prevailing wind at Tai Po Kau; "
            "--park-prevailing prints the latest prevailing wind at King's Park; "
            "--lau-fau-prevailing prints the latest prevailing wind at Lau Fau Shan; "
            "--sha-lo-wan-prevailing prints the latest prevailing wind at Sha Lo Wan; "
            "--wong-chuk-hang-prevailing prints the latest prevailing wind at Wong Chuk Hang; "
            "--sai-kung-prevailing prints the latest prevailing wind at Sai Kung; "
            "--tseung-kwan-o-prevailing prints the latest prevailing wind at Tseung Kwan O; "
            "--shek-kong-prevailing prints the latest prevailing wind at Shek Kong; "
            "--sha-tin-prevailing prints the latest prevailing wind at Sha Tin; "
            "--ta-kwu-ling-prevailing prints the latest prevailing wind at Ta Kwu Ling; "
            "--wetland-prevailing prints the latest prevailing wind at Wetland Park; "
            "--tai-mo-prevailing prints the latest prevailing wind at Tai Mo Shan; "
            "--airport-prevailing prints the latest prevailing wind at the airport; "
            "--kai-tak-prevailing prints the latest prevailing wind at Kai Tak; "
            "--green-island-prevailing prints the latest prevailing wind at Green Island; "
            "--ngong-ping-prevailing prints the latest prevailing wind at Ngong Ping; "
            "--tai-mei-tuk-prevailing prints the latest prevailing wind at Tai Mei Tuk; "
            "--central-pier-prevailing prints the latest prevailing wind at Central Pier; "
            "--nei-lak-shan-prevailing prints the latest prevailing wind at Nei Lak Shan; "
            "--buoy-2-prevailing prints the latest prevailing wind at Automatic Weather Buoy No.2; "
            "--mean-wind prints the latest daily mean wind speed; "
            "--cheung-wind prints the latest daily mean wind speed at Cheung Chau; "
            "--lau-fau-wind prints the latest daily mean wind speed at Lau Fau Shan; "
            "--peng-chau-wind prints the latest daily mean wind speed at Peng Chau; "
            "--tai-po-kau-wind prints the latest daily mean wind speed at Tai Po Kau; "
            "--tai-mo-to-wind prints the latest daily mean wind speed at Tai Mo To; "
            "--tai-mo-wind prints the latest daily mean wind speed at Tai Mo Shan; "
            "--tate-wind prints the latest daily mean wind speed at Tate's Cairn; "
            "--shek-kong-wind prints the latest daily mean wind speed at Shek Kong; "
            "--sai-kung-wind prints the latest daily mean wind speed at Sai Kung; "
            "--sha-tin-wind prints the latest daily mean wind speed at Sha Tin; "
            "--wong-chuk-hang-wind prints the latest daily mean wind speed at Wong Chuk Hang; "
            "--park-wind prints the latest daily mean wind speed at King's Park; "
            "--wetland-wind prints the latest daily mean wind speed at Wetland Park; "
            "--tseung-kwan-o-wind prints the latest daily mean wind speed at Tseung Kwan O; "
            "--ta-kwu-ling-wind prints the latest daily mean wind speed at Ta Kwu Ling; "
            "--sha-lo-wan-wind prints the latest daily mean wind speed at Sha Lo Wan; "
            "--ping-chau-wind prints the latest daily mean wind speed at Ping Chau; "
            "--airport-wind prints the latest daily mean wind speed at the airport; "
            "--green-island-wind prints the latest daily mean wind speed at Green Island; "
            "--ngong-ping-wind prints the latest daily mean wind speed at Ngong Ping; "
            "--tai-mei-tuk-wind prints the latest daily mean wind speed at Tai Mei Tuk; "
            "--lamma-island-wind prints the latest daily mean wind speed at Lamma Island; "
            "--kai-tak-wind prints the latest daily mean wind speed at Kai Tak; "
            "--central-pier-wind prints the latest daily mean wind speed at Central Pier; "
            "--nei-lak-shan-wind prints the latest daily mean wind speed at Nei Lak Shan; "
            "--buoy-2-wind prints the latest daily mean wind speed at Automatic Weather Buoy No.2; "
            "--forecast-icon prints each day's weather icon; "
            "--quake lists the latest earthquake message; "
            "--felt prints the locally felt earth tremor; --today prints today; "
            "--yesterday prints yesterday's Observatory summary; "
            "--mean-temp prints the latest daily mean temperature; "
            "--tai-mo-temp prints the latest daily mean temperature at Tai Mo Shan; "
            "--tate-temp prints the latest daily mean temperature at Tate's Cairn; "
            "--sai-kung-temp prints the latest daily mean temperature at Sai Kung; "
            "--sha-tin-temp prints the latest daily mean temperature at Sha Tin; "
            "--sheung-shui-temp prints the latest daily mean temperature at Sheung Shui; "
            "--wong-chuk-hang-temp prints the latest daily mean temperature at Wong Chuk Hang; "
            "--lau-fau-temp prints the latest daily mean temperature at Lau Fau Shan; "
            "--tseung-kwan-o-temp prints the latest daily mean temperature at Tseung Kwan O; "
            "--sham-shui-po-temp prints the latest daily mean temperature at Sham Shui Po; "
            "--shek-kong-temp prints the latest daily mean temperature at Shek Kong; "
            "--wetland-temp prints the latest daily mean temperature at Wetland Park; "
            "--ta-kwu-ling-temp prints the latest daily mean temperature at Ta Kwu Ling; "
            "--peng-chau-temp prints the latest daily mean temperature at Peng Chau; "
            "--park-temp prints the latest daily mean temperature at King's Park; "
            "--cheung-chau-temp prints the latest daily mean temperature at Cheung Chau; "
            "--waglan-temp prints the latest daily mean temperature at Waglan Island; "
            "--ping-chau-temp prints the latest daily mean temperature at Ping Chau; "
            "--sha-lo-wan-temp prints the latest daily mean temperature at Sha Lo Wan; "
            "--airport-temp prints the latest daily mean temperature at the airport; "
            "--clear-water-bay-temp prints the latest daily mean temperature at Clear Water Bay; "
            "--hong-kong-park-temp prints the latest daily mean temperature at Hong Kong Park; "
            "--ngong-ping-temp prints the latest daily mean temperature at Ngong Ping; "
            "--kwun-tong-temp prints the latest daily mean temperature at Kwun Tong; "
            "--wong-tai-sin-temp prints the latest daily mean temperature at Wong Tai Sin; "
            "--tsuen-wan-temp prints the latest daily mean temperature at Tsuen Wan; "
            "--yuen-long-park-temp prints the latest daily mean temperature at Yuen Long Park; "
            "--tap-mun-temp prints the latest daily mean temperature at Tap Mun; "
            "--shau-kei-wan-temp prints the latest daily mean temperature at Shau Kei Wan; "
            "--happy-valley-temp prints the latest daily mean temperature at Happy Valley; "
            "--tai-mei-tuk-temp prints the latest daily mean temperature at Tai Mei Tuk; "
            "--kau-sai-chau-temp prints the latest daily mean temperature at Kau Sai Chau; "
            "--kadoorie-farm-temp prints the latest daily mean temperature at Kadoorie Farm and Botanic Garden; "
            "--the-peak-temp prints the latest daily mean temperature at The Peak; "
            "--kat-o-temp prints the latest daily mean temperature at Kat O; "
            "--pak-tam-chung-temp prints the latest daily mean temperature at Pak Tam Chung (Tsak Yue Wu); "
            "--beas-river-temp prints the latest daily mean temperature at Beas River; "
            "--bluff-head-temp prints the latest daily mean temperature at Bluff Head; "
            "--runway-park-temp prints the latest daily mean temperature at Kai Tak Runway Park; "
            "--kowloon-city-temp prints the latest daily mean temperature at Kowloon City; "
            "--nei-lak-shan-temp prints the latest daily mean temperature at Nei Lak Shan; "
            "--new-tsing-yi-temp prints the latest daily mean temperature at New Tsing Yi Station; "
            "--stanley-temp prints the latest daily mean temperature at Stanley; "
            "--shing-mun-valley-temp prints the latest daily mean temperature at Tsuen Wan Shing Mun Valley; "
            "--tuen-mun-home-temp prints the latest daily mean temperature at Tuen Mun Children and Juvenile Home; "
            "--buoy-2-temp prints the latest daily mean temperature at Automatic Weather Buoy No.2; "
            "--buoy-8-temp prints the latest daily mean temperature at Automatic Weather Buoy No.8; "
            "--max-temp prints the latest daily maximum temperature; "
            "--min-temp prints the latest daily minimum temperature; "
            "--tai-mo-min prints the latest daily minimum temperature at Tai Mo Shan; "
            "--tate-min prints the latest daily minimum temperature at Tate's Cairn; "
            "--sai-kung-min prints the latest daily minimum temperature at Sai Kung; "
            "--wong-chuk-hang-min prints the latest daily minimum temperature at Wong Chuk Hang; "
            "--waglan-min prints the latest daily minimum temperature at Waglan Island; "
            "--sha-tin-min prints the latest daily minimum temperature at Sha Tin; "
            "--cheung-chau-min prints the latest daily minimum temperature at Cheung Chau; "
            "--park-min prints the latest daily minimum temperature at King's Park; "
            "--lau-fau-min prints the latest daily minimum temperature at Lau Fau Shan; "
            "--sheung-shui-min prints the latest daily minimum temperature at Sheung Shui; "
            "--tseung-kwan-o-min prints the latest daily minimum temperature at Tseung Kwan O; "
            "--sham-shui-po-min prints the latest daily minimum temperature at Sham Shui Po; "
            "--shek-kong-min prints the latest daily minimum temperature at Shek Kong; "
            "--wetland-min prints the latest daily minimum temperature at Wetland Park; "
            "--ta-kwu-ling-min prints the latest daily minimum temperature at Ta Kwu Ling; "
            "--sha-lo-wan-min prints the latest daily minimum temperature at Sha Lo Wan; "
            "--airport-min prints the latest daily minimum temperature at the airport; "
            "--yuen-long-park-min prints the latest daily minimum temperature at Yuen Long Park; "
            "--clear-water-bay-min prints the latest daily minimum temperature at Clear Water Bay; "
            "--tap-mun-min prints the latest daily minimum temperature at Tap Mun; "
            "--hong-kong-park-min prints the latest daily minimum temperature at Hong Kong Park; "
            "--ngong-ping-min prints the latest daily minimum temperature at Ngong Ping; "
            "--kwun-tong-min prints the latest daily minimum temperature at Kwun Tong; "
            "--wong-tai-sin-min prints the latest daily minimum temperature at Wong Tai Sin; "
            "--tsuen-wan-min prints the latest daily minimum temperature at Tsuen Wan; "
            "--kau-sai-chau-min prints the latest daily minimum temperature at Kau Sai Chau; "
            "--kadoorie-farm-min prints the latest daily minimum temperature at Kadoorie Farm and Botanic Garden; "
            "--the-peak-min prints the latest daily minimum temperature at The Peak; "
            "--kat-o-min prints the latest daily minimum temperature at Kat O; "
            "--pak-tam-chung-min prints the latest daily minimum temperature at Pak Tam Chung (Tsak Yue Wu); "
            "--beas-river-min prints the latest daily minimum temperature at Beas River; "
            "--kowloon-city-min prints the latest daily minimum temperature at Kowloon City; "
            "--new-tsing-yi-min prints the latest daily minimum temperature at New Tsing Yi Station; "
            "--stanley-min prints the latest daily minimum temperature at Stanley; "
            "--shing-mun-valley-min prints the latest daily minimum temperature at Tsuen Wan Shing Mun Valley; "
            "--tuen-mun-home-min prints the latest daily minimum temperature at Tuen Mun Children and Juvenile Home; "
            "--buoy-2-min prints the latest daily minimum temperature at Automatic Weather Buoy No.2; "
            "--tai-mo-max prints the latest daily maximum temperature at Tai Mo Shan; "
            "--tseung-kwan-o-max prints the latest daily maximum temperature at Tseung Kwan O; "
            "--sheung-shui-max prints the latest daily maximum temperature at Sheung Shui; "
            "--waglan-max prints the latest daily maximum temperature at Waglan Island; "
            "--shek-kong-max prints the latest daily maximum temperature at Shek Kong; "
            "--cheung-chau-max prints the latest daily maximum temperature at Cheung Chau; "
            "--park-max prints the latest daily maximum temperature at King's Park; "
            "--lau-fau-max prints the latest daily maximum temperature at Lau Fau Shan; "
            "--sai-kung-max prints the latest daily maximum temperature at Sai Kung; "
            "--sha-tin-max prints the latest daily maximum temperature at Sha Tin; "
            "--tate-max prints the latest daily maximum temperature at Tate's Cairn; "
            "--wong-chuk-hang-max prints the latest daily maximum temperature at Wong Chuk Hang; "
            "--sham-shui-po-max prints the latest daily maximum temperature at Sham Shui Po; "
            "--wetland-max prints the latest daily maximum temperature at Wetland Park; "
            "--ta-kwu-ling-max prints the latest daily maximum temperature at Ta Kwu Ling; "
            "--sha-lo-wan-max prints the latest daily maximum temperature at Sha Lo Wan; "
            "--airport-max prints the latest daily maximum temperature at the airport; "
            "--yuen-long-park-max prints the latest daily maximum temperature at Yuen Long Park; "
            "--clear-water-bay-max prints the latest daily maximum temperature at Clear Water Bay; "
            "--tap-mun-max prints the latest daily maximum temperature at Tap Mun; "
            "--hong-kong-park-max prints the latest daily maximum temperature at Hong Kong Park; "
            "--ngong-ping-max prints the latest daily maximum temperature at Ngong Ping; "
            "--kwun-tong-max prints the latest daily maximum temperature at Kwun Tong; "
            "--wong-tai-sin-max prints the latest daily maximum temperature at Wong Tai Sin; "
            "--tsuen-wan-max prints the latest daily maximum temperature at Tsuen Wan; "
            "--kau-sai-chau-max prints the latest daily maximum temperature at Kau Sai Chau; "
            "--kadoorie-farm-max prints the latest daily maximum temperature at Kadoorie Farm and Botanic Garden; "
            "--the-peak-max prints the latest daily maximum temperature at The Peak; "
            "--kat-o-max prints the latest daily maximum temperature at Kat O; "
            "--pak-tam-chung-max prints the latest daily maximum temperature at Pak Tam Chung (Tsak Yue Wu); "
            "--beas-river-max prints the latest daily maximum temperature at Beas River; "
            "--kowloon-city-max prints the latest daily maximum temperature at Kowloon City; "
            "--new-tsing-yi-max prints the latest daily maximum temperature at New Tsing Yi Station; "
            "--stanley-max prints the latest daily maximum temperature at Stanley; "
            "--shing-mun-valley-max prints the latest daily maximum temperature at Tsuen Wan Shing Mun Valley; "
            "--tuen-mun-home-max prints the latest daily maximum temperature at Tuen Mun Children and Juvenile Home; "
            "--buoy-2-max prints the latest daily maximum temperature at Automatic Weather Buoy No.2; "
            "--dew-point prints the latest daily mean dew point; "
            "--park-dew prints the latest daily mean dew point at King's Park; "
            "--cheung-dew prints the latest daily mean dew point at Cheung Chau; "
            "--wong-chuk-hang-dew prints the latest daily mean dew point at Wong Chuk Hang; "
            "--sai-kung-dew prints the latest daily mean dew point at Sai Kung; "
            "--sha-tin-dew prints the latest daily mean dew point at Sha Tin; "
            "--sheung-shui-dew prints the latest daily mean dew point at Sheung Shui; "
            "--waglan-dew prints the latest daily mean dew point at Waglan Island; "
            "--lau-fau-dew prints the latest daily mean dew point at Lau Fau Shan; "
            "--wetland-dew prints the latest daily mean dew point at Wetland Park; "
            "--ta-kwu-ling-dew prints the latest daily mean dew point at Ta Kwu Ling; "
            "--shek-kong-dew prints the latest daily mean dew point at Shek Kong; "
            "--tseung-kwan-o-dew prints the latest daily mean dew point at Tseung Kwan O; "
            "--tai-mo-dew prints the latest daily mean dew point at Tai Mo Shan; "
            "--peng-chau-dew prints the latest daily mean dew point at Peng Chau; "
            "--sha-lo-wan-dew prints the latest daily mean dew point at Sha Lo Wan; "
            "--airport-dew prints the latest daily mean dew point at the airport; "
            "--clear-water-bay-dew prints the latest daily mean dew point at Clear Water Bay; "
            "--hong-kong-park-dew prints the latest daily mean dew point at Hong Kong Park; "
            "--tsuen-wan-dew prints the latest daily mean dew point at Tsuen Wan; "
            "--shau-kei-wan-dew prints the latest daily mean dew point at Shau Kei Wan; "
            "--kau-sai-chau-dew prints the latest daily mean dew point at Kau Sai Chau; "
            "--pak-tam-chung-dew prints the latest daily mean dew point at Pak Tam Chung (Tsak Yue Wu); "
            "--beas-river-dew prints the latest daily mean dew point at Beas River; "
            "--runway-park-dew prints the latest daily mean dew point at Kai Tak Runway Park; "
            "--kowloon-city-dew prints the latest daily mean dew point at Kowloon City; "
            "--nei-lak-shan-dew prints the latest daily mean dew point at Nei Lak Shan; "
            "--new-tsing-yi-dew prints the latest daily mean dew point at New Tsing Yi Station; "
            "--tate-dew prints the latest daily mean dew point at Tate's Cairn; "
            "--shing-mun-valley-dew prints the latest daily mean dew point at Tsuen Wan Shing Mun Valley; "
            "--tuen-mun-home-dew prints the latest daily mean dew point at Tuen Mun Children and Juvenile Home; "
            "--buoy-2-dew prints the latest daily mean dew point at Automatic Weather Buoy No.2; "
            "--cloud prints the latest daily mean cloud amount; "
            "--evaporation prints the latest daily evaporation; "
            "--evapotranspiration prints the latest monthly potential evapotranspiration; "
            "--grass prints yesterday's grass minimum; "
            "--sunshine prints yesterday's sunshine duration; "
            "--daily-sun prints the latest daily bright sunshine total; "
            "--max-uv prints yesterday's maximum UV index; "
            "--uv-peak prints the latest daily maximum UV index and its period; "
            "--mean-uv prints yesterday's mean UV index; "
            "--daily-uv prints the latest daily mean UV index at King's Park; "
            "--dose prints yesterday's gamma dose rate; "
            "--hourly-dose prints the latest hourly gamma dose rate; "
            "--accum-rain prints accumulated rainfall since 1 January; "
            "--avg-rain prints the climatological rainfall normal; "
            "--radiation prints yesterday's gamma radiation report; "
            "--bulletin prints when yesterday's bulletin was issued; "
            "--radiation-note prints the normal radiation range; "
            "--radiation-weather prints how radiation varies with the weather; "
            "--radiation-ground prints how radiation varies with the ground; "
            "--radiation-provisional prints the provisional radiation note; "
            "--tomorrow prints tomorrow; "
            "--day N prints forecast day N (1 is the first entry); "
            "--psr lists the chance of significant rain; "
            "--warning-info prints detailed warning messages; "
            "--weekend prints Saturday and Sunday; "
            "--visibility lists 10-minute mean visibility; "
            "--reduced-vis prints the latest daily hours of reduced visibility; "
            "--hottest prints the warmest place; "
            "--coldest prints the coolest place; "
            "--overnight prints the midnight-to-9am minimum; "
            "--noon-rain prints the midnight-to-noon rainfall note; "
            "--month-rain prints last month's rainfall note; "
            "--year-rain prints the January-to-last-month rainfall note; "
            "--wettest prints the wettest district; "
            "--driest prints the driest district; "
            "--nowcast prints the heaviest rainfall-nowcast cell in each half-hour; "
            "--daily-rain prints the latest daily rainfall total; "
            "--lau-fau-rain prints the latest daily rainfall at Lau Fau Shan; "
            "--shek-kong-rain prints the latest daily rainfall at Shek Kong; "
            "--wetland-rain prints the latest daily rainfall at Wetland Park; "
            "--sham-shui-po-rain prints the latest daily rainfall at Sham Shui Po; "
            "--park-rain prints the latest daily rainfall at King's Park; "
            "--tseung-kwan-o-rain prints the latest daily rainfall at Tseung Kwan O; "
            "--sheung-shui-rain prints the latest daily rainfall at Sheung Shui; "
            "--sha-tin-rain prints the latest daily rainfall at Sha Tin; "
            "--ta-kwu-ling-rain prints the latest daily rainfall at Ta Kwu Ling; "
            "--cheung-chau-rain prints the latest daily rainfall at Cheung Chau; "
            "--waglan-rain prints the latest daily rainfall at Waglan Island; "
            "--tate-rain prints the latest daily rainfall at Tate's Cairn; "
            "--peng-chau-rain prints the latest daily rainfall at Peng Chau; "
            "--ping-chau-rain prints the latest daily rainfall at Ping Chau; "
            "--tai-mo-rain prints the latest daily rainfall at Tai Mo Shan; "
            "--sha-lo-wan-rain prints the latest daily rainfall at Sha Lo Wan; "
            "--airport-rain prints the latest daily rainfall at the airport; "
            "--green-island-rain prints the latest daily rainfall at Green Island; "
            "--tsuen-wan-rain prints the latest daily rainfall at Tsuen Wan; "
            "--tap-mun-rain prints the latest daily rainfall at Tap Mun; "
            "--clear-water-bay-rain prints the latest daily rainfall at Clear Water Bay; "
            "--shau-kei-wan-rain prints the latest daily rainfall at Shau Kei Wan; "
            "--happy-valley-rain prints the latest daily rainfall at Happy Valley; "
            "--tai-mei-tuk-rain prints the latest daily rainfall at Tai Mei Tuk; "
            "--kadoorie-farm-rain prints the latest daily rainfall at Kadoorie Farm and Botanic Garden; "
            "--the-peak-rain prints the latest daily rainfall at The Peak; "
            "--pak-tam-chung-rain prints the latest daily rainfall at Pak Tam Chung (Tsak Yue Wu); "
            "--ching-pak-house-rain prints the latest daily rainfall at Ching Pak House(Tsing Yi); "
            "--kau-sai-chau-rain prints the latest daily rainfall at Kau Sai Chau; "
            "--kai-tak-rain prints the latest daily rainfall at Kai Tak; "
            "--sha-tau-kok-rain prints the latest daily rainfall at Sha Tau Kok; "
            "--beas-river-rain prints the latest daily rainfall at Beas River; "
            "--kat-o-rain prints the latest daily rainfall at Kat O; "
            "--tap-shek-kok-rain prints the latest daily rainfall at Tap Shek Kok; "
            "--tsim-bei-tsui-rain prints the latest daily rainfall at Tsim Bei Tsui; "
            "--tai-mei-tuk-pump-rain prints the latest daily rainfall at Tai Mei Tuk Pumping Station; "
            "--ngong-ping-reservoir-rain prints the latest daily rainfall at Ngong Ping Fresh Water Reservoir; "
            "--discovery-bay-rain prints the latest daily rainfall at Discovery Bay; "
            "--adventist-college-rain prints the latest daily rainfall at Hong Kong Adventist College(Sai Kung); "
            "--wong-shiu-chi-rain prints the latest daily rainfall at Tai Po Wong Shiu Chi Secondary School; "
            "--au-tau-rain prints the latest daily rainfall at Au Tau; "
            "--lok-ma-chau-rain prints the latest daily rainfall at Lok Ma Chau; "
            "--lamma-island-rain prints the latest daily rainfall at Lamma Island; "
            "--tuen-mun-home-rain prints the latest daily rainfall at Tuen Mun Children and Juvenile Home; "
            "--tide prints today's high and low tides; "
            "--tide-hour prints today's hourly tide heights; "
            "--tide-latest prints the latest observed tide height; "
            "--aqhi prints the air quality health index; "
            "--sunrise prints today's sunrise and sunset; "
            "--moon prints today's moonrise and moonset; "
            "--lunar prints today's lunar date; "
            "--rainstorm prints the rainstorm reminder; "
            "--cyclone prints the tropical cyclone message; "
            "--humidest prints the most humid place; "
            "--least-humid prints the least humid place; "
            "--mean-humidity prints the latest daily mean humidity."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {package_version()}",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10,
        help="HTTP timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the report as one JSON object",
    )
    parser.add_argument(
        "-s",
        "--short",
        action="store_true",
        help="Print current conditions on one line",
    )
    parser.add_argument(
        "-S",
        "--summary",
        action="store_true",
        help="Print conditions, active warnings, and today's high and low",
    )
    parser.add_argument(
        "--forecast",
        action="store_true",
        help="Print the local weather forecast instead of current conditions",
    )
    parser.add_argument(
        "--outlook",
        action="store_true",
        help="Print the outlook from the local weather forecast",
    )
    parser.add_argument(
        "--coastal",
        action="store_true",
        help="Print the South China coastal waters area forecast",
    )
    parser.add_argument(
        "--coast-report",
        action="store_true",
        help="Print the latest reports from South China coastal stations",
    )
    parser.add_argument(
        "--forecast-period",
        action="store_true",
        help="Print the period covered by the local weather forecast",
    )
    parser.add_argument(
        "--forecast-desc",
        action="store_true",
        help="Print the description from the local weather forecast",
    )
    parser.add_argument(
        "--forecast-updated",
        action="store_true",
        help="Print when the local weather forecast was last updated",
    )
    parser.add_argument(
        "-g",
        "--situation",
        action="store_true",
        help="Print the general situation from the local forecast",
    )
    parser.add_argument(
        "-f",
        "--fire-danger",
        action="store_true",
        help="Print the fire danger warning from the local forecast",
    )
    parser.add_argument(
        "--tc-info",
        action="store_true",
        help="Print tropical cyclone information from the local forecast",
    )
    parser.add_argument(
        "-n",
        "--nine-day",
        action="store_true",
        help="Print the 9-day forecast",
    )
    parser.add_argument(
        "--sea-temp",
        action="store_true",
        help="Print the sea temperature from the 9-day forecast",
    )
    parser.add_argument(
        "--north-point-am-sea",
        action="store_true",
        help="Print the latest daily morning sea temperature at North Point",
    )
    parser.add_argument(
        "--north-point-pm-sea",
        action="store_true",
        help="Print the latest daily afternoon sea temperature at North Point",
    )
    parser.add_argument(
        "--soil-temp",
        action="store_true",
        help="Print soil temperatures from the 9-day forecast",
    )
    parser.add_argument(
        "--nine-situation",
        action="store_true",
        help="Print the general situation from the 9-day forecast",
    )
    parser.add_argument(
        "--nine-updated",
        action="store_true",
        help="Print when the 9-day forecast was last updated",
    )
    parser.add_argument(
        "--nine-weather",
        action="store_true",
        help="Print each day's weather from the 9-day forecast",
    )
    parser.add_argument(
        "--nine-temp",
        action="store_true",
        help="Print each day's high and low from the 9-day forecast",
    )
    parser.add_argument(
        "--nine-humidity",
        action="store_true",
        help="Print each day's humidity range from the 9-day forecast",
    )
    parser.add_argument(
        "-Y",
        "--today",
        action="store_true",
        help="Print today's day from the 9-day forecast (Hong Kong calendar date)",
    )
    parser.add_argument(
        "--yesterday",
        action="store_true",
        help="Print yesterday's temperature, rainfall, and humidity at the Observatory",
    )
    parser.add_argument(
        "--mean-temp",
        action="store_true",
        help="Print the latest daily mean temperature at the Observatory",
    )
    parser.add_argument(
        "--tai-mo-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Tai Mo Shan",
    )
    parser.add_argument(
        "--tate-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Tate's Cairn",
    )
    parser.add_argument(
        "--sai-kung-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Sai Kung",
    )
    parser.add_argument(
        "--sha-tin-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Sha Tin",
    )
    parser.add_argument(
        "--sheung-shui-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Sheung Shui",
    )
    parser.add_argument(
        "--wong-chuk-hang-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Wong Chuk Hang",
    )
    parser.add_argument(
        "--lau-fau-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Lau Fau Shan",
    )
    parser.add_argument(
        "--tseung-kwan-o-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Tseung Kwan O",
    )
    parser.add_argument(
        "--sham-shui-po-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Sham Shui Po",
    )
    parser.add_argument(
        "--shek-kong-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Shek Kong",
    )
    parser.add_argument(
        "--wetland-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Wetland Park",
    )
    parser.add_argument(
        "--ta-kwu-ling-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Ta Kwu Ling",
    )
    parser.add_argument(
        "--peng-chau-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Peng Chau",
    )
    parser.add_argument(
        "--park-temp",
        action="store_true",
        help="Print the latest daily mean temperature at King's Park",
    )
    parser.add_argument(
        "--cheung-chau-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Cheung Chau",
    )
    parser.add_argument(
        "--waglan-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Waglan Island",
    )
    parser.add_argument(
        "--ping-chau-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Ping Chau",
    )
    parser.add_argument(
        "--sha-lo-wan-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Sha Lo Wan",
    )
    parser.add_argument(
        "--airport-temp",
        action="store_true",
        help="Print the latest daily mean temperature at the airport",
    )
    parser.add_argument(
        "--clear-water-bay-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Clear Water Bay",
    )
    parser.add_argument(
        "--hong-kong-park-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Hong Kong Park",
    )
    parser.add_argument(
        "--ngong-ping-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Ngong Ping",
    )
    parser.add_argument(
        "--kwun-tong-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Kwun Tong",
    )
    parser.add_argument(
        "--wong-tai-sin-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Wong Tai Sin",
    )
    parser.add_argument(
        "--tsuen-wan-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Tsuen Wan",
    )
    parser.add_argument(
        "--yuen-long-park-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Yuen Long Park",
    )
    parser.add_argument(
        "--tap-mun-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Tap Mun",
    )
    parser.add_argument(
        "--shau-kei-wan-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Shau Kei Wan",
    )
    parser.add_argument(
        "--happy-valley-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Happy Valley",
    )
    parser.add_argument(
        "--tai-mei-tuk-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Tai Mei Tuk",
    )
    parser.add_argument(
        "--kau-sai-chau-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Kau Sai Chau",
    )
    parser.add_argument(
        "--kadoorie-farm-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Kadoorie Farm and Botanic Garden",
    )
    parser.add_argument(
        "--the-peak-temp",
        action="store_true",
        help="Print the latest daily mean temperature at The Peak",
    )
    parser.add_argument(
        "--kat-o-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Kat O",
    )
    parser.add_argument(
        "--pak-tam-chung-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Pak Tam Chung (Tsak Yue Wu)",
    )
    parser.add_argument(
        "--beas-river-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Beas River",
    )
    parser.add_argument(
        "--bluff-head-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Bluff Head",
    )
    parser.add_argument(
        "--runway-park-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Kai Tak Runway Park",
    )
    parser.add_argument(
        "--kowloon-city-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Kowloon City",
    )
    parser.add_argument(
        "--nei-lak-shan-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Nei Lak Shan",
    )
    parser.add_argument(
        "--new-tsing-yi-temp",
        action="store_true",
        help="Print the latest daily mean temperature at New Tsing Yi Station",
    )
    parser.add_argument(
        "--stanley-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Stanley",
    )
    parser.add_argument(
        "--shing-mun-valley-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Tsuen Wan Shing Mun Valley",
    )
    parser.add_argument(
        "--tuen-mun-home-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Tuen Mun Children and Juvenile Home",
    )
    parser.add_argument(
        "--buoy-2-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Automatic Weather Buoy No.2",
    )
    parser.add_argument(
        "--buoy-8-temp",
        action="store_true",
        help="Print the latest daily mean temperature at Automatic Weather Buoy No.8",
    )
    parser.add_argument(
        "--max-temp",
        action="store_true",
        help="Print the latest daily maximum temperature at the Observatory",
    )
    parser.add_argument(
        "--min-temp",
        action="store_true",
        help="Print the latest daily minimum temperature at the Observatory",
    )
    parser.add_argument(
        "--tai-mo-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Tai Mo Shan",
    )
    parser.add_argument(
        "--tate-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Tate's Cairn",
    )
    parser.add_argument(
        "--sai-kung-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Sai Kung",
    )
    parser.add_argument(
        "--wong-chuk-hang-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Wong Chuk Hang",
    )
    parser.add_argument(
        "--waglan-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Waglan Island",
    )
    parser.add_argument(
        "--sha-tin-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Sha Tin",
    )
    parser.add_argument(
        "--cheung-chau-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Cheung Chau",
    )
    parser.add_argument(
        "--park-min",
        action="store_true",
        help="Print the latest daily minimum temperature at King's Park",
    )
    parser.add_argument(
        "--lau-fau-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Lau Fau Shan",
    )
    parser.add_argument(
        "--sheung-shui-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Sheung Shui",
    )
    parser.add_argument(
        "--tseung-kwan-o-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Tseung Kwan O",
    )
    parser.add_argument(
        "--sham-shui-po-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Sham Shui Po",
    )
    parser.add_argument(
        "--shek-kong-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Shek Kong",
    )
    parser.add_argument(
        "--wetland-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Wetland Park",
    )
    parser.add_argument(
        "--ta-kwu-ling-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Ta Kwu Ling",
    )
    parser.add_argument(
        "--sha-lo-wan-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Sha Lo Wan",
    )
    parser.add_argument(
        "--airport-min",
        action="store_true",
        help="Print the latest daily minimum temperature at the airport",
    )
    parser.add_argument(
        "--yuen-long-park-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Yuen Long Park",
    )
    parser.add_argument(
        "--clear-water-bay-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Clear Water Bay",
    )
    parser.add_argument(
        "--tap-mun-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Tap Mun",
    )
    parser.add_argument(
        "--hong-kong-park-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Hong Kong Park",
    )
    parser.add_argument(
        "--ngong-ping-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Ngong Ping",
    )
    parser.add_argument(
        "--kwun-tong-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Kwun Tong",
    )
    parser.add_argument(
        "--wong-tai-sin-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Wong Tai Sin",
    )
    parser.add_argument(
        "--tsuen-wan-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Tsuen Wan",
    )
    parser.add_argument(
        "--kau-sai-chau-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Kau Sai Chau",
    )
    parser.add_argument(
        "--kadoorie-farm-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Kadoorie Farm and Botanic Garden",
    )
    parser.add_argument(
        "--the-peak-min",
        action="store_true",
        help="Print the latest daily minimum temperature at The Peak",
    )
    parser.add_argument(
        "--kat-o-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Kat O",
    )
    parser.add_argument(
        "--pak-tam-chung-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Pak Tam Chung (Tsak Yue Wu)",
    )
    parser.add_argument(
        "--beas-river-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Beas River",
    )
    parser.add_argument(
        "--kowloon-city-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Kowloon City",
    )
    parser.add_argument(
        "--new-tsing-yi-min",
        action="store_true",
        help="Print the latest daily minimum temperature at New Tsing Yi Station",
    )
    parser.add_argument(
        "--stanley-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Stanley",
    )
    parser.add_argument(
        "--shing-mun-valley-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Tsuen Wan Shing Mun Valley",
    )
    parser.add_argument(
        "--tuen-mun-home-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Tuen Mun Children and Juvenile Home",
    )
    parser.add_argument(
        "--buoy-2-min",
        action="store_true",
        help="Print the latest daily minimum temperature at Automatic Weather Buoy No.2",
    )
    parser.add_argument(
        "--tai-mo-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Tai Mo Shan",
    )
    parser.add_argument(
        "--tseung-kwan-o-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Tseung Kwan O",
    )
    parser.add_argument(
        "--sheung-shui-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Sheung Shui",
    )
    parser.add_argument(
        "--waglan-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Waglan Island",
    )
    parser.add_argument(
        "--shek-kong-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Shek Kong",
    )
    parser.add_argument(
        "--cheung-chau-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Cheung Chau",
    )
    parser.add_argument(
        "--park-max",
        action="store_true",
        help="Print the latest daily maximum temperature at King's Park",
    )
    parser.add_argument(
        "--lau-fau-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Lau Fau Shan",
    )
    parser.add_argument(
        "--sai-kung-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Sai Kung",
    )
    parser.add_argument(
        "--sha-tin-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Sha Tin",
    )
    parser.add_argument(
        "--tate-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Tate's Cairn",
    )
    parser.add_argument(
        "--wong-chuk-hang-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Wong Chuk Hang",
    )
    parser.add_argument(
        "--sham-shui-po-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Sham Shui Po",
    )
    parser.add_argument(
        "--wetland-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Wetland Park",
    )
    parser.add_argument(
        "--ta-kwu-ling-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Ta Kwu Ling",
    )
    parser.add_argument(
        "--sha-lo-wan-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Sha Lo Wan",
    )
    parser.add_argument(
        "--airport-max",
        action="store_true",
        help="Print the latest daily maximum temperature at the airport",
    )
    parser.add_argument(
        "--yuen-long-park-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Yuen Long Park",
    )
    parser.add_argument(
        "--clear-water-bay-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Clear Water Bay",
    )
    parser.add_argument(
        "--tap-mun-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Tap Mun",
    )
    parser.add_argument(
        "--hong-kong-park-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Hong Kong Park",
    )
    parser.add_argument(
        "--ngong-ping-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Ngong Ping",
    )
    parser.add_argument(
        "--kwun-tong-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Kwun Tong",
    )
    parser.add_argument(
        "--wong-tai-sin-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Wong Tai Sin",
    )
    parser.add_argument(
        "--tsuen-wan-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Tsuen Wan",
    )
    parser.add_argument(
        "--kau-sai-chau-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Kau Sai Chau",
    )
    parser.add_argument(
        "--kadoorie-farm-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Kadoorie Farm and Botanic Garden",
    )
    parser.add_argument(
        "--the-peak-max",
        action="store_true",
        help="Print the latest daily maximum temperature at The Peak",
    )
    parser.add_argument(
        "--kat-o-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Kat O",
    )
    parser.add_argument(
        "--pak-tam-chung-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Pak Tam Chung (Tsak Yue Wu)",
    )
    parser.add_argument(
        "--beas-river-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Beas River",
    )
    parser.add_argument(
        "--kowloon-city-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Kowloon City",
    )
    parser.add_argument(
        "--new-tsing-yi-max",
        action="store_true",
        help="Print the latest daily maximum temperature at New Tsing Yi Station",
    )
    parser.add_argument(
        "--stanley-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Stanley",
    )
    parser.add_argument(
        "--shing-mun-valley-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Tsuen Wan Shing Mun Valley",
    )
    parser.add_argument(
        "--tuen-mun-home-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Tuen Mun Children and Juvenile Home",
    )
    parser.add_argument(
        "--buoy-2-max",
        action="store_true",
        help="Print the latest daily maximum temperature at Automatic Weather Buoy No.2",
    )
    parser.add_argument(
        "--dew-point",
        action="store_true",
        help="Print the latest daily mean dew point at the Observatory",
    )
    parser.add_argument(
        "--park-dew",
        action="store_true",
        help="Print the latest daily mean dew point at King's Park",
    )
    parser.add_argument(
        "--cheung-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Cheung Chau",
    )
    parser.add_argument(
        "--wong-chuk-hang-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Wong Chuk Hang",
    )
    parser.add_argument(
        "--sai-kung-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Sai Kung",
    )
    parser.add_argument(
        "--sha-tin-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Sha Tin",
    )
    parser.add_argument(
        "--sheung-shui-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Sheung Shui",
    )
    parser.add_argument(
        "--waglan-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Waglan Island",
    )
    parser.add_argument(
        "--lau-fau-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Lau Fau Shan",
    )
    parser.add_argument(
        "--wetland-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Wetland Park",
    )
    parser.add_argument(
        "--ta-kwu-ling-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Ta Kwu Ling",
    )
    parser.add_argument(
        "--shek-kong-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Shek Kong",
    )
    parser.add_argument(
        "--tseung-kwan-o-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Tseung Kwan O",
    )
    parser.add_argument(
        "--tai-mo-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Tai Mo Shan",
    )
    parser.add_argument(
        "--peng-chau-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Peng Chau",
    )
    parser.add_argument(
        "--sha-lo-wan-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Sha Lo Wan",
    )
    parser.add_argument(
        "--airport-dew",
        action="store_true",
        help="Print the latest daily mean dew point at the airport",
    )
    parser.add_argument(
        "--clear-water-bay-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Clear Water Bay",
    )
    parser.add_argument(
        "--hong-kong-park-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Hong Kong Park",
    )
    parser.add_argument(
        "--tsuen-wan-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Tsuen Wan",
    )
    parser.add_argument(
        "--shau-kei-wan-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Shau Kei Wan",
    )
    parser.add_argument(
        "--kau-sai-chau-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Kau Sai Chau",
    )
    parser.add_argument(
        "--pak-tam-chung-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Pak Tam Chung (Tsak Yue Wu)",
    )
    parser.add_argument(
        "--beas-river-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Beas River",
    )
    parser.add_argument(
        "--runway-park-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Kai Tak Runway Park",
    )
    parser.add_argument(
        "--kowloon-city-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Kowloon City",
    )
    parser.add_argument(
        "--nei-lak-shan-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Nei Lak Shan",
    )
    parser.add_argument(
        "--new-tsing-yi-dew",
        action="store_true",
        help="Print the latest daily mean dew point at New Tsing Yi Station",
    )
    parser.add_argument(
        "--tate-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Tate's Cairn",
    )
    parser.add_argument(
        "--shing-mun-valley-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Tsuen Wan Shing Mun Valley",
    )
    parser.add_argument(
        "--tuen-mun-home-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Tuen Mun Children and Juvenile Home",
    )
    parser.add_argument(
        "--buoy-2-dew",
        action="store_true",
        help="Print the latest daily mean dew point at Automatic Weather Buoy No.2",
    )
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Print the latest daily mean cloud amount at the Observatory",
    )
    parser.add_argument(
        "--evaporation",
        action="store_true",
        help="Print the latest daily total evaporation at King's Park",
    )
    parser.add_argument(
        "--evapotranspiration",
        action="store_true",
        help="Print the latest monthly potential evapotranspiration at King's Park",
    )
    parser.add_argument(
        "--grass",
        action="store_true",
        help="Print yesterday's grass minimum temperature at the Observatory",
    )
    parser.add_argument(
        "--sunshine",
        action="store_true",
        help="Print yesterday's sunshine duration at King's Park",
    )
    parser.add_argument(
        "--daily-sun",
        action="store_true",
        help="Print the latest daily bright sunshine total at King's Park",
    )
    parser.add_argument(
        "--max-uv",
        action="store_true",
        help="Print yesterday's maximum UV index at King's Park",
    )
    parser.add_argument(
        "--uv-peak",
        action="store_true",
        help="Print the latest daily maximum UV index and when it occurred",
    )
    parser.add_argument(
        "--mean-uv",
        action="store_true",
        help="Print yesterday's mean UV index at King's Park",
    )
    parser.add_argument(
        "--daily-uv",
        action="store_true",
        help="Print the latest daily mean UV index (7 a.m. to 6 p.m.) at King's Park",
    )
    parser.add_argument(
        "--dose",
        action="store_true",
        help="Print yesterday's gamma dose rate at King's Park",
    )
    parser.add_argument(
        "--hourly-dose",
        action="store_true",
        help="Print the latest hourly mean ambient gamma dose rate",
    )
    parser.add_argument(
        "--accum-rain",
        action="store_true",
        help="Print accumulated rainfall from 1 January through yesterday at the Observatory",
    )
    parser.add_argument(
        "--avg-rain",
        action="store_true",
        help="Print the climatological normal of accumulated rainfall through yesterday",
    )
    parser.add_argument(
        "--radiation",
        action="store_true",
        help="Print yesterday's outdoor gamma radiation report from the Observatory",
    )
    parser.add_argument(
        "--bulletin",
        action="store_true",
        help="Print when yesterday's Observatory weather bulletin was issued",
    )
    parser.add_argument(
        "--radiation-note",
        action="store_true",
        help="Print the note on the normal outdoor radiation range",
    )
    parser.add_argument(
        "--radiation-weather",
        action="store_true",
        help="Print how outdoor radiation varies with the weather",
    )
    parser.add_argument(
        "--radiation-ground",
        action="store_true",
        help="Print how outdoor radiation varies with the ground",
    )
    parser.add_argument(
        "--radiation-provisional",
        action="store_true",
        help="Print the provisional-data note on the radiation report",
    )
    parser.add_argument(
        "-T",
        "--tomorrow",
        action="store_true",
        help="Print tomorrow's day from the 9-day forecast",
    )
    parser.add_argument(
        "-E",
        "--weekend",
        action="store_true",
        help="Print Saturday and Sunday from the 9-day forecast",
    )
    parser.add_argument(
        "--day",
        type=_day_number,
        metavar="N",
        help="Print day N of the 9-day forecast (1 is the first entry, not tomorrow)",
    )
    parser.add_argument(
        "-P",
        "--psr",
        action="store_true",
        help="Print the chance of significant rain (PSR) for each day of the 9-day forecast",
    )
    parser.add_argument(
        "--wind",
        action="store_true",
        help="Print the forecast wind from the 9-day forecast",
    )
    parser.add_argument(
        "--gust",
        action="store_true",
        help="Print the latest 10-minute wind and gust at automatic stations",
    )
    parser.add_argument(
        "--prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Waglan Island",
    )
    parser.add_argument(
        "--cheung-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Cheung Chau",
    )
    parser.add_argument(
        "--ping-chau-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Ping Chau",
    )
    parser.add_argument(
        "--tai-mo-to-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Tai Mo To",
    )
    parser.add_argument(
        "--tai-po-kau-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Tai Po Kau",
    )
    parser.add_argument(
        "--park-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at King's Park",
    )
    parser.add_argument(
        "--lau-fau-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Lau Fau Shan",
    )
    parser.add_argument(
        "--sha-lo-wan-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Sha Lo Wan",
    )
    parser.add_argument(
        "--wong-chuk-hang-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Wong Chuk Hang",
    )
    parser.add_argument(
        "--sai-kung-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Sai Kung",
    )
    parser.add_argument(
        "--tseung-kwan-o-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Tseung Kwan O",
    )
    parser.add_argument(
        "--shek-kong-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Shek Kong",
    )
    parser.add_argument(
        "--sha-tin-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Sha Tin",
    )
    parser.add_argument(
        "--ta-kwu-ling-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Ta Kwu Ling",
    )
    parser.add_argument(
        "--wetland-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Wetland Park",
    )
    parser.add_argument(
        "--tai-mo-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Tai Mo Shan",
    )
    parser.add_argument(
        "--airport-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at the airport",
    )
    parser.add_argument(
        "--kai-tak-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Kai Tak",
    )
    parser.add_argument(
        "--green-island-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Green Island",
    )
    parser.add_argument(
        "--ngong-ping-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Ngong Ping",
    )
    parser.add_argument(
        "--tai-mei-tuk-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Tai Mei Tuk",
    )
    parser.add_argument(
        "--central-pier-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Central Pier",
    )
    parser.add_argument(
        "--nei-lak-shan-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Nei Lak Shan",
    )
    parser.add_argument(
        "--buoy-2-prevailing",
        action="store_true",
        help="Print the latest daily prevailing wind direction at Automatic Weather Buoy No.2",
    )
    parser.add_argument(
        "--mean-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Waglan Island",
    )
    parser.add_argument(
        "--cheung-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Cheung Chau",
    )
    parser.add_argument(
        "--lau-fau-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Lau Fau Shan",
    )
    parser.add_argument(
        "--peng-chau-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Peng Chau",
    )
    parser.add_argument(
        "--tai-po-kau-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Tai Po Kau",
    )
    parser.add_argument(
        "--tai-mo-to-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Tai Mo To",
    )
    parser.add_argument(
        "--tai-mo-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Tai Mo Shan",
    )
    parser.add_argument(
        "--tate-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Tate's Cairn",
    )
    parser.add_argument(
        "--shek-kong-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Shek Kong",
    )
    parser.add_argument(
        "--sai-kung-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Sai Kung",
    )
    parser.add_argument(
        "--sha-tin-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Sha Tin",
    )
    parser.add_argument(
        "--wong-chuk-hang-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Wong Chuk Hang",
    )
    parser.add_argument(
        "--park-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at King's Park",
    )
    parser.add_argument(
        "--wetland-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Wetland Park",
    )
    parser.add_argument(
        "--tseung-kwan-o-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Tseung Kwan O",
    )
    parser.add_argument(
        "--ta-kwu-ling-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Ta Kwu Ling",
    )
    parser.add_argument(
        "--sha-lo-wan-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Sha Lo Wan",
    )
    parser.add_argument(
        "--ping-chau-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Ping Chau",
    )
    parser.add_argument(
        "--airport-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at the airport",
    )
    parser.add_argument(
        "--green-island-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Green Island",
    )
    parser.add_argument(
        "--ngong-ping-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Ngong Ping",
    )
    parser.add_argument(
        "--tai-mei-tuk-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Tai Mei Tuk",
    )
    parser.add_argument(
        "--lamma-island-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Lamma Island",
    )
    parser.add_argument(
        "--kai-tak-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Kai Tak",
    )
    parser.add_argument(
        "--central-pier-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Central Pier",
    )
    parser.add_argument(
        "--nei-lak-shan-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Nei Lak Shan",
    )
    parser.add_argument(
        "--buoy-2-wind",
        action="store_true",
        help="Print the latest daily mean wind speed at Automatic Weather Buoy No.2",
    )
    parser.add_argument(
        "--forecast-icon",
        action="store_true",
        help="Print the weather icon for each day of the 9-day forecast",
    )
    parser.add_argument(
        "--quake",
        action="store_true",
        help="List the latest Observatory quick earthquake message",
    )
    parser.add_argument(
        "-q",
        "--felt",
        action="store_true",
        help="Print the latest locally felt earth tremor",
    )
    parser.add_argument(
        "-V",
        "--visibility",
        action="store_true",
        help="Print the latest 10-minute mean visibility",
    )
    parser.add_argument(
        "--reduced-vis",
        action="store_true",
        help="Print the latest daily hours of reduced visibility at the airport",
    )
    parser.add_argument(
        "-I",
        "--tide",
        action="store_true",
        help="Print today's high and low tides at Quarry Bay",
    )
    parser.add_argument(
        "--tide-hour",
        action="store_true",
        help="Print today's hourly tide heights at Quarry Bay",
    )
    parser.add_argument(
        "--tide-latest",
        action="store_true",
        help="Print the latest observed tide height at tide stations",
    )
    parser.add_argument(
        "-A",
        "--aqhi",
        action="store_true",
        help="Print the current Air Quality Health Index by station",
    )
    parser.add_argument(
        "-U",
        "--sunrise",
        action="store_true",
        help="Print today's sunrise, sun transit, and sunset",
    )
    parser.add_argument(
        "-M",
        "--moon",
        action="store_true",
        help="Print today's moonrise, moon transit, and moonset",
    )
    parser.add_argument(
        "--lunar",
        action="store_true",
        help="Print today's lunar date from the Observatory calendar",
    )
    parser.add_argument(
        "-w",
        "--warnings",
        action="store_true",
        help="Print only active weather warnings",
    )
    parser.add_argument(
        "--warning-time",
        action="store_true",
        help="Print issue and expiry times for active weather warnings",
    )
    parser.add_argument(
        "-W",
        "--warning-info",
        action="store_true",
        help="Print detailed warning messages from the Observatory",
    )
    parser.add_argument(
        "-u",
        "--uv",
        action="store_true",
        help="Print the UV index from the current weather report",
    )
    parser.add_argument(
        "--fifteen-uv",
        action="store_true",
        help="Print the latest 15-minute mean UV index at King's Park",
    )
    parser.add_argument(
        "-i",
        "--icon-time",
        action="store_true",
        help="Print when the current weather icon was last updated",
    )
    parser.add_argument(
        "--icon",
        action="store_true",
        help="Print the current weather icon number and label",
    )
    parser.add_argument(
        "--current-updated",
        action="store_true",
        help="Print when the current weather report was last updated",
    )
    parser.add_argument(
        "-t",
        "--tips",
        action="store_true",
        help="Print special weather tips",
    )
    parser.add_argument(
        "--lamppost",
        action="store_true",
        help="Print the experimental reading from smart lamppost GF3637",
    )
    parser.add_argument(
        "-r",
        "--rain",
        action="store_true",
        help="Print rainfall by district from the current report",
    )
    parser.add_argument(
        "--rain-period",
        action="store_true",
        help="Print the past-hour window for district rainfall",
    )
    parser.add_argument(
        "--rain-maint",
        action="store_true",
        help="Print districts whose rainfall gauge is under maintenance",
    )
    parser.add_argument(
        "--hour-rain",
        action="store_true",
        help="Print past-hour rainfall from automatic weather stations",
    )
    parser.add_argument(
        "--hour-wettest",
        action="store_true",
        help="Print the wettest automatic station from the past hour",
    )
    parser.add_argument(
        "--hour-driest",
        action="store_true",
        help="Print the driest automatic station from the past hour",
    )
    parser.add_argument(
        "-R",
        "--wettest",
        action="store_true",
        help="Print the wettest rainfall district from the current report",
    )
    parser.add_argument(
        "-D",
        "--driest",
        action="store_true",
        help="Print the driest rainfall district from the current report",
    )
    parser.add_argument(
        "--nowcast",
        action="store_true",
        help="Print the heaviest cell in each half-hour of the rainfall nowcast",
    )
    parser.add_argument(
        "--daily-rain",
        action="store_true",
        help="Print the latest daily total rainfall at the Observatory",
    )
    parser.add_argument(
        "--lau-fau-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Lau Fau Shan",
    )
    parser.add_argument(
        "--shek-kong-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Shek Kong",
    )
    parser.add_argument(
        "--wetland-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Wetland Park",
    )
    parser.add_argument(
        "--sham-shui-po-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Sham Shui Po",
    )
    parser.add_argument(
        "--park-rain",
        action="store_true",
        help="Print the latest daily total rainfall at King's Park",
    )
    parser.add_argument(
        "--tseung-kwan-o-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tseung Kwan O",
    )
    parser.add_argument(
        "--sheung-shui-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Sheung Shui",
    )
    parser.add_argument(
        "--sha-tin-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Sha Tin",
    )
    parser.add_argument(
        "--ta-kwu-ling-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Ta Kwu Ling",
    )
    parser.add_argument(
        "--cheung-chau-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Cheung Chau",
    )
    parser.add_argument(
        "--waglan-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Waglan Island",
    )
    parser.add_argument(
        "--tate-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tate's Cairn",
    )
    parser.add_argument(
        "--peng-chau-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Peng Chau",
    )
    parser.add_argument(
        "--ping-chau-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Ping Chau",
    )
    parser.add_argument(
        "--tai-mo-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tai Mo Shan",
    )
    parser.add_argument(
        "--sha-lo-wan-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Sha Lo Wan",
    )
    parser.add_argument(
        "--airport-rain",
        action="store_true",
        help="Print the latest daily total rainfall at the airport",
    )
    parser.add_argument(
        "--green-island-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Green Island",
    )
    parser.add_argument(
        "--tsuen-wan-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tsuen Wan",
    )
    parser.add_argument(
        "--tap-mun-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tap Mun",
    )
    parser.add_argument(
        "--clear-water-bay-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Clear Water Bay",
    )
    parser.add_argument(
        "--shau-kei-wan-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Shau Kei Wan",
    )
    parser.add_argument(
        "--happy-valley-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Happy Valley",
    )
    parser.add_argument(
        "--tai-mei-tuk-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tai Mei Tuk",
    )
    parser.add_argument(
        "--kadoorie-farm-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Kadoorie Farm and Botanic Garden",
    )
    parser.add_argument(
        "--the-peak-rain",
        action="store_true",
        help="Print the latest daily total rainfall at The Peak",
    )
    parser.add_argument(
        "--pak-tam-chung-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Pak Tam Chung (Tsak Yue Wu)",
    )
    parser.add_argument(
        "--ching-pak-house-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Ching Pak House(Tsing Yi)",
    )
    parser.add_argument(
        "--kau-sai-chau-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Kau Sai Chau",
    )
    parser.add_argument(
        "--kai-tak-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Kai Tak",
    )
    parser.add_argument(
        "--sha-tau-kok-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Sha Tau Kok",
    )
    parser.add_argument(
        "--beas-river-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Beas River",
    )
    parser.add_argument(
        "--kat-o-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Kat O",
    )
    parser.add_argument(
        "--tap-shek-kok-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tap Shek Kok",
    )
    parser.add_argument(
        "--tsim-bei-tsui-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tsim Bei Tsui",
    )
    parser.add_argument(
        "--tai-mei-tuk-pump-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tai Mei Tuk Pumping Station",
    )
    parser.add_argument(
        "--ngong-ping-reservoir-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Ngong Ping Fresh Water Reservoir",
    )
    parser.add_argument(
        "--discovery-bay-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Discovery Bay",
    )
    parser.add_argument(
        "--adventist-college-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Hong Kong Adventist College(Sai Kung)",
    )
    parser.add_argument(
        "--wong-shiu-chi-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tai Po Wong Shiu Chi Secondary School",
    )
    parser.add_argument(
        "--au-tau-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Au Tau",
    )
    parser.add_argument(
        "--lok-ma-chau-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Lok Ma Chau",
    )
    parser.add_argument(
        "--lamma-island-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Lamma Island",
    )
    parser.add_argument(
        "--tuen-mun-home-rain",
        action="store_true",
        help="Print the latest daily total rainfall at Tuen Mun Children and Juvenile Home",
    )
    parser.add_argument(
        "--rainstorm",
        action="store_true",
        help="Print the rainstorm reminder from the current report",
    )
    parser.add_argument(
        "-c",
        "--cyclone",
        action="store_true",
        help="Print the tropical cyclone message from the current report",
    )
    parser.add_argument(
        "--lightning",
        action="store_true",
        help="List lightning locations from the current report",
    )
    parser.add_argument(
        "-l",
        "--strikes",
        action="store_true",
        help="Print hourly cloud-to-ground and cloud-to-cloud lightning counts",
    )
    parser.add_argument(
        "--daily-strikes",
        action="store_true",
        help="Print the latest daily cloud-to-ground lightning count over Hong Kong",
    )
    parser.add_argument(
        "--cloud-strikes",
        action="store_true",
        help="Print the latest daily cloud-to-cloud lightning count over Hong Kong",
    )
    parser.add_argument(
        "--humidity",
        action="store_true",
        help="Print humidity readings from the current report",
    )
    parser.add_argument(
        "--humidity-time",
        action="store_true",
        help="Print when the current humidity readings were recorded",
    )
    parser.add_argument(
        "--minute-humidity",
        action="store_true",
        help="Print the latest 1-minute mean humidity at automatic stations",
    )
    parser.add_argument(
        "--humidest",
        action="store_true",
        help="Print the most humid place from the current report",
    )
    parser.add_argument(
        "--least-humid",
        action="store_true",
        help="Print the least humid place from the current report",
    )
    parser.add_argument(
        "--mean-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at the Observatory",
    )
    parser.add_argument(
        "--tai-mo-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Tai Mo Shan",
    )
    parser.add_argument(
        "--waglan-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Waglan Island",
    )
    parser.add_argument(
        "--tate-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Tate's Cairn",
    )
    parser.add_argument(
        "--ta-kwu-ling-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Ta Kwu Ling",
    )
    parser.add_argument(
        "--wetland-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Wetland Park",
    )
    parser.add_argument(
        "--shek-kong-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Shek Kong",
    )
    parser.add_argument(
        "--lau-fau-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Lau Fau Shan",
    )
    parser.add_argument(
        "--park-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at King's Park",
    )
    parser.add_argument(
        "--sai-kung-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Sai Kung",
    )
    parser.add_argument(
        "--cheung-chau-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Cheung Chau",
    )
    parser.add_argument(
        "--sha-tin-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Sha Tin",
    )
    parser.add_argument(
        "--sheung-shui-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Sheung Shui",
    )
    parser.add_argument(
        "--wong-chuk-hang-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Wong Chuk Hang",
    )
    parser.add_argument(
        "--tseung-kwan-o-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Tseung Kwan O",
    )
    parser.add_argument(
        "--peng-chau-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Peng Chau",
    )
    parser.add_argument(
        "--sha-lo-wan-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Sha Lo Wan",
    )
    parser.add_argument(
        "--airport-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at the airport",
    )
    parser.add_argument(
        "--tsuen-wan-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Tsuen Wan",
    )
    parser.add_argument(
        "--hong-kong-park-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Hong Kong Park",
    )
    parser.add_argument(
        "--clear-water-bay-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Clear Water Bay",
    )
    parser.add_argument(
        "--shau-kei-wan-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Shau Kei Wan",
    )
    parser.add_argument(
        "--kau-sai-chau-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Kau Sai Chau",
    )
    parser.add_argument(
        "--pak-tam-chung-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Pak Tam Chung (Tsak Yue Wu)",
    )
    parser.add_argument(
        "--beas-river-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Beas River",
    )
    parser.add_argument(
        "--runway-park-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Kai Tak Runway Park",
    )
    parser.add_argument(
        "--kowloon-city-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Kowloon City",
    )
    parser.add_argument(
        "--nei-lak-shan-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Nei Lak Shan",
    )
    parser.add_argument(
        "--new-tsing-yi-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at New Tsing Yi Station",
    )
    parser.add_argument(
        "--shing-mun-valley-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Tsuen Wan Shing Mun Valley",
    )
    parser.add_argument(
        "--tuen-mun-home-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Tuen Mun Children and Juvenile Home",
    )
    parser.add_argument(
        "--buoy-2-humidity",
        action="store_true",
        help="Print the latest daily mean humidity at Automatic Weather Buoy No.2",
    )
    parser.add_argument(
        "--temps",
        action="store_true",
        help="Print temperatures by place from the current report",
    )
    parser.add_argument(
        "--temp-time",
        action="store_true",
        help="Print when the current temperatures were recorded",
    )
    parser.add_argument(
        "--minute-temp",
        action="store_true",
        help="Print the latest 1-minute mean temperature at automatic stations",
    )
    parser.add_argument(
        "--since-midnight",
        action="store_true",
        help="Print each station's maximum and minimum temperature since midnight",
    )
    parser.add_argument(
        "--pressure",
        action="store_true",
        help="Print the latest 1-minute mean sea level pressure at automatic stations",
    )
    parser.add_argument(
        "--mean-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at the Observatory",
    )
    parser.add_argument(
        "--park-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at King's Park",
    )
    parser.add_argument(
        "--sha-tin-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Sha Tin",
    )
    parser.add_argument(
        "--sheung-shui-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Sheung Shui",
    )
    parser.add_argument(
        "--waglan-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Waglan Island",
    )
    parser.add_argument(
        "--cheung-chau-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Cheung Chau",
    )
    parser.add_argument(
        "--lau-fau-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Lau Fau Shan",
    )
    parser.add_argument(
        "--tate-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Tate's Cairn",
    )
    parser.add_argument(
        "--wetland-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Wetland Park",
    )
    parser.add_argument(
        "--peng-chau-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Peng Chau",
    )
    parser.add_argument(
        "--tai-mo-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Tai Mo Shan",
    )
    parser.add_argument(
        "--sha-lo-wan-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Sha Lo Wan",
    )
    parser.add_argument(
        "--shek-kong-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Shek Kong",
    )
    parser.add_argument(
        "--ta-kwu-ling-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Ta Kwu Ling",
    )
    parser.add_argument(
        "--airport-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at the airport",
    )
    parser.add_argument(
        "--nei-lak-shan-pressure",
        action="store_true",
        help="Print the latest daily mean pressure at Nei Lak Shan",
    )
    parser.add_argument(
        "--minute-grass",
        action="store_true",
        help="Print the latest 1-minute mean grass temperature at automatic stations",
    )
    parser.add_argument(
        "--daily-grass",
        action="store_true",
        help="Print the latest daily grass minimum at King's Park",
    )
    parser.add_argument(
        "--obs-grass",
        action="store_true",
        help="Print the latest daily grass minimum at the Observatory",
    )
    parser.add_argument(
        "--temp-diff",
        action="store_true",
        help="Print the past 24-hour temperature change at automatic stations",
    )
    parser.add_argument(
        "--heat-index",
        action="store_true",
        help="Print the latest 10-minute mean Hong Kong Heat Index",
    )
    parser.add_argument(
        "--daily-heat",
        action="store_true",
        help="Print the latest daily maximum Hong Kong Heat Index at King's Park",
    )
    parser.add_argument(
        "--mean-heat",
        action="store_true",
        help="Print the latest daily mean Hong Kong Heat Index at King's Park",
    )
    parser.add_argument(
        "--wbgt",
        action="store_true",
        help="Print the latest 60-minute mean Wet Bulb Globe Temperature",
    )
    parser.add_argument(
        "--wet-bulb",
        action="store_true",
        help="Print the latest daily mean wet-bulb temperature at the Observatory",
    )
    parser.add_argument(
        "--airport-wet",
        action="store_true",
        help="Print the latest daily mean wet-bulb temperature at the airport",
    )
    parser.add_argument(
        "--park-wet",
        action="store_true",
        help="Print the latest daily mean wet-bulb temperature at King's Park",
    )
    parser.add_argument(
        "--sha-lo-wan-wet",
        action="store_true",
        help="Print the latest daily mean wet-bulb temperature at Sha Lo Wan",
    )
    parser.add_argument(
        "--solar",
        action="store_true",
        help="Print the latest 1-minute solar radiation at automatic stations",
    )
    parser.add_argument(
        "--global-solar",
        action="store_true",
        help="Print the latest daily global solar radiation at King's Park",
    )
    parser.add_argument(
        "--kau-sai-chau-solar",
        action="store_true",
        help="Print the latest daily global solar radiation at Kau Sai Chau",
    )
    parser.add_argument(
        "-H",
        "--hottest",
        action="store_true",
        help="Print the warmest place from the current report",
    )
    parser.add_argument(
        "-C",
        "--coldest",
        action="store_true",
        help="Print the coolest place from the current report",
    )
    parser.add_argument(
        "-O",
        "--overnight",
        action="store_true",
        help="Print the midnight-to-9am minimum temperature from the current report",
    )
    parser.add_argument(
        "-N",
        "--noon-rain",
        action="store_true",
        help="Print the midnight-to-noon rainfall note from the current report",
    )
    parser.add_argument(
        "-L",
        "--month-rain",
        action="store_true",
        help="Print last month's rainfall note from the current report",
    )
    parser.add_argument(
        "-y",
        "--year-rain",
        action="store_true",
        help="Print the January-to-last-month rainfall note from the current report",
    )
    parser.add_argument(
        "--stations",
        action="store_true",
        help="List temperature and humidity at each station",
    )
    parser.add_argument(
        "--list-places",
        action="store_true",
        help="List station names from the current report",
    )
    parser.add_argument(
        "--place",
        metavar="NAME",
        help="Print temperature and humidity for stations matching NAME",
    )
    parser.add_argument(
        "--lang",
        choices=("en", "tc", "sc"),
        default="en",
        help="Observatory response language: en, tc, or sc (default: en)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        print("error: timeout must be greater than 0", file=sys.stderr)
        return 2
    try:
        if args.warnings:
            text = format_warnings(
                fetch_warnings(timeout=args.timeout, lang=args.lang),
                as_json=args.json,
            )
        elif args.warning_time:
            warning_time = fetch_warning_time(timeout=args.timeout, lang=args.lang)
            if not warning_time.warnings:
                text = format_warning_time_miss(as_json=args.json)
            else:
                text = (
                    format_json(warning_time)
                    if args.json
                    else format_warning_time(warning_time)
                )
        elif args.warning_info:
            text = format_warning_info(
                fetch_warning_info(timeout=args.timeout, lang=args.lang),
                as_json=args.json,
            )
        elif args.forecast:
            forecast = fetch_forecast(timeout=args.timeout, lang=args.lang)
            text = format_json(forecast) if args.json else format_forecast(forecast)
        elif args.outlook:
            outlook = fetch_outlook(timeout=args.timeout, lang=args.lang)
            if outlook is None:
                text = format_outlook_miss(as_json=args.json)
            else:
                text = format_json(outlook) if args.json else format_outlook(outlook)
        elif args.coastal:
            coastal = fetch_coastal(timeout=args.timeout, lang=args.lang)
            if not coastal.areas:
                text = format_coastal_miss(as_json=args.json)
            else:
                text = format_json(coastal) if args.json else format_coastal(coastal)
        elif args.coast_report:
            coast_report = fetch_coast_report(timeout=args.timeout, lang=args.lang)
            if not coast_report.stations:
                text = format_coast_report_miss(as_json=args.json)
            else:
                text = format_json(coast_report) if args.json else format_coast_report(coast_report)
        elif args.forecast_period:
            forecast_period = fetch_forecast_period(timeout=args.timeout, lang=args.lang)
            if forecast_period is None:
                text = format_forecast_period_miss(as_json=args.json)
            else:
                text = (
                    format_json(forecast_period)
                    if args.json
                    else format_forecast_period(forecast_period)
                )
        elif args.forecast_desc:
            forecast_desc = fetch_forecast_desc(timeout=args.timeout, lang=args.lang)
            if forecast_desc is None:
                text = format_forecast_desc_miss(as_json=args.json)
            else:
                text = (
                    format_json(forecast_desc)
                    if args.json
                    else format_forecast_desc(forecast_desc)
                )
        elif args.forecast_updated:
            forecast_updated = fetch_forecast_updated(timeout=args.timeout, lang=args.lang)
            if forecast_updated is None:
                text = format_forecast_updated_miss(as_json=args.json)
            else:
                text = (
                    format_json(forecast_updated)
                    if args.json
                    else format_forecast_updated(forecast_updated)
                )
        elif args.situation:
            situation = fetch_situation(timeout=args.timeout, lang=args.lang)
            if situation is None:
                text = format_situation_miss(as_json=args.json)
            else:
                text = format_json(situation) if args.json else format_situation(situation)
        elif args.fire_danger:
            fire_danger = fetch_fire_danger(timeout=args.timeout, lang=args.lang)
            if fire_danger is None:
                text = format_fire_danger_miss(as_json=args.json)
            else:
                text = format_json(fire_danger) if args.json else format_fire_danger(fire_danger)
        elif args.tc_info:
            tc_info = fetch_tc_info(timeout=args.timeout, lang=args.lang)
            if tc_info is None:
                text = format_tc_info_miss(as_json=args.json)
            else:
                text = format_json(tc_info) if args.json else format_tc_info(tc_info)
        elif args.nine_day:
            nine_day = fetch_nine_day(timeout=args.timeout, lang=args.lang)
            text = format_json(nine_day) if args.json else format_nine_day(nine_day)
        elif args.sea_temp:
            sea_temp = fetch_sea_temp(timeout=args.timeout, lang=args.lang)
            if sea_temp is None:
                text = format_sea_temp_miss(as_json=args.json)
            else:
                text = format_json(sea_temp) if args.json else format_sea_temp(sea_temp)
        elif args.north_point_am_sea:
            north_point_am_sea = fetch_north_point_am_sea(
                timeout=args.timeout, lang=args.lang
            )
            if north_point_am_sea is None:
                text = format_north_point_am_sea_miss(as_json=args.json)
            else:
                text = (
                    format_json(north_point_am_sea)
                    if args.json
                    else format_morning_sea(north_point_am_sea)
                )
        elif args.north_point_pm_sea:
            north_point_pm_sea = fetch_north_point_pm_sea(
                timeout=args.timeout, lang=args.lang
            )
            if north_point_pm_sea is None:
                text = format_north_point_pm_sea_miss(as_json=args.json)
            else:
                text = (
                    format_json(north_point_pm_sea)
                    if args.json
                    else format_afternoon_sea(north_point_pm_sea)
                )
        elif args.soil_temp:
            soil_temp = fetch_soil_temp(timeout=args.timeout, lang=args.lang)
            if soil_temp is None:
                text = format_soil_temp_miss(as_json=args.json)
            else:
                text = format_json(soil_temp) if args.json else format_soil_temp(soil_temp)
        elif args.nine_situation:
            nine_situation = fetch_nine_situation(timeout=args.timeout, lang=args.lang)
            if nine_situation is None:
                text = format_nine_situation_miss(as_json=args.json)
            else:
                text = (
                    format_json(nine_situation)
                    if args.json
                    else format_nine_situation(nine_situation)
                )
        elif args.nine_updated:
            nine_updated = fetch_nine_updated(timeout=args.timeout, lang=args.lang)
            if nine_updated is None:
                text = format_nine_updated_miss(as_json=args.json)
            else:
                text = format_json(nine_updated) if args.json else format_nine_updated(nine_updated)
        elif args.nine_weather:
            nine_weather = fetch_nine_weather(timeout=args.timeout, lang=args.lang)
            if not nine_weather.days:
                text = format_nine_weather_miss(as_json=args.json)
            else:
                text = format_json(nine_weather) if args.json else format_nine_weather(nine_weather)
        elif args.nine_temp:
            nine_temp = fetch_nine_temp(timeout=args.timeout, lang=args.lang)
            if not nine_temp.days:
                text = format_nine_temp_miss(as_json=args.json)
            else:
                text = format_json(nine_temp) if args.json else format_nine_temp(nine_temp)
        elif args.nine_humidity:
            nine_humidity = fetch_nine_humidity(timeout=args.timeout, lang=args.lang)
            if not nine_humidity.days:
                text = format_nine_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(nine_humidity) if args.json else format_nine_humidity(nine_humidity)
                )
        elif args.today:
            today = fetch_today(timeout=args.timeout, lang=args.lang)
            if today is None:
                text = format_today_miss(as_json=args.json)
            else:
                text = (
                    format_json(today)
                    if args.json
                    else format_tomorrow(today, title="Hong Kong forecast for today")
                )
        elif args.yesterday:
            yesterday = fetch_yesterday(timeout=args.timeout, lang=args.lang)
            if yesterday is None:
                text = format_yesterday_miss(as_json=args.json)
            else:
                text = format_json(yesterday) if args.json else format_yesterday(yesterday)
        elif args.mean_temp:
            mean_temp = fetch_mean_temp(timeout=args.timeout, lang=args.lang)
            if mean_temp is None:
                text = format_mean_temp_miss(as_json=args.json)
            else:
                text = format_json(mean_temp) if args.json else format_mean_temp(mean_temp)
        elif args.tai_mo_temp:
            tai_mo_temp = fetch_tai_mo_temp(timeout=args.timeout, lang=args.lang)
            if tai_mo_temp is None:
                text = format_tai_mo_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mo_temp) if args.json else format_tai_mo_temp(tai_mo_temp)
                )
        elif args.tate_temp:
            tate_temp = fetch_tate_temp(timeout=args.timeout, lang=args.lang)
            if tate_temp is None:
                text = format_tate_temp_miss(as_json=args.json)
            else:
                text = format_json(tate_temp) if args.json else format_tai_mo_temp(tate_temp)
        elif args.sai_kung_temp:
            sai_kung_temp = fetch_sai_kung_temp(timeout=args.timeout, lang=args.lang)
            if sai_kung_temp is None:
                text = format_sai_kung_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(sai_kung_temp)
                    if args.json
                    else format_tai_mo_temp(sai_kung_temp)
                )
        elif args.sha_tin_temp:
            sha_tin_temp = fetch_sha_tin_temp(timeout=args.timeout, lang=args.lang)
            if sha_tin_temp is None:
                text = format_sha_tin_temp_miss(as_json=args.json)
            else:
                text = format_json(sha_tin_temp) if args.json else format_tai_mo_temp(sha_tin_temp)
        elif args.sheung_shui_temp:
            sheung_shui_temp = fetch_sheung_shui_temp(timeout=args.timeout, lang=args.lang)
            if sheung_shui_temp is None:
                text = format_sheung_shui_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(sheung_shui_temp)
                    if args.json
                    else format_tai_mo_temp(sheung_shui_temp)
                )
        elif args.wong_chuk_hang_temp:
            wong_chuk_hang_temp = fetch_wong_chuk_hang_temp(
                timeout=args.timeout, lang=args.lang
            )
            if wong_chuk_hang_temp is None:
                text = format_wong_chuk_hang_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_chuk_hang_temp)
                    if args.json
                    else format_tai_mo_temp(wong_chuk_hang_temp)
                )
        elif args.lau_fau_temp:
            lau_fau_temp = fetch_lau_fau_temp(timeout=args.timeout, lang=args.lang)
            if lau_fau_temp is None:
                text = format_lau_fau_temp_miss(as_json=args.json)
            else:
                text = format_json(lau_fau_temp) if args.json else format_tai_mo_temp(lau_fau_temp)
        elif args.tseung_kwan_o_temp:
            tseung_kwan_o_temp = fetch_tseung_kwan_o_temp(timeout=args.timeout, lang=args.lang)
            if tseung_kwan_o_temp is None:
                text = format_tseung_kwan_o_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(tseung_kwan_o_temp)
                    if args.json
                    else format_tai_mo_temp(tseung_kwan_o_temp)
                )
        elif args.sham_shui_po_temp:
            sham_shui_po_temp = fetch_sham_shui_po_temp(timeout=args.timeout, lang=args.lang)
            if sham_shui_po_temp is None:
                text = format_sham_shui_po_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(sham_shui_po_temp)
                    if args.json
                    else format_tai_mo_temp(sham_shui_po_temp)
                )
        elif args.shek_kong_temp:
            shek_kong_temp = fetch_shek_kong_temp(timeout=args.timeout, lang=args.lang)
            if shek_kong_temp is None:
                text = format_shek_kong_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(shek_kong_temp)
                    if args.json
                    else format_tai_mo_temp(shek_kong_temp)
                )
        elif args.wetland_temp:
            wetland_temp = fetch_wetland_temp(timeout=args.timeout, lang=args.lang)
            if wetland_temp is None:
                text = format_wetland_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(wetland_temp)
                    if args.json
                    else format_tai_mo_temp(wetland_temp)
                )
        elif args.ta_kwu_ling_temp:
            ta_kwu_ling_temp = fetch_ta_kwu_ling_temp(timeout=args.timeout, lang=args.lang)
            if ta_kwu_ling_temp is None:
                text = format_ta_kwu_ling_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(ta_kwu_ling_temp)
                    if args.json
                    else format_tai_mo_temp(ta_kwu_ling_temp)
                )
        elif args.peng_chau_temp:
            peng_chau_temp = fetch_peng_chau_temp(timeout=args.timeout, lang=args.lang)
            if peng_chau_temp is None:
                text = format_peng_chau_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(peng_chau_temp)
                    if args.json
                    else format_tai_mo_temp(peng_chau_temp)
                )
        elif args.park_temp:
            park_temp = fetch_park_temp(timeout=args.timeout, lang=args.lang)
            if park_temp is None:
                text = format_park_temp_miss(as_json=args.json)
            else:
                text = format_json(park_temp) if args.json else format_tai_mo_temp(park_temp)
        elif args.cheung_chau_temp:
            cheung_chau_temp = fetch_cheung_chau_temp(timeout=args.timeout, lang=args.lang)
            if cheung_chau_temp is None:
                text = format_cheung_chau_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(cheung_chau_temp)
                    if args.json
                    else format_tai_mo_temp(cheung_chau_temp)
                )
        elif args.waglan_temp:
            waglan_temp = fetch_waglan_temp(timeout=args.timeout, lang=args.lang)
            if waglan_temp is None:
                text = format_waglan_temp_miss(as_json=args.json)
            else:
                text = format_json(waglan_temp) if args.json else format_tai_mo_temp(waglan_temp)
        elif args.ping_chau_temp:
            ping_chau_temp = fetch_ping_chau_temp(timeout=args.timeout, lang=args.lang)
            if ping_chau_temp is None:
                text = format_ping_chau_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(ping_chau_temp)
                    if args.json
                    else format_tai_mo_temp(ping_chau_temp)
                )
        elif args.sha_lo_wan_temp:
            sha_lo_wan_temp = fetch_sha_lo_wan_temp(timeout=args.timeout, lang=args.lang)
            if sha_lo_wan_temp is None:
                text = format_sha_lo_wan_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_lo_wan_temp)
                    if args.json
                    else format_tai_mo_temp(sha_lo_wan_temp)
                )
        elif args.airport_temp:
            airport_temp = fetch_airport_temp(timeout=args.timeout, lang=args.lang)
            if airport_temp is None:
                text = format_airport_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(airport_temp)
                    if args.json
                    else format_tai_mo_temp(airport_temp)
                )
        elif args.clear_water_bay_temp:
            clear_water_bay_temp = fetch_clear_water_bay_temp(
                timeout=args.timeout, lang=args.lang
            )
            if clear_water_bay_temp is None:
                text = format_clear_water_bay_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(clear_water_bay_temp)
                    if args.json
                    else format_tai_mo_temp(clear_water_bay_temp)
                )
        elif args.hong_kong_park_temp:
            hong_kong_park_temp = fetch_hong_kong_park_temp(
                timeout=args.timeout, lang=args.lang
            )
            if hong_kong_park_temp is None:
                text = format_hong_kong_park_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(hong_kong_park_temp)
                    if args.json
                    else format_tai_mo_temp(hong_kong_park_temp)
                )
        elif args.ngong_ping_temp:
            ngong_ping_temp = fetch_ngong_ping_temp(timeout=args.timeout, lang=args.lang)
            if ngong_ping_temp is None:
                text = format_ngong_ping_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(ngong_ping_temp)
                    if args.json
                    else format_tai_mo_temp(ngong_ping_temp)
                )
        elif args.kwun_tong_temp:
            kwun_tong_temp = fetch_kwun_tong_temp(timeout=args.timeout, lang=args.lang)
            if kwun_tong_temp is None:
                text = format_kwun_tong_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(kwun_tong_temp)
                    if args.json
                    else format_tai_mo_temp(kwun_tong_temp)
                )
        elif args.wong_tai_sin_temp:
            wong_tai_sin_temp = fetch_wong_tai_sin_temp(
                timeout=args.timeout, lang=args.lang
            )
            if wong_tai_sin_temp is None:
                text = format_wong_tai_sin_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_tai_sin_temp)
                    if args.json
                    else format_tai_mo_temp(wong_tai_sin_temp)
                )
        elif args.tsuen_wan_temp:
            tsuen_wan_temp = fetch_tsuen_wan_temp(timeout=args.timeout, lang=args.lang)
            if tsuen_wan_temp is None:
                text = format_tsuen_wan_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(tsuen_wan_temp)
                    if args.json
                    else format_tai_mo_temp(tsuen_wan_temp)
                )
        elif args.yuen_long_park_temp:
            yuen_long_park_temp = fetch_yuen_long_park_temp(
                timeout=args.timeout, lang=args.lang
            )
            if yuen_long_park_temp is None:
                text = format_yuen_long_park_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(yuen_long_park_temp)
                    if args.json
                    else format_tai_mo_temp(yuen_long_park_temp)
                )
        elif args.tap_mun_temp:
            tap_mun_temp = fetch_tap_mun_temp(timeout=args.timeout, lang=args.lang)
            if tap_mun_temp is None:
                text = format_tap_mun_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(tap_mun_temp)
                    if args.json
                    else format_tai_mo_temp(tap_mun_temp)
                )
        elif args.shau_kei_wan_temp:
            shau_kei_wan_temp = fetch_shau_kei_wan_temp(
                timeout=args.timeout, lang=args.lang
            )
            if shau_kei_wan_temp is None:
                text = format_shau_kei_wan_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(shau_kei_wan_temp)
                    if args.json
                    else format_tai_mo_temp(shau_kei_wan_temp)
                )
        elif args.happy_valley_temp:
            happy_valley_temp = fetch_happy_valley_temp(
                timeout=args.timeout, lang=args.lang
            )
            if happy_valley_temp is None:
                text = format_happy_valley_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(happy_valley_temp)
                    if args.json
                    else format_tai_mo_temp(happy_valley_temp)
                )
        elif args.tai_mei_tuk_temp:
            tai_mei_tuk_temp = fetch_tai_mei_tuk_temp(
                timeout=args.timeout, lang=args.lang
            )
            if tai_mei_tuk_temp is None:
                text = format_tai_mei_tuk_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mei_tuk_temp)
                    if args.json
                    else format_tai_mo_temp(tai_mei_tuk_temp)
                )
        elif args.kau_sai_chau_temp:
            kau_sai_chau_temp = fetch_kau_sai_chau_temp(
                timeout=args.timeout, lang=args.lang
            )
            if kau_sai_chau_temp is None:
                text = format_kau_sai_chau_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(kau_sai_chau_temp)
                    if args.json
                    else format_tai_mo_temp(kau_sai_chau_temp)
                )
        elif args.kadoorie_farm_temp:
            kadoorie_farm_temp = fetch_kadoorie_farm_temp(
                timeout=args.timeout, lang=args.lang
            )
            if kadoorie_farm_temp is None:
                text = format_kadoorie_farm_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(kadoorie_farm_temp)
                    if args.json
                    else format_tai_mo_temp(kadoorie_farm_temp)
                )
        elif args.the_peak_temp:
            the_peak_temp = fetch_the_peak_temp(timeout=args.timeout, lang=args.lang)
            if the_peak_temp is None:
                text = format_the_peak_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(the_peak_temp)
                    if args.json
                    else format_tai_mo_temp(the_peak_temp)
                )
        elif args.kat_o_temp:
            kat_o_temp = fetch_kat_o_temp(timeout=args.timeout, lang=args.lang)
            if kat_o_temp is None:
                text = format_kat_o_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(kat_o_temp)
                    if args.json
                    else format_tai_mo_temp(kat_o_temp)
                )
        elif args.pak_tam_chung_temp:
            pak_tam_chung_temp = fetch_pak_tam_chung_temp(
                timeout=args.timeout, lang=args.lang
            )
            if pak_tam_chung_temp is None:
                text = format_pak_tam_chung_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(pak_tam_chung_temp)
                    if args.json
                    else format_tai_mo_temp(pak_tam_chung_temp)
                )
        elif args.beas_river_temp:
            beas_river_temp = fetch_beas_river_temp(timeout=args.timeout, lang=args.lang)
            if beas_river_temp is None:
                text = format_beas_river_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(beas_river_temp)
                    if args.json
                    else format_tai_mo_temp(beas_river_temp)
                )
        elif args.bluff_head_temp:
            bluff_head_temp = fetch_bluff_head_temp(timeout=args.timeout, lang=args.lang)
            if bluff_head_temp is None:
                text = format_bluff_head_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(bluff_head_temp)
                    if args.json
                    else format_tai_mo_temp(bluff_head_temp)
                )
        elif args.runway_park_temp:
            runway_park_temp = fetch_runway_park_temp(
                timeout=args.timeout, lang=args.lang
            )
            if runway_park_temp is None:
                text = format_runway_park_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(runway_park_temp)
                    if args.json
                    else format_tai_mo_temp(runway_park_temp)
                )
        elif args.kowloon_city_temp:
            kowloon_city_temp = fetch_kowloon_city_temp(
                timeout=args.timeout, lang=args.lang
            )
            if kowloon_city_temp is None:
                text = format_kowloon_city_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(kowloon_city_temp)
                    if args.json
                    else format_tai_mo_temp(kowloon_city_temp)
                )
        elif args.nei_lak_shan_temp:
            nei_lak_shan_temp = fetch_nei_lak_shan_temp(
                timeout=args.timeout, lang=args.lang
            )
            if nei_lak_shan_temp is None:
                text = format_nei_lak_shan_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(nei_lak_shan_temp)
                    if args.json
                    else format_tai_mo_temp(nei_lak_shan_temp)
                )
        elif args.new_tsing_yi_temp:
            new_tsing_yi_temp = fetch_new_tsing_yi_temp(
                timeout=args.timeout, lang=args.lang
            )
            if new_tsing_yi_temp is None:
                text = format_new_tsing_yi_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(new_tsing_yi_temp)
                    if args.json
                    else format_tai_mo_temp(new_tsing_yi_temp)
                )
        elif args.stanley_temp:
            stanley_temp = fetch_stanley_temp(timeout=args.timeout, lang=args.lang)
            if stanley_temp is None:
                text = format_stanley_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(stanley_temp)
                    if args.json
                    else format_tai_mo_temp(stanley_temp)
                )
        elif args.shing_mun_valley_temp:
            shing_mun_valley_temp = fetch_shing_mun_valley_temp(
                timeout=args.timeout, lang=args.lang
            )
            if shing_mun_valley_temp is None:
                text = format_shing_mun_valley_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(shing_mun_valley_temp)
                    if args.json
                    else format_tai_mo_temp(shing_mun_valley_temp)
                )
        elif args.tuen_mun_home_temp:
            tuen_mun_home_temp = fetch_tuen_mun_home_temp(
                timeout=args.timeout, lang=args.lang
            )
            if tuen_mun_home_temp is None:
                text = format_tuen_mun_home_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(tuen_mun_home_temp)
                    if args.json
                    else format_tai_mo_temp(tuen_mun_home_temp)
                )
        elif args.buoy_2_temp:
            buoy_2_temp = fetch_buoy_2_temp(timeout=args.timeout, lang=args.lang)
            if buoy_2_temp is None:
                text = format_buoy_2_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(buoy_2_temp)
                    if args.json
                    else format_tai_mo_temp(buoy_2_temp)
                )
        elif args.buoy_8_temp:
            buoy_8_temp = fetch_buoy_8_temp(timeout=args.timeout, lang=args.lang)
            if buoy_8_temp is None:
                text = format_buoy_8_temp_miss(as_json=args.json)
            else:
                text = (
                    format_json(buoy_8_temp)
                    if args.json
                    else format_tai_mo_temp(buoy_8_temp)
                )
        elif args.max_temp:
            max_temp = fetch_max_temp(timeout=args.timeout, lang=args.lang)
            if max_temp is None:
                text = format_max_temp_miss(as_json=args.json)
            else:
                text = format_json(max_temp) if args.json else format_max_temp(max_temp)
        elif args.min_temp:
            min_temp = fetch_min_temp(timeout=args.timeout, lang=args.lang)
            if min_temp is None:
                text = format_min_temp_miss(as_json=args.json)
            else:
                text = format_json(min_temp) if args.json else format_min_temp(min_temp)
        elif args.tai_mo_min:
            tai_mo_min = fetch_tai_mo_min(timeout=args.timeout, lang=args.lang)
            if tai_mo_min is None:
                text = format_tai_mo_min_miss(as_json=args.json)
            else:
                text = format_json(tai_mo_min) if args.json else format_tai_mo_min(tai_mo_min)
        elif args.tate_min:
            tate_min = fetch_tate_min(timeout=args.timeout, lang=args.lang)
            if tate_min is None:
                text = format_tate_min_miss(as_json=args.json)
            else:
                text = format_json(tate_min) if args.json else format_tai_mo_min(tate_min)
        elif args.sai_kung_min:
            sai_kung_min = fetch_sai_kung_min(timeout=args.timeout, lang=args.lang)
            if sai_kung_min is None:
                text = format_sai_kung_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(sai_kung_min)
                    if args.json
                    else format_tai_mo_min(sai_kung_min)
                )
        elif args.wong_chuk_hang_min:
            wong_chuk_hang_min = fetch_wong_chuk_hang_min(timeout=args.timeout, lang=args.lang)
            if wong_chuk_hang_min is None:
                text = format_wong_chuk_hang_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_chuk_hang_min)
                    if args.json
                    else format_tai_mo_min(wong_chuk_hang_min)
                )
        elif args.waglan_min:
            waglan_min = fetch_waglan_min(timeout=args.timeout, lang=args.lang)
            if waglan_min is None:
                text = format_waglan_min_miss(as_json=args.json)
            else:
                text = format_json(waglan_min) if args.json else format_tai_mo_min(waglan_min)
        elif args.sha_tin_min:
            sha_tin_min = fetch_sha_tin_min(timeout=args.timeout, lang=args.lang)
            if sha_tin_min is None:
                text = format_sha_tin_min_miss(as_json=args.json)
            else:
                text = format_json(sha_tin_min) if args.json else format_tai_mo_min(sha_tin_min)
        elif args.cheung_chau_min:
            cheung_chau_min = fetch_cheung_chau_min(timeout=args.timeout, lang=args.lang)
            if cheung_chau_min is None:
                text = format_cheung_chau_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(cheung_chau_min)
                    if args.json
                    else format_tai_mo_min(cheung_chau_min)
                )
        elif args.park_min:
            park_min = fetch_park_min(timeout=args.timeout, lang=args.lang)
            if park_min is None:
                text = format_park_min_miss(as_json=args.json)
            else:
                text = format_json(park_min) if args.json else format_tai_mo_min(park_min)
        elif args.lau_fau_min:
            lau_fau_min = fetch_lau_fau_min(timeout=args.timeout, lang=args.lang)
            if lau_fau_min is None:
                text = format_lau_fau_min_miss(as_json=args.json)
            else:
                text = format_json(lau_fau_min) if args.json else format_tai_mo_min(lau_fau_min)
        elif args.sheung_shui_min:
            sheung_shui_min = fetch_sheung_shui_min(timeout=args.timeout, lang=args.lang)
            if sheung_shui_min is None:
                text = format_sheung_shui_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(sheung_shui_min)
                    if args.json
                    else format_tai_mo_min(sheung_shui_min)
                )
        elif args.tseung_kwan_o_min:
            tseung_kwan_o_min = fetch_tseung_kwan_o_min(timeout=args.timeout, lang=args.lang)
            if tseung_kwan_o_min is None:
                text = format_tseung_kwan_o_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(tseung_kwan_o_min)
                    if args.json
                    else format_tai_mo_min(tseung_kwan_o_min)
                )
        elif args.sham_shui_po_min:
            sham_shui_po_min = fetch_sham_shui_po_min(timeout=args.timeout, lang=args.lang)
            if sham_shui_po_min is None:
                text = format_sham_shui_po_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(sham_shui_po_min)
                    if args.json
                    else format_tai_mo_min(sham_shui_po_min)
                )
        elif args.shek_kong_min:
            shek_kong_min = fetch_shek_kong_min(timeout=args.timeout, lang=args.lang)
            if shek_kong_min is None:
                text = format_shek_kong_min_miss(as_json=args.json)
            else:
                text = format_json(shek_kong_min) if args.json else format_tai_mo_min(shek_kong_min)
        elif args.wetland_min:
            wetland_min = fetch_wetland_min(timeout=args.timeout, lang=args.lang)
            if wetland_min is None:
                text = format_wetland_min_miss(as_json=args.json)
            else:
                text = format_json(wetland_min) if args.json else format_tai_mo_min(wetland_min)
        elif args.ta_kwu_ling_min:
            ta_kwu_ling_min = fetch_ta_kwu_ling_min(timeout=args.timeout, lang=args.lang)
            if ta_kwu_ling_min is None:
                text = format_ta_kwu_ling_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(ta_kwu_ling_min)
                    if args.json
                    else format_tai_mo_min(ta_kwu_ling_min)
                )
        elif args.sha_lo_wan_min:
            sha_lo_wan_min = fetch_sha_lo_wan_min(timeout=args.timeout, lang=args.lang)
            if sha_lo_wan_min is None:
                text = format_sha_lo_wan_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_lo_wan_min)
                    if args.json
                    else format_tai_mo_min(sha_lo_wan_min)
                )
        elif args.airport_min:
            airport_min = fetch_airport_min(timeout=args.timeout, lang=args.lang)
            if airport_min is None:
                text = format_airport_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(airport_min) if args.json else format_tai_mo_min(airport_min)
                )
        elif args.yuen_long_park_min:
            yuen_long_park_min = fetch_yuen_long_park_min(
                timeout=args.timeout, lang=args.lang
            )
            if yuen_long_park_min is None:
                text = format_yuen_long_park_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(yuen_long_park_min)
                    if args.json
                    else format_tai_mo_min(yuen_long_park_min)
                )
        elif args.clear_water_bay_min:
            clear_water_bay_min = fetch_clear_water_bay_min(
                timeout=args.timeout, lang=args.lang
            )
            if clear_water_bay_min is None:
                text = format_clear_water_bay_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(clear_water_bay_min)
                    if args.json
                    else format_tai_mo_min(clear_water_bay_min)
                )
        elif args.tap_mun_min:
            tap_mun_min = fetch_tap_mun_min(timeout=args.timeout, lang=args.lang)
            if tap_mun_min is None:
                text = format_tap_mun_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(tap_mun_min)
                    if args.json
                    else format_tai_mo_min(tap_mun_min)
                )
        elif args.hong_kong_park_min:
            hong_kong_park_min = fetch_hong_kong_park_min(
                timeout=args.timeout, lang=args.lang
            )
            if hong_kong_park_min is None:
                text = format_hong_kong_park_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(hong_kong_park_min)
                    if args.json
                    else format_tai_mo_min(hong_kong_park_min)
                )
        elif args.ngong_ping_min:
            ngong_ping_min = fetch_ngong_ping_min(timeout=args.timeout, lang=args.lang)
            if ngong_ping_min is None:
                text = format_ngong_ping_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(ngong_ping_min)
                    if args.json
                    else format_tai_mo_min(ngong_ping_min)
                )
        elif args.kwun_tong_min:
            kwun_tong_min = fetch_kwun_tong_min(timeout=args.timeout, lang=args.lang)
            if kwun_tong_min is None:
                text = format_kwun_tong_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(kwun_tong_min)
                    if args.json
                    else format_tai_mo_min(kwun_tong_min)
                )
        elif args.wong_tai_sin_min:
            wong_tai_sin_min = fetch_wong_tai_sin_min(
                timeout=args.timeout, lang=args.lang
            )
            if wong_tai_sin_min is None:
                text = format_wong_tai_sin_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_tai_sin_min)
                    if args.json
                    else format_tai_mo_min(wong_tai_sin_min)
                )
        elif args.tsuen_wan_min:
            tsuen_wan_min = fetch_tsuen_wan_min(timeout=args.timeout, lang=args.lang)
            if tsuen_wan_min is None:
                text = format_tsuen_wan_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(tsuen_wan_min)
                    if args.json
                    else format_tai_mo_min(tsuen_wan_min)
                )
        elif args.kau_sai_chau_min:
            kau_sai_chau_min = fetch_kau_sai_chau_min(
                timeout=args.timeout, lang=args.lang
            )
            if kau_sai_chau_min is None:
                text = format_kau_sai_chau_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(kau_sai_chau_min)
                    if args.json
                    else format_tai_mo_min(kau_sai_chau_min)
                )
        elif args.kadoorie_farm_min:
            kadoorie_farm_min = fetch_kadoorie_farm_min(
                timeout=args.timeout, lang=args.lang
            )
            if kadoorie_farm_min is None:
                text = format_kadoorie_farm_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(kadoorie_farm_min)
                    if args.json
                    else format_tai_mo_min(kadoorie_farm_min)
                )
        elif args.the_peak_min:
            the_peak_min = fetch_the_peak_min(timeout=args.timeout, lang=args.lang)
            if the_peak_min is None:
                text = format_the_peak_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(the_peak_min)
                    if args.json
                    else format_tai_mo_min(the_peak_min)
                )
        elif args.kat_o_min:
            kat_o_min = fetch_kat_o_min(timeout=args.timeout, lang=args.lang)
            if kat_o_min is None:
                text = format_kat_o_min_miss(as_json=args.json)
            else:
                text = format_json(kat_o_min) if args.json else format_tai_mo_min(kat_o_min)
        elif args.pak_tam_chung_min:
            pak_tam_chung_min = fetch_pak_tam_chung_min(
                timeout=args.timeout, lang=args.lang
            )
            if pak_tam_chung_min is None:
                text = format_pak_tam_chung_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(pak_tam_chung_min)
                    if args.json
                    else format_tai_mo_min(pak_tam_chung_min)
                )
        elif args.beas_river_min:
            beas_river_min = fetch_beas_river_min(timeout=args.timeout, lang=args.lang)
            if beas_river_min is None:
                text = format_beas_river_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(beas_river_min)
                    if args.json
                    else format_tai_mo_min(beas_river_min)
                )
        elif args.kowloon_city_min:
            kowloon_city_min = fetch_kowloon_city_min(
                timeout=args.timeout, lang=args.lang
            )
            if kowloon_city_min is None:
                text = format_kowloon_city_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(kowloon_city_min)
                    if args.json
                    else format_tai_mo_min(kowloon_city_min)
                )
        elif args.new_tsing_yi_min:
            new_tsing_yi_min = fetch_new_tsing_yi_min(
                timeout=args.timeout, lang=args.lang
            )
            if new_tsing_yi_min is None:
                text = format_new_tsing_yi_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(new_tsing_yi_min)
                    if args.json
                    else format_tai_mo_min(new_tsing_yi_min)
                )
        elif args.stanley_min:
            stanley_min = fetch_stanley_min(timeout=args.timeout, lang=args.lang)
            if stanley_min is None:
                text = format_stanley_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(stanley_min)
                    if args.json
                    else format_tai_mo_min(stanley_min)
                )
        elif args.shing_mun_valley_min:
            shing_mun_valley_min = fetch_shing_mun_valley_min(
                timeout=args.timeout, lang=args.lang
            )
            if shing_mun_valley_min is None:
                text = format_shing_mun_valley_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(shing_mun_valley_min)
                    if args.json
                    else format_tai_mo_min(shing_mun_valley_min)
                )
        elif args.tuen_mun_home_min:
            tuen_mun_home_min = fetch_tuen_mun_home_min(
                timeout=args.timeout, lang=args.lang
            )
            if tuen_mun_home_min is None:
                text = format_tuen_mun_home_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(tuen_mun_home_min)
                    if args.json
                    else format_tai_mo_min(tuen_mun_home_min)
                )
        elif args.buoy_2_min:
            buoy_2_min = fetch_buoy_2_min(timeout=args.timeout, lang=args.lang)
            if buoy_2_min is None:
                text = format_buoy_2_min_miss(as_json=args.json)
            else:
                text = (
                    format_json(buoy_2_min)
                    if args.json
                    else format_tai_mo_min(buoy_2_min)
                )
        elif args.tai_mo_max:
            tai_mo_max = fetch_tai_mo_max(timeout=args.timeout, lang=args.lang)
            if tai_mo_max is None:
                text = format_tai_mo_max_miss(as_json=args.json)
            else:
                text = format_json(tai_mo_max) if args.json else format_tai_mo_max(tai_mo_max)
        elif args.tseung_kwan_o_max:
            tseung_kwan_o_max = fetch_tseung_kwan_o_max(timeout=args.timeout, lang=args.lang)
            if tseung_kwan_o_max is None:
                text = format_tseung_kwan_o_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(tseung_kwan_o_max)
                    if args.json
                    else format_tai_mo_max(tseung_kwan_o_max)
                )
        elif args.sheung_shui_max:
            sheung_shui_max = fetch_sheung_shui_max(timeout=args.timeout, lang=args.lang)
            if sheung_shui_max is None:
                text = format_sheung_shui_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(sheung_shui_max)
                    if args.json
                    else format_tai_mo_max(sheung_shui_max)
                )
        elif args.waglan_max:
            waglan_max = fetch_waglan_max(timeout=args.timeout, lang=args.lang)
            if waglan_max is None:
                text = format_waglan_max_miss(as_json=args.json)
            else:
                text = format_json(waglan_max) if args.json else format_tai_mo_max(waglan_max)
        elif args.shek_kong_max:
            shek_kong_max = fetch_shek_kong_max(timeout=args.timeout, lang=args.lang)
            if shek_kong_max is None:
                text = format_shek_kong_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(shek_kong_max)
                    if args.json
                    else format_tai_mo_max(shek_kong_max)
                )
        elif args.cheung_chau_max:
            cheung_chau_max = fetch_cheung_chau_max(timeout=args.timeout, lang=args.lang)
            if cheung_chau_max is None:
                text = format_cheung_chau_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(cheung_chau_max)
                    if args.json
                    else format_tai_mo_max(cheung_chau_max)
                )
        elif args.park_max:
            park_max = fetch_park_max(timeout=args.timeout, lang=args.lang)
            if park_max is None:
                text = format_park_max_miss(as_json=args.json)
            else:
                text = format_json(park_max) if args.json else format_tai_mo_max(park_max)
        elif args.lau_fau_max:
            lau_fau_max = fetch_lau_fau_max(timeout=args.timeout, lang=args.lang)
            if lau_fau_max is None:
                text = format_lau_fau_max_miss(as_json=args.json)
            else:
                text = format_json(lau_fau_max) if args.json else format_tai_mo_max(lau_fau_max)
        elif args.sai_kung_max:
            sai_kung_max = fetch_sai_kung_max(timeout=args.timeout, lang=args.lang)
            if sai_kung_max is None:
                text = format_sai_kung_max_miss(as_json=args.json)
            else:
                text = format_json(sai_kung_max) if args.json else format_tai_mo_max(sai_kung_max)
        elif args.sha_tin_max:
            sha_tin_max = fetch_sha_tin_max(timeout=args.timeout, lang=args.lang)
            if sha_tin_max is None:
                text = format_sha_tin_max_miss(as_json=args.json)
            else:
                text = format_json(sha_tin_max) if args.json else format_tai_mo_max(sha_tin_max)
        elif args.tate_max:
            tate_max = fetch_tate_max(timeout=args.timeout, lang=args.lang)
            if tate_max is None:
                text = format_tate_max_miss(as_json=args.json)
            else:
                text = format_json(tate_max) if args.json else format_tai_mo_max(tate_max)
        elif args.wong_chuk_hang_max:
            wong_chuk_hang_max = fetch_wong_chuk_hang_max(
                timeout=args.timeout, lang=args.lang
            )
            if wong_chuk_hang_max is None:
                text = format_wong_chuk_hang_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_chuk_hang_max)
                    if args.json
                    else format_tai_mo_max(wong_chuk_hang_max)
                )
        elif args.sham_shui_po_max:
            sham_shui_po_max = fetch_sham_shui_po_max(timeout=args.timeout, lang=args.lang)
            if sham_shui_po_max is None:
                text = format_sham_shui_po_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(sham_shui_po_max)
                    if args.json
                    else format_tai_mo_max(sham_shui_po_max)
                )
        elif args.wetland_max:
            wetland_max = fetch_wetland_max(timeout=args.timeout, lang=args.lang)
            if wetland_max is None:
                text = format_wetland_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(wetland_max)
                    if args.json
                    else format_tai_mo_max(wetland_max)
                )
        elif args.ta_kwu_ling_max:
            ta_kwu_ling_max = fetch_ta_kwu_ling_max(timeout=args.timeout, lang=args.lang)
            if ta_kwu_ling_max is None:
                text = format_ta_kwu_ling_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(ta_kwu_ling_max)
                    if args.json
                    else format_tai_mo_max(ta_kwu_ling_max)
                )
        elif args.sha_lo_wan_max:
            sha_lo_wan_max = fetch_sha_lo_wan_max(timeout=args.timeout, lang=args.lang)
            if sha_lo_wan_max is None:
                text = format_sha_lo_wan_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_lo_wan_max)
                    if args.json
                    else format_tai_mo_max(sha_lo_wan_max)
                )
        elif args.airport_max:
            airport_max = fetch_airport_max(timeout=args.timeout, lang=args.lang)
            if airport_max is None:
                text = format_airport_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(airport_max) if args.json else format_tai_mo_max(airport_max)
                )
        elif args.yuen_long_park_max:
            yuen_long_park_max = fetch_yuen_long_park_max(
                timeout=args.timeout, lang=args.lang
            )
            if yuen_long_park_max is None:
                text = format_yuen_long_park_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(yuen_long_park_max)
                    if args.json
                    else format_tai_mo_max(yuen_long_park_max)
                )
        elif args.clear_water_bay_max:
            clear_water_bay_max = fetch_clear_water_bay_max(
                timeout=args.timeout, lang=args.lang
            )
            if clear_water_bay_max is None:
                text = format_clear_water_bay_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(clear_water_bay_max)
                    if args.json
                    else format_tai_mo_max(clear_water_bay_max)
                )
        elif args.tap_mun_max:
            tap_mun_max = fetch_tap_mun_max(timeout=args.timeout, lang=args.lang)
            if tap_mun_max is None:
                text = format_tap_mun_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(tap_mun_max)
                    if args.json
                    else format_tai_mo_max(tap_mun_max)
                )
        elif args.hong_kong_park_max:
            hong_kong_park_max = fetch_hong_kong_park_max(
                timeout=args.timeout, lang=args.lang
            )
            if hong_kong_park_max is None:
                text = format_hong_kong_park_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(hong_kong_park_max)
                    if args.json
                    else format_tai_mo_max(hong_kong_park_max)
                )
        elif args.ngong_ping_max:
            ngong_ping_max = fetch_ngong_ping_max(timeout=args.timeout, lang=args.lang)
            if ngong_ping_max is None:
                text = format_ngong_ping_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(ngong_ping_max)
                    if args.json
                    else format_tai_mo_max(ngong_ping_max)
                )
        elif args.kwun_tong_max:
            kwun_tong_max = fetch_kwun_tong_max(timeout=args.timeout, lang=args.lang)
            if kwun_tong_max is None:
                text = format_kwun_tong_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(kwun_tong_max)
                    if args.json
                    else format_tai_mo_max(kwun_tong_max)
                )
        elif args.wong_tai_sin_max:
            wong_tai_sin_max = fetch_wong_tai_sin_max(
                timeout=args.timeout, lang=args.lang
            )
            if wong_tai_sin_max is None:
                text = format_wong_tai_sin_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_tai_sin_max)
                    if args.json
                    else format_tai_mo_max(wong_tai_sin_max)
                )
        elif args.tsuen_wan_max:
            tsuen_wan_max = fetch_tsuen_wan_max(timeout=args.timeout, lang=args.lang)
            if tsuen_wan_max is None:
                text = format_tsuen_wan_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(tsuen_wan_max)
                    if args.json
                    else format_tai_mo_max(tsuen_wan_max)
                )
        elif args.kau_sai_chau_max:
            kau_sai_chau_max = fetch_kau_sai_chau_max(
                timeout=args.timeout, lang=args.lang
            )
            if kau_sai_chau_max is None:
                text = format_kau_sai_chau_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(kau_sai_chau_max)
                    if args.json
                    else format_tai_mo_max(kau_sai_chau_max)
                )
        elif args.kadoorie_farm_max:
            kadoorie_farm_max = fetch_kadoorie_farm_max(
                timeout=args.timeout, lang=args.lang
            )
            if kadoorie_farm_max is None:
                text = format_kadoorie_farm_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(kadoorie_farm_max)
                    if args.json
                    else format_tai_mo_max(kadoorie_farm_max)
                )
        elif args.the_peak_max:
            the_peak_max = fetch_the_peak_max(timeout=args.timeout, lang=args.lang)
            if the_peak_max is None:
                text = format_the_peak_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(the_peak_max)
                    if args.json
                    else format_tai_mo_max(the_peak_max)
                )
        elif args.kat_o_max:
            kat_o_max = fetch_kat_o_max(timeout=args.timeout, lang=args.lang)
            if kat_o_max is None:
                text = format_kat_o_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(kat_o_max) if args.json else format_tai_mo_max(kat_o_max)
                )
        elif args.pak_tam_chung_max:
            pak_tam_chung_max = fetch_pak_tam_chung_max(
                timeout=args.timeout, lang=args.lang
            )
            if pak_tam_chung_max is None:
                text = format_pak_tam_chung_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(pak_tam_chung_max)
                    if args.json
                    else format_tai_mo_max(pak_tam_chung_max)
                )
        elif args.beas_river_max:
            beas_river_max = fetch_beas_river_max(timeout=args.timeout, lang=args.lang)
            if beas_river_max is None:
                text = format_beas_river_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(beas_river_max)
                    if args.json
                    else format_tai_mo_max(beas_river_max)
                )
        elif args.kowloon_city_max:
            kowloon_city_max = fetch_kowloon_city_max(
                timeout=args.timeout, lang=args.lang
            )
            if kowloon_city_max is None:
                text = format_kowloon_city_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(kowloon_city_max)
                    if args.json
                    else format_tai_mo_max(kowloon_city_max)
                )
        elif args.new_tsing_yi_max:
            new_tsing_yi_max = fetch_new_tsing_yi_max(
                timeout=args.timeout, lang=args.lang
            )
            if new_tsing_yi_max is None:
                text = format_new_tsing_yi_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(new_tsing_yi_max)
                    if args.json
                    else format_tai_mo_max(new_tsing_yi_max)
                )
        elif args.stanley_max:
            stanley_max = fetch_stanley_max(timeout=args.timeout, lang=args.lang)
            if stanley_max is None:
                text = format_stanley_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(stanley_max)
                    if args.json
                    else format_tai_mo_max(stanley_max)
                )
        elif args.shing_mun_valley_max:
            shing_mun_valley_max = fetch_shing_mun_valley_max(
                timeout=args.timeout, lang=args.lang
            )
            if shing_mun_valley_max is None:
                text = format_shing_mun_valley_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(shing_mun_valley_max)
                    if args.json
                    else format_tai_mo_max(shing_mun_valley_max)
                )
        elif args.tuen_mun_home_max:
            tuen_mun_home_max = fetch_tuen_mun_home_max(
                timeout=args.timeout, lang=args.lang
            )
            if tuen_mun_home_max is None:
                text = format_tuen_mun_home_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(tuen_mun_home_max)
                    if args.json
                    else format_tai_mo_max(tuen_mun_home_max)
                )
        elif args.buoy_2_max:
            buoy_2_max = fetch_buoy_2_max(timeout=args.timeout, lang=args.lang)
            if buoy_2_max is None:
                text = format_buoy_2_max_miss(as_json=args.json)
            else:
                text = (
                    format_json(buoy_2_max)
                    if args.json
                    else format_tai_mo_max(buoy_2_max)
                )
        elif args.dew_point:
            dew_point = fetch_dew_point(timeout=args.timeout, lang=args.lang)
            if dew_point is None:
                text = format_dew_point_miss(as_json=args.json)
            else:
                text = format_json(dew_point) if args.json else format_dew_point(dew_point)
        elif args.park_dew:
            park_dew = fetch_park_dew(timeout=args.timeout, lang=args.lang)
            if park_dew is None:
                text = format_park_dew_miss(as_json=args.json)
            else:
                text = format_json(park_dew) if args.json else format_dew_point(park_dew)
        elif args.cheung_dew:
            cheung_dew = fetch_cheung_dew(timeout=args.timeout, lang=args.lang)
            if cheung_dew is None:
                text = format_cheung_dew_miss(as_json=args.json)
            else:
                text = format_json(cheung_dew) if args.json else format_dew_point(cheung_dew)
        elif args.wong_chuk_hang_dew:
            wong_chuk_hang_dew = fetch_wong_chuk_hang_dew(timeout=args.timeout, lang=args.lang)
            if wong_chuk_hang_dew is None:
                text = format_wong_chuk_hang_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_chuk_hang_dew)
                    if args.json
                    else format_dew_point(wong_chuk_hang_dew)
                )
        elif args.sai_kung_dew:
            sai_kung_dew = fetch_sai_kung_dew(timeout=args.timeout, lang=args.lang)
            if sai_kung_dew is None:
                text = format_sai_kung_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(sai_kung_dew) if args.json else format_dew_point(sai_kung_dew)
                )
        elif args.sha_tin_dew:
            sha_tin_dew = fetch_sha_tin_dew(timeout=args.timeout, lang=args.lang)
            if sha_tin_dew is None:
                text = format_sha_tin_dew_miss(as_json=args.json)
            else:
                text = format_json(sha_tin_dew) if args.json else format_dew_point(sha_tin_dew)
        elif args.sheung_shui_dew:
            sheung_shui_dew = fetch_sheung_shui_dew(timeout=args.timeout, lang=args.lang)
            if sheung_shui_dew is None:
                text = format_sheung_shui_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(sheung_shui_dew)
                    if args.json
                    else format_dew_point(sheung_shui_dew)
                )
        elif args.waglan_dew:
            waglan_dew = fetch_waglan_dew(timeout=args.timeout, lang=args.lang)
            if waglan_dew is None:
                text = format_waglan_dew_miss(as_json=args.json)
            else:
                text = format_json(waglan_dew) if args.json else format_dew_point(waglan_dew)
        elif args.lau_fau_dew:
            lau_fau_dew = fetch_lau_fau_dew(timeout=args.timeout, lang=args.lang)
            if lau_fau_dew is None:
                text = format_lau_fau_dew_miss(as_json=args.json)
            else:
                text = format_json(lau_fau_dew) if args.json else format_dew_point(lau_fau_dew)
        elif args.wetland_dew:
            wetland_dew = fetch_wetland_dew(timeout=args.timeout, lang=args.lang)
            if wetland_dew is None:
                text = format_wetland_dew_miss(as_json=args.json)
            else:
                text = format_json(wetland_dew) if args.json else format_dew_point(wetland_dew)
        elif args.ta_kwu_ling_dew:
            ta_kwu_ling_dew = fetch_ta_kwu_ling_dew(timeout=args.timeout, lang=args.lang)
            if ta_kwu_ling_dew is None:
                text = format_ta_kwu_ling_dew_miss(as_json=args.json)
            else:
                text = format_json(ta_kwu_ling_dew) if args.json else format_dew_point(ta_kwu_ling_dew)
        elif args.shek_kong_dew:
            shek_kong_dew = fetch_shek_kong_dew(timeout=args.timeout, lang=args.lang)
            if shek_kong_dew is None:
                text = format_shek_kong_dew_miss(as_json=args.json)
            else:
                text = format_json(shek_kong_dew) if args.json else format_dew_point(shek_kong_dew)
        elif args.tseung_kwan_o_dew:
            tseung_kwan_o_dew = fetch_tseung_kwan_o_dew(timeout=args.timeout, lang=args.lang)
            if tseung_kwan_o_dew is None:
                text = format_tseung_kwan_o_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(tseung_kwan_o_dew)
                    if args.json
                    else format_dew_point(tseung_kwan_o_dew)
                )
        elif args.tai_mo_dew:
            tai_mo_dew = fetch_tai_mo_dew(timeout=args.timeout, lang=args.lang)
            if tai_mo_dew is None:
                text = format_tai_mo_dew_miss(as_json=args.json)
            else:
                text = format_json(tai_mo_dew) if args.json else format_dew_point(tai_mo_dew)
        elif args.peng_chau_dew:
            peng_chau_dew = fetch_peng_chau_dew(timeout=args.timeout, lang=args.lang)
            if peng_chau_dew is None:
                text = format_peng_chau_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(peng_chau_dew)
                    if args.json
                    else format_dew_point(peng_chau_dew)
                )
        elif args.sha_lo_wan_dew:
            sha_lo_wan_dew = fetch_sha_lo_wan_dew(timeout=args.timeout, lang=args.lang)
            if sha_lo_wan_dew is None:
                text = format_sha_lo_wan_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_lo_wan_dew)
                    if args.json
                    else format_dew_point(sha_lo_wan_dew)
                )
        elif args.airport_dew:
            airport_dew = fetch_airport_dew(timeout=args.timeout, lang=args.lang)
            if airport_dew is None:
                text = format_airport_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(airport_dew) if args.json else format_dew_point(airport_dew)
                )
        elif args.clear_water_bay_dew:
            clear_water_bay_dew = fetch_clear_water_bay_dew(
                timeout=args.timeout, lang=args.lang
            )
            if clear_water_bay_dew is None:
                text = format_clear_water_bay_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(clear_water_bay_dew)
                    if args.json
                    else format_dew_point(clear_water_bay_dew)
                )
        elif args.hong_kong_park_dew:
            hong_kong_park_dew = fetch_hong_kong_park_dew(
                timeout=args.timeout, lang=args.lang
            )
            if hong_kong_park_dew is None:
                text = format_hong_kong_park_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(hong_kong_park_dew)
                    if args.json
                    else format_dew_point(hong_kong_park_dew)
                )
        elif args.tsuen_wan_dew:
            tsuen_wan_dew = fetch_tsuen_wan_dew(timeout=args.timeout, lang=args.lang)
            if tsuen_wan_dew is None:
                text = format_tsuen_wan_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(tsuen_wan_dew)
                    if args.json
                    else format_dew_point(tsuen_wan_dew)
                )
        elif args.shau_kei_wan_dew:
            shau_kei_wan_dew = fetch_shau_kei_wan_dew(
                timeout=args.timeout, lang=args.lang
            )
            if shau_kei_wan_dew is None:
                text = format_shau_kei_wan_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(shau_kei_wan_dew)
                    if args.json
                    else format_dew_point(shau_kei_wan_dew)
                )
        elif args.kau_sai_chau_dew:
            kau_sai_chau_dew = fetch_kau_sai_chau_dew(
                timeout=args.timeout, lang=args.lang
            )
            if kau_sai_chau_dew is None:
                text = format_kau_sai_chau_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(kau_sai_chau_dew)
                    if args.json
                    else format_dew_point(kau_sai_chau_dew)
                )
        elif args.pak_tam_chung_dew:
            pak_tam_chung_dew = fetch_pak_tam_chung_dew(
                timeout=args.timeout, lang=args.lang
            )
            if pak_tam_chung_dew is None:
                text = format_pak_tam_chung_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(pak_tam_chung_dew)
                    if args.json
                    else format_dew_point(pak_tam_chung_dew)
                )
        elif args.beas_river_dew:
            beas_river_dew = fetch_beas_river_dew(timeout=args.timeout, lang=args.lang)
            if beas_river_dew is None:
                text = format_beas_river_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(beas_river_dew)
                    if args.json
                    else format_dew_point(beas_river_dew)
                )
        elif args.runway_park_dew:
            runway_park_dew = fetch_runway_park_dew(
                timeout=args.timeout, lang=args.lang
            )
            if runway_park_dew is None:
                text = format_runway_park_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(runway_park_dew)
                    if args.json
                    else format_dew_point(runway_park_dew)
                )
        elif args.kowloon_city_dew:
            kowloon_city_dew = fetch_kowloon_city_dew(
                timeout=args.timeout, lang=args.lang
            )
            if kowloon_city_dew is None:
                text = format_kowloon_city_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(kowloon_city_dew)
                    if args.json
                    else format_dew_point(kowloon_city_dew)
                )
        elif args.nei_lak_shan_dew:
            nei_lak_shan_dew = fetch_nei_lak_shan_dew(
                timeout=args.timeout, lang=args.lang
            )
            if nei_lak_shan_dew is None:
                text = format_nei_lak_shan_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(nei_lak_shan_dew)
                    if args.json
                    else format_dew_point(nei_lak_shan_dew)
                )
        elif args.new_tsing_yi_dew:
            new_tsing_yi_dew = fetch_new_tsing_yi_dew(
                timeout=args.timeout, lang=args.lang
            )
            if new_tsing_yi_dew is None:
                text = format_new_tsing_yi_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(new_tsing_yi_dew)
                    if args.json
                    else format_dew_point(new_tsing_yi_dew)
                )
        elif args.tate_dew:
            tate_dew = fetch_tate_dew(timeout=args.timeout, lang=args.lang)
            if tate_dew is None:
                text = format_tate_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(tate_dew) if args.json else format_dew_point(tate_dew)
                )
        elif args.shing_mun_valley_dew:
            shing_mun_valley_dew = fetch_shing_mun_valley_dew(
                timeout=args.timeout, lang=args.lang
            )
            if shing_mun_valley_dew is None:
                text = format_shing_mun_valley_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(shing_mun_valley_dew)
                    if args.json
                    else format_dew_point(shing_mun_valley_dew)
                )
        elif args.tuen_mun_home_dew:
            tuen_mun_home_dew = fetch_tuen_mun_home_dew(
                timeout=args.timeout, lang=args.lang
            )
            if tuen_mun_home_dew is None:
                text = format_tuen_mun_home_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(tuen_mun_home_dew)
                    if args.json
                    else format_dew_point(tuen_mun_home_dew)
                )
        elif args.buoy_2_dew:
            buoy_2_dew = fetch_buoy_2_dew(timeout=args.timeout, lang=args.lang)
            if buoy_2_dew is None:
                text = format_buoy_2_dew_miss(as_json=args.json)
            else:
                text = (
                    format_json(buoy_2_dew)
                    if args.json
                    else format_dew_point(buoy_2_dew)
                )
        elif args.cloud:
            cloud = fetch_cloud(timeout=args.timeout, lang=args.lang)
            if cloud is None:
                text = format_cloud_miss(as_json=args.json)
            else:
                text = format_json(cloud) if args.json else format_cloud(cloud)
        elif args.evaporation:
            evaporation = fetch_evaporation(timeout=args.timeout, lang=args.lang)
            if evaporation is None:
                text = format_evaporation_miss(as_json=args.json)
            else:
                text = format_json(evaporation) if args.json else format_evaporation(evaporation)
        elif args.evapotranspiration:
            evapotranspiration = fetch_evapotranspiration(timeout=args.timeout, lang=args.lang)
            if evapotranspiration is None:
                text = format_evapotranspiration_miss(as_json=args.json)
            else:
                text = (
                    format_json(evapotranspiration)
                    if args.json
                    else format_evapotranspiration(evapotranspiration)
                )
        elif args.grass:
            grass = fetch_grass(timeout=args.timeout, lang=args.lang)
            if grass is None:
                text = format_grass_miss(as_json=args.json)
            else:
                text = format_json(grass) if args.json else format_grass(grass)
        elif args.sunshine:
            sunshine = fetch_sunshine(timeout=args.timeout, lang=args.lang)
            if sunshine is None:
                text = format_sunshine_miss(as_json=args.json)
            else:
                text = format_json(sunshine) if args.json else format_sunshine(sunshine)
        elif args.daily_sun:
            daily_sun = fetch_daily_sun(timeout=args.timeout, lang=args.lang)
            if daily_sun is None:
                text = format_daily_sun_miss(as_json=args.json)
            else:
                text = format_json(daily_sun) if args.json else format_daily_sun(daily_sun)
        elif args.max_uv:
            max_uv = fetch_max_uv(timeout=args.timeout, lang=args.lang)
            if max_uv is None:
                text = format_max_uv_miss(as_json=args.json)
            else:
                text = format_json(max_uv) if args.json else format_max_uv(max_uv)
        elif args.uv_peak:
            uv_peak = fetch_uv_peak(timeout=args.timeout, lang=args.lang)
            if uv_peak is None:
                text = format_uv_peak_miss(as_json=args.json)
            else:
                text = format_json(uv_peak) if args.json else format_uv_peak(uv_peak)
        elif args.mean_uv:
            mean_uv = fetch_mean_uv(timeout=args.timeout, lang=args.lang)
            if mean_uv is None:
                text = format_mean_uv_miss(as_json=args.json)
            else:
                text = format_json(mean_uv) if args.json else format_mean_uv(mean_uv)
        elif args.daily_uv:
            daily_uv = fetch_daily_uv(timeout=args.timeout, lang=args.lang)
            if daily_uv is None:
                text = format_daily_uv_miss(as_json=args.json)
            else:
                text = format_json(daily_uv) if args.json else format_mean_uv(daily_uv)
        elif args.dose:
            dose = fetch_dose(timeout=args.timeout, lang=args.lang)
            if dose is None:
                text = format_dose_miss(as_json=args.json)
            else:
                text = format_json(dose) if args.json else format_dose(dose)
        elif args.hourly_dose:
            hourly_dose = fetch_hourly_dose(timeout=args.timeout, lang=args.lang)
            if not hourly_dose.stations:
                text = format_hourly_dose_miss(as_json=args.json)
            else:
                text = format_json(hourly_dose) if args.json else format_hourly_dose(hourly_dose)
        elif args.accum_rain:
            accum_rain = fetch_accum_rain(timeout=args.timeout, lang=args.lang)
            if accum_rain is None:
                text = format_accum_rain_miss(as_json=args.json)
            else:
                text = format_json(accum_rain) if args.json else format_accum_rain(accum_rain)
        elif args.avg_rain:
            avg_rain = fetch_avg_rain(timeout=args.timeout, lang=args.lang)
            if avg_rain is None:
                text = format_avg_rain_miss(as_json=args.json)
            else:
                text = format_json(avg_rain) if args.json else format_avg_rain(avg_rain)
        elif args.radiation:
            radiation = fetch_radiation(timeout=args.timeout, lang=args.lang)
            if radiation is None:
                text = format_radiation_miss(as_json=args.json)
            else:
                text = format_json(radiation) if args.json else format_radiation(radiation)
        elif args.bulletin:
            bulletin = fetch_bulletin(timeout=args.timeout, lang=args.lang)
            if bulletin is None:
                text = format_bulletin_miss(as_json=args.json)
            else:
                text = format_json(bulletin) if args.json else format_bulletin(bulletin)
        elif args.radiation_note:
            radiation_note = fetch_radiation_note(timeout=args.timeout, lang=args.lang)
            if radiation_note is None:
                text = format_radiation_note_miss(as_json=args.json)
            else:
                text = (
                    format_json(radiation_note)
                    if args.json
                    else format_radiation_note(radiation_note)
                )
        elif args.radiation_weather:
            radiation_weather = fetch_radiation_weather(timeout=args.timeout, lang=args.lang)
            if radiation_weather is None:
                text = format_radiation_weather_miss(as_json=args.json)
            else:
                text = (
                    format_json(radiation_weather)
                    if args.json
                    else format_radiation_weather(radiation_weather)
                )
        elif args.radiation_ground:
            radiation_ground = fetch_radiation_ground(timeout=args.timeout, lang=args.lang)
            if radiation_ground is None:
                text = format_radiation_ground_miss(as_json=args.json)
            else:
                text = (
                    format_json(radiation_ground)
                    if args.json
                    else format_radiation_ground(radiation_ground)
                )
        elif args.radiation_provisional:
            radiation_provisional = fetch_radiation_provisional(
                timeout=args.timeout, lang=args.lang
            )
            if radiation_provisional is None:
                text = format_radiation_provisional_miss(as_json=args.json)
            else:
                text = (
                    format_json(radiation_provisional)
                    if args.json
                    else format_radiation_provisional(radiation_provisional)
                )
        elif args.tomorrow:
            tomorrow = fetch_tomorrow(timeout=args.timeout, lang=args.lang)
            if tomorrow is None:
                text = format_tomorrow_miss(as_json=args.json)
            else:
                text = format_json(tomorrow) if args.json else format_tomorrow(tomorrow)
        elif args.weekend:
            weekend = fetch_weekend(timeout=args.timeout, lang=args.lang)
            if not weekend.days:
                text = format_weekend_miss(as_json=args.json)
            else:
                text = format_json(weekend) if args.json else format_weekend(weekend)
        elif args.day is not None:
            forecast_day = fetch_forecast_day(args.day, timeout=args.timeout, lang=args.lang)
            if forecast_day is None:
                text = format_day_miss(args.day, as_json=args.json)
            else:
                title = f"Hong Kong forecast day {args.day}"
                text = (
                    format_json(forecast_day)
                    if args.json
                    else format_tomorrow(forecast_day, title=title)
                )
        elif args.psr:
            psr = fetch_psr(timeout=args.timeout, lang=args.lang)
            text = format_json(psr) if args.json else format_psr(psr)
        elif args.wind:
            wind = fetch_wind(timeout=args.timeout, lang=args.lang)
            text = format_json(wind) if args.json else format_wind(wind)
        elif args.gust:
            gust = fetch_gust(timeout=args.timeout, lang=args.lang)
            if not gust.stations:
                text = format_gust_miss(as_json=args.json)
            else:
                text = format_json(gust) if args.json else format_gust(gust)
        elif args.prevailing:
            prevailing = fetch_prevailing(timeout=args.timeout, lang=args.lang)
            if prevailing is None:
                text = format_prevailing_miss(as_json=args.json)
            else:
                text = format_json(prevailing) if args.json else format_prevailing(prevailing)
        elif args.cheung_prevailing:
            cheung_prevailing = fetch_cheung_prevailing(timeout=args.timeout, lang=args.lang)
            if cheung_prevailing is None:
                text = format_cheung_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(cheung_prevailing)
                    if args.json
                    else format_prevailing(cheung_prevailing)
                )
        elif args.ping_chau_prevailing:
            ping_chau_prevailing = fetch_ping_chau_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if ping_chau_prevailing is None:
                text = format_ping_chau_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(ping_chau_prevailing)
                    if args.json
                    else format_prevailing(ping_chau_prevailing)
                )
        elif args.tai_mo_to_prevailing:
            tai_mo_to_prevailing = fetch_tai_mo_to_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if tai_mo_to_prevailing is None:
                text = format_tai_mo_to_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mo_to_prevailing)
                    if args.json
                    else format_prevailing(tai_mo_to_prevailing)
                )
        elif args.tai_po_kau_prevailing:
            tai_po_kau_prevailing = fetch_tai_po_kau_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if tai_po_kau_prevailing is None:
                text = format_tai_po_kau_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_po_kau_prevailing)
                    if args.json
                    else format_prevailing(tai_po_kau_prevailing)
                )
        elif args.park_prevailing:
            park_prevailing = fetch_park_prevailing(timeout=args.timeout, lang=args.lang)
            if park_prevailing is None:
                text = format_park_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(park_prevailing)
                    if args.json
                    else format_prevailing(park_prevailing)
                )
        elif args.lau_fau_prevailing:
            lau_fau_prevailing = fetch_lau_fau_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if lau_fau_prevailing is None:
                text = format_lau_fau_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(lau_fau_prevailing)
                    if args.json
                    else format_prevailing(lau_fau_prevailing)
                )
        elif args.sha_lo_wan_prevailing:
            sha_lo_wan_prevailing = fetch_sha_lo_wan_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if sha_lo_wan_prevailing is None:
                text = format_sha_lo_wan_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_lo_wan_prevailing)
                    if args.json
                    else format_prevailing(sha_lo_wan_prevailing)
                )
        elif args.wong_chuk_hang_prevailing:
            wong_chuk_hang_prevailing = fetch_wong_chuk_hang_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if wong_chuk_hang_prevailing is None:
                text = format_wong_chuk_hang_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_chuk_hang_prevailing)
                    if args.json
                    else format_prevailing(wong_chuk_hang_prevailing)
                )
        elif args.sai_kung_prevailing:
            sai_kung_prevailing = fetch_sai_kung_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if sai_kung_prevailing is None:
                text = format_sai_kung_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(sai_kung_prevailing)
                    if args.json
                    else format_prevailing(sai_kung_prevailing)
                )
        elif args.tseung_kwan_o_prevailing:
            tseung_kwan_o_prevailing = fetch_tseung_kwan_o_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if tseung_kwan_o_prevailing is None:
                text = format_tseung_kwan_o_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(tseung_kwan_o_prevailing)
                    if args.json
                    else format_prevailing(tseung_kwan_o_prevailing)
                )
        elif args.shek_kong_prevailing:
            shek_kong_prevailing = fetch_shek_kong_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if shek_kong_prevailing is None:
                text = format_shek_kong_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(shek_kong_prevailing)
                    if args.json
                    else format_prevailing(shek_kong_prevailing)
                )
        elif args.sha_tin_prevailing:
            sha_tin_prevailing = fetch_sha_tin_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if sha_tin_prevailing is None:
                text = format_sha_tin_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_tin_prevailing)
                    if args.json
                    else format_prevailing(sha_tin_prevailing)
                )
        elif args.ta_kwu_ling_prevailing:
            ta_kwu_ling_prevailing = fetch_ta_kwu_ling_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if ta_kwu_ling_prevailing is None:
                text = format_ta_kwu_ling_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(ta_kwu_ling_prevailing)
                    if args.json
                    else format_prevailing(ta_kwu_ling_prevailing)
                )
        elif args.wetland_prevailing:
            wetland_prevailing = fetch_wetland_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if wetland_prevailing is None:
                text = format_wetland_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(wetland_prevailing)
                    if args.json
                    else format_prevailing(wetland_prevailing)
                )
        elif args.tai_mo_prevailing:
            tai_mo_prevailing = fetch_tai_mo_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if tai_mo_prevailing is None:
                text = format_tai_mo_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mo_prevailing)
                    if args.json
                    else format_prevailing(tai_mo_prevailing)
                )
        elif args.airport_prevailing:
            airport_prevailing = fetch_airport_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if airport_prevailing is None:
                text = format_airport_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(airport_prevailing)
                    if args.json
                    else format_prevailing(airport_prevailing)
                )
        elif args.kai_tak_prevailing:
            kai_tak_prevailing = fetch_kai_tak_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if kai_tak_prevailing is None:
                text = format_kai_tak_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(kai_tak_prevailing)
                    if args.json
                    else format_prevailing(kai_tak_prevailing)
                )
        elif args.green_island_prevailing:
            green_island_prevailing = fetch_green_island_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if green_island_prevailing is None:
                text = format_green_island_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(green_island_prevailing)
                    if args.json
                    else format_prevailing(green_island_prevailing)
                )
        elif args.ngong_ping_prevailing:
            ngong_ping_prevailing = fetch_ngong_ping_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if ngong_ping_prevailing is None:
                text = format_ngong_ping_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(ngong_ping_prevailing)
                    if args.json
                    else format_prevailing(ngong_ping_prevailing)
                )
        elif args.tai_mei_tuk_prevailing:
            tai_mei_tuk_prevailing = fetch_tai_mei_tuk_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if tai_mei_tuk_prevailing is None:
                text = format_tai_mei_tuk_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mei_tuk_prevailing)
                    if args.json
                    else format_prevailing(tai_mei_tuk_prevailing)
                )
        elif args.central_pier_prevailing:
            central_pier_prevailing = fetch_central_pier_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if central_pier_prevailing is None:
                text = format_central_pier_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(central_pier_prevailing)
                    if args.json
                    else format_prevailing(central_pier_prevailing)
                )
        elif args.nei_lak_shan_prevailing:
            nei_lak_shan_prevailing = fetch_nei_lak_shan_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if nei_lak_shan_prevailing is None:
                text = format_nei_lak_shan_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(nei_lak_shan_prevailing)
                    if args.json
                    else format_prevailing(nei_lak_shan_prevailing)
                )
        elif args.buoy_2_prevailing:
            buoy_2_prevailing = fetch_buoy_2_prevailing(
                timeout=args.timeout, lang=args.lang
            )
            if buoy_2_prevailing is None:
                text = format_buoy_2_prevailing_miss(as_json=args.json)
            else:
                text = (
                    format_json(buoy_2_prevailing)
                    if args.json
                    else format_prevailing(buoy_2_prevailing)
                )
        elif args.mean_wind:
            mean_wind = fetch_mean_wind(timeout=args.timeout, lang=args.lang)
            if mean_wind is None:
                text = format_mean_wind_miss(as_json=args.json)
            else:
                text = format_json(mean_wind) if args.json else format_mean_wind(mean_wind)
        elif args.cheung_wind:
            cheung_wind = fetch_cheung_wind(timeout=args.timeout, lang=args.lang)
            if cheung_wind is None:
                text = format_cheung_wind_miss(as_json=args.json)
            else:
                text = format_json(cheung_wind) if args.json else format_mean_wind(cheung_wind)
        elif args.lau_fau_wind:
            lau_fau_wind = fetch_lau_fau_wind(timeout=args.timeout, lang=args.lang)
            if lau_fau_wind is None:
                text = format_lau_fau_wind_miss(as_json=args.json)
            else:
                text = format_json(lau_fau_wind) if args.json else format_mean_wind(lau_fau_wind)
        elif args.peng_chau_wind:
            peng_chau_wind = fetch_peng_chau_wind(timeout=args.timeout, lang=args.lang)
            if peng_chau_wind is None:
                text = format_peng_chau_wind_miss(as_json=args.json)
            else:
                text = format_json(peng_chau_wind) if args.json else format_mean_wind(peng_chau_wind)
        elif args.tai_po_kau_wind:
            tai_po_kau_wind = fetch_tai_po_kau_wind(timeout=args.timeout, lang=args.lang)
            if tai_po_kau_wind is None:
                text = format_tai_po_kau_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_po_kau_wind)
                    if args.json
                    else format_mean_wind(tai_po_kau_wind)
                )
        elif args.tai_mo_to_wind:
            tai_mo_to_wind = fetch_tai_mo_to_wind(timeout=args.timeout, lang=args.lang)
            if tai_mo_to_wind is None:
                text = format_tai_mo_to_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mo_to_wind)
                    if args.json
                    else format_mean_wind(tai_mo_to_wind)
                )
        elif args.tai_mo_wind:
            tai_mo_wind = fetch_tai_mo_wind(timeout=args.timeout, lang=args.lang)
            if tai_mo_wind is None:
                text = format_tai_mo_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mo_wind)
                    if args.json
                    else format_mean_wind(tai_mo_wind)
                )
        elif args.tate_wind:
            tate_wind = fetch_tate_wind(timeout=args.timeout, lang=args.lang)
            if tate_wind is None:
                text = format_tate_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(tate_wind)
                    if args.json
                    else format_mean_wind(tate_wind)
                )
        elif args.shek_kong_wind:
            shek_kong_wind = fetch_shek_kong_wind(timeout=args.timeout, lang=args.lang)
            if shek_kong_wind is None:
                text = format_shek_kong_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(shek_kong_wind)
                    if args.json
                    else format_mean_wind(shek_kong_wind)
                )
        elif args.sai_kung_wind:
            sai_kung_wind = fetch_sai_kung_wind(timeout=args.timeout, lang=args.lang)
            if sai_kung_wind is None:
                text = format_sai_kung_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(sai_kung_wind)
                    if args.json
                    else format_mean_wind(sai_kung_wind)
                )
        elif args.sha_tin_wind:
            sha_tin_wind = fetch_sha_tin_wind(timeout=args.timeout, lang=args.lang)
            if sha_tin_wind is None:
                text = format_sha_tin_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_tin_wind)
                    if args.json
                    else format_mean_wind(sha_tin_wind)
                )
        elif args.wong_chuk_hang_wind:
            wong_chuk_hang_wind = fetch_wong_chuk_hang_wind(
                timeout=args.timeout, lang=args.lang
            )
            if wong_chuk_hang_wind is None:
                text = format_wong_chuk_hang_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_chuk_hang_wind)
                    if args.json
                    else format_mean_wind(wong_chuk_hang_wind)
                )
        elif args.park_wind:
            park_wind = fetch_park_wind(timeout=args.timeout, lang=args.lang)
            if park_wind is None:
                text = format_park_wind_miss(as_json=args.json)
            else:
                text = format_json(park_wind) if args.json else format_mean_wind(park_wind)
        elif args.wetland_wind:
            wetland_wind = fetch_wetland_wind(timeout=args.timeout, lang=args.lang)
            if wetland_wind is None:
                text = format_wetland_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(wetland_wind)
                    if args.json
                    else format_mean_wind(wetland_wind)
                )
        elif args.tseung_kwan_o_wind:
            tseung_kwan_o_wind = fetch_tseung_kwan_o_wind(
                timeout=args.timeout, lang=args.lang
            )
            if tseung_kwan_o_wind is None:
                text = format_tseung_kwan_o_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(tseung_kwan_o_wind)
                    if args.json
                    else format_mean_wind(tseung_kwan_o_wind)
                )
        elif args.ta_kwu_ling_wind:
            ta_kwu_ling_wind = fetch_ta_kwu_ling_wind(
                timeout=args.timeout, lang=args.lang
            )
            if ta_kwu_ling_wind is None:
                text = format_ta_kwu_ling_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(ta_kwu_ling_wind)
                    if args.json
                    else format_mean_wind(ta_kwu_ling_wind)
                )
        elif args.sha_lo_wan_wind:
            sha_lo_wan_wind = fetch_sha_lo_wan_wind(
                timeout=args.timeout, lang=args.lang
            )
            if sha_lo_wan_wind is None:
                text = format_sha_lo_wan_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_lo_wan_wind)
                    if args.json
                    else format_mean_wind(sha_lo_wan_wind)
                )
        elif args.ping_chau_wind:
            ping_chau_wind = fetch_ping_chau_wind(timeout=args.timeout, lang=args.lang)
            if ping_chau_wind is None:
                text = format_ping_chau_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(ping_chau_wind)
                    if args.json
                    else format_mean_wind(ping_chau_wind)
                )
        elif args.airport_wind:
            airport_wind = fetch_airport_wind(timeout=args.timeout, lang=args.lang)
            if airport_wind is None:
                text = format_airport_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(airport_wind)
                    if args.json
                    else format_mean_wind(airport_wind)
                )
        elif args.green_island_wind:
            green_island_wind = fetch_green_island_wind(
                timeout=args.timeout, lang=args.lang
            )
            if green_island_wind is None:
                text = format_green_island_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(green_island_wind)
                    if args.json
                    else format_mean_wind(green_island_wind)
                )
        elif args.ngong_ping_wind:
            ngong_ping_wind = fetch_ngong_ping_wind(
                timeout=args.timeout, lang=args.lang
            )
            if ngong_ping_wind is None:
                text = format_ngong_ping_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(ngong_ping_wind)
                    if args.json
                    else format_mean_wind(ngong_ping_wind)
                )
        elif args.tai_mei_tuk_wind:
            tai_mei_tuk_wind = fetch_tai_mei_tuk_wind(
                timeout=args.timeout, lang=args.lang
            )
            if tai_mei_tuk_wind is None:
                text = format_tai_mei_tuk_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mei_tuk_wind)
                    if args.json
                    else format_mean_wind(tai_mei_tuk_wind)
                )
        elif args.lamma_island_wind:
            lamma_island_wind = fetch_lamma_island_wind(
                timeout=args.timeout, lang=args.lang
            )
            if lamma_island_wind is None:
                text = format_lamma_island_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(lamma_island_wind)
                    if args.json
                    else format_mean_wind(lamma_island_wind)
                )
        elif args.kai_tak_wind:
            kai_tak_wind = fetch_kai_tak_wind(timeout=args.timeout, lang=args.lang)
            if kai_tak_wind is None:
                text = format_kai_tak_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(kai_tak_wind) if args.json else format_mean_wind(kai_tak_wind)
                )
        elif args.central_pier_wind:
            central_pier_wind = fetch_central_pier_wind(
                timeout=args.timeout, lang=args.lang
            )
            if central_pier_wind is None:
                text = format_central_pier_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(central_pier_wind)
                    if args.json
                    else format_mean_wind(central_pier_wind)
                )
        elif args.nei_lak_shan_wind:
            nei_lak_shan_wind = fetch_nei_lak_shan_wind(
                timeout=args.timeout, lang=args.lang
            )
            if nei_lak_shan_wind is None:
                text = format_nei_lak_shan_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(nei_lak_shan_wind)
                    if args.json
                    else format_mean_wind(nei_lak_shan_wind)
                )
        elif args.buoy_2_wind:
            buoy_2_wind = fetch_buoy_2_wind(timeout=args.timeout, lang=args.lang)
            if buoy_2_wind is None:
                text = format_buoy_2_wind_miss(as_json=args.json)
            else:
                text = (
                    format_json(buoy_2_wind)
                    if args.json
                    else format_mean_wind(buoy_2_wind)
                )
        elif args.forecast_icon:
            forecast_icon = fetch_forecast_icon(timeout=args.timeout, lang=args.lang)
            if not forecast_icon.days:
                text = format_forecast_icon_miss(as_json=args.json)
            else:
                text = (
                    format_json(forecast_icon)
                    if args.json
                    else format_forecast_icon(forecast_icon)
                )
        elif args.quake:
            quakes = fetch_quakes(timeout=args.timeout, lang=args.lang)
            text = format_json(quakes) if args.json else format_quakes(quakes)
        elif args.felt:
            felt = fetch_felt(timeout=args.timeout, lang=args.lang)
            if felt is None:
                text = format_felt_miss(as_json=args.json)
            else:
                text = format_json(felt) if args.json else format_felt(felt)
        elif args.visibility:
            visibility = fetch_visibility(timeout=args.timeout, lang=args.lang)
            text = format_json(visibility) if args.json else format_visibility(visibility)
        elif args.reduced_vis:
            reduced_vis = fetch_reduced_vis(timeout=args.timeout, lang=args.lang)
            if reduced_vis is None:
                text = format_reduced_vis_miss(as_json=args.json)
            else:
                text = format_json(reduced_vis) if args.json else format_reduced_vis(reduced_vis)
        elif args.tide:
            tide = fetch_tide(timeout=args.timeout, lang=args.lang)
            if not tide.events:
                text = format_tide_miss(as_json=args.json)
            else:
                text = format_json(tide) if args.json else format_tide(tide)
        elif args.tide_hour:
            tide_hour = fetch_tide_hour(timeout=args.timeout, lang=args.lang)
            if not tide_hour.hours:
                text = format_tide_hour_miss(as_json=args.json)
            else:
                text = format_json(tide_hour) if args.json else format_tide_hour(tide_hour)
        elif args.tide_latest:
            tide_latest = fetch_tide_latest(timeout=args.timeout, lang=args.lang)
            if not tide_latest.stations:
                text = format_tide_latest_miss(as_json=args.json)
            else:
                text = format_json(tide_latest) if args.json else format_tide_latest(tide_latest)
        elif args.aqhi:
            aqhi = fetch_aqhi(timeout=args.timeout, lang=args.lang)
            if not aqhi.readings:
                text = format_aqhi_miss(as_json=args.json)
            else:
                text = format_json(aqhi) if args.json else format_aqhi(aqhi)
        elif args.sunrise:
            sunrise = fetch_sunrise(timeout=args.timeout, lang=args.lang)
            if sunrise is None:
                text = format_sunrise_miss(as_json=args.json)
            else:
                text = format_json(sunrise) if args.json else format_sunrise(sunrise)
        elif args.moon:
            moon = fetch_moon(timeout=args.timeout, lang=args.lang)
            if moon is None:
                text = format_moon_miss(as_json=args.json)
            else:
                text = format_json(moon) if args.json else format_moon(moon)
        elif args.lunar:
            lunar = fetch_lunar(timeout=args.timeout, lang=args.lang)
            if lunar is None:
                text = format_lunar_miss(as_json=args.json)
            else:
                text = format_json(lunar) if args.json else format_lunar(lunar)
        elif args.uv:
            uv = fetch_uv(timeout=args.timeout, lang=args.lang)
            text = format_json(uv) if args.json else format_uv(uv)
        elif args.fifteen_uv:
            fifteen_uv = fetch_fifteen_uv(timeout=args.timeout, lang=args.lang)
            if fifteen_uv is None:
                text = format_fifteen_uv_miss(as_json=args.json)
            else:
                text = format_json(fifteen_uv) if args.json else format_fifteen_uv(fifteen_uv)
        elif args.icon_time:
            icon_time = fetch_icon_time(timeout=args.timeout, lang=args.lang)
            if icon_time is None:
                text = format_icon_time_miss(as_json=args.json)
            else:
                text = format_json(icon_time) if args.json else format_icon_time(icon_time)
        elif args.icon:
            icon = fetch_icon(timeout=args.timeout, lang=args.lang)
            if icon is None:
                text = format_icon_miss(as_json=args.json)
            else:
                text = format_json(icon) if args.json else format_icon(icon)
        elif args.current_updated:
            current_updated = fetch_current_updated(timeout=args.timeout, lang=args.lang)
            if current_updated is None:
                text = format_current_updated_miss(as_json=args.json)
            else:
                text = (
                    format_json(current_updated)
                    if args.json
                    else format_current_updated(current_updated)
                )
        elif args.tips:
            tips = fetch_tips(timeout=args.timeout, lang=args.lang)
            text = format_json(tips) if args.json else format_tips(tips)
        elif args.lamppost:
            lamppost = fetch_lamppost(timeout=args.timeout, lang=args.lang)
            if lamppost is None:
                text = format_lamppost_miss(as_json=args.json)
            else:
                text = format_json(lamppost) if args.json else format_lamppost(lamppost)
        elif args.rain:
            rain = fetch_rain(timeout=args.timeout, lang=args.lang)
            text = format_json(rain) if args.json else format_rain(rain)
        elif args.rain_period:
            rain_period = fetch_rain_period(timeout=args.timeout, lang=args.lang)
            if rain_period is None:
                text = format_rain_period_miss(as_json=args.json)
            else:
                text = format_json(rain_period) if args.json else format_rain_period(rain_period)
        elif args.rain_maint:
            rain_maint = fetch_rain_maint(timeout=args.timeout, lang=args.lang)
            if not rain_maint.places:
                text = format_rain_maint_miss(as_json=args.json)
            else:
                text = format_json(rain_maint) if args.json else format_rain_maint(rain_maint)
        elif args.hour_rain:
            hour_rain = fetch_hour_rain(timeout=args.timeout, lang=args.lang)
            if not hour_rain.readings:
                text = format_hour_rain_miss(as_json=args.json)
            else:
                text = format_json(hour_rain) if args.json else format_hour_rain(hour_rain)
        elif args.hour_wettest:
            hour_wettest = fetch_hour_wettest(timeout=args.timeout, lang=args.lang)
            if hour_wettest is None:
                text = format_hour_rain_miss(as_json=args.json)
            else:
                text = format_json(hour_wettest) if args.json else format_hour_wettest(hour_wettest)
        elif args.hour_driest:
            hour_driest = fetch_hour_driest(timeout=args.timeout, lang=args.lang)
            if hour_driest is None:
                text = format_hour_rain_miss(as_json=args.json)
            else:
                text = format_json(hour_driest) if args.json else format_hour_driest(hour_driest)
        elif args.wettest:
            wettest = fetch_wettest(timeout=args.timeout, lang=args.lang)
            if wettest is None:
                text = format_wettest_miss(as_json=args.json)
            else:
                text = format_json(wettest) if args.json else format_wettest(wettest)
        elif args.driest:
            driest = fetch_driest(timeout=args.timeout, lang=args.lang)
            if driest is None:
                text = format_driest_miss(as_json=args.json)
            else:
                text = format_json(driest) if args.json else format_driest(driest)
        elif args.nowcast:
            nowcast = fetch_nowcast(timeout=args.timeout, lang=args.lang)
            if not nowcast.periods:
                text = format_nowcast_miss(as_json=args.json)
            else:
                text = format_json(nowcast) if args.json else format_nowcast(nowcast)
        elif args.daily_rain:
            daily_rain = fetch_daily_rain(timeout=args.timeout, lang=args.lang)
            if daily_rain is None:
                text = format_daily_rain_miss(as_json=args.json)
            else:
                text = format_json(daily_rain) if args.json else format_daily_rain(daily_rain)
        elif args.lau_fau_rain:
            lau_fau_rain = fetch_lau_fau_rain(timeout=args.timeout, lang=args.lang)
            if lau_fau_rain is None:
                text = format_lau_fau_rain_miss(as_json=args.json)
            else:
                text = format_json(lau_fau_rain) if args.json else format_daily_rain(lau_fau_rain)
        elif args.shek_kong_rain:
            shek_kong_rain = fetch_shek_kong_rain(timeout=args.timeout, lang=args.lang)
            if shek_kong_rain is None:
                text = format_shek_kong_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(shek_kong_rain)
                    if args.json
                    else format_daily_rain(shek_kong_rain)
                )
        elif args.wetland_rain:
            wetland_rain = fetch_wetland_rain(timeout=args.timeout, lang=args.lang)
            if wetland_rain is None:
                text = format_wetland_rain_miss(as_json=args.json)
            else:
                text = format_json(wetland_rain) if args.json else format_daily_rain(wetland_rain)
        elif args.sham_shui_po_rain:
            sham_shui_po_rain = fetch_sham_shui_po_rain(timeout=args.timeout, lang=args.lang)
            if sham_shui_po_rain is None:
                text = format_sham_shui_po_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(sham_shui_po_rain)
                    if args.json
                    else format_daily_rain(sham_shui_po_rain)
                )
        elif args.park_rain:
            park_rain = fetch_park_rain(timeout=args.timeout, lang=args.lang)
            if park_rain is None:
                text = format_park_rain_miss(as_json=args.json)
            else:
                text = format_json(park_rain) if args.json else format_daily_rain(park_rain)
        elif args.tseung_kwan_o_rain:
            tseung_kwan_o_rain = fetch_tseung_kwan_o_rain(timeout=args.timeout, lang=args.lang)
            if tseung_kwan_o_rain is None:
                text = format_tseung_kwan_o_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(tseung_kwan_o_rain)
                    if args.json
                    else format_daily_rain(tseung_kwan_o_rain)
                )
        elif args.sheung_shui_rain:
            sheung_shui_rain = fetch_sheung_shui_rain(timeout=args.timeout, lang=args.lang)
            if sheung_shui_rain is None:
                text = format_sheung_shui_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(sheung_shui_rain)
                    if args.json
                    else format_daily_rain(sheung_shui_rain)
                )
        elif args.sha_tin_rain:
            sha_tin_rain = fetch_sha_tin_rain(timeout=args.timeout, lang=args.lang)
            if sha_tin_rain is None:
                text = format_sha_tin_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_tin_rain)
                    if args.json
                    else format_daily_rain(sha_tin_rain)
                )
        elif args.ta_kwu_ling_rain:
            ta_kwu_ling_rain = fetch_ta_kwu_ling_rain(timeout=args.timeout, lang=args.lang)
            if ta_kwu_ling_rain is None:
                text = format_ta_kwu_ling_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(ta_kwu_ling_rain)
                    if args.json
                    else format_daily_rain(ta_kwu_ling_rain)
                )
        elif args.cheung_chau_rain:
            cheung_chau_rain = fetch_cheung_chau_rain(timeout=args.timeout, lang=args.lang)
            if cheung_chau_rain is None:
                text = format_cheung_chau_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(cheung_chau_rain)
                    if args.json
                    else format_daily_rain(cheung_chau_rain)
                )
        elif args.waglan_rain:
            waglan_rain = fetch_waglan_rain(timeout=args.timeout, lang=args.lang)
            if waglan_rain is None:
                text = format_waglan_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(waglan_rain)
                    if args.json
                    else format_daily_rain(waglan_rain)
                )
        elif args.tate_rain:
            tate_rain = fetch_tate_rain(timeout=args.timeout, lang=args.lang)
            if tate_rain is None:
                text = format_tate_rain_miss(as_json=args.json)
            else:
                text = format_json(tate_rain) if args.json else format_daily_rain(tate_rain)
        elif args.peng_chau_rain:
            peng_chau_rain = fetch_peng_chau_rain(timeout=args.timeout, lang=args.lang)
            if peng_chau_rain is None:
                text = format_peng_chau_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(peng_chau_rain)
                    if args.json
                    else format_daily_rain(peng_chau_rain)
                )
        elif args.ping_chau_rain:
            ping_chau_rain = fetch_ping_chau_rain(timeout=args.timeout, lang=args.lang)
            if ping_chau_rain is None:
                text = format_ping_chau_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(ping_chau_rain)
                    if args.json
                    else format_daily_rain(ping_chau_rain)
                )
        elif args.tai_mo_rain:
            tai_mo_rain = fetch_tai_mo_rain(timeout=args.timeout, lang=args.lang)
            if tai_mo_rain is None:
                text = format_tai_mo_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mo_rain)
                    if args.json
                    else format_daily_rain(tai_mo_rain)
                )
        elif args.sha_lo_wan_rain:
            sha_lo_wan_rain = fetch_sha_lo_wan_rain(timeout=args.timeout, lang=args.lang)
            if sha_lo_wan_rain is None:
                text = format_sha_lo_wan_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_lo_wan_rain)
                    if args.json
                    else format_daily_rain(sha_lo_wan_rain)
                )
        elif args.airport_rain:
            airport_rain = fetch_airport_rain(timeout=args.timeout, lang=args.lang)
            if airport_rain is None:
                text = format_airport_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(airport_rain) if args.json else format_daily_rain(airport_rain)
                )
        elif args.green_island_rain:
            green_island_rain = fetch_green_island_rain(
                timeout=args.timeout, lang=args.lang
            )
            if green_island_rain is None:
                text = format_green_island_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(green_island_rain)
                    if args.json
                    else format_daily_rain(green_island_rain)
                )
        elif args.tsuen_wan_rain:
            tsuen_wan_rain = fetch_tsuen_wan_rain(timeout=args.timeout, lang=args.lang)
            if tsuen_wan_rain is None:
                text = format_tsuen_wan_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(tsuen_wan_rain)
                    if args.json
                    else format_daily_rain(tsuen_wan_rain)
                )
        elif args.tap_mun_rain:
            tap_mun_rain = fetch_tap_mun_rain(timeout=args.timeout, lang=args.lang)
            if tap_mun_rain is None:
                text = format_tap_mun_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(tap_mun_rain)
                    if args.json
                    else format_daily_rain(tap_mun_rain)
                )
        elif args.clear_water_bay_rain:
            clear_water_bay_rain = fetch_clear_water_bay_rain(
                timeout=args.timeout, lang=args.lang
            )
            if clear_water_bay_rain is None:
                text = format_clear_water_bay_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(clear_water_bay_rain)
                    if args.json
                    else format_daily_rain(clear_water_bay_rain)
                )
        elif args.shau_kei_wan_rain:
            shau_kei_wan_rain = fetch_shau_kei_wan_rain(
                timeout=args.timeout, lang=args.lang
            )
            if shau_kei_wan_rain is None:
                text = format_shau_kei_wan_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(shau_kei_wan_rain)
                    if args.json
                    else format_daily_rain(shau_kei_wan_rain)
                )
        elif args.happy_valley_rain:
            happy_valley_rain = fetch_happy_valley_rain(
                timeout=args.timeout, lang=args.lang
            )
            if happy_valley_rain is None:
                text = format_happy_valley_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(happy_valley_rain)
                    if args.json
                    else format_daily_rain(happy_valley_rain)
                )
        elif args.tai_mei_tuk_rain:
            tai_mei_tuk_rain = fetch_tai_mei_tuk_rain(
                timeout=args.timeout, lang=args.lang
            )
            if tai_mei_tuk_rain is None:
                text = format_tai_mei_tuk_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mei_tuk_rain)
                    if args.json
                    else format_daily_rain(tai_mei_tuk_rain)
                )
        elif args.kadoorie_farm_rain:
            kadoorie_farm_rain = fetch_kadoorie_farm_rain(
                timeout=args.timeout, lang=args.lang
            )
            if kadoorie_farm_rain is None:
                text = format_kadoorie_farm_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(kadoorie_farm_rain)
                    if args.json
                    else format_daily_rain(kadoorie_farm_rain)
                )
        elif args.the_peak_rain:
            the_peak_rain = fetch_the_peak_rain(timeout=args.timeout, lang=args.lang)
            if the_peak_rain is None:
                text = format_the_peak_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(the_peak_rain)
                    if args.json
                    else format_daily_rain(the_peak_rain)
                )
        elif args.pak_tam_chung_rain:
            pak_tam_chung_rain = fetch_pak_tam_chung_rain(
                timeout=args.timeout, lang=args.lang
            )
            if pak_tam_chung_rain is None:
                text = format_pak_tam_chung_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(pak_tam_chung_rain)
                    if args.json
                    else format_daily_rain(pak_tam_chung_rain)
                )
        elif args.ching_pak_house_rain:
            ching_pak_house_rain = fetch_ching_pak_house_rain(
                timeout=args.timeout, lang=args.lang
            )
            if ching_pak_house_rain is None:
                text = format_ching_pak_house_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(ching_pak_house_rain)
                    if args.json
                    else format_daily_rain(ching_pak_house_rain)
                )
        elif args.kau_sai_chau_rain:
            kau_sai_chau_rain = fetch_kau_sai_chau_rain(
                timeout=args.timeout, lang=args.lang
            )
            if kau_sai_chau_rain is None:
                text = format_kau_sai_chau_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(kau_sai_chau_rain)
                    if args.json
                    else format_daily_rain(kau_sai_chau_rain)
                )
        elif args.kai_tak_rain:
            kai_tak_rain = fetch_kai_tak_rain(timeout=args.timeout, lang=args.lang)
            if kai_tak_rain is None:
                text = format_kai_tak_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(kai_tak_rain)
                    if args.json
                    else format_daily_rain(kai_tak_rain)
                )
        elif args.sha_tau_kok_rain:
            sha_tau_kok_rain = fetch_sha_tau_kok_rain(
                timeout=args.timeout, lang=args.lang
            )
            if sha_tau_kok_rain is None:
                text = format_sha_tau_kok_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_tau_kok_rain)
                    if args.json
                    else format_daily_rain(sha_tau_kok_rain)
                )
        elif args.beas_river_rain:
            beas_river_rain = fetch_beas_river_rain(
                timeout=args.timeout, lang=args.lang
            )
            if beas_river_rain is None:
                text = format_beas_river_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(beas_river_rain)
                    if args.json
                    else format_daily_rain(beas_river_rain)
                )
        elif args.kat_o_rain:
            kat_o_rain = fetch_kat_o_rain(timeout=args.timeout, lang=args.lang)
            if kat_o_rain is None:
                text = format_kat_o_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(kat_o_rain) if args.json else format_daily_rain(kat_o_rain)
                )
        elif args.tap_shek_kok_rain:
            tap_shek_kok_rain = fetch_tap_shek_kok_rain(
                timeout=args.timeout, lang=args.lang
            )
            if tap_shek_kok_rain is None:
                text = format_tap_shek_kok_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(tap_shek_kok_rain)
                    if args.json
                    else format_daily_rain(tap_shek_kok_rain)
                )
        elif args.tsim_bei_tsui_rain:
            tsim_bei_tsui_rain = fetch_tsim_bei_tsui_rain(
                timeout=args.timeout, lang=args.lang
            )
            if tsim_bei_tsui_rain is None:
                text = format_tsim_bei_tsui_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(tsim_bei_tsui_rain)
                    if args.json
                    else format_daily_rain(tsim_bei_tsui_rain)
                )
        elif args.tai_mei_tuk_pump_rain:
            tai_mei_tuk_pump_rain = fetch_tai_mei_tuk_pump_rain(
                timeout=args.timeout, lang=args.lang
            )
            if tai_mei_tuk_pump_rain is None:
                text = format_tai_mei_tuk_pump_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mei_tuk_pump_rain)
                    if args.json
                    else format_daily_rain(tai_mei_tuk_pump_rain)
                )
        elif args.ngong_ping_reservoir_rain:
            ngong_ping_reservoir_rain = fetch_ngong_ping_reservoir_rain(
                timeout=args.timeout, lang=args.lang
            )
            if ngong_ping_reservoir_rain is None:
                text = format_ngong_ping_reservoir_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(ngong_ping_reservoir_rain)
                    if args.json
                    else format_daily_rain(ngong_ping_reservoir_rain)
                )
        elif args.discovery_bay_rain:
            discovery_bay_rain = fetch_discovery_bay_rain(
                timeout=args.timeout, lang=args.lang
            )
            if discovery_bay_rain is None:
                text = format_discovery_bay_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(discovery_bay_rain)
                    if args.json
                    else format_daily_rain(discovery_bay_rain)
                )
        elif args.adventist_college_rain:
            adventist_college_rain = fetch_adventist_college_rain(
                timeout=args.timeout, lang=args.lang
            )
            if adventist_college_rain is None:
                text = format_adventist_college_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(adventist_college_rain)
                    if args.json
                    else format_daily_rain(adventist_college_rain)
                )
        elif args.wong_shiu_chi_rain:
            wong_shiu_chi_rain = fetch_wong_shiu_chi_rain(
                timeout=args.timeout, lang=args.lang
            )
            if wong_shiu_chi_rain is None:
                text = format_wong_shiu_chi_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_shiu_chi_rain)
                    if args.json
                    else format_daily_rain(wong_shiu_chi_rain)
                )
        elif args.au_tau_rain:
            au_tau_rain = fetch_au_tau_rain(timeout=args.timeout, lang=args.lang)
            if au_tau_rain is None:
                text = format_au_tau_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(au_tau_rain) if args.json else format_daily_rain(au_tau_rain)
                )
        elif args.lok_ma_chau_rain:
            lok_ma_chau_rain = fetch_lok_ma_chau_rain(
                timeout=args.timeout, lang=args.lang
            )
            if lok_ma_chau_rain is None:
                text = format_lok_ma_chau_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(lok_ma_chau_rain)
                    if args.json
                    else format_daily_rain(lok_ma_chau_rain)
                )
        elif args.lamma_island_rain:
            lamma_island_rain = fetch_lamma_island_rain(
                timeout=args.timeout, lang=args.lang
            )
            if lamma_island_rain is None:
                text = format_lamma_island_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(lamma_island_rain)
                    if args.json
                    else format_daily_rain(lamma_island_rain)
                )
        elif args.tuen_mun_home_rain:
            tuen_mun_home_rain = fetch_tuen_mun_home_rain(
                timeout=args.timeout, lang=args.lang
            )
            if tuen_mun_home_rain is None:
                text = format_tuen_mun_home_rain_miss(as_json=args.json)
            else:
                text = (
                    format_json(tuen_mun_home_rain)
                    if args.json
                    else format_daily_rain(tuen_mun_home_rain)
                )
        elif args.rainstorm:
            rainstorm = fetch_rainstorm(timeout=args.timeout, lang=args.lang)
            if rainstorm is None:
                text = format_rainstorm_miss(as_json=args.json)
            else:
                text = format_json(rainstorm) if args.json else format_rainstorm(rainstorm)
        elif args.cyclone:
            cyclone = fetch_cyclone(timeout=args.timeout, lang=args.lang)
            if cyclone is None:
                text = format_cyclone_miss(as_json=args.json)
            else:
                text = format_json(cyclone) if args.json else format_cyclone(cyclone)
        elif args.lightning:
            lightning = fetch_lightning(timeout=args.timeout, lang=args.lang)
            text = format_json(lightning) if args.json else format_lightning(lightning)
        elif args.strikes:
            strikes = fetch_strikes(timeout=args.timeout, lang=args.lang)
            if not strikes.counts:
                text = format_strikes_miss(as_json=args.json)
            else:
                text = format_json(strikes) if args.json else format_strikes(strikes)
        elif args.daily_strikes:
            daily_strikes = fetch_daily_strikes(timeout=args.timeout, lang=args.lang)
            if daily_strikes is None:
                text = format_daily_strikes_miss(as_json=args.json)
            else:
                text = (
                    format_json(daily_strikes) if args.json else format_daily_strikes(daily_strikes)
                )
        elif args.cloud_strikes:
            cloud_strikes = fetch_cloud_strikes(timeout=args.timeout, lang=args.lang)
            if cloud_strikes is None:
                text = format_cloud_strikes_miss(as_json=args.json)
            else:
                text = (
                    format_json(cloud_strikes)
                    if args.json
                    else format_cloud_strikes(cloud_strikes)
                )
        elif args.humidity:
            humidity = fetch_humidity(timeout=args.timeout, lang=args.lang)
            text = format_json(humidity) if args.json else format_humidity(humidity)
        elif args.humidity_time:
            humidity_time = fetch_humidity_time(timeout=args.timeout, lang=args.lang)
            if humidity_time is None:
                text = format_humidity_time_miss(as_json=args.json)
            else:
                text = format_json(humidity_time) if args.json else format_humidity_time(humidity_time)
        elif args.minute_humidity:
            minute_humidity = fetch_minute_humidity(timeout=args.timeout, lang=args.lang)
            if not minute_humidity.stations:
                text = format_minute_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(minute_humidity)
                    if args.json
                    else format_minute_humidity(minute_humidity)
                )
        elif args.humidest:
            humidest = fetch_humidest(timeout=args.timeout, lang=args.lang)
            if humidest is None:
                text = format_humidest_miss(as_json=args.json)
            else:
                text = format_json(humidest) if args.json else format_humidest(humidest)
        elif args.least_humid:
            least_humid = fetch_least_humid(timeout=args.timeout, lang=args.lang)
            if least_humid is None:
                text = format_least_humid_miss(as_json=args.json)
            else:
                text = format_json(least_humid) if args.json else format_least_humid(least_humid)
        elif args.mean_humidity:
            mean_humidity = fetch_mean_humidity(timeout=args.timeout, lang=args.lang)
            if mean_humidity is None:
                text = format_mean_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(mean_humidity)
                    if args.json
                    else format_mean_humidity(mean_humidity)
                )
        elif args.tai_mo_humidity:
            tai_mo_humidity = fetch_tai_mo_humidity(timeout=args.timeout, lang=args.lang)
            if tai_mo_humidity is None:
                text = format_tai_mo_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mo_humidity)
                    if args.json
                    else format_mean_humidity(tai_mo_humidity)
                )
        elif args.waglan_humidity:
            waglan_humidity = fetch_waglan_humidity(timeout=args.timeout, lang=args.lang)
            if waglan_humidity is None:
                text = format_waglan_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(waglan_humidity)
                    if args.json
                    else format_mean_humidity(waglan_humidity)
                )
        elif args.tate_humidity:
            tate_humidity = fetch_tate_humidity(timeout=args.timeout, lang=args.lang)
            if tate_humidity is None:
                text = format_tate_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(tate_humidity)
                    if args.json
                    else format_mean_humidity(tate_humidity)
                )
        elif args.ta_kwu_ling_humidity:
            ta_kwu_ling_humidity = fetch_ta_kwu_ling_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if ta_kwu_ling_humidity is None:
                text = format_ta_kwu_ling_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(ta_kwu_ling_humidity)
                    if args.json
                    else format_mean_humidity(ta_kwu_ling_humidity)
                )
        elif args.wetland_humidity:
            wetland_humidity = fetch_wetland_humidity(timeout=args.timeout, lang=args.lang)
            if wetland_humidity is None:
                text = format_wetland_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(wetland_humidity)
                    if args.json
                    else format_mean_humidity(wetland_humidity)
                )
        elif args.shek_kong_humidity:
            shek_kong_humidity = fetch_shek_kong_humidity(timeout=args.timeout, lang=args.lang)
            if shek_kong_humidity is None:
                text = format_shek_kong_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(shek_kong_humidity)
                    if args.json
                    else format_mean_humidity(shek_kong_humidity)
                )
        elif args.lau_fau_humidity:
            lau_fau_humidity = fetch_lau_fau_humidity(timeout=args.timeout, lang=args.lang)
            if lau_fau_humidity is None:
                text = format_lau_fau_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(lau_fau_humidity)
                    if args.json
                    else format_mean_humidity(lau_fau_humidity)
                )
        elif args.park_humidity:
            park_humidity = fetch_park_humidity(timeout=args.timeout, lang=args.lang)
            if park_humidity is None:
                text = format_park_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(park_humidity)
                    if args.json
                    else format_mean_humidity(park_humidity)
                )
        elif args.sai_kung_humidity:
            sai_kung_humidity = fetch_sai_kung_humidity(timeout=args.timeout, lang=args.lang)
            if sai_kung_humidity is None:
                text = format_sai_kung_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(sai_kung_humidity)
                    if args.json
                    else format_mean_humidity(sai_kung_humidity)
                )
        elif args.cheung_chau_humidity:
            cheung_chau_humidity = fetch_cheung_chau_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if cheung_chau_humidity is None:
                text = format_cheung_chau_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(cheung_chau_humidity)
                    if args.json
                    else format_mean_humidity(cheung_chau_humidity)
                )
        elif args.sha_tin_humidity:
            sha_tin_humidity = fetch_sha_tin_humidity(timeout=args.timeout, lang=args.lang)
            if sha_tin_humidity is None:
                text = format_sha_tin_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_tin_humidity)
                    if args.json
                    else format_mean_humidity(sha_tin_humidity)
                )
        elif args.sheung_shui_humidity:
            sheung_shui_humidity = fetch_sheung_shui_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if sheung_shui_humidity is None:
                text = format_sheung_shui_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(sheung_shui_humidity)
                    if args.json
                    else format_mean_humidity(sheung_shui_humidity)
                )
        elif args.wong_chuk_hang_humidity:
            wong_chuk_hang_humidity = fetch_wong_chuk_hang_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if wong_chuk_hang_humidity is None:
                text = format_wong_chuk_hang_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(wong_chuk_hang_humidity)
                    if args.json
                    else format_mean_humidity(wong_chuk_hang_humidity)
                )
        elif args.tseung_kwan_o_humidity:
            tseung_kwan_o_humidity = fetch_tseung_kwan_o_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if tseung_kwan_o_humidity is None:
                text = format_tseung_kwan_o_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(tseung_kwan_o_humidity)
                    if args.json
                    else format_mean_humidity(tseung_kwan_o_humidity)
                )
        elif args.peng_chau_humidity:
            peng_chau_humidity = fetch_peng_chau_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if peng_chau_humidity is None:
                text = format_peng_chau_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(peng_chau_humidity)
                    if args.json
                    else format_mean_humidity(peng_chau_humidity)
                )
        elif args.sha_lo_wan_humidity:
            sha_lo_wan_humidity = fetch_sha_lo_wan_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if sha_lo_wan_humidity is None:
                text = format_sha_lo_wan_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_lo_wan_humidity)
                    if args.json
                    else format_mean_humidity(sha_lo_wan_humidity)
                )
        elif args.airport_humidity:
            airport_humidity = fetch_airport_humidity(timeout=args.timeout, lang=args.lang)
            if airport_humidity is None:
                text = format_airport_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(airport_humidity)
                    if args.json
                    else format_mean_humidity(airport_humidity)
                )
        elif args.tsuen_wan_humidity:
            tsuen_wan_humidity = fetch_tsuen_wan_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if tsuen_wan_humidity is None:
                text = format_tsuen_wan_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(tsuen_wan_humidity)
                    if args.json
                    else format_mean_humidity(tsuen_wan_humidity)
                )
        elif args.hong_kong_park_humidity:
            hong_kong_park_humidity = fetch_hong_kong_park_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if hong_kong_park_humidity is None:
                text = format_hong_kong_park_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(hong_kong_park_humidity)
                    if args.json
                    else format_mean_humidity(hong_kong_park_humidity)
                )
        elif args.clear_water_bay_humidity:
            clear_water_bay_humidity = fetch_clear_water_bay_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if clear_water_bay_humidity is None:
                text = format_clear_water_bay_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(clear_water_bay_humidity)
                    if args.json
                    else format_mean_humidity(clear_water_bay_humidity)
                )
        elif args.shau_kei_wan_humidity:
            shau_kei_wan_humidity = fetch_shau_kei_wan_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if shau_kei_wan_humidity is None:
                text = format_shau_kei_wan_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(shau_kei_wan_humidity)
                    if args.json
                    else format_mean_humidity(shau_kei_wan_humidity)
                )
        elif args.kau_sai_chau_humidity:
            kau_sai_chau_humidity = fetch_kau_sai_chau_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if kau_sai_chau_humidity is None:
                text = format_kau_sai_chau_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(kau_sai_chau_humidity)
                    if args.json
                    else format_mean_humidity(kau_sai_chau_humidity)
                )
        elif args.pak_tam_chung_humidity:
            pak_tam_chung_humidity = fetch_pak_tam_chung_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if pak_tam_chung_humidity is None:
                text = format_pak_tam_chung_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(pak_tam_chung_humidity)
                    if args.json
                    else format_mean_humidity(pak_tam_chung_humidity)
                )
        elif args.beas_river_humidity:
            beas_river_humidity = fetch_beas_river_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if beas_river_humidity is None:
                text = format_beas_river_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(beas_river_humidity)
                    if args.json
                    else format_mean_humidity(beas_river_humidity)
                )
        elif args.runway_park_humidity:
            runway_park_humidity = fetch_runway_park_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if runway_park_humidity is None:
                text = format_runway_park_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(runway_park_humidity)
                    if args.json
                    else format_mean_humidity(runway_park_humidity)
                )
        elif args.kowloon_city_humidity:
            kowloon_city_humidity = fetch_kowloon_city_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if kowloon_city_humidity is None:
                text = format_kowloon_city_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(kowloon_city_humidity)
                    if args.json
                    else format_mean_humidity(kowloon_city_humidity)
                )
        elif args.nei_lak_shan_humidity:
            nei_lak_shan_humidity = fetch_nei_lak_shan_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if nei_lak_shan_humidity is None:
                text = format_nei_lak_shan_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(nei_lak_shan_humidity)
                    if args.json
                    else format_mean_humidity(nei_lak_shan_humidity)
                )
        elif args.new_tsing_yi_humidity:
            new_tsing_yi_humidity = fetch_new_tsing_yi_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if new_tsing_yi_humidity is None:
                text = format_new_tsing_yi_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(new_tsing_yi_humidity)
                    if args.json
                    else format_mean_humidity(new_tsing_yi_humidity)
                )
        elif args.shing_mun_valley_humidity:
            shing_mun_valley_humidity = fetch_shing_mun_valley_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if shing_mun_valley_humidity is None:
                text = format_shing_mun_valley_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(shing_mun_valley_humidity)
                    if args.json
                    else format_mean_humidity(shing_mun_valley_humidity)
                )
        elif args.tuen_mun_home_humidity:
            tuen_mun_home_humidity = fetch_tuen_mun_home_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if tuen_mun_home_humidity is None:
                text = format_tuen_mun_home_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(tuen_mun_home_humidity)
                    if args.json
                    else format_mean_humidity(tuen_mun_home_humidity)
                )
        elif args.buoy_2_humidity:
            buoy_2_humidity = fetch_buoy_2_humidity(
                timeout=args.timeout, lang=args.lang
            )
            if buoy_2_humidity is None:
                text = format_buoy_2_humidity_miss(as_json=args.json)
            else:
                text = (
                    format_json(buoy_2_humidity)
                    if args.json
                    else format_mean_humidity(buoy_2_humidity)
                )
        elif args.temps:
            temps = fetch_temps(timeout=args.timeout, lang=args.lang)
            text = format_json(temps) if args.json else format_temps(temps)
        elif args.temp_time:
            temp_time = fetch_temp_time(timeout=args.timeout, lang=args.lang)
            if temp_time is None:
                text = format_temp_time_miss(as_json=args.json)
            else:
                text = format_json(temp_time) if args.json else format_temp_time(temp_time)
        elif args.minute_temp:
            minute_temp = fetch_minute_temp(timeout=args.timeout, lang=args.lang)
            if not minute_temp.stations:
                text = format_minute_temp_miss(as_json=args.json)
            else:
                text = format_json(minute_temp) if args.json else format_minute_temp(minute_temp)
        elif args.since_midnight:
            since_midnight = fetch_since_midnight(timeout=args.timeout, lang=args.lang)
            if not since_midnight.stations:
                text = format_since_midnight_miss(as_json=args.json)
            else:
                text = (
                    format_json(since_midnight)
                    if args.json
                    else format_since_midnight(since_midnight)
                )
        elif args.pressure:
            pressure = fetch_pressure(timeout=args.timeout, lang=args.lang)
            if not pressure.stations:
                text = format_pressure_miss(as_json=args.json)
            else:
                text = format_json(pressure) if args.json else format_pressure(pressure)
        elif args.mean_pressure:
            mean_pressure = fetch_mean_pressure(timeout=args.timeout, lang=args.lang)
            if mean_pressure is None:
                text = format_mean_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(mean_pressure)
                    if args.json
                    else format_mean_pressure(mean_pressure)
                )
        elif args.park_pressure:
            park_pressure = fetch_park_pressure(timeout=args.timeout, lang=args.lang)
            if park_pressure is None:
                text = format_park_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(park_pressure)
                    if args.json
                    else format_mean_pressure(park_pressure)
                )
        elif args.sha_tin_pressure:
            sha_tin_pressure = fetch_sha_tin_pressure(timeout=args.timeout, lang=args.lang)
            if sha_tin_pressure is None:
                text = format_sha_tin_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_tin_pressure)
                    if args.json
                    else format_mean_pressure(sha_tin_pressure)
                )
        elif args.sheung_shui_pressure:
            sheung_shui_pressure = fetch_sheung_shui_pressure(
                timeout=args.timeout, lang=args.lang
            )
            if sheung_shui_pressure is None:
                text = format_sheung_shui_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(sheung_shui_pressure)
                    if args.json
                    else format_mean_pressure(sheung_shui_pressure)
                )
        elif args.waglan_pressure:
            waglan_pressure = fetch_waglan_pressure(timeout=args.timeout, lang=args.lang)
            if waglan_pressure is None:
                text = format_waglan_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(waglan_pressure)
                    if args.json
                    else format_mean_pressure(waglan_pressure)
                )
        elif args.cheung_chau_pressure:
            cheung_chau_pressure = fetch_cheung_chau_pressure(
                timeout=args.timeout, lang=args.lang
            )
            if cheung_chau_pressure is None:
                text = format_cheung_chau_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(cheung_chau_pressure)
                    if args.json
                    else format_mean_pressure(cheung_chau_pressure)
                )
        elif args.lau_fau_pressure:
            lau_fau_pressure = fetch_lau_fau_pressure(timeout=args.timeout, lang=args.lang)
            if lau_fau_pressure is None:
                text = format_lau_fau_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(lau_fau_pressure)
                    if args.json
                    else format_mean_pressure(lau_fau_pressure)
                )
        elif args.tate_pressure:
            tate_pressure = fetch_tate_pressure(timeout=args.timeout, lang=args.lang)
            if tate_pressure is None:
                text = format_tate_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(tate_pressure)
                    if args.json
                    else format_mean_pressure(tate_pressure)
                )
        elif args.wetland_pressure:
            wetland_pressure = fetch_wetland_pressure(timeout=args.timeout, lang=args.lang)
            if wetland_pressure is None:
                text = format_wetland_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(wetland_pressure)
                    if args.json
                    else format_mean_pressure(wetland_pressure)
                )
        elif args.peng_chau_pressure:
            peng_chau_pressure = fetch_peng_chau_pressure(timeout=args.timeout, lang=args.lang)
            if peng_chau_pressure is None:
                text = format_peng_chau_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(peng_chau_pressure)
                    if args.json
                    else format_mean_pressure(peng_chau_pressure)
                )
        elif args.tai_mo_pressure:
            tai_mo_pressure = fetch_tai_mo_pressure(timeout=args.timeout, lang=args.lang)
            if tai_mo_pressure is None:
                text = format_tai_mo_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(tai_mo_pressure)
                    if args.json
                    else format_mean_pressure(tai_mo_pressure)
                )
        elif args.sha_lo_wan_pressure:
            sha_lo_wan_pressure = fetch_sha_lo_wan_pressure(
                timeout=args.timeout, lang=args.lang
            )
            if sha_lo_wan_pressure is None:
                text = format_sha_lo_wan_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(sha_lo_wan_pressure)
                    if args.json
                    else format_mean_pressure(sha_lo_wan_pressure)
                )
        elif args.shek_kong_pressure:
            shek_kong_pressure = fetch_shek_kong_pressure(
                timeout=args.timeout, lang=args.lang
            )
            if shek_kong_pressure is None:
                text = format_shek_kong_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(shek_kong_pressure)
                    if args.json
                    else format_mean_pressure(shek_kong_pressure)
                )
        elif args.ta_kwu_ling_pressure:
            ta_kwu_ling_pressure = fetch_ta_kwu_ling_pressure(
                timeout=args.timeout, lang=args.lang
            )
            if ta_kwu_ling_pressure is None:
                text = format_ta_kwu_ling_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(ta_kwu_ling_pressure)
                    if args.json
                    else format_mean_pressure(ta_kwu_ling_pressure)
                )
        elif args.airport_pressure:
            airport_pressure = fetch_airport_pressure(timeout=args.timeout, lang=args.lang)
            if airport_pressure is None:
                text = format_airport_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(airport_pressure)
                    if args.json
                    else format_mean_pressure(airport_pressure)
                )
        elif args.nei_lak_shan_pressure:
            nei_lak_shan_pressure = fetch_nei_lak_shan_pressure(
                timeout=args.timeout, lang=args.lang
            )
            if nei_lak_shan_pressure is None:
                text = format_nei_lak_shan_pressure_miss(as_json=args.json)
            else:
                text = (
                    format_json(nei_lak_shan_pressure)
                    if args.json
                    else format_mean_pressure(nei_lak_shan_pressure)
                )
        elif args.minute_grass:
            minute_grass = fetch_minute_grass(timeout=args.timeout, lang=args.lang)
            if not minute_grass.stations:
                text = format_minute_grass_miss(as_json=args.json)
            else:
                text = format_json(minute_grass) if args.json else format_minute_grass(minute_grass)
        elif args.daily_grass:
            daily_grass = fetch_daily_grass(timeout=args.timeout, lang=args.lang)
            if daily_grass is None:
                text = format_daily_grass_miss(as_json=args.json)
            else:
                text = format_json(daily_grass) if args.json else format_daily_grass(daily_grass)
        elif args.obs_grass:
            obs_grass = fetch_obs_grass(timeout=args.timeout, lang=args.lang)
            if obs_grass is None:
                text = format_obs_grass_miss(as_json=args.json)
            else:
                text = format_json(obs_grass) if args.json else format_daily_grass(obs_grass)
        elif args.temp_diff:
            temp_diff = fetch_temp_diff(timeout=args.timeout, lang=args.lang)
            if not temp_diff.stations:
                text = format_temp_diff_miss(as_json=args.json)
            else:
                text = format_json(temp_diff) if args.json else format_temp_diff(temp_diff)
        elif args.heat_index:
            heat_index = fetch_heat_index(timeout=args.timeout, lang=args.lang)
            if not heat_index.stations:
                text = format_heat_index_miss(as_json=args.json)
            else:
                text = format_json(heat_index) if args.json else format_heat_index(heat_index)
        elif args.daily_heat:
            daily_heat = fetch_daily_heat(timeout=args.timeout, lang=args.lang)
            if daily_heat is None:
                text = format_daily_heat_miss(as_json=args.json)
            else:
                text = format_json(daily_heat) if args.json else format_daily_heat(daily_heat)
        elif args.mean_heat:
            mean_heat = fetch_mean_heat(timeout=args.timeout, lang=args.lang)
            if mean_heat is None:
                text = format_mean_heat_miss(as_json=args.json)
            else:
                text = format_json(mean_heat) if args.json else format_mean_heat(mean_heat)
        elif args.wbgt:
            wbgt = fetch_wbgt(timeout=args.timeout, lang=args.lang)
            if not wbgt.stations:
                text = format_wbgt_miss(as_json=args.json)
            else:
                text = format_json(wbgt) if args.json else format_wbgt(wbgt)
        elif args.wet_bulb:
            wet_bulb = fetch_wet_bulb(timeout=args.timeout, lang=args.lang)
            if wet_bulb is None:
                text = format_wet_bulb_miss(as_json=args.json)
            else:
                text = format_json(wet_bulb) if args.json else format_wet_bulb(wet_bulb)
        elif args.airport_wet:
            airport_wet = fetch_airport_wet(timeout=args.timeout, lang=args.lang)
            if airport_wet is None:
                text = format_airport_wet_miss(as_json=args.json)
            else:
                text = format_json(airport_wet) if args.json else format_wet_bulb(airport_wet)
        elif args.park_wet:
            park_wet = fetch_park_wet(timeout=args.timeout, lang=args.lang)
            if park_wet is None:
                text = format_park_wet_miss(as_json=args.json)
            else:
                text = format_json(park_wet) if args.json else format_wet_bulb(park_wet)
        elif args.sha_lo_wan_wet:
            sha_lo_wan_wet = fetch_sha_lo_wan_wet(timeout=args.timeout, lang=args.lang)
            if sha_lo_wan_wet is None:
                text = format_sha_lo_wan_wet_miss(as_json=args.json)
            else:
                text = format_json(sha_lo_wan_wet) if args.json else format_wet_bulb(sha_lo_wan_wet)
        elif args.solar:
            solar = fetch_solar(timeout=args.timeout, lang=args.lang)
            if not solar.stations:
                text = format_solar_miss(as_json=args.json)
            else:
                text = format_json(solar) if args.json else format_solar(solar)
        elif args.global_solar:
            global_solar = fetch_global_solar(timeout=args.timeout, lang=args.lang)
            if global_solar is None:
                text = format_global_solar_miss(as_json=args.json)
            else:
                text = format_json(global_solar) if args.json else format_global_solar(global_solar)
        elif args.kau_sai_chau_solar:
            kau_sai_chau_solar = fetch_kau_sai_chau_solar(
                timeout=args.timeout, lang=args.lang
            )
            if kau_sai_chau_solar is None:
                text = format_kau_sai_chau_solar_miss(as_json=args.json)
            else:
                text = (
                    format_json(kau_sai_chau_solar)
                    if args.json
                    else format_global_solar(kau_sai_chau_solar)
                )
        elif args.hottest:
            hottest = fetch_hottest(timeout=args.timeout, lang=args.lang)
            if hottest is None:
                text = format_hottest_miss(as_json=args.json)
            else:
                text = format_json(hottest) if args.json else format_hottest(hottest)
        elif args.coldest:
            coldest = fetch_coldest(timeout=args.timeout, lang=args.lang)
            if coldest is None:
                text = format_coldest_miss(as_json=args.json)
            else:
                text = format_json(coldest) if args.json else format_coldest(coldest)
        elif args.overnight:
            overnight = fetch_overnight(timeout=args.timeout, lang=args.lang)
            if overnight is None:
                text = format_overnight_miss(as_json=args.json)
            else:
                text = format_json(overnight) if args.json else format_overnight(overnight)
        elif args.noon_rain:
            noon_rain = fetch_noon_rain(timeout=args.timeout, lang=args.lang)
            if noon_rain is None:
                text = format_noon_rain_miss(as_json=args.json)
            else:
                text = format_json(noon_rain) if args.json else format_noon_rain(noon_rain)
        elif args.month_rain:
            month_rain = fetch_month_rain(timeout=args.timeout, lang=args.lang)
            if month_rain is None:
                text = format_month_rain_miss(as_json=args.json)
            else:
                text = format_json(month_rain) if args.json else format_month_rain(month_rain)
        elif args.year_rain:
            year_rain = fetch_year_rain(timeout=args.timeout, lang=args.lang)
            if year_rain is None:
                text = format_year_rain_miss(as_json=args.json)
            else:
                text = format_json(year_rain) if args.json else format_year_rain(year_rain)
        elif args.stations:
            stations = fetch_stations(timeout=args.timeout, lang=args.lang)
            text = format_json(stations) if args.json else format_stations(stations)
        elif args.list_places:
            places = fetch_stations(timeout=args.timeout, lang=args.lang)
            text = format_places(places, as_json=args.json)
        elif args.place is not None:
            query = args.place.strip()
            if not query:
                print("error: place must not be empty", file=sys.stderr)
                return 2
            matched = filter_stations(
                fetch_stations(timeout=args.timeout, lang=args.lang),
                query,
            )
            if matched.stations:
                text = format_json(matched) if args.json else format_stations(matched)
            else:
                text = format_place_miss(query, matched.update_time, as_json=args.json)
        elif args.summary:
            summary = fetch_summary(timeout=args.timeout, lang=args.lang)
            text = format_json(summary) if args.json else format_summary(summary)
        else:
            weather = fetch_current(timeout=args.timeout, lang=args.lang)
            if args.json:
                text = format_json(weather)
            elif args.short:
                text = format_short(weather)
            else:
                text = format_report(weather)
    except WeatherError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0
