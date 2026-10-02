"""Current Hong Kong weather from the Hong Kong Observatory open data API."""

from hk_weather.hko import CurrentWeather, WeatherError, fetch_current, format_report

__all__ = ["CurrentWeather", "WeatherError", "fetch_current", "format_report"]
__version__ = "0.1.0"
