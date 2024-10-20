# Forex Trading Journal Telegram Bot

A Telegram bot to log forex trades in a journal. The bot stores trade data based on the user's Telegram ID and allows users to view and delete their trade history.

## Features
- Add new trade entries
- View personal trading journal
- Delete specific trade entries
- Clear the entire journal
- Store trade data based on Telegram ID using SQLite

## Getting Started

### Prerequisites
- Python 3.8+
- Telegram account
- A bot created via Telegram's BotFather

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/trading-journal-bot.git
   cd trading-journal-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add your Telegram bot token:
   ```bash
   TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
   ```

4. Run the bot:
   ```bash
   python trading_journal_bot.py
   ```

## Usage
- `/addtrade` Add a new trade to your journal
- `/show` Display your trading journal
- `/delete_entry` Delete a specific trade
- `/clear_journal` Clear your entire journal

## License
This project is licensed under the MIT License.
