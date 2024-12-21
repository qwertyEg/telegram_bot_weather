import requests
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from dash import dash_table
import folium #для ТЕПЛОВОЙ карты, пришлось от нее отказаться в силу неоптимизированности
from flask import Flask

# API ключ и URL
API_KEY = "996566916623226a832d3fb57dc04d1b"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"

# Получение данных о погоде

def get_weather_data(city):
    url = f"{BASE_URL}"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
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

# Создание обычной карты с прогнозом погоды

def create_weather_map(city_list):
    weather_map = folium.Map(location=[55.7558, 37.6173], zoom_start=5)

    for city in city_list:
        data = get_weather_data(city)
        if data:
            lat, lon = get_city_coordinates(city)
            if lat and lon:
                weather = data["list"][0]
                popup_text = (
                    f"<b>{city}</b><br>"
                    f"Температура: {weather['main']['temp']}°C<br>"
                    f"Ветер: {weather['wind']['speed']} м/с<br>"
                    f"Осадки: {weather.get('pop', 0) * 100}%"
                )
                folium.Marker([lat, lon], popup=popup_text).add_to(weather_map)

    return weather_map._repr_html_()

# Инициализация Dash приложения

app = dash.Dash(__name__)
server = app.server
app.title = "Визуализация погоды"

app.layout = html.Div([
    html.H1("Визуализация погодных данных", style={"textAlign": "center", "marginBottom": "20px"}),

    # Поля для ввода маршрута
    html.Div([
        html.Div([
            html.Label("Введите начальную точку маршрута:"),
            dcc.Input(
                id="start-city",
                type="text",
                placeholder="Например, Москва",
                style={"width": "300px", "marginBottom": "10px"}
            ),
        ], style={"marginRight": "20px"}),

        html.Div([
            html.Label("Введите промежуточные точки маршрута (по одной в каждой строке):"),
            dcc.Textarea(
                id="mid-cities",
                placeholder="Например:\nТверь\nСанкт-Петербург",
                style={"width": "300px", "height": "100px", "marginBottom": "10px"}
            ),
        ], style={"marginRight": "20px"}),

        html.Div([
            html.Label("Введите конечную точку маршрута:"),
            dcc.Input(
                id="end-city",
                type="text",
                placeholder="Например, Петрозаводск",
                style={"width": "300px", "marginBottom": "20px"}
            ),
        ]),
    ], style={"display": "flex", "justifyContent": "center", "marginBottom": "20px"}),

    # Ползунок для временного интервала
    html.Div([
        html.Label("Выберите временной интервал (в днях):", style={"textAlign": "center", "marginBottom": "10px"}),
        dcc.Slider(
            id="interval-slider",
            min=1,
            max=5,
            step=1,
            marks={i: f"{i} день" for i in range(1, 6)},
            value=3,
            tooltip={"placement": "bottom"}
        ),
    ], style={"width": "50%", "margin": "0 auto", "marginBottom": "20px"}),

    # Кнопка отправки
    html.Div([
        html.Button("Отправить", id="submit-button", n_clicks=0, style={"marginTop": "20px"})
    ], style={"textAlign": "center", "marginBottom": "20px"}),

    # Обычная карта
    html.Div(id="weather-map-container", style={"marginBottom": "20px"}),

    # Вкладки для графиков
    dcc.Tabs(id="tabs", value="temperature", children=[
        dcc.Tab(label="Температура", value="temperature"),
        dcc.Tab(label="Скорость ветра", value="wind_speed"),
        dcc.Tab(label="Вероятность осадков", value="precipitation"),
        dcc.Tab(label="Влажность", value="humidity"),
        dcc.Tab(label="Давление", value="pressure")
    ]),

    # Контейнер для графика
    dcc.Graph(id="weather-graph"),

    # Таблица с данными
    html.Div([
        dash_table.DataTable(
            id="weather-table",
            columns=[
                {"name": "Город", "id": "city"},
                {"name": "Время", "id": "time"},
                {"name": "Температура (°C)", "id": "temperature"},
                {"name": "Скорость ветра (м/с)", "id": "wind_speed"},
                {"name": "Вероятность осадков (%)", "id": "precipitation"},
                {"name": "Влажность (%)", "id": "humidity"},
                {"name": "Давление (гПа)", "id": "pressure"}
            ],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center"},
            style_header={"backgroundColor": "#f4f4f4", "fontWeight": "bold"}
        )
    ], style={"marginTop": "20px"})
])

