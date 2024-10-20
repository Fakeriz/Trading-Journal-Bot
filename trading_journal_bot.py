import logging
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Logging untuk debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup database SQLite
def setup_database():
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS journal (
                    user_id INTEGER,
                    pair TEXT,
                    order_type TEXT,
                    entry_price REAL,
                    take_profit REAL,
                    stop_loss REAL,
                    exit_price REAL,
                    profit_loss REAL,
                    datetime TEXT
                )''')
    conn.commit()
    conn.close()

# Fungsi untuk memulai bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Selamat datang di bot jurnal trading forex! Gunakan /addtrade untuk menambah jurnal.')

# Fungsi untuk menambah entri trading ke database
async def addtrade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        args = context.args
        if len(args) != 7:
            await update.message.reply_text('Format salah! Gunakan format:\n/addtrade <Pair> <OrderType> <EntryPrice> <TP> <SL> <ExitPrice> <Profit/Loss>')
            return
        
        pair = args[0]
        order_type = args[1]
        entry_price = float(args[2])
        tp = float(args[3])
        sl = float(args[4])
        exit_price = float(args[5])
        profit_loss = float(args[6])
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Menyimpan data ke database
        conn = sqlite3.connect('trading_journal.db')
        c = conn.cursor()
        c.execute('''INSERT INTO journal (user_id, pair, order_type, entry_price, take_profit, stop_loss, exit_price, profit_loss, datetime)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                     (user_id, pair, order_type, entry_price, tp, sl, exit_price, profit_loss, timestamp))
        conn.commit()
        conn.close()

        await update.message.reply_text(f'Trade berhasil ditambahkan: {pair} {order_type} di harga {entry_price}.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

# Fungsi untuk menampilkan jurnal trading user
async def show_journal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute('SELECT * FROM journal WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()

    if len(rows) == 0:
        await update.message.reply_text('Belum ada trade yang dicatat.')
        return
    
    message = "Jurnal Trading:\n"
    for row in rows:
        message += f"{row[8]} | {row[1]} | {row[2]} | Entry: {row[3]} | TP: {row[4]} | SL: {row[5]} | Exit: {row[6]} | P/L: {row[7]}\n"
    
    await update.message.reply_text(message)

# Fungsi untuk menghapus satu entri trading
async def delete_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        entry_id = int(context.args[0])
        conn = sqlite3.connect('trading_journal.db')
        c = conn.cursor()
        c.execute('DELETE FROM journal WHERE rowid = ? AND user_id = ?', (entry_id, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f'Entri trading berhasil dihapus dengan ID {entry_id}.')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)}')

# Fungsi untuk menghapus semua entri trading user
async def clear_journal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conn = sqlite3.connect('trading_journal.db')
    c = conn.cursor()
    c.execute('DELETE FROM journal WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text('Semua entri trading berhasil dihapus.')

# Fungsi untuk meng-handle error
def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)

# Fungsi utama untuk menjalankan bot
async def main() -> None:
    setup_database()
    # Token bot dari BotFather
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    # Setup bot dengan ApplicationBuilder (Python terbaru)
    application = ApplicationBuilder().token(TOKEN).build()

    # Tambahkan handler untuk perintah
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addtrade", addtrade))
    application.add_handler(CommandHandler("show", show_journal))
    application.add_handler(CommandHandler("delete_entry", delete_entry))
    application.add_handler(CommandHandler("clear_journal", clear_journal))

    # Inisialisasi bot sebelum menjalankan
    await application.initialize()

    # Start bot setelah inisialisasi selesai
    await application.start()
    await application.updater.start_polling()  # Menambahkan polling jika dibutuhkan
    await application.idle()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
