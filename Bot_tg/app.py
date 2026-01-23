import os
import sys
import json
import asyncio
import time
from datetime import datetime, timedelta
from aiohttp import web
from telebot.async_telebot import AsyncTeleBot
from telebot.types import BotCommand, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# --- Настройка путей для корректного импорта ---
# Добавляем родительскую директорию в sys.path, чтобы работал импорт Bot_tg...
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Импорты из упрощенных модулей ---
from Bot_tg.config import TELEGRAM_BOT_TOKEN, RESULTS_FILE, WEBAPP_HTML_FILE, GITHUB_PAGES_URL, FinalResult, Interaction, PROFILE_FILE, GREETING_QUESTIONS_FILE
from Bot_tg.agents import (
    agent_01, 
    agent_02, 
    agent_03, 
    agent_04,
    agent_05,
    agent_06,
    generate_webapp_url
)
from Bot_tg.utils import read_file_sync, write_file_sync, generate_webapp_url, create_initial_profile

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле.")

bot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)
user_states = {}

# --- Вспомогательные функции для асинхронного I/O ---
def read_file_sync(filepath: str) -> str:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def write_json_sync(filepath: str, data: list):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_json_sync(filepath: str) -> list:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []
    return []

# --- Фоновая задача очистки старых сессий ---
async def cleanup_user_states(interval_seconds: int = 300, timeout_minutes: int = 60):
    """Периодически удаляет старые сессии из user_states."""
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
                    # Если метки нет, ставим текущее время (на случай старых сессий)
                    state["last_activity"] = now
            
            for key in expired_keys:
                print(f"[CLEANUP] Удалена неактивная сессия: {key}")
                user_states.pop(key, None)
                
        except Exception as e:
            print(f"[CLEANUP] Ошибка: {e}")

# --- Установка команд меню (асинхронная) ---
async def set_bot_commands(bot_instance):
    commands = [
        BotCommand("start", "Перезапустить бота"),
        BotCommand("greetings", "Пройти знакомство (Быстро)"),
        BotCommand("profile", "Заполнить пробелы (Быстро)"),
        BotCommand("analysis", "Глубокий анализ профиля"),
        BotCommand("tasks", "Мои задачи и план")
    ]
    await bot_instance.set_my_commands(commands)
    print("[APP] Команды меню установлены.")

# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
async def start_message(message):
    chat_id = message.chat.id
    if chat_id in user_states: user_states.pop(chat_id)
    
    # Проверяем, существует ли профиль и не пустой ли он
    profile_content = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    if not profile_content.strip():
        await handle_new_user_flow(chat_id, message.from_user.first_name, profile_content)
        return

    await bot.send_message(chat_id, 'Привет! /greeting для знакомства, /profile для работы с профилем.')

async def handle_new_user_flow(chat_id, user_first_name, profile_content):
    """Orchestrates the onboarding flow for a new user."""
    user_name = user_first_name or "Друг"
    await bot.send_message(chat_id, f"Привет, {user_name}! Вижу, что мы еще не знакомы. Генерирую для тебя персональную анкету для настройки...")
    
    # Используем статические вопросы для знакомства (Agent 00 удален)
    questions = await asyncio.to_thread(load_json_sync, GREETING_QUESTIONS_FILE)
    
    if questions:
        # Генерируем ссылку
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
        # Fallback if generation fails
        print("[APP] Error generating onboarding questions for new user.")
        await bot.send_message(chat_id, "Хм, возникла небольшая заминка при подготовке анкеты. Попробуй нажать /start еще раз или используй /greeting.")

