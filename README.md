

# Suggestions Telegram Bot

A Telegram bot for collecting, moderating, and managing user suggestions. Built with Python 3.10+ and [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI).

## Features
- User onboarding and suggestion intake
- Moderation workflow with status tracking
- Custom and inline keyboards for user interaction
- Weekly and monthly reports for managers
- Configurable SQLite database location
- HTML-formatted messages (including clickable author names in reports)

## Project Structure
```
requirements.txt
src/
    __init__.py
    config.py
    main.py
    db.py
    handlers/
        __init__.py
        intake.py
        misc.py
        moderation.py
        new_user.py
        start.py
        reports.py
    keyboards/
        __init__.py
        common.py
    utils/
        __init__.py
        text.py
data/
    suggestions.db
```

## Quick Start

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/avekutepov/suggestions_tg_bot.git
   ```
2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Set environment variables:**
   - `BOT_TOKEN` — Telegram bot token (required)
   - `MANAGERS_CHAT_ID` — Chat ID for the managers' group (required for moderation and reports)
   - `DB_PATH` — (optional) Path to the SQLite database file (default: `data/suggestions.db`)
   - `PUBLIC_CHAT_ID` — (optional) ID of the public group for onboarding
   - `ALLOW_MEDIA` — (optional, default: true) Allow media attachments

   Example for Windows PowerShell:
   ```powershell
   $env:BOT_TOKEN = "<your_token>"
   $env:MANAGERS_CHAT_ID = "-1001234567890"
   python -m src.main
   ```
4. **Run the bot:**
   ```powershell
   python -m src.main
   ```

## Usage

- Users can submit suggestions via `/suggest` in private chat.
- Moderators can approve or reject suggestions via inline buttons in the managers' group.
- All suggestions are stored in a SQLite database (location is configurable).

### Reports

Managers can use the following commands in the managers' group:
- `/weekly` — show all in_process suggestions for the last 7 days
- `/monthly` — show all in_process suggestions for the last 30 days

## Dependencies

- pyTelegramBotAPI==4.14.0
- python-dotenv==1.0.1

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
MIT
