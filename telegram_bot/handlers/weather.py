from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

# Состояния для машины состояний
class WeatherForm(StatesGroup):
    start_city = State()
    mid_cities = State()
    end_city = State()
    interval = State()
    choice = State()

# Генерация клавиатуры для выбора действия
def generate_weather_options():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Карта прогноза", callback_data="map"),
        InlineKeyboardButton("График температуры", callback_data="graph_temperature"),
        InlineKeyboardButton("График влажности", callback_data="graph_humidity"),
        InlineKeyboardButton("График ветра", callback_data="graph_wind_speed"),
        InlineKeyboardButton("График давления", callback_data="graph_pressure"),
        InlineKeyboardButton("График осадков", callback_data="graph_precipitation"),
        InlineKeyboardButton("Текстовый прогноз", callback_data="forecast")
    )
    keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_interval"))
    return keyboard

# Обработка текстового прогноза
async def handle_forecast_selection(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    start_city = data.get("start_city")
    end_city = data.get("end_city")
    mid_cities = data.get("mid_cities")

    url = f"http://127.0.0.1:8050/get_detailed_forecast?start_city={start_city}&mid_cities={mid_cities}&end_city={end_city}"
    response = requests.get(url)
    if response.status_code == 200:
        forecast = response.json().get("forecast")
        await callback_query.message.answer(f"Прогноз погоды:\n\n{forecast}")
    else:
        await callback_query.message.answer("Не удалось загрузить прогноз. Попробуйте позже.")



# Генерация клавиатуры для выбора интервала
def generate_interval_options():
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("1 день", callback_data="interval_1"),
        InlineKeyboardButton("3 дня", callback_data="interval_3"),
        InlineKeyboardButton("5 дней", callback_data="interval_5")
    )
    return keyboard

# Команда /weather
async def weather_command(message: types.Message):
    await WeatherForm.start_city.set()
    await message.answer("Введите начальный город:")

# Обработка начального города
async def process_start_city(message: types.Message, state: FSMContext):
    await state.update_data(start_city=message.text)
    await WeatherForm.next()
    await message.answer("Введите промежуточные города через запятую (или напишите 'нет'):")

# Обработка промежуточных городов
async def process_mid_cities(message: types.Message, state: FSMContext):
    mid_cities = message.text if message.text.lower() != "нет" else ""
    await state.update_data(mid_cities=mid_cities)
    await WeatherForm.next()
    await message.answer("Введите конечный город:")

# Обработка конечного города
async def process_end_city(message: types.Message, state: FSMContext):
    await state.update_data(end_city=message.text)
    await WeatherForm.next()
    await message.answer("Выберите интервал прогноза:", reply_markup=generate_interval_options())

# Обработка выбора интервала
async def handle_interval_selection(callback_query: types.CallbackQuery, state: FSMContext):
    interval = int(callback_query.data.split("_")[1])
    await state.update_data(interval=interval)
    await callback_query.message.answer("Интервал прогноза установлен. Выберите действие:", reply_markup=generate_weather_options())
    await WeatherForm.next()

# Обработка выбора графика
async def handle_graph_selection(callback_query: types.CallbackQuery, state: FSMContext):
    graph_type = callback_query.data.replace("graph_", "")
    data = await state.get_data()
    start_city = data.get("start_city")
    end_city = data.get("end_city")
    mid_cities = data.get("mid_cities")
    interval = data.get("interval", 1)

    url = f"http://127.0.0.1:8050/generate_graph/{graph_type}?start_city={start_city}&mid_cities={mid_cities}&end_city={end_city}&interval={interval}"
    response = requests.get(url)

    if response.status_code == 200:
        # Сохраняем график как файл и отправляем пользователю
        with open(f"{graph_type}.png", "wb") as file:
            file.write(response.content)

        with open(f"{graph_type}.png", "rb") as file:
            await callback_query.message.answer_photo(file, caption=f"График: {graph_type}")

        # После отправки графика возвращаем пользователя в выбор действий
        await callback_query.message.answer("Выберите следующее действие:", reply_markup=generate_weather_options())
        await WeatherForm.choice.set()
    else:
        await callback_query.message.answer("Не удалось загрузить график. Попробуйте позже.")


async def handle_map_selection(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    start_city = data.get("start_city")
    mid_cities = data.get("mid_cities", "")
    end_city = data.get("end_city")

    # Формируем запрос
    url = f"http://127.0.0.1:8050/generate_map_interactive?start_city={start_city}&mid_cities={mid_cities}&end_city={end_city}"
    response = requests.get(url)

    if response.status_code == 200:
        map_url = response.json().get("url")
        await callback_query.message.answer(f"Карта прогноза: [Открыть карту]({map_url})", parse_mode="Markdown")
    else:
        await callback_query.message.answer("Не удалось загрузить карту. Попробуйте позже.")


# Обработка текстового прогноза
async def handle_forecast_selection(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    start_city = data.get("start_city")
    end_city = data.get("end_city")
    mid_cities = data.get("mid_cities")

    url = f"http://127.0.0.1:8050/get_detailed_forecast?start_city={start_city}&mid_cities={mid_cities}&end_city={end_city}"
    response = requests.get(url)
    if response.status_code == 200:
        forecast = response.json().get("forecast")
        await callback_query.message.answer(f"Прогноз погоды:\n\n{forecast}")
    else:
        await callback_query.message.answer("Не удалось загрузить прогноз. Попробуйте позже.")

# Обработка кнопки "Назад"
async def handle_back_to_interval(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Выберите интервал прогноза:", reply_markup=generate_interval_options())
    await WeatherForm.interval.set()  # Переводим бота в состояние выбора интервала




# Регистрация хендлеров
def register_handlers_weather(dp: Dispatcher):
    dp.register_message_handler(weather_command, commands=["weather"], state="*")
    dp.register_message_handler(process_start_city, state=WeatherForm.start_city)
    dp.register_message_handler(process_mid_cities, state=WeatherForm.mid_cities)
    dp.register_message_handler(process_end_city, state=WeatherForm.end_city)
    dp.register_callback_query_handler(handle_interval_selection, lambda c: c.data.startswith("interval_"), state=WeatherForm.interval)
    dp.register_callback_query_handler(handle_graph_selection, lambda c: c.data.startswith("graph_"), state=WeatherForm.choice)
    dp.register_callback_query_handler(handle_map_selection, lambda c: c.data == "map", state=WeatherForm.choice)
    dp.register_callback_query_handler(handle_forecast_selection, lambda c: c.data == "forecast", state=WeatherForm.choice)
    dp.register_callback_query_handler(
        handle_back_to_interval,
        lambda c: c.data == "back_to_interval",
        state=WeatherForm.choice
    )


