from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message
from utils import load_users, save_users
from datetime import datetime, timedelta
import logging

# --- Кнопки профиля ---
def profile_buttons():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("✏️ изменить имя"), KeyboardButton("🏷 изменить класс"))
    kb.add(KeyboardButton("🌟 изменить аватар"))
    return kb

# --- Показать профиль ---
def show_profile(bot, message):
    user_id = str(message.from_user.id)
    users = load_users()
    user = users.get(user_id)

    if not user:
        logging.warning(f"show_profile: пользователь {user_id} не зарегистрирован")
        bot.send_message(message.chat.id, "вы ещё не зарегистрированы.")
        return

    avatar = user.get('avatar', '🙂')
    name = user.get('name', message.from_user.first_name or 'без имени')
    user_class = user.get('class', 'не указан')
    reg_date = user.get('registered_at', 'неизвестно')
    last_seen = user.get('last_active', 'неизвестно')

    profile_text = (
        f"{avatar} <b>ваш профиль:</b>\n\n"
        f"<b>имя:</b> {name}\n"
        f"<b>класс:</b> {user_class}\n"
        f"<b>telegram ID:</b> {user_id}\n"
        f"<b>дата регистрации:</b> {reg_date}\n"
        f"<b>последняя активность:</b> {last_seen}"
    )

    logging.info(f"show_profile: показываем профиль пользователя {user_id}")
    bot.send_message(user_id, profile_text, reply_markup=profile_buttons(), parse_mode='HTML')

# --- Обработка изменения имени ---
def handle_change_name(bot, message):
    logging.info(f"handle_change_name: запрос на изменение имени от пользователя {message.from_user.id}")
    msg = bot.send_message(message.chat.id, "введите новое имя:")
    bot.register_next_step_handler(msg, lambda m: save_new_name(bot, m))

