from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Стартовая клавиатура
start_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="➕ Выбрать номер и забронировать"), KeyboardButton(text="📋 Текущие брони")],
    [KeyboardButton(text="➖ Удалить бронь"), KeyboardButton(text="/start")]
], resize_keyboard=True, input_field_placeholder="Что хотите сделать?")

# Запрос контакта
request_contact = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="☎️ Поделиться контактом?",request_contact=True)]])

# Удаление брони