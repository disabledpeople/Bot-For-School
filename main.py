import logging
import colorlog
from telebot import *
from telebot.types import *
from datetime import datetime, timedelta

# --- модули ---
from schedule import get_schedule
from holidays import schedule_holiday_notifications, send_holiday_on_command
from exаms import send_ege_schedule, send_oge_schedule
from food import send_today_food_menu
from teacher import show_teachers
from important_numbers import send_important_numbers
from dejur import handle_duty, handle_duty_week
from admin import increment_daily_stat, handle_stats, handle_del_user, cmd_get_users, handle_set_class, handle_announcement, feedback_users, save_feedback_users
from utils import load_users, register_user_with_date_if_new
from anon_feedback import anon_feedback_users, save_anon_feedback_users
from user_profile import show_profile, handle_change_name, handle_change_class, handle_change_avatar, add_score,show_top_users

# --- конфиг ---
from conf import TG_BOT_TOKEN, log_colors, ADMIN_ID

# --- Настройка логов ---
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

# --- Инициализировать бота ---
bot = TeleBot(TG_BOT_TOKEN)

# --- Обработчик команды /start ---
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
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(chat_id, "Добро пожаловать! Пожалуйста, выберите класс:")

    # Создание кнопок для выбора класса
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item8 = types.KeyboardButton("8")
    item9 = types.KeyboardButton("9")
    item10 = types.KeyboardButton("10")
    item11 = types.KeyboardButton("11")
    markup.add(item8, item9, item10, item11)
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(chat_id, text="Выберите класс:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["8", "9", "10", "11"])
def class_selection(message):
    selected_class = message.text
    logging.info(f"Пользователь {message.from_user.id} выбрал класс {selected_class}")

    chat_id = str(message.chat.id)

    # сохраняем класс и, если нужно, дату регистрации
    register_user_with_date_if_new(chat_id, selected_class)

    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(chat_id, f"Вы выбрали класс: {selected_class}")
    show_navigation_buttons(chat_id)


# --- Функция для отображения навигационных кнопок ---
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
        '👩‍🏫 Показать учителей',
        '📝 Дежурныe сегодня',
        '📝 Дежурные на всю неделю',
        '📢 Обратная связь',
        '📢 Анонимная жалоба',
        '👤 Профиль',
        '🏆 ТОПЫ'
    )

    users = load_users()
    if chat_id in users and users[chat_id].get('class') == '10':
        commands_markup.add(
            '📞 Важные номера (только для 10)',
        )

    bot.send_message(chat_id, "Вот доступные команды:", reply_markup=commands_markup)
    logging.debug("Навигационные кнопки успешно отправлены.")

# --- Обрабатывать запросы по расписанию ---
@bot.message_handler(func=lambda message: message.text in ['📅 Сегодняшнее расписание', '📅 Завтрашнее расписание', '📅 Расписание на неделю'])
def handle_schedule_request(message):
    chat_id = str(message.chat.id)
    today = datetime.now().strftime('%A').lower()
    logging.info(f"Запрос расписания от пользователя {chat_id} на день {today}")

    def normalize_day(day_name):
        # если выходной — возвращаем None, чтобы не менять день сразу
        if day_name in ['saturday', 'sunday']:
            return None
        return day_name

    if message.text == '📅 Сегодняшнее расписание':
        day_to_get = normalize_day(today)
        if day_to_get is None:
            bot.send_message(chat_id, "Сегодня выходной. Расписание на ближайший учебный день (понедельник):")
            day_to_get = 'monday'
        schedule = get_schedule(chat_id, day_to_get)
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(chat_id, schedule)

    elif message.text == '📅 Завтрашнее расписание':
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%A').lower()
        day_to_get = normalize_day(tomorrow)
        if day_to_get is None:
            bot.send_message(chat_id, "Завтра выходной. Расписание на ближайший учебный день (понедельник):")
            day_to_get = 'monday'
        schedule = get_schedule(chat_id, day_to_get)
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(chat_id, schedule)

    elif message.text == '📅 Расписание на неделю':
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        week_schedule = []
        for day in days:
            schedule = get_schedule(chat_id, day)
            week_schedule.append(f"{day.capitalize()}:\n{schedule}")
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(chat_id, "📅 Расписание на неделю:\n\n" + "\n\n".join(week_schedule))

