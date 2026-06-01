from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ErrorEvent

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from datetime import datetime

from db.repository import (check_user, get_user_id, create_user, 
                           get_available_rooms, cancel_booking, 
                           get_user_bookings_history, confirm_booking,
                           get_booking_dates, get_booking_status)

from bot.keyboards import (start_keyboard, request_contact, delete_keyboard)

from services.booking_service import create_booking_flow

import asyncio

from services.redis_service import (set_booking_cache, delete_booking_cache, 
                                    acquire_lock, release_lock)

router = Router()


#! Ответ на команду старт. Регистрация пользователя
class AddNewUser(StatesGroup):
    wait_fullname = State()
    wait_phone = State()
# Ответ на команду старт и перезапуск бота
@router.message(CommandStart())
async def restart_bot(message: Message, state: FSMContext):
    if await check_user(message.from_user.username):
        await message.answer(text="🏨 Привет! Меня зовут Юлия, я - твой личный помощник при бронировании номеров! Что Вас интересует?", reply_markup=start_keyboard)
    else:
        await message.answer(text="🏨 Привет! Меня зовут Юлия, я - твой личный помощник при бронировании номеров! Пройди регистрацию, чтобы создать свою первую бронь!\n\nВведите свое полное имя:")
        await state.set_state(AddNewUser.wait_fullname)
# Добавление нового пользователя
@router.message(AddNewUser.wait_fullname)
async def get_phone(message: Message, state: FSMContext):
    if not isinstance(message.text, str):
        await message.answer(text="Это не текст! Пожалуйста, укажите ваше имя, строго использую только буквы")
        return
    
    await state.update_data(fullname=message.text)
    await state.set_state(AddNewUser.wait_phone)
    await message.answer(text="💐 Спасибо! А тперь мне нужен ваш номер телефона, чтобы я могла связаться с вами.", reply_markup=request_contact)
# Конец регистрации нового пользователя и добавление в бд
@router.message(AddNewUser.wait_phone)
async def add_new_user(message: Message, state: FSMContext):
    if message.contact is None:
        await message.answer(text="Что-то пошло не так! Пожалуйста, укажите свой номер телефона!")
        return

    await state.update_data(phone=message.contact.phone_number)
    user_data = await state.get_data()
    fullname = user_data['fullname']
    phone = user_data['phone']

    await create_user(message.from_user.username, fullname, phone)
    await message.answer(text=f"Спасибо, {fullname}. Теперь вы можете пользоваться всеми возможностями", reply_markup=start_keyboard)
    await state.clear()

#! Создание брони
async def auto_cancel(booking_id: int, room_id: int) -> None:
    await asyncio.sleep(600)
    status = await get_booking_status(booking_id, room_id)
    if status == 'pending':
        await cancel_booking(booking_id)
        await delete_booking_cache(room_id)

class CreateNewBooking(StatesGroup):
    wait_check_in = State()
    wait_check_out = State()
    wait_room_id = State()

@router.message(F.text == '➕ Выбрать номер и забронировать')
async def create_new_booking(message: Message, state: FSMContext):
    await message.answer(text="🗓️ укажите дату заезда в формате ДД.ММ.ГГГГ")
    await state.set_state(CreateNewBooking.wait_check_in)