def save_new_name(bot, message):
    user_id = str(message.from_user.id)
    new_name = message.text.strip()

    users = load_users()
    user = users.get(user_id, {})
    user['name'] = new_name
    user['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    users[user_id] = user

    save_users(users)
    logging.info(f"save_new_name: имя пользователя {user_id} изменено на '{new_name}'")
    bot.send_message(
        message.chat.id,
        f"*Имя обновлено:* _{new_name}_",
        parse_mode='Markdown'
    )

# --- Обработка изменения класса ---
def handle_change_class(bot, message):
    logging.info(f"handle_change_class: запрос на изменение класса от пользователя {message.from_user.id}")
    msg = bot.send_message(message.chat.id, "введите ваш класс (доступны: 8, 9, 10, 11):")
    bot.register_next_step_handler(msg, lambda m: save_new_class(bot, m))

def save_new_class(bot, message):
    user_id = str(message.from_user.id)
    new_class = message.text.strip()

    if new_class not in ['8', '9', '10', '11']:
        logging.warning(f"save_new_class: пользователь {user_id} ввёл недопустимый класс '{new_class}'")
        bot.send_message(
            message.chat.id,
            "❌ *Ошибка:* допустимы только классы *8*, *9*, *10* или *11*. Попробуйте снова.",
            parse_mode='Markdown'
        )
        return handle_change_class(bot, message)  # повторный запрос

    users = load_users()
    user = users.get(user_id, {})
    user['class'] = new_class
    user['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    users[user_id] = user

    save_users(users)
    logging.info(f"save_new_class: класс пользователя {user_id} изменён на '{new_class}'")
    bot.send_message(
        message.chat.id,
        f"*Класс обновлён:* _{new_class}_",
        parse_mode='Markdown'
    )

# --- Обработка изменения аватара ---
def handle_change_avatar(bot, message):
    logging.info(f"handle_change_avatar: запрос на изменение аватара от пользователя {message.from_user.id}")
    msg = bot.send_message(message.chat.id, "введите новый аватар (эмодзи, максимум 2 символа):")
    bot.register_next_step_handler(msg, lambda m: save_new_avatar(bot, m))

def save_new_avatar(bot, message):
    user_id = str(message.from_user.id)
    new_avatar = message.text.strip()

    if len(new_avatar) > 2:
        logging.warning(f"save_new_avatar: пользователь {user_id} ввёл слишком длинный аватар '{new_avatar}'")
        bot.send_message(
            message.chat.id,
            "❌ Слишком длинный аватар. Используйте максимум *2* символа.",
            parse_mode='Markdown'
        )
        return

    users = load_users()
    user = users.get(user_id, {})
    user['avatar'] = new_avatar
    user['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    users[user_id] = user

    save_users(users)
    logging.info(f"save_new_avatar: аватар пользователя {user_id} изменён на '{new_avatar}'")
    bot.send_message(
        message.chat.id,
        f"*Аватар обновлён:* {new_avatar}",
        parse_mode='Markdown'
    )

def add_score(user_id: str):
    users = load_users()
    user = users.get(user_id, {})
    
    now = datetime.now()

    last_score_time_str = user.get('last_score_time')
    if last_score_time_str:
        try:
            last_score_time = datetime.strptime(last_score_time_str, "%Y-%m-%d %H:%M:%S")
            if now < last_score_time + timedelta(minutes=10):
                logging.info(f"add_score: пользователь {user_id} в cooldown, баллы не начислены")
                return False
        except Exception as e:
            logging.error(f"add_score: ошибка парсинга времени для пользователя {user_id}: {e}")

    # начисляем балл
    user['score'] = user.get('score', 0) + 1
    user['last_score_time'] = now.strftime("%Y-%m-%d %H:%M:%S")
    user['last_active'] = now.strftime("%Y-%m-%d %H:%M")
    
    users[user_id] = user
    save_users(users)
    logging.info(f"add_score: пользователю {user_id} начислен балл. Текущий счет: {user['score']}")
    return True

def safe_dt(date_str, fmt="%Y-%m-%d %H:%M:%S"):
    try:
        return datetime.strptime(date_str, fmt)
    except Exception:
        return datetime.max  # чтобы min() не ломалось, если дата пустая/неверная

def show_top_users(bot, message: Message):
    users = load_users()
    chat_id = message.chat.id
    
    if not users:
        logging.info("show_top_users: нет данных о пользователях")
        bot.send_message(chat_id, "нет данных о пользователях.")
        return

    # 👑 Самый активный (по score)
    top_score_user = max(users.values(), key=lambda u: u.get('score', 0), default=None)

    # 📅 Самый старый (по registration_date)
    oldest_user = min(users.values(), key=lambda u: safe_dt(u.get('registration_date', '')), default=None)

    # 🕒 Самый новый (по registration_date)
    newest_user = max(users.values(), key=lambda u: safe_dt(u.get('registration_date', '')), default=None)

    # 🧠 Самый длинный ник
    longest_name_user = max(users.values(), key=lambda u: len(u.get('name', '')), default=None)

    # 🐣 Самый короткий ник
    shortest_name_user = min(users.values(), key=lambda u: len(u.get('name', '')), default=None)

    msg = "🏆 *ТОПЫ ПОЛЬЗОВАТЕЛЕЙ:*\n\n"

    if top_score_user:
        msg += f"👑 *Активный:* {top_score_user.get('name', '—')} — {top_score_user.get('score', 0)} очков\n"
    else:
        logging.warning("show_top_users: не найден активный пользователь")

    if oldest_user:
        reg_date = oldest_user.get('registration_date', '—')
        msg += f"📅 *Старейший:* {oldest_user.get('name', '—')} — {reg_date}\n"
    else:
        logging.warning("show_top_users: не найден старейший пользователь")

    if newest_user:
        reg_date = newest_user.get('registration_date', '—')
        msg += f"🕒 *Новый:* {newest_user.get('name', '—')} — {reg_date}\n"
    else:
        logging.warning("show_top_users: не найден новый пользователь")

    if longest_name_user:
        length = len(longest_name_user.get('name', ''))
        msg += f"🧠 *Длинный ник:* {longest_name_user.get('name', '—')} ({length} символов)\n"
    else:
        logging.warning("show_top_users: не найден пользователь с длинным ником")

    if shortest_name_user:
        length = len(shortest_name_user.get('name', ''))
        msg += f"🐣 *Короткий ник:* {shortest_name_user.get('name', '—')} ({length} символов)\n"
    else:
        logging.warning("show_top_users: не найден пользователь с коротким ником")

    try:
        bot.send_message(chat_id, msg, parse_mode='Markdown')
        logging.info(f"show_top_users: топы пользователей отправлены в чат {chat_id}")
    except Exception as e:
        logging.error(f"show_top_users: ошибка при отправке сообщения в чат {chat_id}: {e}")