@bot.message_handler(commands=['greeting', 'greetings'])
async def greeting_command(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name or "Друг"
    await bot.send_message(chat_id, f"Привет, {user_name}! Моментально открываю анкету...")
    
    # Используем заранее подготовленные вопросы для мгновенного отклика
    # Загружаем вопросы из JSON файла
    questions = await asyncio.to_thread(load_json_sync, GREETING_QUESTIONS_FILE)
    
    if not questions:
        await bot.send_message(chat_id, "Не удалось загрузить вопросы. Использую резервный список.")
        questions = [
            {
                "question_text": "Какая сфера жизни сейчас в приоритете?",
                "type": "multiple_choice",
                "variants": ["Карьера и работа", "Личная эффективность", "Здоровье и спорт", "Обучение"]
            },
            {
                "question_text": "Что мешает вам достигать целей?",
                "type": "multiple_choice",
                "variants": ["Нет времени", "Нет мотивации", "Не знаю с чего начать", "Страх неудачи"]
            },
            {
                "question_text": "Какой формат взаимодействия вам удобнее?",
                "type": "multiple_choice",
                "variants": ["Четкие задачи", "Дружеская беседа", "Жесткий коучинг", "Свободный полет"]
            }
        ]
    
    # Генерируем ссылку для GitHub Pages
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

@bot.message_handler(commands=['tasks'])
async def tasks_command(message):
    chat_id = message.chat.id
    await bot.send_message(chat_id, "Загружаю ваш актуальный план задач...")
    
    tasks_text = "Ваш список задач пока пуст. Сформулируйте цель в чате, чтобы я помог составить план!"
    
    content = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    
    if content:
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
        user_states[chat_id] = {
            "mode": "profiling", 
            "questions": questions_data, 
            "step": 0, 
            "interactions": [],
            "last_activity": datetime.now()
        }
    except Exception as e:
        print(f"[APP] Ошибка в /profile: {e}")
        await bot.send_message(chat_id, "Извини, произошла заминка при анализе профиля. Попробуй еще раз через минуту.")

@bot.message_handler(commands=['analysis', 'анализ'])
async def analysis_command(message):
    chat_id = message.chat.id
    await bot.send_message(chat_id, "🔍 Приступаю к глубокому анализу вашего профиля... Это может занять около 30 секунд. Я ищу скрытые смыслы и противоречия.")
    
    try:
        # Agent 06: Generate deep questions
        questions_data = await agent_06()
        
        if not questions_data or len(questions_data) < 1:
            await bot.send_message(chat_id, "Ваш профиль настолько гармоничен, что у меня пока нет к нему вопросов! Попробуйте позже, когда мы больше пообщаемся.")
            return
        
        # Limit to 5 questions as per requirement if agent generates more
        questions_data = questions_data[:5]
        
        # Generate URL
        url = generate_webapp_url(GITHUB_PAGES_URL, questions_data)
        
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("🧠 НАЧАТЬ ИССЛЕДОВАНИЕ", web_app=WebAppInfo(url=url)))
        
        await bot.send_message(chat_id, f"Анализ завершен. Я подготовил {len(questions_data)} вопросов, которые помогут раскрыть вашу личность с новой стороны.", reply_markup=markup)
        
        user_states[chat_id] = {
            "mode": "analysis", 
            "questions": questions_data, 
            "step": 0, 
            "interactions": [],
            "last_activity": datetime.now()
        }
        
    except Exception as e:
        print(f"[APP] Ошибка в /analysis: {e}")
        await bot.send_message(chat_id, "Мой аналитический модуль перегрелся 🤯 Попробуйте чуть позже.")

# --- Обработчик данных из WebApp ---
@bot.message_handler(content_types=['web_app_data'])
async def handle_webapp_data(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if not state:
        await bot.send_message(chat_id, "Сессия не найдена. Попробуйте еще раз.")
        return
    
    state["last_activity"] = datetime.now()

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
    
    if state:
        state["last_activity"] = datetime.now()
        await process_step(chat_id, message.text, state)
    else:
        await handle_default_dialog(chat_id, message.text)

# --- Логика диалогов ---
async def handle_default_dialog(chat_id, user_input):
    await bot.send_message(chat_id, "Анализирую ваше желание...")
    questions_data = await agent_01(user_input)
    if not questions_data or len(questions_data) < 3:
        await bot.send_message(chat_id, "Не удалось проанализировать ваш запрос. Попробуйте переформулировать.")
        return
    user_states[chat_id] = {
        "mode": "default", 
        "original_text": user_input, 
        "questions": questions_data, 
        "step": 0, 
        "interactions": [],
        "last_activity": datetime.now()
    }
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
    await bot.send_message(chat_id, "Спасибо за ответы. Обрабатываю информацию и обновляю ваш профиль...")
    
    # 1. Сначала обновляем профиль на основе полученных ответов (Agent 03)
    answers_list = [i.model_dump() for i in state["interactions"]]
    answers_json = json.dumps(answers_list, ensure_ascii=False, indent=2)
    
    # Ждем завершения обновления, чтобы Agent 06 получил свежие данные
    await agent_03(answers_json)
    
    await bot.send_message(chat_id, "Профиль обновлен. Теперь, чтобы закрепить результат, я проведу глубокий анализ...")
    
    # 2. Запускаем Deep Profiler (Agent 06) для генерации следующих вопросов
    try:
        questions_data = await agent_06()
        
        if not questions_data or len(questions_data) < 1:
            await bot.send_message(chat_id, "На данном этапе вопросов больше нет.")
            user_states.pop(chat_id, None)
            return

        # Ограничиваем количество вопросов (например, 5)
        questions_data = questions_data[:5]
        
        # Генерируем WebApp URL
        url = generate_webapp_url(GITHUB_PAGES_URL, questions_data)
        
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("🧠 НАЧАТЬ ИССЛЕДОВАНИЕ", web_app=WebAppInfo(url=url)))
        
        await bot.send_message(chat_id, f"Я сформировал {len(questions_data)} глубоких вопросов для уточнения вашего портрета.", reply_markup=markup)
        
        # Переключаем состояние в режим 'analysis', чтобы следующая порция ответов
        # обрабатывалась через on_analysis_completion (который снова запустит Agent 03)
        user_states[chat_id] = {
            "mode": "analysis", 
            "questions": questions_data, 
            "step": 0, 
            "interactions": [],
            "last_activity": datetime.now()
        }
        
    except Exception as e:
        print(f"[APP] Ошибка при переходе к Agent 06: {e}")
        await bot.send_message(chat_id, "Произошла ошибка при генерации дополнительных вопросов.")
        user_states.pop(chat_id, None)

    # Сохраняем первичную сессию в историю (опционально)
    final_result = FinalResult(
        session_id=f"{chat_id}_initial_{datetime.now().strftime('%Y%m%d%H%M%S')}", 
        original_text=state["original_text"], 
        interactions=state["interactions"], 
        final_text="Первичный сбор данных через Agent 01 завершен.", 
        timestamp=datetime.now().isoformat()
    )
    await asyncio.to_thread(append_to_json_file, final_result)

