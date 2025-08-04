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
import chess

# Settings
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
PROJECT_ID = "teaching-466210"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.0-flash-001"

CHAT_BOX = (428, 567, 881, 60)
INPUT_BOX_COORDS = (774, 744)

# AI系统指令
AI_PLAYER_PROMPT = """
你是一个名为“字符棋圣”的世界级国际象棋AI。你的任务是，根据提供给你的FEN棋局状态，决定出你（白方）的最佳一步棋。
你的回复必须非常简洁，只包含你决定要走的这一步棋的标准代数记谱法（SAN）字符串。
例如，如果决定走马到f3，就只回复 `Nf3`。如果决定王翼易位，就只回复 `O-O`。
不要包含任何额外的解释、问候或评论。

当前FEN:
{fen}
"""

USER_INPUT_PARSER_PROMPT = """
你是一个国际象棋术语解析器。你的任务是将用户用自然语言描述的象棋走法，转换成标准代数记谱法（SAN）。
用户的输入是：'{user_input}'
请只返回SAN格式的走法。例如，如果用户说“我的兵到e5”，你就返回 `e5`。如果用户说“马g8到f6”，你就返回 `Nf6`。
不要返回任何其他多余的文字。如果无法解析，就返回 '无效走法'。
"""


def initialize_ai(project_id, location, model_name):
    try:
        vertexai.init(project=project_id, location=location)
        model = GenerativeModel(model_name)
        print("✅ AI 助手初始化完成！")
        return model
    except Exception as e:
        print(f"❌ AI 初始化失败: {e}")
        return None


def capture_and_ocr(region: tuple) -> str:
    try:
        screenshot = pyautogui.screenshot(region=region)
        gray = screenshot.convert('L')
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(2.0)
        bw = enhanced.point(lambda x: 0 if x < 180 else 255)
        config = '--psm 6 --oem 3'
        text = pytesseract.image_to_string(bw, lang='chi_sim+eng', config=config)
        text = re.sub(r'撤回了一条消息|拍了拍你|You recalled a message. Re-edit|\[.*?\]', '', text)
        return text.strip()
    except Exception as e:
        print(f"❌ 截屏或OCR失败: {e}")
        return ""


def send_wechat_message(text: str, input_coords: tuple) -> bool:
    try:
        script = 'tell application "System Events" to tell process "WeChat" to set frontmost to true'
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
        time.sleep(0.5)
        pyperclip.copy(text)
        pyautogui.click(input_coords)
        time.sleep(0.1)
        pyautogui.hotkey('command', 'a')
        pyautogui.hotkey('command', 'v')
        pyautogui.press('enter')
        print(f"🚀 已发送消息: {text[:40].replace(chr(10), ' ')}...")
        return True
    except Exception as e:
        print(f"❌ 发送消息失败: {e}")
        return False


def generate_text_board(board: chess.Board) -> str:
    unicode_pieces = {
        'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
        'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔'
    }
    board_str = ""
    for i in range(7, -1, -1):
        board_str += f"{i + 1} "
        for j in range(8):
            piece = board.piece_at(chess.square(j, i))
            board_str += unicode_pieces.get(piece.symbol(), ". ") if piece else ". "
        board_str += "\n"
    board_str += "  ａ ｂ ｃ ｄ ｅ ｆ ｇ ｈ"
    return board_str


# --- 3. 主程序 (v5 Final) ---

