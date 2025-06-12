from utils import load_anon_feedback_users, save_anon_feedback_users
from conf import ADMIN_ID
import logging

anon_feedback_users = load_anon_feedback_users()

def start_anon_feedback(bot, message):
    user_id = message.from_user.id
    if user_id in anon_feedback_users:
        bot.send_message(user_id, "вы уже в режиме отправки анонимной жалобы. пожалуйста, отправьте ваше сообщение или напишите /cancel_anon для отмены.")
    else:
        anon_feedback_users.add(user_id)
        save_anon_feedback_users(anon_feedback_users)
        bot.send_message(user_id, "пожалуйста, отправьте ваше анонимное сообщение с жалобой или предложением.")

def cancel_anon_feedback(bot, message):
    user_id = message.from_user.id
    if user_id in anon_feedback_users:
        anon_feedback_users.remove(user_id)
        save_anon_feedback_users(anon_feedback_users)
        bot.send_message(user_id, "отмена отправки анонимной жалобы. если захотите — снова используйте /anon_feedback.")
    else:
        bot.send_message(user_id, "вы не находитесь в режиме отправки анонимной жалобы.")

def receive_anon_feedback(bot, message):
    user_id = message.from_user.id
    anon_feedback_users.remove(user_id)
    save_anon_feedback_users(anon_feedback_users)

    feedback_text = message.text
    logging.info(f"Анонимная жалоба получена от пользователя {user_id}")

    for admin_id in ADMIN_ID:
        try:
            bot.send_message(admin_id, f"🚨 Анонимное сообщение:\n\n{feedback_text}")
            logging.info(f"Анонимное сообщение отправлено администратору {admin_id}")
        except Exception as e:
            logging.error(f"Ошибка при отправке анонимного сообщения администратору {admin_id}: {e}")

    bot.send_message(user_id, "спасибо за ваше анонимное сообщение! мы обязательно его рассмотрим.")