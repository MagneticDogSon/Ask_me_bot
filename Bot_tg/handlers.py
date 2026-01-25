import json
import asyncio
import re
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from Bot_tg.config import (
    PROFILE_FILE, GITHUB_PAGES_URL, GREETING_QUESTIONS_FILE, 
    TELOS_QUESTIONS_FILE, USER_PROGRESS_FILE, Interaction
)
from Bot_tg.agents import agent_01, agent_04, agent_06, agent_07_questions, generate_webapp_url
from Bot_tg.utils import read_file_sync, load_json_sync, create_initial_profile
from Bot_tg.state_manager import user_states, user_progress, register_user_activity, update_last_activity, save_user_progress
from Bot_tg.flow import COMPLETION_HANDLERS

def register_handlers(bot):

    @bot.message_handler(commands=['start'])
    async def start_message(message):
        chat_id = message.chat.id
        if chat_id in user_states: user_states.pop(chat_id)
        register_user_activity(chat_id, USER_PROGRESS_FILE)
        profile_content = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
        if not profile_content.strip():
            await handle_new_user_flow(bot, chat_id, message.from_user.first_name)
            return
        await bot.send_message(chat_id, 'Привет! /greeting для знакомства, /profile для работы с профилем.')

    async def handle_new_user_flow(bot, chat_id, user_first_name):
        user_name = user_first_name or "Друг"
        await bot.send_message(chat_id, f"Привет, {user_name}! Вижу, что мы еще не знакомы. Генерирую для тебя персональную анкету для настройки...")
        questions = await asyncio.to_thread(load_json_sync, GREETING_QUESTIONS_FILE)
        if questions:
            url = generate_webapp_url(GITHUB_PAGES_URL, questions)
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(KeyboardButton("ОТКРЫТЬ АНКЕТУ", web_app=WebAppInfo(url=url)))
            await bot.send_message(chat_id, "Анкета готова! Нажми кнопку ниже, чтобы пройти быстрый тест личности (10 вопросов).", reply_markup=markup)
            user_states[chat_id] = {
                "mode": "onboarding", 
                "questions": questions, 
                "step": 0, 
                "interactions": [],
                "last_activity": datetime.now()
            }
        else:
            await bot.send_message(chat_id, "Хм, возникла небольшая заминка при подготовке анкеты. Попробуй нажать /start еще раз.")

    @bot.message_handler(commands=['greeting', 'greetings'])
    async def greeting_command(message):
        chat_id = message.chat.id
        await bot.send_message(chat_id, "Моментально открываю анкету...")
        questions = await asyncio.to_thread(load_json_sync, GREETING_QUESTIONS_FILE)
        if not questions:
            await bot.send_message(chat_id, "Ошибка загрузки вопросов.")
            return
        url = generate_webapp_url(GITHUB_PAGES_URL, questions)
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("📝 ОТКРЫТЬ АНКЕТУ", web_app=WebAppInfo(url=url)))
        await bot.send_message(chat_id, "Вопросы готовы! Жми кнопку ниже 👇", reply_markup=markup)
        user_states[chat_id] = {
            "mode": "onboarding", 
            "questions": questions, 
            "step": 0, 
            "interactions": [],
            "last_activity": datetime.now()
        }
        register_user_activity(chat_id, USER_PROGRESS_FILE)

    @bot.message_handler(commands=['tasks'])
    async def tasks_command(message):
        chat_id = message.chat.id
        await bot.send_message(chat_id, "Загружаю ваш актуальный план задач...")
        tasks_text = "Ваш список задач пока пуст. Сформулируйте цель в чате, чтобы я помог составить план!"
        content = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
        if content:
            match = re.search(r"### 9\. ЗАДАЧИ\n(.*?)(?=\n###|$)", content, re.DOTALL)
            if match and match.group(1).strip():
                tasks_text = f"**Ваш текущий план:**\n{match.group(1).strip()}"
        await bot.send_message(chat_id, tasks_text, parse_mode='Markdown')

    @bot.message_handler(commands=['profile'])
    async def profile_command(message):
        chat_id = message.chat.id
        await bot.send_message(chat_id, "Анализирую твой профиль... Пожалуйста, подожди около 10-15 секунд.")
        try:
            questions_data = await agent_04()
            if not questions_data or len(questions_data) < 1:
                await bot.send_message(chat_id, "Твой профиль уже достаточно подробный!")
                return
            url = generate_webapp_url(GITHUB_PAGES_URL, questions_data)
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(KeyboardButton("ЗАПОЛНИТЬ ПРОФИЛЬ", web_app=WebAppInfo(url=url)))
            await bot.send_message(chat_id, "Я нашел интересные темы для обсуждения. Нажми кнопку ниже.", reply_markup=markup)
            user_states[chat_id] = {
                "mode": "profiling", 
                "questions": questions_data, 
                "step": 0, 
                "interactions": [],
                "last_activity": datetime.now()
            }
        except Exception as e:
            print(f"[HANDLERS] Ошибка в /profile: {e}")
            await bot.send_message(chat_id, "Ошибка при анализе профиля.")

    @bot.message_handler(commands=['analysis'])
    async def analysis_command(message):
        chat_id = message.chat.id
        await bot.send_message(chat_id, "🔍 Приступаю к глубокому анализу вашего профиля...")
        try:
            questions_data = await agent_06()
            if not questions_data or len(questions_data) < 1:
                await bot.send_message(chat_id, "Ваш профиль пока не требует глубокого анализа.")
                return
            questions_data = questions_data[:5]
            url = generate_webapp_url(GITHUB_PAGES_URL, questions_data)
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(KeyboardButton("🧠 НАЧАТЬ ИССЛЕДОВАНИЕ", web_app=WebAppInfo(url=url)))
            await bot.send_message(chat_id, f"Анализ завершен. Я подготовил {len(questions_data)} вопросов.", reply_markup=markup)
            user_states[chat_id] = {
                "mode": "analysis", 
                "questions": questions_data, 
                "step": 0, 
                "interactions": [],
                "last_activity": datetime.now()
            }
        except Exception as e:
            print(f"[HANDLERS] Ошибка в /analysis: {e}")
            await bot.send_message(chat_id, "Ошибка анализа.")

    @bot.message_handler(commands=['ikigai', 'икигай'])
    async def ikigai_command(message):
        chat_id = message.chat.id
        await bot.send_message(chat_id, "🌊 Начинаем погружение в поиск вашего Икигай...")
        try:
            questions_data = await agent_07_questions()
            if not questions_data or len(questions_data) < 1:
                await bot.send_message(chat_id, "Не удалось начать сессию Икигай.")
                return
            url = generate_webapp_url(GITHUB_PAGES_URL, questions_data)
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(KeyboardButton("⛩️ ПУТЬ ИКИГАЙ", web_app=WebAppInfo(url=url)))
            await bot.send_message(chat_id, "Вопросы готовы. Отключите логику, включите чувства.", reply_markup=markup)
            user_states[chat_id] = {
                "mode": "ikigai", 
                "questions": questions_data, 
                "step": 0, 
                "interactions": [],
                "last_activity": datetime.now()
            }
        except Exception as e:
            print(f"[HANDLERS] Ошибка в /ikigai: {e}")
            await bot.send_message(chat_id, "Ошибка инициализации Икигай.")

    @bot.message_handler(commands=['continue', 'продолжить'])
    async def continue_profile_command(message):
        from Bot_tg.app_logic import trigger_daily_questions
        await trigger_daily_questions(bot, message.chat.id, manual=True)

    @bot.message_handler(content_types=['web_app_data'])
    async def handle_webapp_data(message):
        chat_id = message.chat.id
        state = user_states.get(chat_id)
        if not state:
            await bot.send_message(chat_id, "Сессия не найдена.")
            return
        update_last_activity(chat_id)
        try:
            data = json.loads(message.web_app_data.data)
            interactions = [Interaction(question=item['question'], answer=item['answer']) for item in data]
            state["interactions"] = interactions
            await COMPLETION_HANDLERS[state["mode"]](bot, chat_id, state)
        except Exception as e:
            print(f"[HANDLERS] Ошибка WebApp: {e}")
            await bot.send_message(chat_id, "Ошибка обработки данных.")

    @bot.message_handler(func=lambda message: True)
    async def handle_message(message):
        chat_id = message.chat.id
        state = user_states.get(chat_id)
        if state:
            update_last_activity(chat_id)
            await process_step(bot, chat_id, message.text, state)
        else:
            await handle_default_dialog(bot, chat_id, message.text)

