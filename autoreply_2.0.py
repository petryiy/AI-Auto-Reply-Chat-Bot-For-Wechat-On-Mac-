import pytesseract
from PIL import Image, ImageEnhance
import pyautogui
import time
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import os
import re
import pyperclip
import subprocess
import numpy as np

# Settings
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
PROJECT_ID = "teaching-466210"
LOCATION = "us-central1"

# system prompt, you can change it based on your preference
SYSTEM_PROMPT = """
你是一个我的微信聊天助手，请遵守以下规则：

"""


# screenshot area. Need to change based on different screen location
CHAT_BOX = (428, 567, 881, 60)
INPUT_BOX = (774, 744)

# Menu bar WeChat icon location
MENU_BAR_ICON_REGION = (1034, 0, 38, 24)  # top left point location. (distance to the left), (distance to the top), (width), (height)

CHANGE_THRESHOLD = 1500

# initialise vertex AI
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel("gemini-2.0-flash-001")
    chat = model.start_chat()
    print("AI 助手初始化完成！")
    chat.send_message(SYSTEM_PROMPT)
except Exception as e:
    print(f"初始化失败: {e}")
    exit(1)

last_proceed_text = ""


# OCR
def preprocess_image(image: Image.Image) -> Image.Image:
    gray = image.convert('L')
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(2.0)
    bw = enhanced.point(lambda x: 0 if x < 180 else 255)
    return bw


