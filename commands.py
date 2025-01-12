from telebot import types
from datetime import datetime, timedelta

from test import find_schedule_by_teacher
from book import send_pdfs_from_folder
from holidays import get_holidays_info, is_holiday
from schedule import get_schedule
from food import send_today_food_menu
from ege_calendar import get_ege_schedule_message
from important_numbers import send_important_numbers  # Импортируем функцию из нового файла
from oge import send_oge_schedule
from conf import TG_CHAT_IDS
from dejurni import find_duty_by_day
import os
import json


import colorlog
import logging
from conf import log_colors
formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    log_colors=log_colors)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('homework_bot.log', encoding='utf-8'),
        handler
    ])


def send_schedule_on_command(bot, message):
    logging.info(f"Получена команда /rasp от пользователя {message.chat.id}")
    today_day = datetime.now().strftime('%A').lower()
    bot.send_chat_action(message.chat.id, 'typing')
    get_schedule(bot, message, today_day)


def send_schedule_for_tomorrow_on_command(bot, message):
    logging.info(f"Получена команда /raspz от пользователя {message.chat.id}")
    today = datetime.now().strftime('%A').lower()
    if today == 'friday':
        tomorrow_day = 'monday'
    if today == 'sunday':
        tomorrow_day = 'monday'
    if today == 'saturday':
        tomorrow_day = 'monday'
    else:
        tomorrow_day = (datetime.now() + timedelta(days=1)).strftime('%A').lower()
    bot.send_chat_action(message.chat.id, 'typing')
    get_schedule(bot, message, tomorrow_day)


def send_holiday_on_command(bot, message):
    logging.info(f"Получена команда /holiday от пользователя {message.chat.id}")
    holidays_info = get_holidays_info()
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, holidays_info if holidays_info else "Нет ближайших каникул.")

def classroom(bot, message):
    logging.info(f"Получена запрос на кабинет от пользователя {message.chat.id}")
    classroom = find_schedule_by_teacher()
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, classroom)

def send_ege_schedule(bot, message):
    logging.info(f"Получена команда /ege от пользователя {message.chat.id}")
    ege_schedule_message = get_ege_schedule_message()
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, ege_schedule_message)

def find_duty(bot, message):
    logging.info(f"Получена команда /duty от пользователя {message.chat.id}")
    find_duty = find_duty_by_day()
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, find_duty)

def show_navigation_buttons(bot, message):
    logging.info(f"Отображение навигационных кнопок для пользователя {message.chat.id}")
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    holiday_info = types.KeyboardButton('🏖 Каникулы')
    food_today = types.KeyboardButton('🍽️ Что дают?')
    oge_info = types.KeyboardButton('📅 Расписание ОГЭ')
    ege_info = types.KeyboardButton('📅 Расписание ЕГЭ')
    boost_command = types.KeyboardButton('🚀 Boost')

    markup.add(holiday_info, food_today, oge_info, ege_info, boost_command)

    if str(message.chat.id) in TG_CHAT_IDS:
        rasp_today = types.KeyboardButton('📅 Сегодняшнее расписание (только для 11)')
        rasp_tomorrow = types.KeyboardButton('📅 Завтрашнее расписание (только для 11)')
        important_numbers = types.KeyboardButton('📞 Важные номера (только для 11)')
        find_duty = types.KeyboardButton('📝 Дежурныe (только для 11)')
        book = types.KeyboardButton('PDF Учебники (только для 11)')
        markup.add(rasp_today, rasp_tomorrow, important_numbers, find_duty, book)
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