# Коллбэк для отображения карты
@app.callback(
    Output("weather-map-container", "children"),
    [Input("submit-button", "n_clicks")],
    [State("start-city", "value"), State("mid-cities", "value"), State("end-city", "value")]
)
def update_map(n_clicks, start_city, mid_cities, end_city):
    if not start_city or not end_city:
        return html.Div("Пожалуйста, введите начальную и конечную точки маршрута.", style={"textAlign": "center"})

    city_list = [start_city]
    if mid_cities:
        city_list += [city.strip() for city in mid_cities.split("\n") if city.strip()]
    city_list.append(end_city)

    weather_map_html = create_weather_map(city_list)

    return html.Iframe(srcDoc=weather_map_html, style={"width": "100%", "height": "500px", "border": "none"})

# Коллбэк для обновления графиков и таблицы
@app.callback(
    [Output("weather-graph", "figure"), Output("weather-table", "data")],
    [Input("submit-button", "n_clicks"), Input("tabs", "value")],
    [State("start-city", "value"), State("mid-cities", "value"), State("end-city", "value"), State("interval-slider", "value")]
)
def update_graph_and_table(n_clicks, tab, start_city, mid_cities, end_city, interval):
    if not start_city or not end_city:
        return go.Figure(layout={"title": "Пожалуйста, введите начальную и конечную точки маршрута."}), []

    city_list = [start_city]
    if mid_cities:
        city_list += [city.strip() for city in mid_cities.split("\n") if city.strip()]
    city_list.append(end_city)

    all_data = {}
    combined_table_data = []

    for city in city_list:
        data = get_weather_data(city)
        if data:
            processed_data = [
                {
                    "city": city,
                    "time": entry["dt_txt"],
                    "temperature": entry["main"]["temp"],
                    "wind_speed": entry["wind"]["speed"],
                    "precipitation": entry.get("pop", 0) * 100,
                    "humidity": entry["main"]["humidity"],
                    "pressure": entry["main"]["pressure"]
                }
                for entry in data["list"][:interval * 8]
            ]
            all_data[city] = processed_data
            combined_table_data.extend(processed_data)

    if tab == "temperature":
        fig = go.Figure()
        for city, data in all_data.items():
            fig.add_trace(go.Scatter(
                x=[entry["time"] for entry in data],
                y=[entry["temperature"] for entry in data],
                mode="lines+markers",
                name=city
            ))
        fig.update_layout(title="Температура по маршруту", xaxis_title="Время", yaxis_title="Температура (°C)")

    elif tab == "wind_speed":
        fig = go.Figure()
        for city, data in all_data.items():
            fig.add_trace(go.Bar(
                x=[entry["time"] for entry in data],
                y=[entry["wind_speed"] for entry in data],
                name=city
            ))
        fig.update_layout(title="Скорость ветра по маршруту", xaxis_title="Время", yaxis_title="Скорость ветра (м/с)")

    elif tab == "precipitation":
        fig = go.Figure()
        for city, data in all_data.items():
            fig.add_trace(go.Bar(
                x=[entry["time"] for entry in data],
                y=[entry["precipitation"] for entry in data],
                name=city
            ))
        fig.update_layout(title="Вероятность осадков по маршруту", xaxis_title="Время", yaxis_title="Вероятность осадков (%)", legend=dict(x=1, y=1, traceorder="normal"))

    elif tab == "humidity":
        fig = go.Figure()
        for city, data in all_data.items():
            fig.add_trace(go.Scatter(
                x=[entry["time"] for entry in data],
                y=[entry["humidity"] for entry in data],
                mode="lines+markers",
                name=city
            ))
        fig.update_layout(title="Влажность по маршруту", xaxis_title="Время", yaxis_title="Влажность (%)")

    elif tab == "pressure":
        fig = go.Figure()
        for city, data in all_data.items():
            fig.add_trace(go.Scatter(
                x=[entry["time"] for entry in data],
                y=[entry["pressure"] for entry in data],
                mode="lines+markers",
                name=city
            ))
        fig.update_layout(title="Давление по маршруту", xaxis_title="Время", yaxis_title="Давление (гПа)")

    return fig, combined_table_data

if __name__ == "__main__":
    app.run(debug=True)










