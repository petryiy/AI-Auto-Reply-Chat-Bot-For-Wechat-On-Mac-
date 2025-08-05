# state_manager.py
import json
import logging
from collections import deque
from config import settings


class StateManager:
    def __init__(self, history_file='conversation_history.json'):
        self.history_file = history_file
        self.max_history_len = settings.get('ai_settings.max_history_len', 20)
        self.conversations = self._load_history()

    def _load_history(self):
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {chat_id: deque(history, maxlen=self.max_history_len) for chat_id, history in data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            logging.warning(f"无法加载对话历史文件'{self.history_file}'，将创建新的历史。")
            return {}

    def _save_history(self):
        try:
            serializable_data = {chat_id: list(history) for chat_id, history in self.conversations.items()}
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"保存对话历史失败: {e}", exc_info=True)

    def get_history(self, chat_id: str) -> deque:
        if chat_id not in self.conversations:
            logging.info(f"为 '{chat_id}' 创建新的对话历史。")
            self.conversations[chat_id] = deque(maxlen=self.max_history_len)
        return self.conversations[chat_id]

    def update_history(self, chat_id: str, user_message: str, ai_response: str):
        history = self.get_history(chat_id)
        history.append({'role': 'user', 'parts': [{'text': user_message}]})
        history.append({'role': 'model', 'parts': [{'text': ai_response}]})
        self._save_history()
        logging.info(f"已更新并保存 '{chat_id}' 的对话历史。")


# 创建一个全局的状态管理器实例
state = StateManager()
