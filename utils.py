# --- utils.py ---
import json
import logging
import os
from datetime import datetime

# --- Пути к файлам ---
USERS_FILE = 'json/users.json'
SCHEDULE_FILE = 'json/schedule.json'
DEJUR_FILE = 'json/dejur.json'
TEACHERS_FILE = 'json/teachers.json'
STATS_FILE = 'json/daily_stats.json'
FEEDBACK_STATE_FILE = 'json/feedback_users.json'
ANON_FEEDBACK_USERS_FILE = 'json/anon_feedback_users.json'

# --- Загрузка JSON из файла ---
def load_json(file_path):
    if not os.path.exists(file_path):
        logging.warning(f"Файл {file_path} не найден, возвращаю пустой словарь")
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.debug(f"Успешно загружен файл {file_path}")
            return data
    except Exception as e:
        logging.error(f"Ошибка при загрузке JSON файла {file_path}: {e}")
        return {}

# --- Сохранение JSON в файл ---
def save_json(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.debug(f"Успешно сохранён файл {file_path}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении JSON файла {file_path}: {e}")

# --- Работа с пользователями ---
def load_users():
    logging.info("Загрузка пользователей...")
    users = load_json(USERS_FILE)
    logging.info(f"Успешно загружены пользователи: {len(users)}")
    logging.debug(f"Загруженные пользователи: {users}")
    return users

def save_users(users):
    logging.debug(f"Сохранение пользователей: {users}")
    save_json(USERS_FILE, users)

# --- Работа с учителями ---
def load_teachers():
    logging.debug("Загрузка учителей...")
    try:
        with open(TEACHERS_FILE, 'r', encoding='utf-8') as file:
            teachers = json.load(file)
            logging.info("Успешно загружены учителя.")
            logging.debug(f"Загружены учителя: {teachers}")
            return teachers
    except FileNotFoundError:
        logging.error(f"Файл с учителями не найден: {TEACHERS_FILE}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка декодирования JSON (учителя): {e}")
        return {}

def load_feedback_users():
    if not os.path.exists(FEEDBACK_STATE_FILE):
        return set()  # файл не найден — возвращаем пустое множество
    try:
        with open(FEEDBACK_STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data)  # преобразуем список в множество для быстрого поиска
    except Exception as e:
        logging.error(f"Ошибка при загрузке файла обратной связи: {e}")
        return set()  # в случае ошибки тоже возвращаем пустое множество

def save_feedback_users(users_set):
    try:
        with open(FEEDBACK_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(users_set), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка при сохранении файла обратной связи: {e}")

def load_anon_feedback_users():
    try:
        with open(ANON_FEEDBACK_USERS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_anon_feedback_users(users_set):
    with open(ANON_FEEDBACK_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(users_set), f, ensure_ascii=False, indent=2)

from datetime import datetime

def register_user_with_date_if_new(chat_id: str, selected_class: str):
    users = load_users()

    if chat_id not in users:
        users[chat_id] = {
            "class": selected_class,
            "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        users[chat_id]["class"] = selected_class
        if "registration_date" not in users[chat_id]:
            users[chat_id]["registration_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_users(users)