def main():
    """主程序循环 (v5.0 Final - 指令启动、逻辑加固)"""
    print("🟢 微信国际象棋陪练启动 (v5.0 最终版)...")
    model = initialize_ai(PROJECT_ID, LOCATION, MODEL_NAME)
    if not model: return

    # --- 等待启动指令 ---
    time.sleep(5)
    print("五秒进入聊天框")
    last_ocr_text = ""

    # -- 初始化棋局 --
    board = chess.Board()
    try:
        # 发送初始棋盘，并邀请用户先走
        initial_board_text = generate_text_board(board)
        reply_to_user = f"好的，棋局开始！\n\n{initial_board_text}\n\n您执黑棋，请走第一步。"

        if not send_wechat_message(reply_to_user, INPUT_BOX_COORDS): return

        time.sleep(2)
        last_ocr_text = capture_and_ocr(CHAT_BOX_REGION)

    except Exception as e:
        print(f"💥 开局失败: {e}");
        return

    print("\n✅ 开局完成，进入主监听循环。按 Ctrl+C 退出。")

    # -- 主监听循环 --
    while True:
        try:
            current_ocr_text = capture_and_ocr(CHAT_BOX_REGION)
            if not current_ocr_text or current_ocr_text == last_ocr_text:
                time.sleep(3);
                continue

            # 为了防止误读自己发出去的 multi-line message, 我们只取最新的一段文本
            new_content = current_ocr_text
            if last_ocr_text and current_ocr_text.startswith(last_ocr_text):
                new_content = current_ocr_text[len(last_ocr_text):].strip()

            if not new_content:
                last_ocr_text = current_ocr_text
                continue

            print(f"💬 检测到用户输入: '{new_content}'")

            # --- 核心交互逻辑 ---
            print("🤖 正在解析用户的走法...")
            response = model.generate_content(USER_INPUT_PARSER_PROMPT.format(user_input=new_content))
            user_move_san = response.text.strip()

            try:
                board.push_san(user_move_san)
                print(f"✅ 用户走法 '{user_move_san}' 合法，已更新棋盘。")
            except (chess.IllegalMoveError, chess.InvalidMoveError):
                print(f"❌ 用户走法 '{user_move_san}' 不合法！")
                reply_to_user = f"你走的 '{user_move_san}' 好像不符合规则哦，请换一步棋试试。"
                send_wechat_message(reply_to_user, INPUT_BOX_COORDS)
                last_ocr_text = capture_and_ocr(CHAT_BOX_REGION)  # 更新last_text防止死循环
                continue

            if board.is_game_over():
                result_text = f"游戏结束！结果是：{board.result()}"
                print(f"🎉 {result_text}");
                send_wechat_message(result_text, INPUT_BOX_COORDS);
                break

            print("🧠 AI正在思考下一步...")
            response = model.generate_content(AI_PLAYER_PROMPT.format(fen=board.fen()))
            # 【修复】只取AI回复的第一个词作为走法，防止它一次走多步
            ai_move_san = response.text.strip().split()[0]

            try:
                board.push_san(ai_move_san)
                print(f"✅ AI走法 '{ai_move_san}' 合法，已更新棋盘。")
            except (chess.IllegalMoveError, chess.InvalidMoveError):
                print(f"❌ AI走出了不合法的棋 '{ai_move_san}'！这是AI的错误。")
                reply_to_user = "哎呀，我好像算错了，让我再想想..."
                send_wechat_message(reply_to_user, INPUT_BOX_COORDS)
                last_ocr_text = capture_and_ocr(CHAT_BOX_REGION)
                board.pop()  # 撤销用户刚才那步棋，让AI重新思考
                continue

            new_board_text = generate_text_board(board)
            reply_to_user = f"你走了 {user_move_san}，我想了想，决定走 {ai_move_san}。\n\n{new_board_text}"
            send_wechat_message(reply_to_user, INPUT_BOX_COORDS)

            if board.is_game_over():
                result_text = f"游戏结束！结果是：{board.result()}"
                print(f"🎉 {result_text}");
                send_wechat_message(result_text, INPUT_BOX_COORDS);
                break

            time.sleep(2)
            last_ocr_text = capture_and_ocr(CHAT_BOX_REGION)  # 发送后立即更新，防止自我响应

        except KeyboardInterrupt:
            print("\n🛑 脚本已手动停止。再见！");
            break
        except Exception as e:
            print(f"💥 主循环发生严重错误: {e}\n将在5秒后重试...");
            time.sleep(5)


if __name__ == '__main__':
    try:
        pyautogui.size()
        print("✅ GUI自动化权限正常。")
    except Exception as e:
        print(f"❌ 权限检查失败: {e}，请检查屏幕录制等权限！");
        exit(1)

    main()


