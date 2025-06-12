import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from utils import load_json
from conf import DAYS_RU
DEJUR_FILE = 'json/dejur.json'
USERS_FILE = 'json/users.json'

# --- Получение класса пользователя ---
def get_user_class(user_id):
    users = load_json(USERS_FILE)
    return users.get(str(user_id), {}).get("class")

# --- Поиск дежурных на сегодня ---
def find_duty_by_day_for_class(user_class):
    duty_data = load_json(DEJUR_FILE)
    current_weekday = datetime.now().strftime('%A')
    current_weekday_ru = DAYS_RU.get(current_weekday, current_weekday)

    for duty in duty_data:
        if duty['day'] == current_weekday:
            duties = duty.get(str(user_class), [f"Дежурные для {user_class} класса не указаны."])
            return current_weekday_ru, duties

    return current_weekday_ru, ["Дежурные на сегодня не найдены."]

# --- Поиск дежурных на всю неделю ---
def find_duty_for_week_by_class(user_class):
    duty_data = load_json(DEJUR_FILE)
    result = []

    for duty in duty_data:
        day_en = duty.get('day', 'Unknown')
        day_ru = DAYS_RU.get(day_en, day_en)
        duties = duty.get(str(user_class), [f"Дежурные для {user_class} класса не указаны"])
        duties_str = ", ".join(duties)
        result.append(f"*{day_ru}*: {duties_str}")

    return result

# --- Команда /duty ---
def handle_duty(bot, message):
    logging.info(f"Получена команда /duty от пользователя {message.chat.id}")
    user_class = get_user_class(message.chat.id)

    if not user_class:
        bot.send_message(message.chat.id, "❌ Ваш класс не найден в системе.")
        return

    weekday_ru, duty_list = find_duty_by_day_for_class(user_class)
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(
        message.chat.id,
        f"👮 Сегодня *{weekday_ru}*, в {user_class} классе дежурят:\n" + ", ".join(duty_list),
        parse_mode='Markdown'
    )

# --- Команда /duty_week ---
def handle_duty_week(bot, message):
    logging.info(f"Получена команда /duty_week от пользователя {message.chat.id}")
    user_class = get_user_class(message.chat.id)

    if not user_class:
        bot.send_message(message.chat.id, "❌ Ваш класс не найден в системе.")
        return

    duty_week_list = find_duty_for_week_by_class(user_class)
    bot.send_chat_action(message.chat.id, 'typing')
    message_text = f"📋 *Дежурные на неделю для {user_class} класса:*\n\n" + "\n".join(duty_week_list)
    bot.send_message(message.chat.id, message_text, parse_mode='Markdown')

# --- Рассылка дежурств утром ---
def send_daily_duty(bot):
    users = load_json(USERS_FILE)
    duty_data = load_json(DEJUR_FILE)

    current_weekday = datetime.now().strftime('%A')
    current_weekday_ru = DAYS_RU.get(current_weekday, current_weekday)

    if current_weekday in ['Saturday', 'Sunday']:
        logging.info(f"Выходной день ({current_weekday_ru}), рассылка не выполняется.")
        return

    for duty in duty_data:
        if duty['day'] == current_weekday:
            for user_id_str, user_info in users.items():
                user_class = user_info.get("class")
                duties = duty.get(str(user_class))

                if duties:
                    message = f"🔔 Доброе утро!\n\nСегодня ({current_weekday_ru}) в {user_class} классе дежурят:\n" + ", ".join(duties)
                else:
                    message = f"Сегодня ({current_weekday_ru}) у {user_class} класса нет назначенных дежурных."

                try:
                    bot.send_message(int(user_id_str), message)
                    logging.info(f"Уведомление отправлено {user_id_str}")
                except Exception as e:
                    logging.warning(f"Не удалось отправить сообщение пользователю {user_id_str}: {e}")
            break


def setup_scheduler(bot):
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_duty, 'cron', hour=8, minute=0, args=[bot])
    scheduler.start()
    return scheduler
