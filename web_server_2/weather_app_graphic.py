from flask import Flask, request, jsonify, send_file, render_template_string
import requests
import io
from urllib.parse import unquote, unquote_plus, quote
import plotly.graph_objects as go
import os
import aiohttp
import asyncio
import logging
import urllib


# API ключ и URL
API_KEY = "57329f26a9f5f1a4b08f5f000e67e00d"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"

# Инициализация Flask
app = Flask(__name__)

# Получение данных о погоде

def get_weather_data(city):
    # Кодируем название города в правильной кодировке
    city_encoded = quote(city)
    url = f"{BASE_URL}?q={city_encoded}&appid={API_KEY}&units=metric&lang=ru"
    try:
        logging.debug(f"Отправка запроса на URL: {url}")
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе API для города {city}: {e}")
        return None



# Получение координат города
def get_city_coordinates(city):
    url = f"http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city,
        "appid": API_KEY,
        "limit": 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]["lat"], data[0]["lon"]
    return None, None


@app.route("/generate_graph/<graph_type>")
def generate_graph(graph_type):
    try:
        start_city = unquote_plus(request.args.get("start_city", "").strip())
        mid_cities = unquote_plus(request.args.get("mid_cities", "").strip())
        end_city = unquote_plus(request.args.get("end_city", "").strip())
        interval = int(request.args.get("interval", 1))
    except Exception as e:
        app.logger.error(f"Ошибка при декодировании параметров: {e}")
        return jsonify({"error": "Ошибка при декодировании параметров"}), 400

    # Проверка городов
    cities = [start_city] + [city.strip() for city in mid_cities.split(",") if city.strip()] + [end_city]
    valid_cities = []
    for city in cities:
        lat, lon = get_city_coordinates(city)
        if lat and lon:
            valid_cities.append(city)
        else:
            app.logger.warning(f"Город '{city}' не найден.")
            return jsonify({"error": f"Город '{city}' не найден"}), 400

    # Сбор данных для графика
    all_data = {}
    for city in valid_cities:
        data = get_weather_data(city)
        if data:
            all_data[city] = [
                {
                    "time": entry["dt_txt"],
                    "temperature": entry["main"]["temp"],
                    "wind_speed": entry["wind"]["speed"],
                    "precipitation": entry.get("pop", 0) * 100,
                    "humidity": entry["main"]["humidity"],
                    "pressure": entry["main"]["pressure"]
                }
                for entry in data["list"][:interval * 8]
            ]

    if not all_data:
        return jsonify({"error": "Нет данных для графика"}), 400

    # Генерация графика
    fig = go.Figure()
    if graph_type in ["temperature", "humidity", "wind_speed", "pressure", "precipitation"]:
        for city, data in all_data.items():
            fig.add_trace(go.Scatter(
                x=[entry["time"] for entry in data],
                y=[entry[graph_type] for entry in data],
                mode="lines+markers",
                name=city
            ))

        titles = {
            "temperature": "Температура (°C)",
            "humidity": "Влажность (%)",
            "wind_speed": "Скорость ветра (м/с)",
            "pressure": "Давление (гПа)",
            "precipitation": "Осадки (%)"
        }

        fig.update_layout(
            title=f"{titles[graph_type]} по маршруту",
            xaxis_title="Время",
            yaxis_title=titles[graph_type]
        )
    else:
        return jsonify({"error": "Неверный тип графика"}), 400

    # Сохранение графика в память
    output = io.BytesIO()
    fig.write_image(output, format="png")
    output.seek(0)

    return send_file(output, mimetype="image/png", as_attachment=True, download_name="graph.png")



# Генерация карты с использованием асинхронных запросов
async def create_interactive_map_with_weather(cities):
    app.logger.debug(f"Начало генерации карты для городов: {cities}")

    latitudes = []
    longitudes = []
    annotations = []

    weather_data_list = await fetch_all_weather(cities)
    coordinates_list = await fetch_all_coordinates(cities)

    for city, weather_data, coords in zip(cities, weather_data_list, coordinates_list):
        app.logger.debug(f"Обработка города: {city}")
        if not weather_data:
            app.logger.error(f"Нет данных о погоде для города {city}")
            continue
        if not coords or coords == (None, None):
            app.logger.error(f"Не удалось получить координаты для города {city}")
            continue

        lat, lon = coords
        temperature = weather_data["list"][0]["main"]["temp"]
        wind_speed = weather_data["list"][0]["wind"]["speed"]
        precipitation = weather_data["list"][0].get("pop", 0) * 100

        latitudes.append(lat)
        longitudes.append(lon)
        annotations.append(
            f"<b>{city}</b><br>Температура: {temperature}°C<br>Ветер: {wind_speed} м/с<br>Осадки: {precipitation}%"
        )

    if not latitudes or not longitudes:
        raise ValueError("Не удалось получить данные для карты. Проверьте корректность городов.")

    app.logger.debug(f"Собраны данные: latitudes={latitudes}, longitudes={longitudes}, annotations={annotations}")

    # Генерация карты
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=latitudes,
        lon=longitudes,
        mode="markers+text",
        marker=go.scattermapbox.Marker(size=14, color="blue"),
        text=annotations,
        textposition="top center",
        hoverinfo="text"
    ))
    fig.update_layout(
        mapbox={
            "style": "carto-positron",
            "center": {"lat": latitudes[0], "lon": longitudes[0]},
            "zoom": 5,
        },
        title="Интерактивная карта прогноза погоды",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig

# Асинхронная функция для получения координат города
async def fetch_coordinates(session, city):
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city,
        "appid": API_KEY,
        "limit": 1
    }
    try:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    return data[0]["lat"], data[0]["lon"]
            return None, None
    except Exception as e:
        app.logger.error(f"Ошибка сети при запросе координат для города {city}: {e}")
        return None, None


