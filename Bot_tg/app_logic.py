import asyncio
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from Bot_tg.config import (
    GITHUB_PAGES_URL, TELOS_QUESTIONS_FILE, USER_PROGRESS_FILE
)
from Bot_tg.agents import generate_webapp_url
from Bot_tg.utils import load_json_sync
from Bot_tg.state_manager import user_states, user_progress, save_user_progress, register_user_activity

async def cleanup_user_states(interval_seconds: int = 300, timeout_minutes: int = 60):
    print("[APP] Запущен сборщик мусора сессий.")
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            now = datetime.now()
            expired_keys = []
            for chat_id, state in user_states.items():
                last_activity = state.get("last_activity")
                if last_activity and (now - last_activity) > timedelta(minutes=timeout_minutes):
                    expired_keys.append(chat_id)
                elif not last_activity:
                    state["last_activity"] = now
            for key in expired_keys:
                print(f"[CLEANUP] Удалена неактивная сессия: {key}")
                user_states.pop(key, None)
        except Exception as e:
            print(f"[CLEANUP] Ошибка: {e}")

async def trigger_daily_questions(bot, chat_id, manual=False):
    try:
        all_questions = await asyncio.to_thread(load_json_sync, TELOS_QUESTIONS_FILE)
        if not all_questions:
            if manual: await bot.send_message(chat_id, "Не удалось загрузить вопросы.")
            return

        cid = str(chat_id)
        answered = user_progress.get(cid, [])
        available = [q for q in all_questions if q['question_text'] not in answered]
        
        if not available:
            if manual:
                await bot.send_message(chat_id, "Вы ответили на все вопросы базового профиля! 🏆")
            return

        batch = available[:10]
        url = generate_webapp_url(GITHUB_PAGES_URL, batch)
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("✍️ ПРОДОЛЖИТЬ ЗАПОЛНЕНИЕ", web_app=WebAppInfo(url=url)))
        
        msg = "Настало время продолжить профиль." if not manual else "Вот следующая порция вопросов."
        await bot.send_message(chat_id, msg, reply_markup=markup)
        
        user_states[chat_id] = {
            "mode": "continuing_profile", 
            "questions": batch, 
            "step": 0, 
            "interactions": [],
            "last_activity": datetime.now()
        }
        register_user_activity(chat_id, USER_PROGRESS_FILE)
    except Exception as e:
        print(f"[LOGIC] Error in trigger_daily_questions: {e}")

async def daily_scheduler(bot):
    print("[SCHEDULER] Daily scheduler started.")
    while True:
        try:
            now = datetime.now()
            if now.hour == 18 and now.minute == 0:
                for chat_id_str in list(user_progress.keys()):
                    try:
                        cid = int(chat_id_str)
                        asyncio.create_task(trigger_daily_questions(bot, cid, manual=False))
                    except ValueError: pass
                await asyncio.sleep(61)
            else:
                await asyncio.sleep(30)
        except Exception as e:
            print(f"[SCHEDULER] Error: {e}")
            await asyncio.sleep(30)
