import unittest
import asyncio
from unittest.mock import patch, mock_open
import sys
import os

# --- Настройка путей для импорта тестируемых модулей ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Импорт агентов для тестирования из нового расположения ---
from Bot_tg.agents import (
    generate_onboarding_questions,
    agent_01,
    agent_02,
    agent_03,
    agent_04
)
from Bot_tg.config import Interaction

# --- Утилита для создания моков асинхронных вызовов ---
def async_mock_return_value(value):
    future = asyncio.Future()
    future.set_result(value)
    return future

# --- Класс с асинхронными тестами ---
class TestAgents(unittest.IsolatedAsyncioTestCase):

    @patch('Bot_tg.agents.chain_generate_questions')
    @patch('builtins.open', new_callable=mock_open, read_data="") # Мокируем чтение пустого профиля
    async def test_agent_00_generate_questions(self, mock_file, mock_chain):
        mock_response = [{"question_text": "Как тебя зовут?", "type": "open_text"}]
        mock_chain.ainvoke.return_value = async_mock_return_value(mock_response)
        result = await generate_onboarding_questions()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch('Bot_tg.agents.agent_01_chain')
    async def test_agent_01_psychology_questions(self, mock_chain):
        mock_response = [{"question_text": "Что для вас значит успех?", "variants": ["Признание", "Богатство", "Свобода", "Власть"]}]
        mock_chain.ainvoke.return_value = async_mock_return_value(mock_response)
        result = await agent_01("Я хочу стать успешным")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    @patch('Bot_tg.agents.agent_02_chain')
    async def test_agent_02_rewrite_text(self, mock_chain):
        mock_response = "Это финальный, переписанный текст."
        interactions = [Interaction(question="Какой жанр?", answer="Фантастика")]
        mock_chain.ainvoke.return_value = async_mock_return_value(mock_response)
        result = await agent_02("Исходный текст", interactions)
        self.assertEqual(result, mock_response)

    @patch('builtins.open', new_callable=mock_open, read_data='{"sessions": []}')
    @patch('Bot_tg.agents.agent_03_chain')
    async def test_agent_03_update_profile(self, mock_chain, mock_file):
        mock_chain.ainvoke.return_value = async_mock_return_value("Обновленный профиль")
        test_json_data = '[{"session_id": "123"}]'
        await agent_03(test_json_data)
        mock_chain.ainvoke.assert_called_once()
        call_args = mock_chain.ainvoke.call_args[0][0]
        self.assertIn(test_json_data, call_args['json_data'])

    @patch('builtins.open', new_callable=mock_open, read_data="### Профиль\n- Имя: Алекс")
    @patch('Bot_tg.agents.agent_04_chain')
    async def test_agent_04_profile_questions(self, mock_chain, mock_file):
        mock_response = [{"question_text": "Какой ваш любимый фильм?", "variants": ["Боевик", "Комедия", "Драма", "Следующий вопрос"]}]
        mock_chain.ainvoke.return_value = async_mock_return_value(mock_response)
        result = await agent_04()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

if __name__ == '__main__':
    unittest.main()
