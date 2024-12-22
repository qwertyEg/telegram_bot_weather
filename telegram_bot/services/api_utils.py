import logging
import requests

WEB_SERVER_URL = "http://127.0.0.1:8050/get_detailed_forecast"

def get_weather_forecast(start_city, mid_cities, end_city):
    try:
        response = requests.get(
            WEB_SERVER_URL,
            params={
                "start_city": start_city,
                "mid_cities": mid_cities,
                "end_city": end_city,
            },
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе к веб-сервису: {e}")
        return {"error": "Ошибка при соединении с сервером. Попробуйте позже."}