async def on_profiling_completion(chat_id, state):
    await bot.send_message(chat_id, "Спасибо за ответы! Обновляю ваш профиль...")
    final_result = FinalResult(session_id=f"{chat_id}_profile_{datetime.now().strftime('%Y%m%d%H%M%S')}", original_text="Профилирование по команде /profile", interactions=state["interactions"], final_text="Пользователь ответил на вопросы для углубления профиля.", timestamp=datetime.now().isoformat())
    await asyncio.to_thread(append_to_json_file, final_result)
    asyncio.create_task(run_background_agent_03())
    user_states.pop(chat_id, None)

async def on_onboarding_completion(chat_id, state):
    await bot.send_message(chat_id, "Большое спасибо за ответы! Создаю ваш персональный профиль...")
    
    # Используем простую функцию для создания профиля на основе шаблона (без LLM)
    await asyncio.to_thread(create_initial_profile, state["interactions"])
    
    await bot.send_message(chat_id, "Профиль успешно заполнен! Теперь вы можете использовать команду /profile для его дополнения или просто общаться со мной.")
    user_states.pop(chat_id, None)

async def on_analysis_completion(chat_id, state):
    await bot.send_message(chat_id, "Благодарю за откровенность. Это ценная информация.")
    await bot.send_message(chat_id, "⏳ Обновляю ваш профиль, добавляя новые грани личности...")
    
    # Собираем данные для Agent 03
    final_result = FinalResult(
        session_id=f"{chat_id}_analysis_{datetime.now().strftime('%Y%m%d%H%M%S')}", 
        original_text="Глубокий анализ по команде /analysis", 
        interactions=state["interactions"], 
        final_text="Пользователь прошел углубленное интервью.", 
        timestamp=datetime.now().isoformat()
    )
    
    # Save to history
    await asyncio.to_thread(append_to_json_file, final_result)
    
    # Run Agent 03 to UPDATE profile with deep insights
    # We pass the interactions specifically from this session
    answers_list = [i.model_dump() for i in state["interactions"]]
    answers_json = json.dumps(answers_list, ensure_ascii=False, indent=2)
    
    success = await agent_03(answers_json)
    
    if success:
        await bot.send_message(chat_id, "✅ Профиль успешно обновлен! Я стал еще лучше понимать вас.")
    else:
        await bot.send_message(chat_id, "⚠️ Данные сохранены, но обновление профиля задерживается.")
    
    user_states.pop(chat_id, None)

COMPLETION_HANDLERS = {
    "default": on_default_completion,
    "profiling": on_profiling_completion,
    "onboarding": on_onboarding_completion,
    "analysis": on_analysis_completion
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
        all_results = load_json_sync(RESULTS_FILE)
        all_results.append(result.model_dump())
        write_json_sync(RESULTS_FILE, all_results)
    except IOError as e:
        print(f"[APP] Ошибка при работе с файлом результатов: {e}")

async def run_background_agent_03():
    print("[APP] Запускаем фоновую задачу для agent_03.")
    try:
        json_data = await asyncio.to_thread(read_file_sync, RESULTS_FILE)
        if len(json_data) > 10:
            await agent_03(json_data)
    except Exception as e:
        print(f"[APP] Ошибка в фоновой задаче agent_03: {e}")

# --- Точка входа ---
async def main():
    await set_bot_commands(bot)
    
    # Запуск фоновых задач
    asyncio.create_task(cleanup_user_states())
    
    # Запускаем веб-сервер в фоне (если нужен, но тут не реализован запуск, только заглушка в комменте)
    print("[APP] Бот запускается в асинхронном режиме...")
    await bot.polling()

if __name__ == "__main__":
    asyncio.run(main())
