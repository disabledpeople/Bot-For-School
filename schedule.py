import logging
from utils import load_users,load_json

SCHEDULE_FILE = 'json/schedule.json'

# --- Получить расписание ---
def get_schedule(chat_id, day):
    logging.debug(f"Получение расписания для пользователя {chat_id} на день {day}")

    users = load_users()
    user_info = users.get(str(chat_id), {})
    user_class = user_info.get('class', 'unknown')

    logging.debug(f"Класс пользователя {chat_id}: {user_class}")

    if user_class == 'unknown':
        logging.warning(f"Класс пользователя {chat_id} не найден.")
        return "Ваш класс не найден."

    days_mapping = {
        'monday': 'Monday',
        'tuesday': 'Tuesday',
        'wednesday': 'Wednesday',
        'thursday': 'Thursday',
        'friday': 'Friday',
        'saturday': 'Saturday',
        'sunday': 'Sunday'
    }

    day = day.lower()
    if day not in days_mapping:
        logging.error("Неверный день недели.")
        return "Неверный день недели."

    day_key = days_mapping[day]
    schedule_data = load_json(SCHEDULE_FILE)

    if user_class in schedule_data:
        daily_schedule = schedule_data[user_class].get(day_key, [])

        if not daily_schedule:
            return "Сегодня нет уроков."

        response = []
        for lesson in daily_schedule:
            response.append(f"🕒 {lesson['time']}: 📚 {lesson['subject']} (Учитель: {lesson['teacher']})")

        logging.debug(f"Получено расписание: {response}")
        return '\n'.join(response)

    return "Расписание для вашего класса не найдено."