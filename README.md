# BaleBot

BaleBot is a small bridge that lets you control a Bale account from Telegram.
It lists your Bale chats, opens recent history, sends Telegram text into the selected Bale chat, and forwards new Bale messages back to Telegram while that chat is open.

## Features

- Choose a Bale private chat or group from Telegram inline buttons.
- View recent Bale chat history with sender names.
- Send messages from Telegram to the selected Bale chat.
- Receive new incoming Bale messages while you are typing or chatting.
- Use the `return` button to go back to the chat picker.
- Ignore local secrets and session files before uploading to GitHub.

## Setup

1. Install the Python packages:

```powershell
pip install python-telegram-bot aiobale pydantic
```

2. Open `mytelebot.py` and put your Telegram bot token here:

```python
TOKEN = ""
```

Example for local running only:

```python
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
```

3. Run the bot:

```powershell
python mytelebot.py
```

4. In Telegram, send `/start` to the bot and choose a Bale chat.

## Security

Before uploading to GitHub, keep:

```python
TOKEN = ""
```

Do not commit your real Telegram bot token.
Do not commit `session.bale` or any `*.bale` files. They are ignored by `.gitignore`.

## Files

- `mytelebot.py` - Telegram bot UI, chat selection, live forwarding, and polling fallback.
- `mybale.py` - Bale client setup, message sending, history loading, and compatibility fixes for Bale payloads.
- `.gitignore` - Keeps local sessions, virtual environments, caches, and IDE files out of GitHub.
