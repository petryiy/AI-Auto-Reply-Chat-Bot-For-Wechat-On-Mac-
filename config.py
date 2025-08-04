# config.py
# Some settings
import json
import os


class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, config_path='config.json'):
        if not hasattr(self, 'loaded'):
            self.config_path = config_path
            self._load_config()
            self._load_system_prompt()
            self.loaded = True

    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print(f"错误：配置文件 '{self.config_path}' 未找到。")
            exit(1)
        except json.JSONDecodeError:
            print(f"错误：配置文件 '{self.config_path}' 格式无效。")
            exit(1)

    def _load_system_prompt(self):
        prompt_file = self.get('ai_settings.system_prompt_file')
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.data['ai_settings']['system_prompt'] = f.read()
        except FileNotFoundError:
            print(f"错误：系统提示文件 '{prompt_file}' 未找到。")
            self.data['ai_settings']['system_prompt'] = "你是一个ai助手"
        except Exception as e:
            print(f"error: {e}")
            exit(1)

    def get(self, key_string, default=None):
        keys = key_string.split('.')
        value = self.data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value


settings = Config()