@bot.message_handler(func=lambda message: message.text == '📅 Сегодняшнее расписание')
def handle_schedule(message):
    increment_daily_stat('schedule_today_requests')
    add_score(str(message.from_user.id))
    handle_schedule_request(bot, message)

@bot.message_handler(func=lambda message: message.text == '📅 Завтрашнее расписание')
def handle_schedule(message):
    increment_daily_stat('schedule_tomorrow_requests')
    add_score(str(message.from_user.id))
    handle_schedule_request(bot, message)

@bot.message_handler(func=lambda message: message.text == '📅 Расписание на неделю')
def handle_schedule(message):
    increment_daily_stat('schedule_week_requests')
    add_score(str(message.from_user.id))
    handle_schedule_request(bot, message)

@bot.message_handler(func=lambda message: message.text == '🏖 Каникулы')
def handle_holiday(message):
    increment_daily_stat('holiday_requests')
    add_score(str(message.from_user.id))
    send_holiday_on_command(bot, message)

@bot.message_handler(func=lambda message: message.text == '🍽️ Что дают?')
def handle_food(message):
    increment_daily_stat('food_requests')
    add_score(str(message.from_user.id))
    send_today_food_menu(bot, message)

@bot.message_handler(func=lambda message: message.text == '📅 Расписание ЕГЭ')
def handle_ege(message):
    increment_daily_stat('ege_schedule_requests')
    add_score(str(message.from_user.id))
    send_ege_schedule(bot, message)

@bot.message_handler(func=lambda message: message.text == '📅 Расписание ОГЭ')
def handle_oge(message):
    increment_daily_stat('oge_schedule_requests')
    add_score(str(message.from_user.id))
    send_oge_schedule(bot, message)

@bot.message_handler(func=lambda message: message.text == '👩‍🏫 Показать учителей')
def handle_teachers(message):
    increment_daily_stat('teachers_requests')
    add_score(str(message.from_user.id))
    show_teachers(bot, message)

@bot.message_handler(func=lambda message: message.text == '📞 Важные номера (только для 10)')
def handle_important(message):
    increment_daily_stat('important_numbers_requests')
    add_score(str(message.from_user.id))
    send_important_numbers(bot, message)

@bot.message_handler(func=lambda message: message.text == '📝 Дежурныe сегодня')
def handle_dute(message):
    increment_daily_stat('duty_requests')
    add_score(str(message.from_user.id))
    handle_duty(bot, message)

@bot.message_handler(func=lambda message: message.text == '📝 Дежурные на всю неделю')
def handle_dute(message):
    increment_daily_stat('duty_week_requests')
    add_score(str(message.from_user.id))
    handle_duty_week(bot, message)

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "❌ у вас нет прав на использование этой команды.")
        return
    logging.info(f"обработка команды /stats от пользователя {message.from_user.id}")
    handle_stats(bot, message)


