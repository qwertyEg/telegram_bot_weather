import urllib.parse
import aiohttp
from telegram_bot.utils.config import OPENWEATHER_URL

async def get_weather_from_openweather(city):
    encoded_city = urllib.parse.quote(city)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{OPENWEATHER_URL}/check-weather", params={"city": encoded_city}) as response:
                if response.status == 200:
                    return await response.json()
                return {"error": f"Ошибка {response.status}: {await response.text()}"}
        except aiohttp.ClientConnectorError:
            return {"error": "Ошибка подключения к OpenWeather"}
        except aiohttp.ClientTimeout:
            return {"error": "Время ожидания ответа истекло"}


