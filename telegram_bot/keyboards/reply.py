from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("AccuWeather"))
    keyboard.add(KeyboardButton("OpenWeather"))
    return keyboard
