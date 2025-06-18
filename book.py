import logging
import os
import json

USERS_FILE = 'json/users.json'

# * Отправка PDF-файлов из папки по классу *
def send_pdfs_from_folder(bot, chat_id):
    logging.debug(f"Попытка отправить PDF-файлы пользователю {chat_id}")

    # * загрузка пользователей *
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
    except Exception as e:
        logging.error(f"Ошибка при загрузке users.json: {e}")
        return

    # * получение класса пользователя *
    user_data = users.get(str(chat_id))
    if not user_data or 'class' not in user_data:
        logging.warning(f"Пользователь {chat_id} не найден или не указан класс.")
        bot.send_message(chat_id, "Не удалось определить ваш класс. Пожалуйста, обратитесь к администратору.")
        return

    class_name = str(user_data['class'])
    folder_path = os.path.join('book', class_name)

    if not os.path.isdir(folder_path):
        logging.warning(f"Папка для класса {class_name} не найдена.")
        bot.send_message(chat_id, f"Папка для вашего класса ({class_name}) не найдена.")
        return

    # * получение PDF-файлов *
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

    if not pdf_files:
        logging.warning(f"Нет PDF-файлов в папке {folder_path}")
        bot.send_message(chat_id, f"В папке для класса {class_name} нет файлов.")
        return

    try:
        bot.send_chat_action(chat_id, 'upload_document')
        for pdf_file in pdf_files:
            file_path = os.path.join(folder_path, pdf_file)
            with open(file_path, 'rb') as f:
                bot.send_document(chat_id, f, caption=pdf_file)
        logging.info(f"PDF-файлы для класса {class_name} успешно отправлены пользователю {chat_id}")
    except Exception as e:
        logging.error(f"Ошибка при отправке PDF-файлов: {e}")
        bot.send_message(chat_id, "Произошла ошибка при отправке файлов.")
