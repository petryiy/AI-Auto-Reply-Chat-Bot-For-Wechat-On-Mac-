# main.py
import pyautogui
import pyperclip
import time
import logging
import os
import re
from config import settings
from vision import are_images_different
from automation import (
    open_wechat_and_focus,
    send_message_robust,
    hide_wechat,
    get_chat_text_via_applescript,
    get_current_chat_id,
    jump_to_next_unread_and_verify
)
from ai_service import ai_client
from state_manager import state


# using logging to record status
def setup_logging():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)


def parse_and_get_last_opponent_message(full_text: str) -> str:
    # ... (此函数内容不变) ...
    if not full_text:
        return ""
    opponent_messages = []
    lines = full_text.strip().split('\n')
    for line in lines:
        if not line.startswith("MeSaid:"):
            cleaned_line = re.sub(r'^.*?Said:', '', line).strip()
            if cleaned_line:
                opponent_messages.append(cleaned_line)
    if opponent_messages:
        last_message = opponent_messages[-1]
        logging.info(f"    └──> 解析出的对方最后一条消息: '{last_message[:50]}...'")
        return last_message
    else:
        logging.info("    └──> 未解析出任何有效的对方消息。")
        return ""


def process_current_chat():
    """【已升级】处理当前窗口，完全依赖AppleScript"""
    logging.info("  └──> 开始处理当前对话...")
    chat_id = get_current_chat_id()
    if not chat_id:
        logging.warning("无法获取当前chat_id，跳过处理。")
        return

    # 【已统一】只使用 AppleScript 获取文本
    full_text_block = get_chat_text_via_applescript()
    if not full_text_block:
        logging.warning(f"在 '{chat_id}' 中未能获取到文本。")
        return

    last_opponent_message = parse_and_get_last_opponent_message(full_text_block)

    history = state.get_history(chat_id)

    # 检查这条消息是否已经在历史中
    if history and any(msg['role'] == 'user' and msg['parts'][0]['text'] == last_opponent_message for msg in history):
        logging.info(f"'{chat_id}' 中的最新消息已在历史中，判定为无新内容。")
        return

    if last_opponent_message:
        logging.info(f"在 '{chat_id}' 中发现新内容: '{last_opponent_message[:50]}...'")
        ai_reply = ai_client.get_reply(history, last_opponent_message)
        if send_message_robust(ai_reply):
            state.update_history(chat_id, last_opponent_message, ai_reply)
    else:
        logging.info(f"'{chat_id}' 中无新内容需要回复。")


def main():
    setup_logging()
    logging.info("微信 AI 自动回复脚本已启动 (终极修正版)。")
    menu_bar_region = settings.get('screen_regions.menu_bar_icon')
    logging.info(f"正在监视菜单栏区域: {menu_bar_region}")

    last_icon_screenshot = pyautogui.screenshot(region=menu_bar_region)

    while True:
        try:
            current_icon_screenshot = pyautogui.screenshot(region=menu_bar_region)
            if are_images_different(last_icon_screenshot, current_icon_screenshot):
                logging.info("侦测到菜单栏图标变化！")

                open_wechat_and_focus()

                # 1. 先处理一次当前窗口
                process_current_chat()

                # 2. 使用新的、可靠的导航函数来循环处理其他未读消息
                while jump_to_next_unread_and_verify():
                    process_current_chat()

                hide_wechat()

                logging.info("...所有消息处理完毕，已返回侦察模式...")
                last_icon_screenshot = pyautogui.screenshot(region=menu_bar_region)

            time.sleep(settings.get('timing.main_loop_sleep', 3))

        except KeyboardInterrupt:
            logging.info("脚本已手动停止。")
            break
        except Exception as e:
            logging.critical(f"主循环发生致命错误: {e}", exc_info=True)
            time.sleep(5)


if __name__ == '__main__':
    print("--- 脚本入口 __main__ 已成功执行 ---")
    try:
        __import__('numpy')
        pyautogui.size()
        pyperclip.copy('test')
        assert pyperclip.paste() == 'test'
        print("自动化权限及依赖正常。")
    except ImportError:
        print("缺少必要的库: numpy。请运行 'pip install numpy' 来安装它。")
        exit(1)
    except Exception as e:
        print(f"权限检查失败: {e}")
        exit(1)
    main()
