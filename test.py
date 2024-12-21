import requests

API_KEY = ""
TEST_URL = "http://api.openweathermap.org/data/2.5/weather"

params = {
    "q": "Москва",
    "appid": API_KEY,
    "units": "metric"
}

response = requests.get(TEST_URL, params=params)

if response.status_code == 200:
    print("API доступен. Ответ:", response.json())
else:
    print(f"Ошибка: {response.status_code}, {response.json()}")
