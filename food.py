import logging
from bs4 import BeautifulSoup
import requests
import os 
from datetime import datetime
from conf import FOOD_URL
# Отправка PDF-файлов из папки
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

# Send today food menu
def send_today_food_menu(bot, message):
    logging.info(f"Получен запрос на сегодняшнее меню от пользователя {message.chat.id}")
    url = FOOD_URL
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
