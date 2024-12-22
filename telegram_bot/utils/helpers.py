def format_weather_data(data):
    return (
        f"Температура: {data['temperature']}°C\n"
        f"Ветер: {data['wind_speed']} м/с\n"
        f"Осадки: {data['precipitation_probability']}%"
    )
