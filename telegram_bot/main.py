from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils.config import BOT_TOKEN
from handlers.start import start_command
from handlers.help import help_command
from handlers.weather import register_handlers_weather

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Регистрация хэндлеров
dp.register_message_handler(start_command, commands=["start"])
dp.register_message_handler(help_command, commands=["help"])

# Регистрация хэндлеров для работы с погодой
register_handlers_weather(dp)

if __name__ == "__main__":
    from utils.logging import logger

    logger.info("Бот запущен!")
    executor.start_polling(dp, skip_updates=True)