async def fetch_all_coordinates(cities):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_coordinates(session, city) for city in cities]
        return await asyncio.gather(*tasks)


@app.route("/generate_map_interactive", methods=["GET"])
async def generate_map_interactive():
    try:
        # Декодируем параметры без использования 'latin-1'
        start_city = request.args.get("start_city", "").strip()
        mid_cities = request.args.get("mid_cities", "").strip()
        end_city = request.args.get("end_city", "").strip()

        app.logger.debug(f"Полученные параметры: start_city={start_city}, mid_cities={mid_cities}, end_city={end_city}")

        # Формируем список городов
        cities = [start_city] + [city.strip() for city in mid_cities.split(",") if city.strip()] + [end_city]

        # Генерация карты
        fig = await create_interactive_map_with_weather(cities)

        # Сохраняем карту
        html_file = os.path.join(os.getcwd(), "telegram_bot/web_server_2/interactive_map.html")
        fig.write_html(html_file)

        # Логируем путь к файлу
        app.logger.debug(f"Карта сохранена в файле: {html_file}")

        # Возвращаем ссылку на карту
        return jsonify({"url": f"http://127.0.0.1:8050/telegram_bot/web_server_2/interactive_map.html"})
    except ValueError as e:
        app.logger.error(f"Ошибка при генерации карты: {e}")
        return jsonify({"error": f"Ошибка при генерации карты: {e}"}), 400
    except Exception as e:
        app.logger.error(f"Неизвестная ошибка при генерации карты: {e}")
        return jsonify({"error": f"Неизвестная ошибка при генерации карты: {e}"}), 500






# Сервис для отображения HTML файла
@app.route("/<path:filename>")
def serve_html(filename):
    file_path = f"/Users/egor/Desktop/PROJECT3/VisualWebServer/web_server_2/{filename}"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        app.logger.error(f"Файл не найден: {file_path}")
        return "Файл не найден", 404

# Асинхронная функция для получения данных о погоде (для карты)
async def fetch_weather(session, city):
    url = f"{BASE_URL}"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    try:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                app.logger.error(f"Ошибка при запросе API для города {city}: {response.status}")
                return None
    except Exception as e:
        app.logger.error(f"Ошибка сети при запросе для города {city}: {e}")
        return None

# Асинхронная функция для получения прогнозов для списка городов
async def fetch_all_weather(cities):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_weather(session, city) for city in cities]
        return await asyncio.gather(*tasks)

# Обновленный маршрут
@app.route("/get_detailed_forecast", methods=["GET"])
def get_detailed_forecast():
    try:
        # Декодирование параметров
        start_city = request.args.get("start_city", "").strip()
        mid_cities = request.args.get("mid_cities", "").strip()
        end_city = request.args.get("end_city", "").strip()

        # Декодируем и формируем список городов
        start_city = unquote_plus(start_city)
        mid_cities = [unquote_plus(city.strip()) for city in mid_cities.split(",") if city.strip()]
        end_city = unquote_plus(end_city)

        cities = [start_city] + mid_cities + [end_city]
        logging.debug(f"Список городов для прогноза: {cities}")

        forecast_text = []

        # Получение данных для каждого города
        for city in cities:
            city_encoded = quote(city)
            logging.debug(f"Город: {city}, Кодированный: {city_encoded}")
            data = get_weather_data(city)
            if data:
                # Получение первого значения прогноза
                forecast = data["list"][0]
                temp = forecast["main"]["temp"]
                humidity = forecast["main"]["humidity"]
                wind_speed = forecast["wind"]["speed"]
                pressure = forecast["main"]["pressure"]

                forecast_text.append(
                    f"{city}:\n"
                    f"- Температура: {temp}°C\n"
                    f"- Влажность: {humidity}%\n"
                    f"- Ветер: {wind_speed} м/с\n"
                    f"- Давление: {pressure} гПа\n"
                )
            else:
                forecast_text.append(f"{city}:\n- Данные о погоде недоступны.\n")

        # Возвращаем текстовый ответ
        result = "\n".join(forecast_text)
        logging.debug(f"Сформированный текст прогноза:\n{result}")
        return jsonify({"forecast": result})

    except Exception as e:
        logging.error(f"Ошибка при обработке прогноза: {e}")
        return jsonify({"error": "Ошибка при обработке запроса"}), 500







if __name__ == "__main__":
    app.run(debug=True, port=8050)



























