import json
import asyncio
import logging
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from Bot_tg.config import (
    llm_pro, llm_flash, 
    PROFILE_FILE, WEBAPP_HTML_FILE,
    Interaction, 
    JsonParser
)
from Bot_tg.prompts import (
    PROMPT_AGENT_01_PSYCHOLOGY_INSTRUCTION,
    PROMPT_AGENT_02_INSTRUCTION,
    PROMPT_AGENT_03_INSTRUCTION,
    PROMPT_AGENT_04_INSTRUCTION,
    PROMPT_AGENT_05_TASK_DECOMPOSITION,
    PROMPT_AGENT_06_DEEP_ANALYSIS,
    PROMPT_AGENT_07_IKIGAI,
    PROMPT_AGENT_07_IKIGAI_ANALYSIS
)
from .utils import read_file_sync, write_file_sync, generate_webapp_url

# --- Logging Configuration ---
logger = logging.getLogger(__name__)

# --- Agent 00: Onboarding ---



# --- Agent 01: Psychology Analysis ---

agent_01_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_01_PSYCHOLOGY_INSTRUCTION) 
    | llm_pro 
    | JsonParser()
)

async def agent_01(user_text: str) -> List[Dict[str, list]]:
    """Асинхронно запускает цепочку Агента 1."""
    logger.info(f"[AGENT_01] Запуск (pro) для текста: '{user_text[:50]}...'")
    user_profile = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    try:
        return await agent_01_chain.ainvoke({"user_text": user_text, "user_profile": user_profile})
    except Exception as e:
        logger.error(f"[AGENT_01] Ошибка в цепочке: {e}")
        return []

# --- Agent 02: Text Rewriter ---

agent_02_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_02_INSTRUCTION) 
    | llm_flash 
    | StrOutputParser()
)

async def agent_02(original_text: str, interactions: List[Interaction]) -> str:
    """Асинхронно запускает цепочку Агента 2."""
    logger.info("[AGENT_02] Запуск (flash) для переписывания текста...")
    
    user_profile = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    history = "\n".join([f"- На вопрос \"{item.question}\" был дан ответ \"{item.answer}\"." for item in interactions])
    
    try:
        return await agent_02_chain.ainvoke({"original_text": original_text, "history": history, "user_profile": user_profile})
    except Exception as e:
        logger.error(f"[AGENT_02] Ошибка в цепочке: {e}")
        return "Не удалось переписать текст из-за ошибки."

# --- Agent 03: Profile Analyst (Background) ---

agent_03_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_03_INSTRUCTION) 
    | llm_pro 
    | StrOutputParser()
)

async def agent_03(json_data: str) -> bool:
    """Асинхронно запускает цепочку Агента 3. Возвращает True при успешном обновлении."""
    logger.info("[AGENT_03] Асинхронный запуск (pro) для обновления профиля.")
    
    existing_profile = await asyncio.to_thread(read_file_sync, PROFILE_FILE)

    try:
        profile_text = await agent_03_chain.ainvoke({"existing_profile": existing_profile, "json_data": json_data})
        
        await asyncio.to_thread(write_file_sync, PROFILE_FILE, profile_text)
        logger.info(f"[AGENT_03] Файл {PROFILE_FILE} успешно обновлен.")
        return True

    except Exception as e:
        logger.error(f"[AGENT_03] Ошибка в цепочке: {e}")
        return False

# --- Agent 04: Profile Growth ---

agent_04_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_04_INSTRUCTION) 
    | llm_flash 
    | JsonParser()
)

async def agent_04() -> List[Dict[str, list]]:
    """Асинхронно запускает цепочку Агента 4."""
    logger.info("[AGENT_04] Асинхронный запуск (flash) для анализа файла профиля...")
    
    profile_text = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    
    if not profile_text:
        logger.warning("[AGENT_04] Файл профиля пуст или не найден.")
        return []

    try:
        return await agent_04_chain.ainvoke({"profile_text": profile_text})
    except Exception as e:
        logger.error(f"[AGENT_04] Ошибка в цепочке: {e}")
        return []

# --- HTML Renderer for WebApp ---

# --- Agent 05: Task Architect (Goal Decomposition) ---

agent_05_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_05_TASK_DECOMPOSITION) 
    | llm_flash 
    | JsonParser()
)

async def agent_05(final_goal: str) -> List[Dict]:
    """Асинхронно запускает цепочку Агента 5 для декомпозиции цели."""
    logger.info(f"[AGENT_05] Запуск (flash) для декомпозиции цели: '{final_goal[:50]}...'")
    user_profile = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    try:
        return await agent_05_chain.ainvoke({"final_goal": final_goal, "user_profile": user_profile})
    except Exception as e:
        logger.error(f"[AGENT_05] Ошибка в цепочке: {e}")
        return []

# --- Agent 06: Deep Profiler ---

agent_06_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_06_DEEP_ANALYSIS)
    | llm_pro
    | JsonParser()
)

async def agent_06() -> List[Dict[str, list]]:
    """Асинхронно запускает цепочку Агента 6 для глубокого анализа профиля."""
    logger.info("[AGENT_06] Запуск (pro) для глубокого анализа профиля...")
    
    profile_text = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    
    if not profile_text:
        logger.warning("[AGENT_06] Файл профиля пуст или не найден.")
        return []

    try:
        return await agent_06_chain.ainvoke({"profile_text": profile_text})
    except Exception as e:
        logger.error(f"[AGENT_06] Ошибка в цепочке: {e}")
        return []

# --- Agent 07: Ikigai Sensei ---

agent_07_questions_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_07_IKIGAI)
    | llm_pro
    | JsonParser()
)

agent_07_analysis_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_07_IKIGAI_ANALYSIS)
    | llm_pro
    | StrOutputParser()
)

async def agent_07_questions() -> List[Dict[str, list]]:
    """Generates 5 Ikigai questions."""
    logger.info("[AGENT_07] Generating Ikigai questions...")
    profile_text = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    try:
        return await agent_07_questions_chain.ainvoke({"profile_text": profile_text})
    except Exception as e:
        logger.error(f"[AGENT_07] Error generating questions: {e}")
        return []

async def agent_07_analysis(interactions_json: str) -> str:
    """Performs deep Ikigai analysis."""
    logger.info("[AGENT_07] Performing Ikigai analysis...")
    profile_text = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    try:
        return await agent_07_analysis_chain.ainvoke({
            "interactions_json": interactions_json,
            "profile_text": profile_text
        })
    except Exception as e:
        logger.error(f"[AGENT_07] Error interacting Ikigai analysis: {e}")
        return "Ошибка анализа Ikigai."
