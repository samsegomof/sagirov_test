import logging

import datetime
import re

import phonenumbers

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from database import db_init  # DB initialization


API_TOKEN = '5833200290:AAExo0dsiEJcwr4oYnwoFT5-CPLzuoYyhGI'  # BOT API TOKEN

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)


def validate_email(email):
    """Validating email addresses"""

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.fullmatch(regex, email):
        print("Email is valid")
    else:
        raise ValueError


def validate_number(phone_number):
    """Validating phone number with phonenumbers lib"""

    number = phonenumbers.parse(phone_number)
    try:
        phonenumbers.is_valid_number(number)
        print('Phone number is valid')

    except Exception:
        raise ValueError


def validate_birth_date(date):
    """Validating birthdate format"""

    datetime.datetime.strptime(date, '%Y-%m-%d')
    print('Date is valid')


class FSMData(StatesGroup):
    """State handler"""
    first_name = State()
    last_name = State()
    email = State()
    phone_number = State()
    birth_date = State()


@dp.message_handler(commands='start')
async def start_handler(message: types.Message, state: FSMContext):
    """Start command handler"""

    await message.answer(
        'Пожалуйста, напишите /form для начала заполнения формы. Когда ваша очередь подойдет, вы получите скриншот'
        )


@dp.message_handler(state="*", commands='cancel') # Прекратить заполнение /cancel
async def cancel_handler(message: types.Message, state: FSMContext):
    """Cancel command handler"""

    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply('Заполнение формы прекращено')


@dp.message_handler(commands='form', state=None)  # Ответ на /form
async def cm_start(message: types.Message):
    """Form command handler"""

    await FSMData.first_name.set()
    await message.reply('Напишите ваше имя')


@dp.message_handler(content_types=['text'], state=FSMData.first_name)  # Запрос имени
async def pass_first_name(message: types.Message, state: FSMContext):
    """Form first name handler"""

    async with state.proxy() as data: # Add first name to state
        data['first_name'] = message.text 

    await FSMData.next()
    await message.reply('Теперь напишите вашу фамилию')


@dp.message_handler(content_types=['text'], state=FSMData.last_name) # Запрос фамилии
async def pass_last_name(message: types.Message, state: FSMContext): 
    """Form last name handler"""

    async with state.proxy() as data:  # Add last name to state
        data['last_name'] = message.text

    await FSMData.next()
    await message.reply('Укажите ваш e-mail')


@dp.message_handler(state=FSMData.email)  # Запрос email
async def pass_email(message: types.Message, state: FSMContext):
    """Form email handler"""

    try:  # Email validation
        validate_email(message.text)
    except ValueError:
        await message.reply('Неправильный формат e-mail')
        return await pass_email(types.Message, FSMContext)  # Repeat the message

    async with state.proxy() as data:  # Add email name to state
        data['email'] = message.text

    await FSMData.next()
    await message.reply('Напишите ваш номер телефона')


@dp.message_handler(state=FSMData.phone_number)  # Запрос номера телефона
async def pass_phone_number(message: types.Message, state: FSMContext):
    """Form phone number handler"""

    try:  # Phone number validation
        validate_number(message.text)
    except phonenumbers.phonenumberutil.NumberParseException:
        await message.reply('Неправильный формат телефона')
        return await pass_phone_number(types.Message, FSMContext)  # Repeat the message

    async with state.proxy() as data:  # Add phone number to state
        data['phone_number'] = message.text

    await FSMData.next()
    await message.reply('И последний шаг, напишите вашу дату рождения в формате YYYY-MM-DD')


@dp.message_handler(state=FSMData.birth_date)  # Запрос даты рождения
async def pass_birth_date(message: types.Message, state: FSMContext):
    """Form birthdate handler"""

    try:  # Birthdate validation
        validate_birth_date(message.text)
    except ValueError:
        await message.reply('Неправильный формат даты')
        return await pass_birth_date(types.Message, FSMContext)  # Repeat the message

    current_time = datetime.datetime.now()  # Time of request for FIFO queue

    async with state.proxy() as data:  # Add birthdate and user_id to state
        data['birth_date'] = message.text
        data['user_id'] = message.from_user.id

    await db_init.database_controller.sql_add_command(state, current_time)  # export states to sqlite3 database
    await message.answer('Спасибо! Данные собраны, ожидайте ответа :)')
    await state.finish()


async def send_screenshot(chat_id, screenshot):
    """Sends screenshot back to the user"""
    await bot.send_photo(chat_id=chat_id, photo=open(screenshot, 'rb'))


async def on_shutdown():
    dp.stop_polling()
    await dp.wait_closed()
    await bot.close()


def start():
    """Commands on startup"""
    db_init.database_controller.connect_check()
    executor.start_polling(dp, skip_updates=True)
    print('STARTED')


if __name__ == "main":
    start()
