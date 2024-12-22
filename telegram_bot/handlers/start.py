from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command

async def start_command(message: types.Message, state: FSMContext):
    await message.answer(
        "Добро пожаловать в WeatherBot! 🌤\n"
        "Я помогу вам узнать прогноз погоды для маршрута.\n"
        "Для списка доступных команд используйте /help."
    )



