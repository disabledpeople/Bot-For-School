from datetime import datetime, timedelta
import logging
import time
from utils import load_users
from conf import holiday_ranges

# --- Проверка на каникулы ---
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
    for chat_id in load_users:
        bot.send_message(chat_id, message)
    logging.info(f"Отправлено уведомление о начале каникул: {message}")

def notify_holiday_end(bot, end):
    message = f"Каникулы закончились! С {end.strftime('%d.%m.%Y')} до {end + timedelta(days=1)}"
    for chat_id in load_users:
        bot.send_message(chat_id, message)
    logging.info(f"Отправлено уведомление о завершении каникул: {message}")
    
def schedule_holiday_notifications(bot):
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            check_holidays(bot)
        time.sleep(60)  # Check every 60 seconds

def get_holidays_info():
    now = datetime.now()
    holidays_info = []
    for start, end in holiday_ranges:
        time_left = start - now
        if time_left.total_seconds() > 0:
            days_left = time_left.days
            hours_left = time_left.seconds // 3600
            holidays_info.append(
                f"Каникулы с {start.strftime('%d.%m.%Y %H:%M')} по {end.strftime('%d.%m.%Y %H:%M')} ({days_left} дня(ей) {hours_left} час(ов) осталось)"
            )
    return "\n".join(holidays_info)

def send_holiday_on_command(bot, message):
    logging.info(f"Получена команда /holiday от пользователя {message.chat.id}")
    holidays_info = get_holidays_info()
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, holidays_info if holidays_info else "Нет ближайших каникул.")
