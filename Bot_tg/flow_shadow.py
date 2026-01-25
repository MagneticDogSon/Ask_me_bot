import json
import asyncio
from datetime import datetime
from Bot_tg.config import (
    PROFILE_FILE, RESULTS_FILE, GITHUB_PAGES_URL,
    FinalResult
)
from Bot_tg.agents_shadow import agent_08_analysis
from Bot_tg.utils import read_file_sync, write_file_sync
from Bot_tg.state_manager import user_states

async def on_shadow_completion(bot, chat_id, state):
    await bot.send_message(chat_id, "🏮 Сессия завершена. Я ухожу в тишину, чтобы осмыслить твои слова...")
    
    # Analyze results
    answers_list = [i.model_dump() for i in state["interactions"]]
    answers_json = json.dumps(answers_list, ensure_ascii=False, indent=2)
    
    analysis_text = await agent_08_analysis(answers_json)
    
    # Send result to user
    await bot.send_message(chat_id, f"**ТВОЙ SHADOW ARCHETYPE:**\n\n{analysis_text}", parse_mode='Markdown')

    # Update profile
    current_profile = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    header = "### 17. SHADOW ARCHETYPE"
    
    if header in current_profile:
        parts = current_profile.split(header)
        new_profile = parts[0].strip() + "\n\n" + analysis_text
    else:
        new_profile = current_profile.strip() + "\n\n" + analysis_text
    
    await asyncio.to_thread(write_file_sync, PROFILE_FILE, new_profile)
    await bot.send_message(chat_id, "Эта часть твоей Тени теперь освещена и сохранена в профиле.")
    user_states.pop(chat_id, None)
