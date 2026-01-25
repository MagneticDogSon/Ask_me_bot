import os
import sys
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.types import BotCommand

# --- Настройка путей ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Импорты ---
from Bot_tg.config import TELEGRAM_BOT_TOKEN, USER_PROGRESS_FILE
from Bot_tg.state_manager import load_user_progress
from Bot_tg.handlers import register_handlers
from Bot_tg.handlers_shadow import register_shadow_handlers # Новое
from Bot_tg.app_logic import cleanup_user_states, daily_scheduler

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле.")

bot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)

# --- Инициализация ---
load_user_progress(USER_PROGRESS_FILE)
register_handlers(bot)
register_shadow_handlers(bot) # Новое

async def set_bot_commands(bot_instance):
    commands = [
        BotCommand("start", "Перезапустить бота"),
        BotCommand("greetings", "Пройти знакомство"),
        BotCommand("profile", "Заполнить пробелы"),
        BotCommand("analysis", "Глубокий анализ"),
        BotCommand("continue", "Продолжить заполнение"),
        BotCommand("ikigai", "Найти Икигай"),
        BotCommand("shadow", "Теневая работа (Дзен)"), # Новое
        BotCommand("tasks", "Мои задачи")
    ]
    await bot_instance.set_my_commands(commands)
    print("[APP] Команды меню установлены.")

async def main():
    await set_bot_commands(bot)
    
    # Запуск фоновых задач
    asyncio.create_task(cleanup_user_states())
    asyncio.create_task(daily_scheduler(bot))
    
    print("[APP] Бот запускается...")
    await bot.polling()

if __name__ == "__main__":
    asyncio.run(main())
