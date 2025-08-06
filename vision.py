# vision.py
# Contains all the computer vision and OCR logic. Taking screenshot, processing image, extracting text.
import pytesseract
from PIL import Image
import pyautogui
import numpy as np
import re
from config import settings
import logging
import imagehash
import cv2


# image processing using opencv
def preprocess_for_ocr(image: Image.Image) -> Image.Image:

    try:
        logging.info("    └──> OCR...")
        # convert PIL.Image to OpenCV style (numpy array)
        open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # gray
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 5
        )

        kernel = np.ones((2, 2), np.uint8)
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # 5. convert back to PIL.Image for Tesseract
        final_image = Image.fromarray(opened)
        logging.info("    └──> 高级OCR预处理完成。")
        return final_image
    except Exception as e:
        logging.error(f"OCR 图像预处理失败: {e}", exc_info=True)
        return image  # 失败时返回原始图像


# clean raw text from Tesseract, removing system messages and unwanted artifacts
def extract_valid_text(text: str) -> str:
    text = re.sub(r'撤回了一条消息|拍了拍你|You recalled a message. Re-edit|\[.*?\]', '', text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return ' '.join(lines)


# captures screenshot of the chat area
def get_chat_text() -> str:
    try:
        chat_box_region = settings.get('screen_regions.chat_box')
        if not chat_box_region:
            logging.error("配置错误：未找到 'screen_regions.chat_box'。")
            return ""

        screenshot = pyautogui.screenshot(region=chat_box_region)
        screenshot.save("debug_ocr_original.png")

        processed_img = preprocess_for_ocr(screenshot)
        processed_img.save("debug_ocr_processed.png")

        config = settings.get('ocr_settings.tesseract_config')
        lang = settings.get('ocr_settings.language')

        text = pytesseract.image_to_string(processed_img, lang=lang, config=config)
        return extract_valid_text(text)
    except Exception as e:
        logging.error(f"获取聊天文本时出错: {e}", exc_info=True)
        return ""


# Use hashing to compare two images of the menu bar icon
def are_images_different(img1: Image.Image, img2: Image.Image) -> bool:

    if img1 is None or img2 is None:
        return True

    try:
        hash1 = imagehash.phash(img1)
        hash2 = imagehash.phash(img2)

        distance = hash1 - hash2

        threshold = settings.get('detection_settings.icon_change_threshold_phash')

        if distance > threshold:
            logging.info(f"检测到图标变化。pHash 距离: {distance} (阈值: {threshold})")
            return True
        else:
            return False

    except Exception as e:
        logging.error(f"使用 pHash 比较图像时出错: {e}", exc_info=True)
        return True