# Получение даты въезда и запрос даты выезда
@router.message(CreateNewBooking.wait_check_in)
async def get_check_in(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer(text="❌ Похоже вы указали дату не в том формате... Попробуйте еще раз")
        return
    check_in = datetime.strptime(message.text, '%d.%m.%Y').strftime('%Y-%m-%d')
    await state.update_data(check_in=check_in)
    await state.set_state(CreateNewBooking.wait_check_out)
    await message.answer(text="🗓️ укажите дату выезда в формате ДД.ММ.ГГГГ")
# Получение даты выезда и запрос номера
@router.message(CreateNewBooking.wait_check_out)
async def get_check_out(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await message.answer(text="❌ Похоже вы указали дату не в том формате... Попробуйте еще раз")
        return
    
    data = await state.get_data()
    check_in = data['check_in']
    check_out = datetime.strptime(message.text, "%d.%m.%Y").strftime("%Y-%m-%d")
    if check_out < check_in:
        await message.answer(text="❌ Похоже вы указали дату выезда раньше даты заезда... Попробуйте еще раз")
        return

    check_out = datetime.strptime(message.text, '%d.%m.%Y').strftime('%Y-%m-%d')
    await state.update_data(check_out=check_out)
    await message.answer(text="✅ Отлично! Теперь выберите номер.\nСтоит сказать, что здесь указаны толдько те номера, которые доступны для бронирования в выбранные даты.")

    data = await state.get_data()
    check_in = data['check_in']
    check_out = data['check_out']
    available_rooms = await get_available_rooms(check_in, check_out)
    for row in available_rooms:
        await message.answer_photo(photo=f"{row[4]}", 
                                  caption=f"id комнаты для брони: {row[0]}\nЧисло гостей: {row[3]}\nНазвание номера: {row[1]}\n\n{row[2]}")

    await state.set_state(CreateNewBooking.wait_room_id)
# Получение айди комнаты и запись брони
@router.message(CreateNewBooking.wait_room_id)
async def get_room_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(text="❌ В сообщении с описанием номера есть id комнаты, вам надо указать именно его.")
        return

    if message.text is None:
        await message.answer(text="❌ Вы ничего не указали. В сообщении с комнатой есть её id, укажите его.")
        return
    
    await state.update_data(room_id=int(message.text))
    data = await state.get_data()

    user_id = await get_user_id(message.from_user.username)
    check_in = data['check_in']
    check_out = data['check_out']
    room_id = data['room_id']
    booking_id = await create_booking_flow(user_id, room_id, check_in, check_out)

    # Кнопка оплачено
    success_button = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Оплачено", callback_data=f"paid:{booking_id}")]])

    asyncio.create_task(auto_cancel(booking_id, room_id))
    await acquire_lock(room_id)

    await message.answer(text="✅ Ваша бронь успешно создана! Нажав на '📋 Текущие брони' вы можете ознакомится с ней подробнее.\n\nДля оплаты и подтверждения брони, перейдите по ссылке ниже.", reply_markup=success_button)
    await state.clear()
# Смена статуса на подтверждено
@router.callback_query(F.data.startswith("paid:"))
async def change_status(callback: CallbackQuery):
    booking_id = callback.data.split(":")[1]
    await confirm_booking(int(booking_id))

    data = await get_booking_dates(booking_id)
    row = data[0]
    room_id = row[1]
    dates = str(row[0]).strip("[)").split(",")
    # check_in = datetime.strptime(dates[0].strip(), "%Y-%m-%d").strftime("%d.%m.%Y")
    # check_out = datetime.strptime(dates[1].strip(), "%Y-%m-%d").strftime("%d.%m.%Y")
    check_in = dates[0].strip()
    check_out = dates[1].strip()

    await set_booking_cache(room_id, check_in, check_out)
    await callback.message.edit_text(text="✅ Бронирование успешно создано! Спасибо за оплату, ждем вас!", reply_markup=None)
    await release_lock(room_id)
    await callback.answer()

#! Удаление записи
@router.message(F.text == '➖ Удалить бронь')
async def delete(message: Message):
    user_id = await get_user_id(message.from_user.username)
    inline_kb = await delete_keyboard(user_id)
    await message.answer(text="💁🏻 Здесь вы можете выбрать одну из пяти последних записей, чтобы удалить её:", reply_markup=inline_kb)

@router.callback_query(F.data.startswith("del:"))
async def delete_booking(callback: CallbackQuery):
    id = callback.data.split(":")[1]
    await cancel_booking(int(id))
    await callback.message.edit_text(text="✅ Успешно удалено бронирование.", reply_markup=None)
    await callback.answer()

#! История бронирования
@router.message(F.text == '📋 Текущие брони')
async def bookings_right_now(message: Message):
    user_id = await get_user_id(message.from_user.username)
    data = await get_user_bookings_history(user_id)
    text = ""
    text += "🛠️ Ваша история бронирования.\n"
    for row in data:
        accommodation = str(row[3])
        accommodation = accommodation.strip("[)]").split(",")
        check_in = datetime.strptime(accommodation[0].strip(), "%Y-%m-%d").strftime("%d.%m.%Y")
        check_out = datetime.strptime(accommodation[1].strip(), "%Y-%m-%d").strftime("%d.%m.%Y")
        text += (
            f"📋 <b>Бронь #{row[0]}</b>\n"
            f"🏠 ID номера: {row[2]}\n"
            f"📅 Даты: c {check_in} по {check_out}\n"
            f"🔖 Статус: {row[4]}\n"
            f"➖➖➖➖➖➖➖➖➖\n"
        )
    await message.answer(text=text, parse_mode="HTML")