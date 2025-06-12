import logging
from conf import TRUST_ID, ADMIN_ID, IMPORTANT_NUMBERS

def send_important_numbers(bot, message):
    logging.info(f"Получена команда /important_numbers от пользователя {message.chat.id}")

    if str(message.chat.id) in TRUST_ID or ADMIN_ID:
        message_text = "📞 *Важные номера:*\n\n"
        for name, number in IMPORTANT_NUMBERS:
            message_text += f"👤 {name} — `{number}`\n"

        bot.send_message(message.chat.id, message_text, parse_mode='Markdown')
        logging.info(f"Важное сообщение отправлено (chat_id: {message.chat.id})")
    else:
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой информации.")
        logging.warning(f"Попытка доступа от chat_id {message.chat.id}, не входящего в список TG_CHAT_IDS.")