@bot.message_handler(commands=['users'])
def admin_get_users(message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав на использование этой команду.")
        return
    logging.info(f"Обработка команды /get_users от пользователя {message.from_user.id}")
    cmd_get_users(bot, message)

@bot.message_handler(commands=['set_class'])
def admin_class(message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав на использование этой команды.")
        return
    logging.info(f"Обработка команды /set_class от пользователя {message.from_user.id}")
    handle_set_class(bot, message)

@bot.message_handler(commands=['del_user'])
def admin_user(message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав на использование этой команды.")
        return
    logging.info(f"Обработка команды /del_user от пользователя {message.from_user.id}")
    handle_del_user(bot, message)

@bot.message_handler(commands=['new'])
def new_command(message):
    handle_announcement(bot, message, ADMIN_ID)

@bot.message_handler(func=lambda m: m.text == "📢 Обратная связь")
def start_feedback(message):
    user_id = message.from_user.id
    if user_id in feedback_users:
        bot.send_message(user_id, "вы уже в режиме отправки обратной связи. отправьте сообщение или нажмите ❌ Отмена.", 
                         reply_markup=feedback_cancel_keyboard())
    else:
        feedback_users.add(user_id)
        save_feedback_users(feedback_users)
        increment_daily_stat('feedback')
        add_score(str(message.from_user.id))
        bot.send_message(user_id, "пожалуйста, напишите ваше сообщение. чтобы отменить — нажмите ❌ Отмена.",
                         reply_markup=feedback_cancel_keyboard())
        

@bot.message_handler(func=lambda m: m.text == "❌ Отмена")
def cancel_feedback(message):
    user_id = message.from_user.id
    if user_id in feedback_users:
        feedback_users.remove(user_id)
        save_feedback_users(feedback_users)
        bot.send_message(user_id, "отправка обратной связи отменена.", show_navigation_buttons(user_id))
    else:
        bot.send_message(user_id, "вы не в режиме обратной связи.", show_navigation_buttons(user_id))

def feedback_cancel_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("❌ Отмена"))
    return kb

def anon_feedback_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("❌ Отмена"))
    return kb

@bot.message_handler(func=lambda m: m.text == "📢 Анонимная жалоба")
def anon_feedback_start(message):
    user_id = message.from_user.id
    if user_id in anon_feedback_users:
        bot.send_message(user_id, "вы уже в режиме отправки анонимной жалобы. пожалуйста, отправьте сообщение или нажмите «Отмена».", reply_markup=anon_feedback_kb())
    else:
        anon_feedback_users.add(user_id)
        save_anon_feedback_users(anon_feedback_users)
        increment_daily_stat('anon_feedback')
        add_score(str(message.from_user.id))
        bot.send_message(user_id, "пожалуйста, отправьте ваше анонимное сообщение с жалобой или предложением.", reply_markup=anon_feedback_kb())



@bot.message_handler(func=lambda m: m.text == "❌ Отмена")
def anon_feedback_cancel(message):
    user_id = message.from_user.id
    if user_id in anon_feedback_users:
        anon_feedback_users.remove(user_id)
        save_anon_feedback_users(anon_feedback_users)
        bot.send_message(user_id, "вы отменили отправку анонимной жалобы.", show_navigation_buttons(user_id))
    else:
        bot.send_message(user_id, "вы не находитесь в режиме отправки анонимной жалобы.", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile_cmd(message):
    increment_daily_stat('profile')
    add_score(str(message.from_user.id))
    show_profile(bot, message)

@bot.message_handler(func=lambda m: m.text == "✏️ изменить имя")
def change_name(message):
    handle_change_name(bot, message)

@bot.message_handler(func=lambda m: m.text == "🏷 изменить класс")
def change_class(message):
    handle_change_class(bot, message)

@bot.message_handler(func=lambda m: m.text == "🌟 изменить аватар")
def change_avatar(message):
    handle_change_avatar(bot, message)

@bot.message_handler(func=lambda m: m.text == "❌ Назад")
def vglm(message):
    user_id = message.from_user.id
    show_navigation_buttons(user_id)

@bot.message_handler(func=lambda m: m.text == "🏆 ТОПЫ")
def otptops(message):
    increment_daily_stat('tops')
    add_score(str(message.from_user.id))
    show_top_users(bot, message)

# в крации не трогать это переменные для авто рестарта 
MAX_RETRIES = 10  # Максимальное количество попыток перезапуска
retry_count = 0
        
# просто логи и бот пулинг 
if __name__ == "__main__":
    logging.info("Запуск домашнего бота...")

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from dejur import setup_scheduler
        scheduler = setup_scheduler(bot)
        logging.info("Планировщик заданий запущен.")
    except Exception as e:
        logging.error(f"Ошибка при запуске планировщика: {e}")

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
                retry_count = 0
            except Exception as e:
                logging.error(f"Ошибка при опросе бота: {e}")
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    logging.info(f"Попытка перезапуска опроса бота... (попытка {retry_count})")
                    time.sleep(5)
                else:
                    logging.error("Достигнуто максимальное количество попыток. Остановка бота.")
    except KeyboardInterrupt:
        logging.info("Опрос бота остановлен пользователем.")