def handle_text(bot, message):
    logging.info(f"Обработка текстового сообщения от пользователя {message.chat.id}: {message.text}")

    if message.text in ['📅 Сегодняшнее расписание (только для 11)', '📅 Завтрашнее расписание (только для 11)', '📞 Важные номера (только для 11)', '📝 Д/З (только для 11)', '/rasp', '/raspz', '/important_numbers', '/homework']:
        if str(message.chat.id) not in TG_CHAT_IDS:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")
            logging.warning(f"Unauthorized access attempt by user {message.chat.id}")
            return

    if message.text == '📅 Сегодняшнее расписание (только для 11)':
        send_schedule_on_command(bot, message)
    elif message.text == '📅 Завтрашнее расписание (только для 11)':
        send_schedule_for_tomorrow_on_command(bot, message)
    elif message.text == '🏖 Каникулы':
        send_holiday_on_command(bot, message)
    elif message.text == '🍽️ Что дают?':
        send_today_food_menu(bot, message)
    elif message.text == '📅 Расписание ЕГЭ':
        send_ege_schedule(bot, message)
    elif message.text == '📞 Важные номера (только для 11)':
        send_important_numbers(bot, message)
    elif message.text == '📝 Д/З (только для 11)':
        send_homework_command(bot, message)
    elif message.text == '📅 Расписание ОГЭ':
        send_oge_schedule(bot, message)
    elif message.text == '🚀 Boost':
        send_boost_info(bot, message)
    elif message.text == '📝 Дежурныe (только для 11)':
        find_duty(bot, message)
    elif message.text == 'PDF Учебники (только для 11)':
        send_pdfs_from_folder(bot, message)
    elif message.text == '/books':
        send_pdfs_from_folder(bot, message)
    elif message.text == '/duty':
        find_duty(bot, message)
    elif message.text == '/boost':
        send_boost_info(bot, message)
    elif message.text == '/rasp':
        send_schedule_on_command(bot, message)
    elif message.text == '/raspz':
        send_schedule_for_tomorrow_on_command(bot, message)
    elif message.text == '/holiday':
        send_holiday_on_command(bot, message)
    elif message.text == '/food':
        send_today_food_menu(bot, message)
    elif message.text == '/ege':
        send_ege_schedule(bot, message)
    elif message.text == '/important_numbers':
        send_important_numbers(bot, message)
    elif message.text == '/homework':
        send_homework_command(bot, message)
    elif message.text == '/oge_schedule':
        send_oge_schedule(bot, message)
    else:
        teachers_data = load_teachers_data('json/teachers.json')
        result = find_teacher_by_subject(teachers_data, message.text.strip())
        bot.send_message(message.chat.id, result)

def send_boost_info(bot, message):
    logging.info(f"Получена команда /boost от пользователя {message.chat.id}")
    boost_message = (
        "Ton - UQCeGJyRMbM8LhR0HkAy0iGdVaniUPW8ObCq3Yya0r05Z5IO\n"
    )
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, boost_message)

def load_teachers_data(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_teacher_by_subject(teachers_data, subject):
    for teacher in teachers_data:
        if subject in teacher['leson']:
            return f"Имя: {teacher['name']}"
    for leson in teachers_data:
        if subject in leson['name']:
            return f"Предмет {leson['leson']}"



# Добавляем функцию для получения домашнего задания из JSON
def get_homework_from_json():
    today = datetime.today().strftime('%Y-%m-%d')
    file_name = f"archive/homework_{today}.json"
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            homework = json.load(f)
            return homework
    else:
        return "Нет данных о домашнем задании на сегодня. (Обновляется в 14:30)   (Времено не работает) (Когда то я доделаю эту мразь)"


def handle_message(message):
    teacher_name = message.text
    logging.info(f"Получено сообщение: {teacher_name}")
    schedule = find_schedule_by_teacher(teacher_name)
    if schedule:
        response_text = '\n'.join(schedule)
    else:
        response_text = "Ничего не найдено"


def send_start_text(bot, message):
    logging.info(f"Получена команда /start от пользователя {message.chat.id}")
    start_text = (
        "🌟 Бот @school_livint_bot: твой помощник в учёбе! \n"
        "\n"
        "Бот @school_livint_bot — это простой и удобный способ получить нужную информацию быстро и без лишних усилий. Попробуйте сами! 😉\n"
    )
    bot.send_message(message.chat.id, start_text)

# Функция для отправки домашнего задания через бота
def send_homework_command(bot, message):
    logging.info(f"Получена команда /homework от пользователя {message.chat.id}")
    homework = get_homework_from_json()
    if isinstance(homework, list):
        homework_message = "\n".join(homework)
    else:
        homework_message = homework
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, homework_message)
