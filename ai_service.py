# ai_service.py
import os
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import logging
from config import settings


class AIService:
    def __init__(self):
        self.model = None
        self._initialize()

    def _initialize(self):
        try:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.get(
                'api_credentials.google_application_credentials')
            vertexai.init(project=settings.get('api_credentials.project_id'),
                          location=settings.get('api_credentials.location'))
            self.model = GenerativeModel(settings.get('ai_settings.model_name'))
            logging.info("AI 服务初始化成功。")
        except Exception as e:
            logging.error(f"AI 服务初始化失败: {e}", exc_info=True)
            exit(1)

    def get_reply(self, history: list, new_content: str) -> str:
        if not self.model:
            return "抱歉，AI服务当前不可用。"
        try:
            # 基于历史记录开始一个新的（临时的）聊天会话
            system_prompt = settings.get('ai_settings.system_prompt')
            chat_session = self.model.start_chat(history=list(history))

            # 发送包含系统提示和新消息的完整Prompt
            full_prompt = f"{system_prompt}\n\n---\n\n{new_content}"

            logging.info(f"向AI发送新内容: '{new_content}'")
            response = chat_session.send_message(Part.from_text(full_prompt))
            ai_reply = response.text.strip()
            logging.info(f"收到AI回复: '{ai_reply[:30]}...'")
            return ai_reply
        except Exception as e:
            logging.error(f"获取AI回复时出错: {e}", exc_info=True)
            return "抱歉，我在思考时遇到了点问题。"


ai_client = AIService()
