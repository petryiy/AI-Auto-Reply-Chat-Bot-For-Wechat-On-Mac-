# WeChat AI Assistant for macOS

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)](https://www.apple.com/macos)

An intelligent, autonomous chat assistant for the WeChat desktop client on macOS. This bot runs unobtrusively in the background, automatically detecting, reading, and responding to new messages using Google's Gemini AI.

## ✨ Key Features

- **Sentry Mode:** Operates silently in the background by monitoring the macOS menu bar icon for new message notifications, allowing you to use your computer without interruption.
- **Smart Navigation:** Automatically opens WeChat upon detecting a new message and uses native keyboard shortcuts (`Command+G`) to cycle through all unread conversations.
- **AI-Powered Conversation:** Integrates with Google's Gemini Pro API via Vertex AI to provide context-aware, stateful, and human-like conversational replies.
- **Customizable Persona:** The bot's personality, name, background story, and response rules can be extensively customized by editing the `SYSTEM_PROMPT`.
- **Persistent Memory:** The AI maintains a continuous conversation context, preventing it from replying to its own messages or re-replying to old ones.
- **Multi-Language Support:** The bot can understand and reply in both Chinese and English based on the language of the incoming message.

## ⚙️ How It Works

The bot operates on a sophisticated state-based loop:

1.  **Monitor:** It continuously takes small screenshots of the WeChat icon in the macOS menu bar and uses NumPy for image comparison to detect changes (i.e., a new message badge).
2.  **Activate:** Upon detecting a change, it simulates a click on the icon to bring the WeChat window to the foreground.
3.  **Navigate:** It systematically presses `Command+G` to jump to each unread conversation. It verifies a successful jump by comparing screen text before and after the keystroke.
4.  **Process:** For each new conversation, it uses Tesseract OCR to read the text from the chat window.
5.  **Respond:** The new text is sent to the Gemini AI model, which generates a response based on its persistent memory and defined persona.
6.  **Send:** The AI's response is sent by simulating keyboard actions (copy, paste, enter).
7.  **Hide:** After cycling through all unread messages, it hides the WeChat window and returns to monitoring mode.

## ⚠️ Prerequisites

Before you begin, ensure you have the following installed and configured:

1.  **macOS**: This script is designed specifically for macOS.
2.  **Python 3.9+**: [Download Python](https://www.python.org/)
3.  **Homebrew**: The missing package manager for macOS. Install it from [brew.sh](https://brew.sh/).
4.  **Tesseract OCR Engine**: This is the core text recognition engine. Install it and the required language packs via Homebrew:
    ```bash
    brew install tesseract
    brew install tesseract-lang
    ```
5.  **Google Cloud Platform Project**:
    -   A GCP account with a project created.
    -   The **Vertex AI API** must be enabled for your project.
    -   You must have a **Service Account Key** (`.json` file) downloaded for authentication.

## 🛠️ Installation & Configuration

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/petryiy/AI-Auto-Reply-Chat-Bot-For-Wechat-On-Mac-.git](https://github.com/petryiy/AI-Auto-Reply-Chat-Bot-For-Wechat-On-Mac-.git)
    cd AI-Auto-Reply-Chat-Bot-For-Wechat-On-Mac-
    ```

2.  **Install Python Dependencies**
    It's highly recommended to use a virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure Critical Files (Required)**
    -   **Service Account Key**: Place your downloaded Google Cloud key file in the project's root directory and rename it to `service_account.json`. This file is listed in `.gitignore` and will not be uploaded to GitHub.
    -   **Screen Coordinates**: Open the main Python script and **you must update the following coordinate variables** to match your screen resolution and window layout.
        -   `CHAT_BOX`: The region where chat messages appear.
        -   `INPUT_BOX`: The location of the text input field.
        -   `MENU_BAR_ICON_REGION`: The small area around the WeChat icon in the top menu bar.
        *Tip: On macOS, press `Cmd+Shift+4`. Your cursor will turn into a crosshair that displays screen coordinates.*

4.  **Grant System Permissions (Required)**
    This script requires extensive permissions to function. Go to **System Settings > Privacy & Security**:
    -   **Accessibility**: Add and enable your terminal application (e.g., `Terminal`, `iTerm`) or your code editor.
    -   **Screen Recording**: Add and enable your terminal/editor.
    -   **Automation**: Add and enable your terminal/editor, ensuring it has permission to control "WeChat".

## 🚀 Usage

Once all configurations are complete, run the script from your terminal:

```bash
python3 your_script_name.py
```

Press `Ctrl+C` in the terminal to stop the bot at any time.

## 📜 Disclaimer

This project is for educational and personal use only. Automating user accounts on third-party applications may be against their terms of service. The user of this script assumes all responsibility and risk.