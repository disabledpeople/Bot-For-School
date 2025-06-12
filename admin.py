import logging
from datetime import datetime
import time
from utils import load_json, save_json, load_users, load_feedback_users, save_feedback_users
from conf import ADMIN_ID

# --- Пути к файлам ---
USERS_FILE = 'json/users.json'
STATS_FILE = 'json/daily_stats.json'

# --- Получение общего количества пользователей ---
def get_total_users():
    users = load_json(USERS_FILE)
    total = len(users)
    logging.debug(f"Всего пользователей: {total}")
    return total

# --- Инициализация или загрузка статистики ---
def load_or_init_stats():
    stats = load_json(STATS_FILE)
    today = datetime.now().strftime('%Y-%m-%d')

    if not stats or stats.get("date") != today:
        logging.info("Создаю новую статистику на сегодня")
        stats = {
            "date": today,
            "total_users": get_total_users(),
            "total_requests": 0,
            "schedule_today_requests": 0,
            "schedule_tomorrow_requests": 0,
            "schedule_week_requests": 0,
            "holiday_requests": 0,
            "food_requests": 0,
            "ege_schedule_requests": 0,
            "oge_schedule_requests": 0,
            "teachers_requests": 0,
            "important_numbers_requests": 0,
            "duty_requests": 0,
            "duty_week_requests": 0,
            "anon_feedback": 0,
            "feedback": 0,
            "profile": 0,
            "tops": 0
        }
        save_json(STATS_FILE, stats)
        logging.info("Новая статистика сохранена")
    else:
        logging.debug("Загружена существующая статистика на сегодня")
    return stats

# --- Обновление статистики для конкретной команды ---
def increment_daily_stat(command_key):
    logging.info(f"Обновление статистики: команда {command_key}")
    stats = load_or_init_stats()
    stats["total_requests"] = stats.get("total_requests", 0) + 1
    if command_key in stats:
        stats[command_key] += 1
        logging.info(f"Увеличен счётчик для {command_key}: {stats[command_key]}")
    else:
        logging.warning(f"Ключ статистики '{command_key}' не найден")
    stats["total_users"] = get_total_users()
    save_json(STATS_FILE, stats)
    logging.debug("Статистика сохранена")

# --- Команда для получения статистики (например, /stats) ---
def handle_stats(bot, message):
    logging.info(f"Запрошена статистика пользователем {message.from_user.id}")
    stats = load_or_init_stats()
    text = (
        f"📊 Статистика за {stats['date']}:\n\n"
        f"Всего пользователей: {stats['total_users']}\n"
        f"Всего запросов: {stats['total_requests']}\n\n"
        f"Запросы расписания сегодня: {stats['schedule_today_requests']}\n"
        f"Запросы расписания завтра: {stats['schedule_tomorrow_requests']}\n"
        f"Запросы расписания на неделю: {stats['schedule_week_requests']}\n"
        f"Запросы информации о каникулах: {stats['holiday_requests']}\n"
        f"Запросы меню: {stats['food_requests']}\n"
        f"Запросы расписания ЕГЭ: {stats['ege_schedule_requests']}\n"
        f"Запросы расписания ОГЭ: {stats['oge_schedule_requests']}\n"
        f"Запросы списка учителей: {stats['teachers_requests']}\n"
        f"Запросы важных номеров: {stats['important_numbers_requests']}\n"
        f"Запросы дежурных сегодня: {stats['duty_requests']}\n"
        f"Запросы дежурных на неделю: {stats['duty_week_requests']}\n"
        f"Запросы анонимных жалоб: {stats['anon_feedback']}\n"
        f"Запросы жалоб: {stats['feedback']}\n"
        f"Запросы профиль: {stats['profile']}\n"
        f"Запросы топы: {stats['tops']}"
    )
    bot.send_message(message.chat.id, text)
    logging.info("Статистика успешно отправлена")

def cmd_get_users(bot, message):
    logging.info(f"Пользователь {message.from_user.id} запросил список пользователей")
    users = load_users()
    if not users:
        logging.warning("Пользователи не найдены при запросе /get_users")
        bot.send_message(message.chat.id, "Пользователи не найдены.")
        return

    classes = {}
    for uid, data in users.items():
        cls = data.get('class', 'не указан')
        classes.setdefault(cls, []).append(uid)

    def sort_key(x):
        try:
            return int(x)
        except ValueError:
            return 9999

    sorted_classes = sorted(classes.keys(), key=sort_key)
    result_lines = []
    for cls in sorted_classes:
        result_lines.append(f"Класс {cls}:")
        for uid in classes[cls]:
            result_lines.append(f"  ID: {uid}")
        result_lines.append("")

    msg = "Список пользователей по классам:\n\n" + "\n".join(result_lines)
    bot.send_message(message.chat.id, msg)
    logging.info(f"Отправлен список пользователей пользователю {message.from_user.id}")

