import json
import asyncio
from datetime import datetime
from Bot_tg.config import (
    PROFILE_FILE, RESULTS_FILE, USER_PROGRESS_FILE, GITHUB_PAGES_URL,
    FinalResult, Interaction
)
from Bot_tg.agents import (
    agent_03, agent_04, agent_06, agent_07_analysis, generate_webapp_url
)
from Bot_tg.utils import read_file_sync, write_file_sync, load_json_sync, write_json_sync, create_initial_profile
from Bot_tg.state_manager import user_states, save_user_progress, user_progress

def append_to_json_file(result: FinalResult):
    try:
        all_results = load_json_sync(RESULTS_FILE)
        all_results.append(result.model_dump())
        write_json_sync(RESULTS_FILE, all_results)
    except IOError as e:
        print(f"[FLOW] Ошибка при работе с файлом результатов: {e}")

async def on_default_completion(bot, chat_id, state):
    await bot.send_message(chat_id, "Спасибо за ответы. Обрабатываю информацию и обновляю ваш профиль...")
    answers_list = [i.model_dump() for i in state["interactions"]]
    answers_json = json.dumps(answers_list, ensure_ascii=False, indent=2)
    await agent_03(answers_json)
    await bot.send_message(chat_id, "Профиль обновлен. Теперь, чтобы закрепить результат, я проведу глубокий анализ...")
    
    try:
        questions_data = await agent_06()
        if not questions_data or len(questions_data) < 1:
            await bot.send_message(chat_id, "На данном этапе вопросов больше нет.")
            user_states.pop(chat_id, None)
            return

        questions_data = questions_data[:5]
        url = generate_webapp_url(GITHUB_PAGES_URL, questions_data)
        from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("🧠 НАЧАТЬ ИССЛЕДОВАНИЕ", web_app=WebAppInfo(url=url)))
        
        await bot.send_message(chat_id, f"Я сформировал {len(questions_data)} глубоких вопросов для уточнения вашего портрета.", reply_markup=markup)
        
        user_states[chat_id] = {
            "mode": "analysis", 
            "questions": questions_data, 
            "step": 0, 
            "interactions": [],
            "last_activity": datetime.now()
        }
    except Exception as e:
        print(f"[FLOW] Ошибка при переходе к Agent 06: {e}")
        await bot.send_message(chat_id, "Произошла ошибка при генерации дополнительных вопросов.")
        user_states.pop(chat_id, None)

    final_result = FinalResult(
        session_id=f"{chat_id}_initial_{datetime.now().strftime('%Y%m%d%H%M%S')}", 
        original_text=state.get("original_text", ""), 
        interactions=state["interactions"], 
        final_text="Первичный сбор данных через Agent 01 завершен.", 
        timestamp=datetime.now().isoformat()
    )
    await asyncio.to_thread(append_to_json_file, final_result)

async def on_profiling_completion(bot, chat_id, state):
    await bot.send_message(chat_id, "Спасибо за ответы! Обновляю ваш профиль...")
    final_result = FinalResult(
        session_id=f"{chat_id}_profile_{datetime.now().strftime('%Y%m%d%H%M%S')}", 
        original_text="Профилирование по команде /profile", 
        interactions=state["interactions"], 
        final_text="Пользователь ответил на вопросы для углубления профиля.", 
        timestamp=datetime.now().isoformat()
    )
    await asyncio.to_thread(append_to_json_file, final_result)
    
    # Run Agent 03 in background
    answers_list = [i.model_dump() for i in state["interactions"]]
    answers_json = json.dumps(answers_list, ensure_ascii=False, indent=2)
    asyncio.create_task(agent_03(answers_json))
    
    user_states.pop(chat_id, None)

async def on_onboarding_completion(bot, chat_id, state):
    await bot.send_message(chat_id, "Большое спасибо за ответы! Создаю ваш персональный профиль...")
    await asyncio.to_thread(create_initial_profile, state["interactions"])
    await bot.send_message(chat_id, "Профиль успешно заполнен! Теперь вы можете использовать команду /profile для его дополнения или просто общаться со мной.")
    user_states.pop(chat_id, None)

async def on_analysis_completion(bot, chat_id, state):
    await bot.send_message(chat_id, "Благодарю за откровенность. Это ценная информация.")
    await bot.send_message(chat_id, "⏳ Обновляю ваш профиль, добавляя новые грани личности...")
    
    answers_list = [i.model_dump() for i in state["interactions"]]
    answers_json = json.dumps(answers_list, ensure_ascii=False, indent=2)
    await agent_03(answers_json)
    
    user_states.pop(chat_id, None)

async def on_ikigai_completion(bot, chat_id, state):
    await bot.send_message(chat_id, "Ответы приняты. Медитирую над вашим Икигай...")
    answers_list = [i.model_dump() for i in state["interactions"]]
    answers_json = json.dumps(answers_list, ensure_ascii=False, indent=2)
    analysis_text = await agent_07_analysis(answers_json)
    await bot.send_message(chat_id, f"**ВАШ ИКИГАЙ BLUEPRINT (2026):**\n\n{analysis_text}", parse_mode='Markdown')

    current_profile = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    header = "### 16. IKIGAI BLUEPRINT"
    if header in current_profile:
        parts = current_profile.split(header)
        new_profile = parts[0].strip() + "\n\n" + analysis_text
    else:
        new_profile = current_profile.strip() + "\n\n" + analysis_text
    
    await asyncio.to_thread(write_file_sync, PROFILE_FILE, new_profile)
    await bot.send_message(chat_id, "Этот анализ навсегда сохранен в вашем профиле.")
    user_states.pop(chat_id, None)

async def on_continuing_completion(bot, chat_id, state):
    await bot.send_message(chat_id, "Ответы приняты! Обновляю ваш прогресс и профиль...")
    cid = str(chat_id)
    answered_texts = [i.question for i in state["interactions"]]
    if cid not in user_progress: user_progress[cid] = []
    user_progress[cid].extend(answered_texts)
    await asyncio.to_thread(save_user_progress, USER_PROGRESS_FILE)
    
    answers_list = [i.model_dump() for i in state["interactions"]]
    answers_json = json.dumps(answers_list, ensure_ascii=False, indent=2)
    asyncio.create_task(agent_03(answers_json))
    
    await bot.send_message(chat_id, "Профиль успешно обновлен! Следующая порция вопросов будет доступна завтра или по команде /continue.")
    user_states.pop(chat_id, None)

COMPLETION_HANDLERS = {
    "default": on_default_completion,
    "profiling": on_profiling_completion,
    "onboarding": on_onboarding_completion,
    "analysis": on_analysis_completion,
    "ikigai": on_ikigai_completion,
    "continuing_profile": on_continuing_completion
}
