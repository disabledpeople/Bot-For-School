import json
import logging
from utils import load_teachers

def show_teachers(bot, message):
    teachers = load_teachers()
    if not teachers:
        bot.send_message(message.chat.id, "Учителя пока не добавлены.")
        return

    result = "📚 *Список учителей:*\n\n"
    for teacher in teachers:
        name = teacher.get("name", "Без имени")
        subjects = ", ".join(teacher.get("lesson", [])) or "Не указаны"
        result += f"👤 {name}\n📘 Предметы: {subjects}\n\n"

    bot.send_message(message.chat.id, result, parse_mode='Markdown')
