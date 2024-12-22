from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_graph_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="Температура", callback_data="temperature"),
        InlineKeyboardButton(text="Скорость ветра", callback_data="wind_speed"),
        InlineKeyboardButton(text="Осадки", callback_data="precipitation"),
        InlineKeyboardButton(text="Влажность", callback_data="humidity"),
        InlineKeyboardButton(text="Давление", callback_data="pressure"),
    ]
    keyboard.add(*buttons)
    return keyboard



def create_interval_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("1 день", callback_data="1"),
        InlineKeyboardButton("3 дня", callback_data="3"),
        InlineKeyboardButton("5 дней", callback_data="5")
    )
    return keyboard


def create_confirmation_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Подтвердить", callback_data="confirm"),
        InlineKeyboardButton("Отменить", callback_data="cancel")
    )
    return keyboard

