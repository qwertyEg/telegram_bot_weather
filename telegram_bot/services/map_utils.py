import plotly.graph_objects as go
import io


async def generate_interactive_map(route, weather_data):
    """
    Генерирует интерактивную карту маршрута и погодных данных.

    :param route: список координат маршрута [(lat1, lon1), (lat2, lon2), ...]
    :param weather_data: список данных о погоде по точкам маршрута
    :return: байтовые данные изображения карты
    """
    latitudes = [point[0] for point in route]
    longitudes = [point[1] for point in route]
    cities = [data["city"] for data in weather_data]
    temperatures = [data["temperature"] for data in weather_data]

    fig = go.Figure()

    fig.add_trace(go.Scattermapbox(
        mode="markers+lines",
        lon=longitudes,
        lat=latitudes,
        marker={'size': 10, 'color': 'blue'},
        line={'width': 3, 'color': 'royalblue'},
        text=[f"{city}: {temp}°C" for city, temp in zip(cities, temperatures)],
        name="Маршрут"
    ))

    fig.update_layout(
        mapbox={
            'style': "carto-positron",
            'center': {'lat': latitudes[0], 'lon': longitudes[0]},
            'zoom': 5,
        },
        title="Интерактивная карта маршрута",
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    buf = io.BytesIO()
    fig.write_image(buf, format='png')
    buf.seek(0)

    return buf

