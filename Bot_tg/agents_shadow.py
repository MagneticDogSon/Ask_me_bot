import json
import asyncio
import logging
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from Bot_tg.config import (
    llm_pro, llm_flash, 
    PROFILE_FILE, 
    Interaction, 
    JsonParser
)
from Bot_tg.prompts.agent_08 import PROMPT_AGENT_08_SHADOW_WORK, PROMPT_AGENT_08_SHADOW_ANALYSIS
from Bot_tg.utils import read_file_sync, write_file_sync

logger = logging.getLogger(__name__)

# --- Agent 08 Chains ---

agent_08_questions_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_08_SHADOW_WORK)
    | llm_pro
    | JsonParser()
)

agent_08_analysis_chain = (
    ChatPromptTemplate.from_template(PROMPT_AGENT_08_SHADOW_ANALYSIS)
    | llm_pro
    | StrOutputParser()
)

async def agent_08_questions() -> List[Dict[str, list]]:
    """Generates 3-5 Shadow Work questions in Zen style."""
    logger.info("[AGENT_08] Generating Shadow Work questions...")
    profile_text = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    try:
        return await agent_08_questions_chain.ainvoke({"profile_text": profile_text})
    except Exception as e:
        logger.error(f"[AGENT_08] Error generating questions: {e}")
        return []

async def agent_08_analysis(interactions_json: str) -> str:
    """Performs deep Shadow Work analysis."""
    logger.info("[AGENT_08] Performing Shadow analysis...")
    profile_text = await asyncio.to_thread(read_file_sync, PROFILE_FILE)
    try:
        return await agent_08_analysis_chain.ainvoke({
            "interactions_json": interactions_json,
            "profile_text": profile_text
        })
    except Exception as e:
        logger.error(f"[AGENT_08] Error in Shadow analysis: {e}")
        return "Ошибка анализа Тени."
