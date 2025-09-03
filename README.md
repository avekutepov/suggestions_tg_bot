# Suggestions Telegram Bot

A Telegram bot for collecting, moderating, and managing user suggestions. Built with Python.

## Features
- User intake and onboarding
- Suggestion submission and moderation
- Custom keyboards for user interaction
- Utility functions for text processing

## Project Structure
```
requirements.txt
src/
    __init__.py
    config.py
    main.py
    handlers/
        __init__.py
        intake.py
        misc.py
        moderation.py
        new_user.py
        start.py
    keyboards/
        __init__.py
        common.py
    utils/
        __init__.py
        text.py
```

## Getting Started
1. **Clone the repository:**
   ```powershell
   git clone https://github.com/avekutepov/suggestions_tg_bot.git
   ```
2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Configure the bot:**
   - Edit `src/config.py` with your Telegram bot token and other settings.
4. **Run the bot:**
   ```powershell
   python src/main.py
   ```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
MIT
