import asyncio
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from Bot_tg.config import GITHUB_PAGES_URL
from Bot_tg.agents_shadow import agent_08_questions
from Bot_tg.utils import generate_webapp_url # Исправлено
from Bot_tg.state_manager import user_states, register_user_activity
from Bot_tg.flow import COMPLETION_HANDLERS
from Bot_tg.flow_shadow import on_shadow_completion

# Регистрация нового обработчика завершения без изменения flow.py
COMPLETION_HANDLERS["shadow"] = on_shadow_completion

def register_shadow_handlers(bot):

    @bot.message_handler(commands=['shadow', 'тень'])
    async def shadow_command(message):
        chat_id = message.chat.id
        await bot.send_message(chat_id, "🏮 Погружаемся в тишину... Давай заглянем за завесу твоего привычного 'Я'.")
        
        try:
            # Предупреждение о глубине
            await bot.send_message(chat_id, "Эта практика может быть неуютной. Отвечай только если чувствуешь готовность встретиться с правдой.")
            await asyncio.sleep(2)
            
            questions_data = await agent_08_questions()
            
            if not questions_data or len(questions_data) < 1:
                await bot.send_message(chat_id, "Туман сегодня слишком густой. Попробуй позже.")
                return

            # Генерируем URL
            url = generate_webapp_url(GITHUB_PAGES_URL, questions_data)
            
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(KeyboardButton("🕯️ ВОЙТИ В ТЕНЬ", web_app=WebAppInfo(url=url)))
            
            await bot.send_message(chat_id, "Я подготовил 3 вопроса-зеркала. Когда будешь готов, нажми кнопку.", reply_markup=markup)
            
            user_states[chat_id] = {
                "mode": "shadow", 
                "questions": questions_data, 
                "step": 0, 
                "interactions": [],
                "last_activity": datetime.now()
            }
        except Exception as e:
            print(f"[SHADOW] Ошибка: {e}")
            await bot.send_message(chat_id, "Дзен прервался... Попробуйте позже.")
