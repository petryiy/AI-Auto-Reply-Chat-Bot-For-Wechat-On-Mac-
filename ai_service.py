# ai_service.py
# communicate with the gemini api
import os
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import logging
from config import settings


# a class that manages the entire lifecycle of the connection to the gemini api
class AIService:
    def __init__(self):
        self.chat = None
        self._initialize()

    def _initialize(self):
        try:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.get(
                'api_credentials.google_application_credentials')

            vertexai.init(
                project=settings.get('api_credentials.project_id'),
                location=settings.get('api_credentials.location')
            )
            model = GenerativeModel(settings.get('ai_settings.model_name'))
            self.chat = model.start_chat()

            system_prompt = settings.get('ai_settings.system_prompt')
            self.chat.send_message(system_prompt)
            logging.info("AI 服务初始化并发送系统提示成功。")
        except Exception as e:
            logging.error(f"AI 服务初始化失败: {e}", exc_info=True)
            exit(1)

    def get_reply(self, new_content: str) -> str:
        if not self.chat:
            logging.error("AI聊天会话未初始化。")
            return "抱歉，AI服务当前不可用。"
        try:
            logging.info(f"向AI发送内容: '{new_content}'")
            response = self.chat.send_message(Part.from_text(new_content))
            ai_reply = response.text.strip()
            logging.info(f"收到AI回复: '{ai_reply[:30]}...'")
            return ai_reply
        except Exception as e:
            logging.error(f"获取AI回复时出错: {e}", exc_info=True)
            return "抱歉，我在思考时遇到了点问题。"


ai_client = AIService()
