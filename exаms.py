import logging
from conf import EGE_MAIN_PERIOD, EGE_RESERVE_PERIOD,OGE_MAIN_PERIOD,OGE_RESERVE_PERIOD

def get_ege_schedule_message():
    message = "📘 Расписание ЕГЭ:\n\n"
    message += "🟦 Основной период:\n"
    for date, subjects in EGE_MAIN_PERIOD:
        message += f"{date}: {', '.join(subjects)}\n"
    message += "\n🟨 Резервные дни:\n"
    for date, subjects in EGE_RESERVE_PERIOD:
        message += f"{date}: {', '.join(subjects)}\n"
    return message

def send_ege_schedule(bot, message):
    logging.info(f"Получена команда /ege от пользователя {message.chat.id}")
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, get_ege_schedule_message())

def get_oge_schedule_message():
    message = "📘 Расписание ОГЭ:\n\n"
    message += "🟦 Основной период:\n"
    for date, subjects in OGE_MAIN_PERIOD:
        message += f"{date}: {', '.join(subjects)}\n"
    message += "\n🟨 Резервные дни:\n"
    for date, subjects in OGE_RESERVE_PERIOD:
        message += f"{date}: {', '.join(subjects)}\n"
    return message

def send_oge_schedule(bot, message):
    logging.info(f"Получена команда /oge_schedule от пользователя {message.chat.id}")
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, get_oge_schedule_message())
