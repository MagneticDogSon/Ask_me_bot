import os
import sys
import json
import asyncio
from datetime import datetime
from aiohttp import web
from telebot.async_telebot import AsyncTeleBot
from telebot.types import BotCommand, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# --- Настройка путей для корректного импорта ---
# Добавляем родительскую директорию в sys.path, чтобы работал импорт Bot_tg...
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Импорты из упрощенных модулей ---
from Bot_tg.config import TELEGRAM_BOT_TOKEN, RESULTS_FILE, WEBAPP_HTML_FILE, GITHUB_PAGES_URL, FinalResult, Interaction
from Bot_tg.agents import (
    generate_onboarding_questions, 
    fill_profile_from_onboarding,
    agent_01, 
    agent_02, 
    agent_03, 
    agent_04,
    agent_05,
    generate_webapp_url
)

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле.")

bot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)
user_states = {}

# --- Установка команд меню (асинхронная) ---
async def set_bot_commands(bot_instance):
    commands = [
        BotCommand("start", "Перезапустить бота"),
        BotCommand("greeting", "Пройти знакомство"),
        BotCommand("profile", "Дополнить профиль"),
        BotCommand("tasks", "Мои задачи и план")
    ]
    await bot_instance.set_my_commands(commands)
    print("[APP] Команды меню установлены.")

# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
async def start_message(message):
    chat_id = message.chat.id
    await bot.send_message(chat_id, 'Привет! /greeting для знакомства, /profile для работы с профилем.')
    if chat_id in user_states: user_states.pop(chat_id)

@bot.message_handler(commands=['greeting'])
async def greeting_command(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "Друг"
    await bot.send_message(chat_id, f"Рад тебя видеть, {user_name}! Генерирую анкету...")
    
    questions = await generate_onboarding_questions(user_name)
    if not questions:
        await bot.send_message(chat_id, "Похоже, мы уже знакомы! Для дополнения профиля используй /profile.")
        return
    
    # Генерируем ссылку для GitHub Pages
    url = generate_webapp_url(GITHUB_PAGES_URL, questions)
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("ОТКРЫТЬ АНКЕТУ", web_app=WebAppInfo(url=url)))
    
    await bot.send_message(chat_id, "Нажми на кнопку ниже, чтобы открыть анкету.", reply_markup=markup)
    user_states[chat_id] = {"mode": "onboarding", "questions": questions, "step": 0, "interactions": []}

@bot.message_handler(commands=['tasks'])
async def tasks_command(message):
    chat_id = message.chat.id
    await bot.send_message(chat_id, "Загружаю ваш актуальный план задач...")
    
    tasks_text = "Ваш список задач пока пуст. Сформулируйте цель в чате, чтобы я помог составить план!"
    if os.path.exists(Bot_tg.config.PROFILE_FILE):
        with open(Bot_tg.config.PROFILE_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            # Пытаемся найти раздел ЗАДАЧИ
            import re
            match = re.search(r"### 9\. ЗАДАЧИ\n(.*?)(?=\n###|$)", content, re.DOTALL)
            if match and match.group(1).strip():
                tasks_text = f"**Ваш текущий план:**\n{match.group(1).strip()}"
    
    await bot.send_message(chat_id, tasks_text, parse_mode='Markdown')

@bot.message_handler(commands=['profile'])
async def profile_command(message):
    chat_id = message.chat.id
    await bot.send_message(chat_id, "Анализирую твой профиль... Пожалуйста, подожди около 10-15 секунд.")
    try:
        # Устанавливаем таймаут для LLM вызова через asyncio.wait_for если нужно, 
        # но пока просто добавим больше логов.
        questions_data = await agent_04()
        
        if not questions_data or len(questions_data) < 1:
            await bot.send_message(chat_id, "Твой профиль уже достаточно подробный! Если хочешь что-то изменить, просто напиши мне об этом.")
            return
        
        # Генерируем ссылку для GitHub Pages
        url = generate_webapp_url(GITHUB_PAGES_URL, questions_data)
        
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("ЗАПОЛНИТЬ ПРОФИЛЬ", web_app=WebAppInfo(url=url)))
        
        await bot.send_message(chat_id, "Я нашел интересные темы для обсуждения. Нажми кнопку ниже.", reply_markup=markup)
        user_states[chat_id] = {"mode": "profiling", "questions": questions_data, "step": 0, "interactions": []}
    except Exception as e:
        print(f"[APP] Ошибка в /profile: {e}")
        await bot.send_message(chat_id, "Извини, произошла заминка при анализе профиля. Попробуй еще раз через минуту.")

