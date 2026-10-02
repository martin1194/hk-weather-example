"""Hong Kong Observatory weather icon numbers.

Captions follow the public icon list:
https://www.hko.gov.hk/en/textonly/explain/wxicon.htm
Night-time "Fine" icons (70-75) differ by lunar date; the short label is enough here.
"""

WEATHER_ICONS: dict[int, str] = {
    50: "Sunny",
    51: "Sunny Periods",
    52: "Sunny Intervals",
    53: "Sunny Periods with A Few Showers",
    54: "Sunny Intervals with Showers",
    60: "Cloudy",
    61: "Overcast",
    62: "Light Rain",
    63: "Rain",
    64: "Heavy Rain",
    65: "Thunderstorms",
    70: "Fine",
    71: "Fine",
    72: "Fine",
    73: "Fine",
    74: "Fine",
    75: "Fine",
    76: "Mainly Cloudy",
    77: "Mainly Fine",
    80: "Windy",
    81: "Dry",
    82: "Humid",
    83: "Fog",
    84: "Mist",
    85: "Haze",
    90: "Hot",
    91: "Warm",
    92: "Cool",
    93: "Cold",
}


def icon_label(code: int) -> str:
    return WEATHER_ICONS.get(code, f"Icon {code}")
