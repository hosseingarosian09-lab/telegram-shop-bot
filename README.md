# Telegram Shop Bot

Initial portfolio project using Python + Aiogram 3 + Long Polling.

## Structure

```text
telegram-shop-bot/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── start.py
│   └── keyboards/
│       ├── __init__.py
│       └── main_menu.py
├── scripts/
│   └── setup.ps1
├── .env.example
├── .gitignore
├── requirements.txt
├── setup.bat
├── run.bat
└── README.md
```

## Windows setup

Double-click:

```text
setup.bat
```

The setup will:

1. Check for Python 3.10+.
2. Download and install Python 3.13.15 from python.org if needed.
3. Create `.venv`.
4. Install `requirements.txt`.
5. Check `.env`.
6. Ask for `BOT_TOKEN` if it is missing or invalid.
7. Verify the token with Telegram when possible.
8. Ask for `ADMIN_IDS` if it is missing or invalid.
9. Save a clean `.env`.

If you do not know your Telegram user ID yet, leave `ADMIN_IDS` blank during the first setup.

## Run

Double-click:

```text
run.bat
```

Then send:

```text
/start
```

The terminal will print:

```text
Telegram ID: 123456789
Admin: False
```

Run `setup.bat` again and use that ID as `ADMIN_IDS`.

After restarting the bot, `/start` should print:

```text
Admin: True
```

## Security

- `.env` is ignored by Git.
- `.env.example` contains no secrets.
- Never share your Bot Token.