# --- Обработчик данных из WebApp ---
@bot.message_handler(content_types=['web_app_data'])
async def handle_webapp_data(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if not state:
        await bot.send_message(chat_id, "Сессия не найдена. Попробуйте еще раз.")
        return

    try:
        data = json.loads(message.web_app_data.data)
        # Преобразуем данные в формат Interaction
        interactions = [Interaction(question=item['question'], answer=item['answer']) for item in data]
        state["interactions"] = interactions
        
        await COMPLETION_HANDLERS[state["mode"]](chat_id, state)
    except Exception as e:
        print(f"[APP] Ошибка обработки данных WebApp: {e}")
        await bot.send_message(chat_id, "Произошла ошибка при получении данных.")

# --- Основной обработчик сообщений ---
@bot.message_handler(func=lambda message: True)
async def handle_message(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if not state:
        await handle_default_dialog(chat_id, message.text)
    else:
        await process_step(chat_id, message.text, state)

# --- Логика диалогов ---
async def handle_default_dialog(chat_id, user_input):
    await bot.send_message(chat_id, "Анализирую ваше желание...")
    questions_data = await agent_01(user_input)
    if not questions_data or len(questions_data) < 3:
        await bot.send_message(chat_id, "Не удалось проанализировать ваш запрос. Попробуйте переформулировать.")
        return
    user_states[chat_id] = {"mode": "default", "original_text": user_input, "questions": questions_data, "step": 0, "interactions": []}
    await ask_next_question(chat_id)

async def process_step(chat_id, user_input, state):
    current_question = state["questions"][state["step"]]
    if current_question.get("type") == "multiple_choice" and user_input not in current_question.get("variants", []) and user_input != "Следующий вопрос":
        await bot.send_message(chat_id, "Пожалуйста, выберите один из предложенных вариантов.")
        await ask_next_question(chat_id)
        return

    if user_input != "Следующий вопрос":
        state["interactions"].append(Interaction(question=current_question["question_text"], answer=user_input))
    state["step"] += 1

    if state["step"] < len(state["questions"]):
        await ask_next_question(chat_id)
    else:
        await COMPLETION_HANDLERS[state["mode"]](chat_id, state)

# --- Логика завершения диалогов ---
async def on_default_completion(chat_id, state):
    await bot.send_message(chat_id, "Анализирую ваши ответы и формулирую план действий...")
    
    # 1. Формируем финальную цель
    final_text = await agent_02(state["original_text"], state["interactions"])
    await bot.send_message(chat_id, f"**Ваша проработанная цель:**\n{final_text}", parse_mode='Markdown')
    
    # 2. Декомпозируем на задачи
    tasks = await agent_05(final_text)
    if tasks:
        roadmap = "**Предлагаемый пошаговый план:**\n"
        for i, t in enumerate(tasks, 1):
            roadmap += f"{i}. **{t['task_text']}**: {t['description']}\n"
        await bot.send_message(chat_id, roadmap, parse_mode='Markdown')
        await bot.send_message(chat_id, "Я добавил эти задачи в ваш профиль. Вы можете просмотреть их командой /tasks.")
    
    # 3. Сохраняем в JSON и запускаем обновление профиля
    final_result = FinalResult(
        session_id=f"{chat_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}", 
        original_text=state["original_text"], 
        interactions=state["interactions"], 
        final_text=final_text, 
        timestamp=datetime.now().isoformat()
    )
    append_to_json_file(final_result)
    
    # Специальное уведомление для Агента 03, что нужно обновить раздел ЗАДАЧИ
    asyncio.create_task(run_background_agent_03())
    user_states.pop(chat_id, None)

async def on_profiling_completion(chat_id, state):
    await bot.send_message(chat_id, "Спасибо за ответы! Обновляю ваш профиль...")
    final_result = FinalResult(session_id=f"{chat_id}_profile_{datetime.now().strftime('%Y%m%d%H%M%S')}", original_text="Профилирование по команде /profile", interactions=state["interactions"], final_text="Пользователь ответил на вопросы для углубления профиля.", timestamp=datetime.now().isoformat())
    append_to_json_file(final_result)
    asyncio.create_task(run_background_agent_03())
    user_states.pop(chat_id, None)

async def on_onboarding_completion(chat_id, state):
    await bot.send_message(chat_id, "Большое спасибо за ответы! Мой аналитический отдел приступает к работе...")
    await fill_profile_from_onboarding(state["interactions"])
    await bot.send_message(chat_id, "Профиль успешно создан и сохранен. Теперь ты можешь использовать команду /profile для его дополнения или просто общаться со мной.")
    user_states.pop(chat_id, None)

COMPLETION_HANDLERS = {
    "default": on_default_completion,
    "profiling": on_profiling_completion,
    "onboarding": on_onboarding_completion
}

# --- Вспомогательные функции ---
async def ask_next_question(chat_id):
    state = user_states[chat_id]
    question = state["questions"][state["step"]]
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if question.get("type") == "multiple_choice":
        for var in question.get("variants", []):
            markup.add(KeyboardButton(var))
    await bot.send_message(chat_id, f"Вопрос {state['step'] + 1}/{len(state['questions'])}: {question['question_text']}", reply_markup=markup)

def append_to_json_file(result: FinalResult):
    try:
        all_results = []
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                try: all_results = json.load(f)
                except json.JSONDecodeError: all_results = []
        all_results.append(result.model_dump())
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"[APP] Ошибка при работе с файлом результатов: {e}")

async def run_background_agent_03():
    print("[APP] Запускаем фоновую задачу для agent_03.")
    try:
        if not os.path.exists(RESULTS_FILE): return
        with open(RESULTS_FILE, "r", encoding="utf-8") as f: json_data = f.read()
        if len(json_data) > 10:
            await agent_03(json_data)
    except Exception as e:
        print(f"[APP] Ошибка в фоновой задаче agent_03: {e}")

# --- Точка входа ---
async def main():
    await set_bot_commands(bot)
    # Запускаем веб-сервер в фоне
    print("[APP] Бот запускается в асинхронном режиме...")
    await bot.polling()

if __name__ == "__main__":
    asyncio.run(main())
