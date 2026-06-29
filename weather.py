# Zelretch Addons — Weather plugin
# Ported from Ultroid plugins/weather.py
# Copyright (C) 2021-2026 TeamUltroid — AGPL v3
# Copyright (C) 2026 Zelretch Contributors

"""
✘ Commands Available

• `{i}weather <city>`
    Show current weather for a city (OpenWeatherMap).
"""

import requests

from zelretch.config import get_config
from zelretch.core.decorators import zelretch_cmd
from zelretch.core.wrappers import eor


@zelretch_cmd(pattern=r"weather ?(.*)")
async def weather(client, message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return await eor(message, "`Give a city name.`")
    city = parts[1].strip()
    api_key = get_config("OPEN_WEATHER_MAP_APPID", "")
    if not api_key:
        return await eor(message, "`OpenWeatherMap API key not set. Add OPEN_WEATHER_MAP_APPID to config.`")
    msg = await message.reply_text(f"`Fetching weather for {city}…`")
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=15,
        )
        data = resp.json()
        if data.get("cod") != 200:
            return await msg.edit_text(f"`{data.get('message', 'Error')}`")
        main = data["main"]
        weather = data["weather"][0]
        text = (
            f"**Weather — {data['name']}, {data['sys']['country']}**\n\n"
            f"• **Condition:** {weather['main']} ({weather['description']})\n"
            f"• **Temp:** {main['temp']}°C (feels like {main['feels_like']}°C)\n"
            f"• **Humidity:** {main['humidity']}%\n"
            f"• **Wind:** {data['wind']['speed']} m/s"
        )
        await msg.edit_text(text)
    except Exception as err:
        await msg.edit_text(f"`{err}`")
