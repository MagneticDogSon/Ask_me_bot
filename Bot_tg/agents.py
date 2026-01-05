import os
import json
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from Bot_tg.config import (
    llm_pro, llm_flash, 
    PROFILE_FILE, WEBAPP_HTML_FILE,
    Interaction, 
    QuestionParser, JsonParser
)
from Bot_tg.prompts import (
    PROMPT_AGENT_00_INSTRUCTION,
    PROMPT_AGENT_00_FILLER_INSTRUCTION,
    PROMPT_AGENT_01_PSYCHOLOGY_INSTRUCTION,
    PROMPT_AGENT_02_INSTRUCTION,
    PROMPT_AGENT_03_INSTRUCTION,
    PROMPT_AGENT_04_INSTRUCTION
)

# --- Agent 00: Onboarding ---

chain_generate_questions = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_00_INSTRUCTION) 
    | llm_flash 
    | JsonParser()
)

chain_fill_profile = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_00_FILLER_INSTRUCTION) 
    | llm_flash 
    | StrOutputParser()
)

async def generate_onboarding_questions() -> List[Dict]:
    """Асинхронно генерирует анкету знакомства."""
    print("\n[AGENT_00] Запуск (flash) для генерации вопросов...")
    existing_profile = ""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            existing_profile = f.read()
    try:
        return await chain_generate_questions.ainvoke({"existing_profile": existing_profile})
    except Exception as e:
        print(f"[AGENT_00] Ошибка в цепочке: {e}")
        return []

async def fill_profile_from_onboarding(answers: List[Interaction]):
    """Асинхронно заполняет профиль на основе ответов."""
    print("\n[AGENT_00] Запуск (flash) для заполнения профиля...")
    existing_profile = ""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            existing_profile = f.read()
            
    answers_list_of_dicts = [interaction.model_dump() for interaction in answers]
    answers_json = json.dumps(answers_list_of_dicts, ensure_ascii=False, indent=2)

    try:
        profile_text = await chain_fill_profile.ainvoke({
            "existing_profile": existing_profile,
            "onboarding_answers": answers_json
        })
        
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            f.write(profile_text)
        print(f"[AGENT_00] Файл {PROFILE_FILE} успешно обновлен.")
    except Exception as e:
        print(f"[AGENT_00] Ошибка в цепочке: {e}")

# --- Agent 01: Psychology Analysis ---

agent_01_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_01_PSYCHOLOGY_INSTRUCTION) 
    | llm_pro 
    | QuestionParser()
)

async def agent_01(user_text: str) -> List[Dict[str, list]]:
    """Асинхронно запускает цепочку Агента 1."""
    print(f"\n[AGENT_01] Запуск (pro) для текста: '{user_text[:50]}...'")
    try:
        return await agent_01_chain.ainvoke({"user_text": user_text})
    except Exception as e:
        print(f"[AGENT_01] Ошибка в цепочке: {e}")
        return []

# --- Agent 02: Text Rewriter ---

agent_02_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_02_INSTRUCTION) 
    | llm_flash 
    | StrOutputParser()
)

async def agent_02(original_text: str, interactions: List[Interaction]) -> str:
    """Асинхронно запускает цепочку Агента 2."""
    print(f"\n[AGENT_02] Запуск (flash) для переписывания текста...")
    history = ""
    for item in interactions:
        history += f"- На вопрос \"{item.question}\" был дан ответ \"{item.answer}\".\n"
    
    try:
        return await agent_02_chain.ainvoke({"original_text": original_text, "history": history})
    except Exception as e:
        print(f"[AGENT_02] Ошибка в цепочке: {e}")
        return "Не удалось переписать текст из-за ошибки."

# --- Agent 03: Profile Analyst (Background) ---

agent_03_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_03_INSTRUCTION) 
    | llm_pro 
    | StrOutputParser()
)

async def agent_03(json_data: str):
    """Асинхронно запускает цепочку Агента 3."""
    print("\n[AGENT_03] Асинхронный запуск (pro) для обновления профиля.")
    
    existing_profile = ""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            existing_profile = f.read()

    try:
        profile_text = await agent_03_chain.ainvoke({"existing_profile": existing_profile, "json_data": json_data})
        
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            f.write(profile_text)
        print(f"[AGENT_03] Файл {PROFILE_FILE} успешно обновлен.")

    except Exception as e:
        print(f"[AGENT_03] Ошибка в цепочке: {e}")

# --- Agent 04: Profile Growth ---

agent_04_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_04_INSTRUCTION) 
    | llm_flash 
    | QuestionParser()
)

async def agent_04() -> List[Dict[str, list]]:
    """Асинхронно запускает цепочку Агента 4."""
    print(f"\n[AGENT_04] Асинхронный запуск (flash) для анализа файла профиля...")
    
    profile_text = ""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            profile_text = f.read()
    
    if not profile_text:
        print("[AGENT_04] Файл профиля пуст или не найден.")
        return []

    try:
        return await agent_04_chain.ainvoke({"profile_text": profile_text})
    except Exception as e:
        print(f"[AGENT_04] Ошибка в цепочке: {e}")
        return []

# --- HTML Renderer for WebApp ---

# --- URL Generator for Static WebApp (GitHub Pages) ---
import urllib.parse
import base64

def generate_webapp_url(base_url: str, questions: List[Dict]) -> str:
    """
    Генерирует ссылку, добавляя вопросы в хеш URL (base64).
    Это позволяет использовать статическую страницу на GitHub Pages.
    """
    # Минифицируем JSON для экономии места
    json_data = json.dumps(questions, ensure_ascii=False, separators=(',', ':'))
    # Кодируем в Base64 (URL-safe)
    b64_data = base64.urlsafe_b64encode(json_data.encode('utf-8')).decode('utf-8')
    full_url = f"{base_url}#d={b64_data}"
    
    print(f"[URL GEN] Сгенерирована ссылка длиной {len(full_url)} символов.")
    return full_url
