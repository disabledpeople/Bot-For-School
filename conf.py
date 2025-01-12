from datetime import datetime
import os
TG_BOT_TOKEN = "ТОКЕН / TOKEN"
TG_CHAT_IDS = ["IDS admins"]
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # Корневая директория
JSON_DIR = os.path.join(ROOT_DIR, "rasp")  # Папка с JSON файлами
holiday_ranges = [
    (datetime(2024, 10, 26, 0, 0), datetime(2024, 11, 4, 23, 59)),
    (datetime(2024, 12, 29, 0, 0), datetime(2025, 1, 12, 23, 59)),
    (datetime(2025, 3, 29, 0, 0), datetime(2025, 4, 6, 23, 59)),
    (datetime(2025, 5, 27, 0, 0), datetime(2025, 8, 31, 23, 59))
]

log_colors = {
    'DEBUG': 'bold_blue',
    'INFO': 'bold_green',
    'WARNING': 'bold_yellow',
    'ERROR': 'bold_red',
    'CRITICAL': 'bold_red,bg_white',
    'NEW': 'purple'
}

# ВАЖНО ВЕЗДЕ "IDS admins" Замените на свой