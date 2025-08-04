# automation.py
# Direct interaction with the macos user interface
import pyautogui
import pyperclip
import subprocess
import time
import logging
from config import settings


# clicks the menu bar icon and open wechat
def open_wechat_and_focus():
    logging.info("点击菜单栏图标，准备打开微信...")
    try:
        icon_region = settings.get('screen_regions.menu_bar_icon')
        icon_center = pyautogui.center(icon_region)
        pyautogui.click(icon_center)
        time.sleep(settings.get('timing.short_delay'))

        script = 'tell application "System Events" to tell process "WeChat" to set frontmost to true'
        subprocess.run(["osascript", "-e", script], check=True)
    except Exception as e:
        logging.error(f"打开并聚焦微信窗口失败: {e}", exc_info=True)


# use shortcut to close wechat window after processing messages
def hide_wechat():
    logging.info("回复完毕，隐藏微信窗口...")
    try:
        script = 'tell application "System Events" to tell process "WeChat" to set frontmost to true'
        subprocess.run(["osascript", "-e", script], check=True)
        time.sleep(0.5)
        pyautogui.hotkey('command', 'h')
        logging.info("已发送 Command+H 快捷键。")
    except Exception as e:
        logging.error(f"隐藏微信失败: {e}", exc_info=True)


# use shortcut to navigate to the next unread message
def switch_to_unread_chat() -> bool:
    from vision import get_chat_text
    logging.info("正在寻找下一个未读消息...")
    try:
        text_before_jump = get_chat_text()
        pyautogui.hotkey('command', 'g')
        time.sleep(settings.get('timing.short_delay'))
        text_after_jump = get_chat_text()

        if text_after_jump != text_before_jump:
            logging.info("成功跳转到一个新对话！")
            return True
        else:
            logging.info("跳转后内容无变化，判定为已无更多未读对话。")
            return False
    except Exception as e:
        logging.error(f"切换未读聊天时出错: {e}", exc_info=True)
        return False


# use copy and paste to send message
def send_message_robust(text: str) -> bool:
    logging.info(f"准备发送消息: {text[:30]}...")
    try:
        input_box_coords = settings.get('screen_regions.input_box')
        pyperclip.copy(text)
        pyautogui.click(input_box_coords)
        pyautogui.hotkey('command', 'a')
        pyautogui.hotkey('command', 'v')
        pyautogui.press('enter')
        logging.info("消息已发送。")
        return True
    except Exception as e:
        logging.error(f"发送消息失败: {e}", exc_info=True)
        return False
