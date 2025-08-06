# main.py
import pyautogui
import time
import logging
import os
from config import settings
from vision import are_images_different, get_chat_text
from automation import open_wechat_and_focus, switch_to_unread_chat, send_message_robust, hide_wechat
from ai_service import ai_client
import pyperclip


# using logging to record status
def setup_logging():
    # log_dir = 'logs'
    # if not os.path.exists(log_dir):
    #     os.makedirs(log_dir)

    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    # file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
    # file_handler.setFormatter(log_formatter)
    # logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)


# function to handle a single chat window. getting the text, asking AI and sending message
def process_current_chat(last_processed_text_ref):
    logging.info("Processing message...")
    try:
        current_text = get_chat_text()
        if not current_text or current_text == last_processed_text_ref['text']:
            logging.info("No new content。")
            return

        new_content = current_text.replace(last_processed_text_ref['text'], '').strip()
        logging.info(f"Extracted new content: '{new_content}'")

        if new_content:
            ai_reply = ai_client.get_reply(new_content)
            if send_message_robust(ai_reply):
                time.sleep(settings.get('timing.long_delay'))
                last_processed_text_ref['text'] = get_chat_text()
            else:
                logging.warning("memory not updated")
        else:
            last_processed_text_ref['text'] = current_text

    except Exception as e:
        logging.error(f"error: {e}", exc_info=True)


def main():
    setup_logging()
    logging.info("WeChat AI auto reply start")
    menu_bar_region = settings.get('screen_regions.menu_bar_icon')
    logging.info(f"Monitoring menu bar: {menu_bar_region}")

    last_icon_screenshot = pyautogui.screenshot(region=menu_bar_region)
    last_processed_text_ref = {'text': ""}

    while True:
        try:
            current_icon_screenshot = pyautogui.screenshot(region=menu_bar_region)
            if are_images_different(last_icon_screenshot, current_icon_screenshot):
                logging.info("Detected changes in the menu bar button")

                open_wechat_and_focus()

                process_current_chat(last_processed_text_ref)

                while switch_to_unread_chat():
                    process_current_chat(last_processed_text_ref)

                hide_wechat()

                logging.info("...Completed processing message, back to monitoring...")
                last_icon_screenshot = pyautogui.screenshot(region=menu_bar_region)

            time.sleep(settings.get('timing.main_loop_sleep'))

        except KeyboardInterrupt:
            logging.info("Program stopped。")
            break
        except Exception as e:
            logging.critical(f"Error: {e}", exc_info=True)
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