def cmd_set_class(bot, message, user_id, user_class):
    logging.info(f"Пользователь {message.from_user.id} пытается установить класс {user_class} для пользователя {user_id}")
    users = load_json(USERS_FILE)
    if str(user_id) in users:
        users[str(user_id)]["class"] = user_class
    else:
        users[str(user_id)] = {"class": user_class}
    save_json(USERS_FILE, users)
    bot.send_message(message.chat.id, f"✅ Класс пользователя с ID {user_id} установлен на {user_class}.")
    logging.info(f"Класс пользователя {user_id} установлен на {user_class}")

def handle_set_class(bot, message):
    args = message.text.split()
    if len(args) != 3:
        logging.warning(f"Неверный формат команды /set_class от пользователя {message.from_user.id}: {message.text}")
        bot.send_message(message.chat.id, "❌ Использование: /set_class <user_id> <класс>")
        return
    user_id = args[1]
    user_class = args[2]
    cmd_set_class(bot, message, user_id, user_class)

def cmd_del_user(bot, message, user_id):
    logging.info(f"Пользователь {message.from_user.id} пытается удалить пользователя {user_id}")
    users = load_json(USERS_FILE)
    if str(user_id) in users:
        users.pop(str(user_id))
        save_json(USERS_FILE, users)
        bot.send_message(message.chat.id, f"✅ Пользователь с ID {user_id} успешно удалён.")
        logging.info(f"Пользователь {user_id} удалён")
    else:
        logging.warning(f"Пользователь с ID {user_id} не найден для удаления")
        bot.send_message(message.chat.id, f"⚠ Пользователь с ID {user_id} не найден.")

def handle_del_user(bot, message):
    args = message.text.split()
    if len(args) != 2:
        logging.warning(f"Неверный формат команды /del_user от пользователя {message.from_user.id}: {message.text}")
        bot.send_message(message.chat.id, "❌ Использование: /del_user <user_id>")
        return
    user_id = args[1]
    cmd_del_user(bot, message, user_id)

def handle_announcement(bot, message, admin_ids):
    user_id = message.from_user.id
    logging.info(f"Пользователь {user_id} инициировал рассылку")

    if user_id not in admin_ids:
        logging.warning(f"Пользователь {user_id} не имеет доступа к рассылке")
        bot.send_message(message.chat.id, "❌ у вас нет доступа к этой команде.")
        return

    text = message.text.partition(' ')[2].strip()
    if not text:
        bot.send_message(message.chat.id, "❗ пожалуйста, напишите текст после /new")
        return

    users = load_users()
    if not users:
        logging.warning("Список пользователей пуст, рассылка отменена")
        bot.send_message(message.chat.id, "⚠ список пользователей пуст.")
        return

    bot.send_message(message.chat.id, f"🚀 начинаю рассылку {len(users)} пользователям...")
    success, failed = 0, 0

    for uid in users.keys():
        try:
            bot.send_message(int(uid), text, parse_mode="Markdown")
            success += 1
            logging.debug(f"Сообщение успешно отправлено {uid}")
        except Exception as e:
            failed += 1
            logging.error(f"Ошибка отправки пользователю {uid}: {e}")
        time.sleep(0.1)

    bot.send_message(message.chat.id, f"✅ Рассылка завершена.\nУспешно: {success}, ошибок: {failed}")
    logging.info(f"Рассылка завершена: {success} успешно, {failed} с ошибками")

# загружаем множество пользователей, которые в режиме обратной связи
feedback_users = load_feedback_users()

def handle_feedback_start(bot, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Unknown"
    logging.info(f"Пользователь {user_id} ({user_name}) начал отправку обратной связи")
    bot.send_message(user_id, "пожалуйста, отправьте ваше сообщение с обратной связью.")
    feedback_users.add(user_id)
    save_feedback_users(feedback_users)
    logging.debug(f"Пользователь {user_id} добавлен в список feedback_users")

def handle_feedback_receive(bot, message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Unknown"

    if user_id not in feedback_users:
        logging.debug(f"Пользователь {user_id} не в списке feedback_users")
        return

    feedback_text = message.text
    if not feedback_text:
        bot.send_message(user_id, "пожалуйста, отправьте текстовое сообщение с обратной связью.")
        logging.warning(f"Пользователь {user_id} отправил пустое сообщение обратной связи")
        return

    logging.info(f"Получена обратная связь от пользователя {user_id} ({user_name}): {feedback_text}")

    feedback_users.remove(user_id)
    save_feedback_users(feedback_users)
    logging.debug(f"Пользователь {user_id} удалён из списка feedback_users")

    for admin_id in ADMIN_ID:
        try:
            bot.send_message(admin_id, f"📩 Обратная связь от {user_id} ({user_name}):\n\n{feedback_text}")
            logging.info(f"Обратная связь отправлена администратору {admin_id}")
        except Exception as e:
            logging.error(f"Ошибка при отправке обратной связи администратору {admin_id}: {e}")

    bot.send_message(user_id, "спасибо за вашу обратную связь! мы её обязательно рассмотрим.")
    logging.info(f"Пользователю {user_id} отправлено сообщение благодарности")