# exclude useless text
def extract_valid_text(text: str) -> str:
    text = re.sub(r'撤回了一条消息|拍了拍你|You recalled a message. Re-edit|\[.*?\]', '', text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return ' '.join(lines)


# get chat text using screenshot
def get_chat_text() -> str:
    # screenshot
    screenshot = pyautogui.screenshot(region=CHAT_BOX)
    img = preprocess_image(screenshot)
    # save image for debug
    img.save("debug_ocr.png")
    config = '--psm 6 --oem 3'
    text = pytesseract.image_to_string(img, lang='chi_sim+eng', config=config)
    return extract_valid_text(text)


# determine whether need to reply
def should_reply(text: str) -> bool:
    return bool(text and text.strip())


# click input box and send message
def send_message_robust(text: str) -> bool:
    try:
        # copy paste and send to chat
        pyperclip.copy(text)
        pyautogui.click(INPUT_BOX)
        pyautogui.hotkey('command', 'a')
        pyautogui.hotkey('command', 'v')
        pyautogui.press('enter')
        print(f"已发送: {text[:30]}...")
        return True
    except Exception as e:
        print(f"发送消息失败: {e}")
        return False


# compare if the icon has changed
def are_images_different(img1: Image.Image, img2: Image.Image) -> bool:
    if img1 is None or img2 is None: return True
    arr1 = np.array(img1.convert('L'))
    arr2 = np.array(img2.convert('L'))
    diff = np.sum(np.abs(arr1 - arr2))
    return diff > CHANGE_THRESHOLD


# click the wechat button and open it
def open_wechat_and_focus():
    print("  └──> 点击菜单栏图标，准备打开微信...")
    icon_center = pyautogui.center(MENU_BAR_ICON_REGION)
    pyautogui.click(icon_center)
    time.sleep(1)
    script = '''
    tell application "System Events"
        tell process "WeChat"
            set frontmost to true
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script], check=True)


# hide wechat window with shortcut
def hide_wechat():
    print("  └──> 回复完毕，隐藏微信窗口...")

    try:
        script = '''
                tell application "System Events"
                    tell process "WeChat"
                        set frontmost to true
                    end tell
                end tell
                '''
        subprocess.run(["osascript", "-e", script], check=True)
        time.sleep(0.5)
        pyautogui.hotkey('command', 'h')
        print("  └──> 已发送 Command+H 快捷键。")
    except Exception as e:
        print(f"  └──> 隐藏微信失败: {e}")


# use mac shortcut to switch to the unread chat window
def switch_to_unread_chat() -> bool:
    print("  └──> 正在寻找下一个未读消息...")
    try:
        text_before_jump = get_chat_text()
    except Exception as e:
        print(f"  └──> 跳转前获取文本失败: {e}")
        text_before_jump = ""  # 出错则视为空

    pyautogui.hotkey('command', 'g')
    time.sleep(1)  # 等待窗口切换

    try:
        text_after_jump = get_chat_text()
    except Exception as e:
        print(f"  └──> 跳转后获取文本失败: {e}")
        return False

    if text_after_jump != text_before_jump:
        print("  └──> 成功跳转到一个新对话！")
        return True
    else:
        print("  └──> 跳转后内容无变化，判定为已无更多未读对话。")
        return False


# process current chat, send message to AI and wait for the response
def process_current_chat():
    print("  └──> 进入消息处理模式...")
    global last_proceed_text
    try:
        current_text = get_chat_text()
        if not current_text:
            print("  └──> 未能读取到任何文本。")
            last_proceed_text = ""
            return

        if current_text != last_proceed_text:
            new_content = current_text.replace(last_proceed_text, '').strip()
            print(f"    └──> 读取到内容: '{new_content}'")
            if should_reply(new_content):
                print("    └──> 正在向 AI 发送请求...")
                response = chat.send_message(Part.from_text(new_content))
                ai_reply = response.text.strip()
                print(f"    └──> AI 回复: {ai_reply}")

                if send_message_robust(ai_reply):
                    time.sleep(1.5)
                    last_proceed_text = get_chat_text()
                else:
                    print("    └──> 发送失败，记忆未更新。")
            else:
                print("    └──> 无需回复。")
                last_proceed_text = current_text
    except Exception as e:
        print(f"消息处理模块错误: {e}")


# check screen shot
# def is_screenshot_process_running() -> bool:
#     try:
#         cmd = "ps aux | grep screencapture | grep -v grep"
#         result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
#         if result.stdout.strip():
#             return True
#         return False
#     except Exception:
#         return False


# main function
def main():
    global last_proceed_text
    print("微信 AI 自动回复脚本已启动，按 Ctrl+C 退出")
    print(f"[*] 正在监视菜单栏区域: {MENU_BAR_ICON_REGION}")
    print("=" * 30)

    last_icon_screenshot = pyautogui.screenshot(region=MENU_BAR_ICON_REGION)
    idle_counter = 0

    while True:
        try:
            # check screen shot
            # if is_screenshot_process_running():
            #     if idle_counter % 5 == 0:
            #         print(f"[{time.strftime('%H:%M:%S')}] 检测到正在截图，暂停图标监控...")
            #     idle_counter += 1
            #     time.sleep(2)
            #     continue

            current_icon_screenshot = pyautogui.screenshot(region=MENU_BAR_ICON_REGION)
            if are_images_different(last_icon_screenshot, current_icon_screenshot):
                print("-" * 20)
                print(f"[{time.strftime('%H:%M:%S')}] 侦测到菜单栏图标变化")

                open_wechat_and_focus()

                initial_text = get_chat_text()
                if initial_text != last_proceed_text:
                    print("    └──> 当前窗口有新内容")
                    process_current_chat()
                    time.sleep(1.5)
                else:
                    print("    └──> 当前窗口是旧对话")

                while switch_to_unread_chat():
                    process_current_chat()
                    time.sleep(1)

                hide_wechat()

                print("[*] ...未读消息处理完毕，已返回侦察模式...")
                last_icon_screenshot = pyautogui.screenshot(region=MENU_BAR_ICON_REGION)
            else:
                idle_counter += 1
                if idle_counter % 40 == 0:
                    print(f"[{time.strftime('%H:%M:%S')}] 一切正常，继续侦察...")

            time.sleep(3)

        except KeyboardInterrupt:
            print("\n脚本已手动停止。")
            break
        except Exception as e:
            print(f"主循环错误: {e}")
            time.sleep(5)


# Added some checks
if __name__ == '__main__':

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
