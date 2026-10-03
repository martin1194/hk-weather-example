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


# Same codes as WEATHER_ICONS. Unmapped codes get no emoji.
ICON_EMOJI: dict[int, str] = {
    50: "☀️",
    51: "🌤️",
    52: "⛅",
    53: "🌦️",
    54: "🌦️",
    60: "☁️",
    61: "☁️",
    62: "🌦️",
    63: "🌧️",
    64: "🌧️",
    65: "⛈️",
    70: "🌙",
    71: "🌙",
    72: "🌙",
    73: "🌙",
    74: "🌙",
    75: "🌙",
    76: "☁️",
    77: "🌤️",
    80: "💨",
    81: "🏜️",
    82: "💧",
    83: "🌫️",
    84: "🌫️",
    85: "🌫️",
    90: "🥵",
    91: "🌡️",
    92: "🍃",
    93: "🥶",
}

_LABEL_EMOJI: dict[str, str] = {}
for _code, _label in WEATHER_ICONS.items():
    _emoji = ICON_EMOJI.get(_code)
    if _emoji and _label not in _LABEL_EMOJI:
        _LABEL_EMOJI[_label] = _emoji


def icon_label(code: int) -> str:
    return WEATHER_ICONS.get(code, f"Icon {code}")


def conditions_with_emoji(conditions: str) -> str:
    """Prefix known condition labels with their icon emoji.

    Missing or unmapped text is returned unchanged.
    """
    parts = conditions.split(", ")
    emojis = [_LABEL_EMOJI.get(part) for part in parts]
    if not any(emojis):
        return conditions
    rendered = [
        f"{emoji} {part}" if emoji else part for emoji, part in zip(emojis, parts)
    ]
    return ", ".join(rendered)