async def handle_default_dialog(bot, chat_id, user_input):
    await bot.send_message(chat_id, "Анализирую ваше желание...")
    questions_data = await agent_01(user_input)
    if not questions_data or len(questions_data) < 3:
        await bot.send_message(chat_id, "Не удалось проанализировать запрос.")
        return
    user_states[chat_id] = {
        "mode": "default", 
        "original_text": user_input, 
        "questions": questions_data, 
        "step": 0, 
        "interactions": [],
        "last_activity": datetime.now()
    }
    await ask_next_question(bot, chat_id)

async def process_step(bot, chat_id, user_input, state):
    current_question = state["questions"][state["step"]]
    if current_question.get("type") == "multiple_choice" and user_input not in current_question.get("variants", []) and user_input != "Следующий вопрос":
        await bot.send_message(chat_id, "Пожалуйста, выберите один из вариантов.")
        await ask_next_question(bot, chat_id)
        return
    
    if user_input != "Следующий вопрос":
        state["interactions"].append(Interaction(question=current_question["question_text"], answer=user_input))
    state["step"] += 1

    if state["step"] < len(state["questions"]):
        await ask_next_question(bot, chat_id)
    else:
        await COMPLETION_HANDLERS[state["mode"]](bot, chat_id, state)

async def ask_next_question(bot, chat_id):
    state = user_states[chat_id]
    question = state["questions"][state["step"]]
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if question.get("type") == "multiple_choice":
        for var in question.get("variants", []):
            markup.add(KeyboardButton(var))
    await bot.send_message(chat_id, f"Вопрос {state['step'] + 1}/{len(state['questions'])}: {question['question_text']}", reply_markup=markup)
