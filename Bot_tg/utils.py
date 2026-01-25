import os
import json
import base64
from typing import List, Dict
from Bot_tg.config import TELOS_DEFAULT_FILE, PROFILE_FILE, Interaction

def read_file_sync(filepath: str) -> str:
    """Synchronously reads a file and returns its content."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def write_file_sync(filepath: str, content: str):
    """Synchronously writes content to a file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def generate_webapp_url(base_url: str, questions: List[Dict]) -> str:
    """
    Generate a URL by adding questions to the URL hash (base64 encoded).
    This allows using a static page on GitHub Pages.
    """
    # Minify JSON to save space
    json_data = json.dumps(questions, ensure_ascii=False, separators=(',', ':'))
    # Encode to Base64 (URL-safe)
    b64_data = base64.urlsafe_b64encode(json_data.encode('utf-8')).decode('utf-8')
    full_url = f"{base_url}#d={b64_data}"
    
    return full_url

def create_initial_profile(interactions: List[Interaction]) -> str:
    """
    Creates a profile based on answers and the TELOS template (bypassing LLM).
    """
    # Read the template
    template = read_file_sync(TELOS_DEFAULT_FILE)
    if not template:
        print("[UTILS] Template file not found!")
        return "Error: Template not found."

    # Define mapping (partial question text -> Section Header)
    mapping = {
        "Укажи свой возраст": "**1. ИМЯ / ИДЕНТИФИКАЦИЯ**",
        "Какая сфера деятельности": "**4. ПРОФЕССИЯ / РОД ДЕЯТЕЛЬНОСТИ**",
        "Какой стиль общения": "**2. ПРЕДПОЧТИТЕЛЬНЫЙ СТИЛЬ ОБЩЕНИЯ**",
        "Что сейчас для тебя": "**5. ЦЕЛИ И МОТИВАЦИЯ**",
        "Как ты предпочитаешь принимать решения": "**7. КОГНИТИВНЫЙ ПРОФИЛЬ**",
        "Что ты ценишь в людях": "**6. КЛЮЧЕВЫЕ ЦЕННОСТИ**",
        "Как ты обычно проводишь свободное время": "**10. ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ**",
        "В каком формате тебе удобнее": "**7. КОГНИТИВНЫЙ ПРОФИЛЬ**",
        "Как ты относишься к новому": "**3. ЛИЧНОСТНЫЕ ХАРАКТЕРИСТИКИ**",
        "Какую роль ты бы отвел мне": "**10. ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ**"
    }

    # Process interactions
    for interaction in interactions:
        q_text = interaction.question
        a_text = interaction.answer
        
        target_section = None
        for key, section_header in mapping.items():
            if key in q_text:
                target_section = section_header
                break
        
        if target_section:
            label = "Ответ"
            if "возраст" in q_text.lower(): label = "Возраст"
            elif "сфера деятельности" in q_text.lower(): label = "Сфера"
            elif "стиль общения" in q_text.lower(): label = "Стиль общения"
            elif "приоритет" in q_text.lower(): label = "Приоритет"
            elif "принимать решения" in q_text.lower(): label = "Принятие решений"
            elif "ценишь" in q_text.lower(): label = "Ценности"
            elif "свободное время" in q_text.lower(): label = "Хобби/Досуг"
            elif "формате" in q_text.lower(): label = "Формат информации"
            elif "новому" in q_text.lower(): label = "Отношение к новому"
            elif "роль" in q_text.lower(): label = "Роль ассистента"

            formatted_answer = f"\n* **{label}**: {a_text}"
            
            if target_section in template:
                parts = template.split(target_section)
                if len(parts) > 1:
                    # Insert after the header
                    template = parts[0] + target_section + formatted_answer + parts[1]

    # Если файл профиля уже существует, делаем бэкап
    if os.path.exists(PROFILE_FILE):
        import shutil
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = f"{PROFILE_FILE.replace('.md', '')}_{timestamp}_backup.md"
        shutil.copy2(PROFILE_FILE, backup_path)
        print(f"[UTILS] Existing profile backed up to {backup_path}")

    write_file_sync(PROFILE_FILE, template)
    return template
