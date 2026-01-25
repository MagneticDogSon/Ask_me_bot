import os
import re
import json
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

# --- Загрузка и настройки ---
load_dotenv()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

PROFILE_FILE = os.path.join(PROJECT_ROOT, "profile.md")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
RESULTS_FILE = os.path.join(RESULTS_DIR, "results.json")
WEBAPP_HTML_FILE = os.path.join(PROJECT_ROOT, "index.html")
# Ссылка на GitHub Pages для WebApp
GITHUB_PAGES_URL = "https://magneticdogson.github.io/Ask_me_bot/" 
GREETING_QUESTIONS_FILE = os.path.join(PROJECT_ROOT, "data", "greeting_questions.json") 
TELOS_DEFAULT_FILE = os.path.join(PROJECT_ROOT, "data", "telos.md") 
TELOS_QUESTIONS_FILE = os.path.join(PROJECT_ROOT, "data", "telos_questions.json")
USER_PROGRESS_FILE = os.path.join(RESULTS_DIR, "user_progress.json") 

if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

# --- Прокси (Proxy) ---
def setup_proxy():
    """Устанавливает переменные окружения для HTTP и HTTPS прокси."""
    # Пытаемся получить готовый URL прокси из переменных окружения
    proxy_url = os.getenv("HTTP_PROXY")
    
    # Если переменной нет, пробуем собрать из частей (рекомендуется задать их в .env)
    if not proxy_url:
        host = os.getenv("PROXY_HOST", "172.111.196.164") # Fallback (лучше убрать в продакшене)
        port = os.getenv("PROXY_PORT", "8864")
        user = os.getenv("PROXY_USER", "user239363")
        password = os.getenv("PROXY_PASS", "ptxain")
        
        if host and port and user and password:
            proxy_url = f"http://{user}:{password}@{host}:{port}"
    
    if proxy_url:
        os.environ['HTTP_PROXY'] = proxy_url
        os.environ['HTTPS_PROXY'] = proxy_url
        # Маскируем пароль при выводе
        safe_url = proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url
        print(f"[PROXY] Прокси установлен: ...@{safe_url}")
    else:
        print("[PROXY] Переменные для прокси не найдены, работаем напрямую.")

# Активация прокси
setup_proxy()

# --- Инициализация LLM ---
if not GOOGLE_API_KEY:
    raise ValueError("Не найден GOOGLE_API_KEY в .env файле.")

# Модель для сложных, аналитических задач
llm_pro = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview", 
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7
)

# Модель для быстрых, утилитарных задач
llm_flash = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7
)

print("[CONFIG] Модели Gemini инициализированы (gemini-3-flash-preview).")

# --- Схемы данных (Schemas) ---
class Interaction(BaseModel):
    question: str = Field(..., description="Текст вопроса")
    answer: str = Field(..., description="Ответ пользователя")

class FinalResult(BaseModel):
    session_id: str
    original_text: str
    interactions: List[Interaction]
    final_text: str
    timestamp: str

# --- Утилиты (Utils) ---
def load_prompt_text(file_path: str) -> str:
    """Загружает текст промпта из указанного файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[ERROR] Файл промпта не найден: {file_path}")
        return ""

class JsonParser(StrOutputParser):
    """Парсер для извлечения JSON из ответа модели, даже если он обернут в markdown."""
    def parse(self, text: str) -> List[Dict]:
        try:
            json_match = re.search(r"```json\n(.*)\n```", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            return json.loads(text)
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"[ERROR] Ошибка парсинга JSON: {e}")
            return []