# SYSTEM_PROMPT = """
# # 角色与核心任务
# 你是一个名为“字符棋圣”的AI国际象棋引擎和陪练。你的任务是在一个纯文本聊天环境中，与用户进行一场完整的国际象棋对局。你执白棋，用户执黑棋。
#
# # 状态管理：FEN（至关重要）
# 你必须使用FEN (Forsyth-Edwards Notation) 来跟踪和管理整个棋局的状态。在你的每一条回复的末尾，你都必须附上当前局面最新的FEN字符串，并用`<FEN>`标签包裹。格式如下：`<FEN>rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2</FEN>`。我的程序会自动提取这个FEN，并在下一回合发回给你。
#
# # 棋盘表示
# 你必须使用Unicode字符来生成一个8x8的文本棋盘，并包含行列标签。
# - 黑方棋子: ♚ ♛ ♜ ♝ ♞ ♟
# - 白方棋子: ♔ ♕ ♖ ♗ ♘ ♙
# - 空格用 `.` 或空格表示。
#
# 棋盘格式示例：
# ８ ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜
# ７ ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟
# ６ . . . . . . . .
# ５ . . . . . . . .
# ４ . . . ♔ . . . .
# ３ . . . . . . . .
# ２ ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙
# １ ♖ ♘ ♗ ♕ . ♗ ♘ ♖
#    ａ ｂ ｃ ｄ ｅ ｆ ｇ ｈ
#
# # 对弈流程
# 1.  **启动**：如果这是第一回合（没有提供FEN），请使用初始FEN `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1`，生成并发送初始棋盘。
# 2.  **接收输入**：你会收到用户的自然语言走法（例如“我要走马f6”）和上一回合的`<FEN>`存档码。
# 3.  **解析与更新（用户）**：从FEN加载局面，解析用户的走法。如果用户的走法不合法或不清晰，请礼貌地要求用户重新输入。在合法的情况下，更新棋盘状态。
# 4.  **决策与更新（AI）**：现在轮到你了。根据当前局面，决定并走出你（白方）的最佳一步棋。再次更新棋盘状态。
# 5.  **生成回复**：你的回复必须包含以下三部分：
#     a. 一句简短友好的评论（例如“不错的防守！我的回应是：”或“你现在面临一些压力了。”）。
#     b. 根据最终局面生成的全新字符棋盘。
#     c. 在回复的末尾，附上包含了最终局面的、新的`<FEN>`存档码。
#     d. 你的第一句话先是打招呼并且把这个初始棋盘发过去。
#
# 请严格遵守以上规则，开始我们的对局吧！
# """
#
# # Need to change based on different screen location
# CHAT_BOX = (428, 567, 881, 60)
# INPUT_BOX = (774, 744)
#
# # 初始化 Vertex AI
# try:
#     vertexai.init(project=PROJECT_ID, location=LOCATION)
#     model = GenerativeModel("gemini-2.0-flash-001")
#     chat = model.start_chat()
#     print("✅ AI 助手初始化完成！")
#     chat.send_message(SYSTEM_PROMPT)
# except Exception as e:
#     print(f"❌ 初始化失败: {e}")
#     exit(1)
#
#
# # OCR
# def preprocess_image(image: Image.Image) -> Image.Image:
#     gray = image.convert('L')
#     enhancer = ImageEnhance.Contrast(gray)
#     enhanced = enhancer.enhance(2.0)
#     bw = enhanced.point(lambda x: 0 if x < 180 else 255)
#     return bw
#
#
# # exclude useless text
# def extract_valid_text(text: str) -> str:
#     text = re.sub(r'撤回了一条消息|拍了拍你|You recalled a message. Re-edit|\[.*?\]', '', text)
#     lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
#     return ' '.join(lines)
#
#
# # get chat text using screenshot
# def get_chat_text() -> str:
#     screenshot = pyautogui.screenshot(region=CHAT_BOX)
#     img = preprocess_image(screenshot)
#     config = '--psm 6 --oem 3'
#     text = pytesseract.image_to_string(img, lang='chi_sim+eng', config=config)
#     return extract_valid_text(text)
#
#
# # 判断是否需要回复
# def should_reply(text: str) -> bool:
#     return bool(text and text.strip())
#
#
# # click input box and send message
# def send_message_robust(text: str) -> bool:
#     try:
#         # 激活微信窗口
#         script = '''
#         tell application "System Events"
#             tell process "WeChat"
#                 set frontmost to true
#             end tell
#         end tell
#         '''
#         subprocess.run(["osascript", "-e", script], check=True)
#         time.sleep(0.5)
#         pyperclip.copy(text)
#         pyautogui.click(INPUT_BOX)
#         pyautogui.hotkey('command', 'a')
#         pyautogui.hotkey('command', 'v')
#         pyautogui.press('enter')
#         print(f"🚀 已发送: {text[:30]}...")
#         return True
#     except Exception as e:
#         print(f"❌ 发送消息失败: {e}")
#         return False
#
#
# # main loop
# def main():
#     print("🟢 微信 AI 自动回复脚本已启动，按 Ctrl+C 退出")
#     last_processed_text = ""
#     ai_reply = ""
#     idle_counter = 0
#
#     while True:
#         try:
#             current_text = get_chat_text()
#
#             if not current_text or current_text == last_processed_text:
#                 idle_counter += 1
#                 if idle_counter % 10 == 0:
#                     print(f"[{time.strftime('%H:%M:%S')}] 等待新消息...")
#                 time.sleep(3)
#                 continue
#
#             idle_counter = 0
#             print(f"[{time.strftime('%H:%M:%S')}] 检测到聊天内容变化。")
#
#             # extract new message
#             new_content = current_text.replace(last_processed_text, '').strip()
#             # if it's existing reply then ignore
#             if new_content == ai_reply:
#                 print("检测到自己的回复，已忽略。")
#                 last_processed_text = current_text
#                 time.sleep(2)
#                 continue
#
#             print(f"新增内容: {new_content}")
#             if should_reply(new_content):
#                 print("正在向 AI 发送请求...")
#                 response = chat.send_message(Part.from_text(new_content))
#                 ai_reply = response.text.strip()
#                 print(f"AI 回复: {ai_reply}")
#
#                 if send_message_robust(ai_reply):
#                     # wait for the message
#                     time.sleep(2)
#                     last_processed_text = get_chat_text()
#                 else:
#                     print("发送失败，将在下次循环重试。")
#             else:
#                 print("无需回复，更新已处理文本。")
#                 last_processed_text = current_text
#
#             time.sleep(3)
#
#         except KeyboardInterrupt:
#             print("🛑 脚本已手动停止。")
#             break
#         except Exception as e:
#             print(f"💥 主循环错误: {e}")
#             time.sleep(5)
#
#
# if __name__ == '__main__':
#     # check the right
#     try:
#         pyautogui.size()
#         pyperclip.copy('test')
#         assert pyperclip.paste() == 'test'
#         print("✅ 自动化权限正常。")
#     except Exception as e:
#         print(f"❌ 权限检查失败: {e}")
#         exit(1)
#
#     main()
