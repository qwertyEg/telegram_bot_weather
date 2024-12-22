import aiohttp
from telegram_bot.utils.config import ACCUWEATHER_URL

async def get_weather_from_accuweather(city):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{ACCUWEATHER_URL}/check-weather", params={"city": city}) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return {"error": "Город не найден"}
                elif response.status == 500:
                    return {"error": "Ошибка сервера AccuWeather"}
                else:
                    return {"error": f"Неизвестная ошибка: {response.status}"}
        except aiohttp.ClientConnectorError:
            return {"error": "Не удалось подключиться к AccuWeather"}
        except aiohttp.ClientTimeout:
            return {"error": "Превышено время ожидания ответа от AccuWeather"}
