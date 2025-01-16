import os
import json
import logging
import colorlog
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from telebot import TeleBot, types
from requests.exceptions import ConnectionError, Timeout, RequestException, HTTPError
import time
from conf import TG_BOT_TOKEN, TG_CHAT_IDS, log_colors, holiday_ranges
from commands import send_homework_command, send_ege_schedule, send_holiday_on_command, \
    send_boost_info, find_duty

# Setup logger with maximum  details
formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
    log_colors=log_colors)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('homework_bot.log', encoding='utf-8'),
        handler
    ])

# Initialize bot
bot = TeleBot(TG_BOT_TOKEN)




# Paths to JSON files
USERS_FILE = 'json/users.json'
SCHEDULE_FILE = 'json/schedule2.json'
DEJUR_FILE = 'json/dejur.json'

# Load JSON data
def load_json(file_path):
    logging.debug(f"Загрузка данных из файла: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.debug(f"Данные успешно загружены: {data}")
            return data
    except FileNotFoundError:
        logging.error(f"Файл не найден: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка декодирования JSON: {e}")
        return {}

# Save JSON data
def save_json(data, file_path):
    logging.debug(f"Сохранение данных в файл: {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            logging.debug("Данные успешно сохранены.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных в файл {file_path}: {e}")

# Load users
def load_users():
    logging.debug("Загрузка пользователей...")
    users = load_json(USERS_FILE)
    logging.debug(f"Загружены пользователи: {users}")
    return users

# Save users
def save_users(users):
    logging.debug(f"Сохранение пользователей: {users}")
    save_json(users, USERS_FILE)

# Функция для отображения навигационных кнопок
def show_navigation_buttons(chat_id):
    logging.debug(f"Отображение навигационных кнопок для пользователя: {chat_id}")
    commands_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    commands_markup.add(
        '🏖 Каникулы',
        '🍽️ Что дают?',
        '📅 Расписание ОГЭ',
        '📅 Расписание ЕГЭ',
        '📅 Сегодняшнее расписание',
        '📅 Завтрашнее расписание',
        '📅 Расписание на неделю',
        '🚀 Boost'
    )

    users = load_users()
    if chat_id in users and users[chat_id].get('class') == '11':
        commands_markup.add(
            '📞 Важные номера (только для 11)',
            '📝 Дежурныe (только для 11)'
        )

    bot.send_message(chat_id, "Вот доступные команды:", reply_markup=commands_markup)
    logging.debug("Навигационные кнопки успешно отправлены.")

# Обработчик команды /start и /menu
@bot.message_handler(commands=['start'])
def start_command(message):
    logging.info("Команда /start получена от пользователя {}".format(message.from_user.id))

    chat_id = str(message.chat.id)
    users = load_users()  # Загружаем список пользователей

    # Проверяем, существует ли пользователь и есть ли у него класс
    if chat_id in users:
        user_class = users[chat_id].get('class')
        if user_class:
            bot.send_message(chat_id, f"Добро пожаловать! Вы уже выбрали класс: {user_class}.")
            show_navigation_buttons(chat_id)  # Показываем навигационные кнопки
            return  # Выход из функции, если класс уже выбран
    else:
        users[chat_id] = {}  # Создаем запись для нового пользователя
        logging.info(f"Добавлен новый пользователь: {chat_id}")

    bot.send_message(chat_id, "Добро пожаловать! Пожалуйста, выберите класс:")

    # Создание кнопок для выбора класса
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item8 = types.KeyboardButton("8")
    item9 = types.KeyboardButton("9")
    item10 = types.KeyboardButton("10")
    item11 = types.KeyboardButton("11")
    markup.add(item8, item9, item10, item11)
    bot.send_message(chat_id, text="Выберите класс:", reply_markup=markup)

# Обработчик выбора класса
@bot.message_handler(func=lambda message: message.text in ["8", "9", "10", "11"])
def class_selection(message):
    selected_class = message.text  # Получаем выбранный класс
    logging.info(f"Пользователь {message.from_user.id} выбрал класс {selected_class}")

    chat_id = str(message.chat.id)  # Получаем chat_id
    users = load_users()  # Загружаем текущих пользователей

    # Сохраняем класс для пользователя
    users[chat_id] = {'class': selected_class}
    save_users(users)  # Сохраняем обновленный список пользователей

    bot.send_message(chat_id, f"Вы выбрали класс: {selected_class}")
    show_navigation_buttons(chat_id)

# Get schedule
def get_schedule(chat_id, day):
    logging.debug(f"Получение расписания для пользователя {chat_id} на день {day}")

    # Загружаем данные пользователей
    users = load_users()
    user_info = users.get(str(chat_id), {})
    user_class = user_info.get('class', 'unknown')

    logging.debug(f"Класс пользователя {chat_id}: {user_class}")

    if user_class == 'unknown':
        logging.warning(f"Класс пользователя {chat_id} не найден.")
        return "Ваш класс не найден."

    # Сопоставление дней недели с ключами в расписании
    days_mapping = {
        'monday': 'Monday',
        'tuesday': 'Tuesday',
        'wednesday': 'Wednesday',
        'thursday': 'Thursday',
        'friday': 'Friday',
        'saturday': 'Saturday',
        'sunday': 'Sunday'
    }

    # Приведение дня к формату, который используется в расписании
    day = day.lower()
    if day not in days_mapping:
        logging.error("Неверный день недели.")
        return "Неверный день недели."

    day_key = days_mapping[day]

    # Загружаем расписание
    schedule_data = load_json(SCHEDULE_FILE)

    # Получаем расписание для класса и дня
    if user_class in schedule_data:
        daily_schedule = schedule_data[user_class].get(day_key, [])

        if not daily_schedule:
            return "Сегодня нет уроков."

        # Формируем ответ
        response = []
        for lesson in daily_schedule:
            response.append(f"{lesson['time']}: {lesson['subject']} (Учитель: {lesson['teacher']})")

        logging.debug(f"Получено расписание: {response}")
        return '\n'.join(response)

    return "Расписание для вашего класса не найдено."

# Handle schedule requests
@bot.message_handler(func=lambda message: message.text in ['📅 Сегодняшнее расписание', '📅 Завтрашнее расписание', '📅 Расписание на неделю'])
def handle_schedule_request(message):
    chat_id = str(message.chat.id)
    today = datetime.now().strftime('%A').lower()
    logging.info(f"Запрос расписания от пользователя {chat_id} на день {today}")

    if message.text == '📅 Сегодняшнее расписание':
        if today in ['saturday', 'sunday']:
            today = 'monday'
        schedule = get_schedule(chat_id, today)
        bot.send_message(chat_id, schedule)

    elif message.text == '📅 Завтрашнее расписание':
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%A').lower()
        if tomorrow in ['saturday', 'sunday']:
            tomorrow = 'monday'
        schedule = get_schedule(chat_id, tomorrow)
        bot.send_message(chat_id, schedule)

    elif message.text == '📅 Расписание на неделю':
        week_schedule = []
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            schedule = get_schedule(chat_id, day)
            week_schedule.append(f"{day.capitalize()}:\n{schedule}")
        bot.send_message(chat_id, "📅 Расписание на неделю:\n\n" + "\n\n".join(week_schedule))

# Send PDFs from folder
def send_pdfs_from_folder(bot, chat_id):
    logging.debug(f"Отправка PDF-файлов пользователю {chat_id}")
    folder_path = 'book'  # Specify the correct folder path
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

    if not pdf_files:
        logging.error("В указанной папке нет PDF")
        return

    try:
        bot.send_chat_action(chat_id, 'upload_document')
        for pdf_file in pdf_files:
            file_path = os.path.join(folder_path, pdf_file)
            with open(file_path, 'rb') as f:
                bot.send_document(chat_id, f, caption=pdf_file)
        logging.info("PDF-файлы успешно отправлены.")
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF-файлов: {e}")

# Find duty by day
def find_duty_by_day():
    duty_data = load_json(DEJUR_FILE)
    current_weekday = datetime.now().strftime('%A')  # Get current weekday as a string, e.g., "Monday"
    for duty in duty_data:
        if duty['day'] == current_weekday:
            logging.debug(f"Найдены дежурные на {current_weekday}: {duty['duty']}")
            return duty['duty']
    logging.warning("Дежурные на сегодня не найдены")
    return ["Дежурные на сегодня не найдены"]

# Send today food menu
def send_today_food_menu(bot, message):
    logging.info(f"Получен запрос на сегодняшнее меню от пользователя {message.chat.id}")
    url = 'https://livint.ru/food'
    response = requests.get(url)
    if response.status_code == 200:
        logging.info("Успешно получена страница меню блюд")
        soup = BeautifulSoup(response.text, 'html.parser')
        today_date = datetime.now().strftime('%d.%m')
        found = False
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if href.endswith('.pdf') and today_date in link.text:
                found = True
                file_url = href
                file_name = link.text.strip().split('(')[0].strip() + ".pdf"
                file_path = os.path.join('archive', file_name)

                if not os.path.exists('archive'):
                    os.makedirs('archive')

                if not os.path.exists(file_path):
                    pdf_response = requests.get(file_url)
                    if pdf_response.status_code == 200:
                        logging.info(f"Успешно получен PDF-файл: {file_name}")
                        with open(file_path, 'wb') as f:
                            f.write(pdf_response.content)
                        logging.info(f"Сохранил PDF-файл: {file_name} в папку 'archive'")
                    else:
                        logging.error("Не удалось загрузить PDF-файл")
                        bot.send_message(message.chat.id, "Не удалось загрузить файл меню.")

                with open(file_path, 'rb') as f:
                    bot.send_chat_action(message.chat.id, 'upload_document')
                    bot.send_document(message.chat.id, f)
                logging.info(f"Отправил PDF-файл: {file_name} пользователю {message.chat.id}")
        if not found:
            logging.warning("Меню на сегодня не найдено")
            bot.send_message(message.chat.id, "Меню на сегодня не найдено.")
    else:
        logging.error("Не удалось получить страницу меню блюд.")
        bot.send_message(message.chat.id, "Не удалось получить данные о меню.")

# Get EGE schedule message
EGE_SCHEDULE = {
    "23 мая": ["История", "Литература", "Химия"],
    "27 мая": ["Математика (базовая)", "Математика (профильная)"],
    "30 мая": ["Русский язык"],
    "2 июня": ["Обществознание", "Физика"],
    "5 июня": ["Биология", "География", "Иностранные языки (письменная часть)"],
    "10 июня": ["Информатика"],
    "11 июня": ["Иностранные языки (устная часть)"]
}

def get_ege_schedule_message():
    message = "Расписание ЕГЭ:\n\n"
    for date, subjects in EGE_SCHEDULE.items():
        message += f"{date}: {', '.join(subjects)}\n"
    return message

# Send OGE schedule
def send_oge_schedule(bot, message):
    logging.info(f"Получена команда /oge_schedule от пользователя {message.chat.id}")
    oge_schedule = (
        "Основной период\n"
        "21 мая — иностранные языки (английский, испанский, немецкий, французский);\n"
        "22 мая — иностранные языки (английский, испанский, немецкий, французский);\n"
        "26 мая — биология, информатика, обществознание, химия;\n"
        "29 мая — география, история, физика, химия;\n"
        "3 июня — математика;\n"
        "6 июня — география, информатика, обществознание;\n"
        "9 июня — русский язык;\n"
        "16 июня — биология, информатика, литература, физика.\n\n"
        "Резервные дни\n"
        "26 июня — русский язык;\n"
        "27 июня — по всем учебным предметам (кроме русского языка и математики);\n"
        "28 июня — по всем учебным предметам (кроме русского языка и математики);\n"
        "30 июня — математика;\n"
        "1 июля — по всем учебным предметам;\n"
        "2 июля — по всем учебным предметам."
    )
    bot.send_message(message.chat.id, oge_schedule)

# Notify about holidays
def check_holidays(bot):
    now = datetime.now()
    today = now.date()
    logging.debug(f"Проверка праздников на {today}")
    for start, end in holiday_ranges:
        if today == start.date():
            notify_holiday_start(bot, start)
        elif today == end.date() + timedelta(days=1):  # day after holiday ends
            notify_holiday_end(bot, end)

def notify_holiday_start(bot, start):
    message = f"Каникулы начались! С {start.strftime('%d.%m.%Y')} до {start + timedelta(days=1)}"
    for chat_id in TG_CHAT_IDS:
        bot.send_message(chat_id, message)
    logging.info(f"Отправлено уведомление о начале каникул: {message}")

def notify_holiday_end(bot, end):
    message = f"Каникулы закончились! С {end.strftime('%d.%m.%Y')} до {end + timedelta(days=1)}"
    for chat_id in TG_CHAT_IDS:
        bot.send_message(chat_id, message)
    logging.info(f"Отправлено уведомление о завершении каникул: {message}")

def schedule_holiday_notifications(bot):
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            check_holidays(bot)
        time.sleep(60)  # Check every 60 seconds

def send_important_numbers(bot, message):
    logging.info(f"Получена команда /important_numbers от пользователя {message.chat.id}")

    # Проверяем, есть ли chat_id пользователя в списке разрешенных
    if str(message.chat.id) in TG_CHAT_IDS:
        important_numbers = (
            "Важные номера:\n"
        )
        bot.send_message(message.chat.id, important_numbers)
        logging.debug(f"Важноe сообщение отправлено пользователю {message.chat.id}.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой информации.")
        logging.warning(f"Попытка доступа к важным номерам от пользователя {message.chat.id}, который не имеет доступа.")

@bot.message_handler(commands=['new'])
def announce_command(message):
    logging.info(f"Команда /new получена от пользователя {message.from_user.id}")
    if message.from_user.id == 5174606227:  # Проверяем, что это ваш ID
        announcement_text = message.text[4:]  # Убираем '/announce ' из текста
        if announcement_text:
            user_ids = load_users()  # Загружаем список пользователей
            logging.info(f"Список пользователей для рассылки: {user_ids}")
            for chat_id in user_ids:
                try:
                    bot.send_message(chat_id=chat_id, text=announcement_text)
                    logging.info(f"Объявление отправлено пользователю {chat_id}")
                except Exception as e:
                    logging.error(f"Не удалось отправить сообщение пользователю {chat_id}: {e}")
            bot.send_message(chat_id=message.chat.id, text="Объявление отправлено всем пользователям!")
        else:
            bot.send_message(chat_id=message.chat.id, text="Пожалуйста, напишите текст объявления после команды.")
    else:
        bot.send_message(chat_id=message.chat.id, text="У вас нет доступа к этой команде.")

@bot.message_handler(commands=['duty'])
def handle_duty(message):
    duty_message = find_duty_by_day()
    bot.send_message(message.chat.id, "\n".join(duty_message))
    logging.info(f"Дежурные отправлены пользователю {message.chat.id}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    logging.debug(f"Получено сообщение от пользователя {message.chat.id}: {message.text}")
    if message.text == '📅 Сегодняшнее расписание':
        handle_schedule_request(message)
    elif message.text == '📅 Завтрашнее расписание':
        handle_schedule_request(message)
    elif message.text == '📅 Расписание на неделю':
        handle_schedule_request(message)
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
    elif message.text == 'duty':
        find_duty(bot, message)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите команду из меню.")
        show_navigation_buttons(message.chat.id)

MAX_RETRIES = 10  # Максимальное количество попыток перезапуска
retry_count = 0
        
# Main execution block
if __name__ == "__main__":
    logging.info("Запуск домашнего бота...")
    try:
        logging.info("Запуск уведомлений о каникулах...")
        import threading

        holiday_thread = threading.Thread(target=schedule_holiday_notifications, args=(bot,))
        holiday_thread.start()
        logging.info("Поток уведомлений о каникулах запущен.")

    except Exception as e:
        logging.error(f"Ошибка при запуске потока уведомлений: {e}")

    try:
        logging.info("Запуск опроса бота...")
        while retry_count < MAX_RETRIES:
            try:
                bot.polling(none_stop=True)
                retry_count = 0  # Сбрасываем счетчик, если опрос прошел успешно
            except Exception as e:
                logging.error(f"Ошибка при опросе бота: {e}")
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    logging.info(f"Попытка перезапуска опроса бота... (попытка {retry_count})")
                    time.sleep(5)  # Ждем 5 секунд перед следующей попыткой
                    retry_count = 0
                else:
                    logging.error("Достигнуто максимальное количество попыток. Остановка бота.")
    except KeyboardInterrupt:
        logging.info("Опрос бота остановлен пользователем.")
