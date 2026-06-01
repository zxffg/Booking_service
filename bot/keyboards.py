from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardButton, InlineKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.repository import get_user_bookings

# Стартовая клавиатура
start_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="➕ Выбрать номер и забронировать"), KeyboardButton(text="📋 Текущие брони")],
    [KeyboardButton(text="➖ Удалить бронь"), KeyboardButton(text="/start")]
], resize_keyboard=True, input_field_placeholder="Что хотите сделать?")

# Запрос контакта
request_contact = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="☎️ Поделиться контактом?",request_contact=True)]])

# inline для удаления брони
async def delete_keyboard(user_id: int):
    keyboard = InlineKeyboardBuilder()
    data = await get_user_bookings(user_id)
    for row in data:
        button_text = f"ID бронирования: {row[0]}. Даты проживания {row[3]}.\nID номера: {row[2]}"
        callback_value = f"del:{row[0]}"
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_value))
    keyboard.adjust(1)
    return keyboard.as_markup()