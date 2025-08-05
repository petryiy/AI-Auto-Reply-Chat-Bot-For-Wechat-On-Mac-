# automation.py
# Direct interaction with the macos user interface
import pyautogui
import pyperclip
import subprocess
import time
import logging
from config import settings
import os


# clicks the menu bar icon and open wechat
def open_wechat_and_focus():
    logging.info("点击菜单栏图标，准备打开微信...")
    try:
        icon_region = settings.get('screen_regions.menu_bar_icon')
        icon_center = pyautogui.center(icon_region)
        pyautogui.click(icon_center)
        time.sleep(settings.get('timing.short_delay', 1))

        script = 'tell application "System Events" to tell process "WeChat" to set frontmost to true'
        subprocess.run(["osascript", "-e", script], check=True)
    except Exception as e:
        logging.error(f"打开并聚焦微信窗口失败: {e}", exc_info=True)


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


def get_chat_text_via_applescript() -> str | None:
    """【已升级】能更好地处理AppleScript的特定错误返回"""
    script_path = os.path.join(os.path.dirname(__file__), 'get_wechat_messages.applescript')
    try:
        result = subprocess.run(
            ['osascript', script_path], capture_output=True, text=True,
            check=True, encoding='utf-8', timeout=10 # 已有 timeout
        )
        output = result.stdout.strip()
        if output.startswith("Error:") or output.startswith("AppleScript Error:"):
            logging.warning(f"AppleScript 执行返回一个已知的错误: {output}")
            return None
        logging.info("成功通过 AppleScript 获取到聊天文本。")
        return output
    except subprocess.CalledProcessError as e:
        logging.error(f"AppleScript 执行失败 ('{script_path}'), 返回码: {e.returncode}, Stderr: {e.stderr.strip()}")
        return None
    except Exception as e:
        logging.error(f"调用 AppleScript ('{script_path}') 时发生未知错误: {e}", exc_info=True)
        return None


def get_current_chat_id() -> str | None:
    """【已升级】放宽了对ID的过滤，以兼容符号名称"""
    script = 'tell application "System Events" to tell process "WeChat" to return name of window 1'
    try:
        result = subprocess.run(
            ['osascript', '-e', script], capture_output=True, text=True,
            check=True, encoding='utf-8', timeout=5 # 已有 timeout
        )
        chat_id = result.stdout.strip()
        if not chat_id or chat_id == "WeChat":
            logging.warning(f"未能获取到有效的聊天ID，获取到的是: '{chat_id}'")
            return None
        logging.info(f"获取到当前聊天ID: {chat_id}")
        return chat_id
    except Exception as e:
        logging.error(f"获取聊天ID时发生错误: {e}", exc_info=True)
        return None


def press_cmd_g_forcefully():
    """【新增】使用 AppleScript 强制激活微信并发送 Command+G 快捷键。"""
    script = '''
    tell application "System Events" to tell process "WeChat"
        set frontmost to true
        delay 0.2
        keystroke "g" using {command down}
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=5) # 已有 timeout
    except Exception as e:
        logging.error(f"强制发送 Command+G 快捷键失败: {e}", exc_info=True)


def send_message_robust(text: str) -> bool:
    # ... 此函数内容不变 ...
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


def jump_to_next_unread_and_verify() -> bool:
    """【已升级】使用 AppleScript 发送快捷键，并用 AppleScript 读取文本进行验证。"""
    logging.info("尝试跳转到下一个未读对话...")

    text_before_jump = get_chat_text_via_applescript()
    if text_before_jump is None: text_before_jump = ""

    # 使用新的、可靠的快捷键发送方式
    press_cmd_g_forcefully()
    time.sleep(settings.get('timing.long_delay', 1.5))

    text_after_jump = get_chat_text_via_applescript()
    if text_after_jump is None: return False

    if text_after_jump != text_before_jump:
        logging.info("成功跳转到一个新对话！")
        return True
    else:
        logging.info("跳转后内容无变化，判定为已无更多未读对话。")
        return False
