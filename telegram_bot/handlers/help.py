from aiogram import types

async def help_command(message: types.Message):
    await message.answer(
        "Вот список доступных команд:\n"
        "/start - Приветствие и описание возможностей\n"
        "/help - Список команд и инструкция\n"
        "/weather - Прогноз погоды для маршрута\n\n"
        "Пример использования команды:\n"
        "/weather Москва Тверь Санкт-Петербург"
    )
