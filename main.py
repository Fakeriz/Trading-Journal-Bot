import logging
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    CallbackContext,
)

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# State dalam percakapan
(
    DATE, TIME, PAIR, WIN_LOSS, POSITION, ENTRY, STOPLOSS, TAKEPROFIT,
    RR, PNL, STRATEGY, LINK_TRADINGVIEW
) = range(12)

# Fungsi untuk membuat koneksi database per pengguna
def connect_db(user_id):
    return sqlite3.connect(f'user_{user_id}.db')

# Fungsi untuk membuat tabel jika belum ada
def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            pair TEXT,
            win_loss TEXT,
            position TEXT,
            entry REAL,
            stoploss REAL,
            takeprofit REAL,
            rr REAL,
            pnl REAL,
            strategy TEXT,
            link_tradingview TEXT
        )
    ''')
    conn.commit()

# Fungsi untuk memulai bot
async def start(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    conn = connect_db(user_id)
    create_table(conn)
    conn.close()

    await update.message.reply_text(
        "Selamat datang di Jurnal Trading!\n"
        "Silakan masukkan tanggal (YYYY-MM-DD):"
    )
    return DATE

# Fungsi untuk mencatat tanggal
async def date_handler(update: Update, context: CallbackContext) -> int:
    try:
        date = datetime.strptime(update.message.text, '%Y-%m-%d')
        context.user_data['date'] = date.strftime('%Y-%m-%d')
        await update.message.reply_text("Masukkan waktu (HH:MM):")
        return TIME
    except ValueError:
        await update.message.reply_text("Format tanggal tidak valid. Gunakan format YYYY-MM-DD.")
        return DATE

# Fungsi untuk mencatat waktu
async def time_handler(update: Update, context: CallbackContext) -> int:
    try:
        time = datetime.strptime(update.message.text, '%H:%M')
        context.user_data['time'] = time.strftime('%H:%M')
        await update.message.reply_text("Masukkan pasangan mata uang (contoh: XAUUSD):")
        return PAIR
    except ValueError:
        await update.message.reply_text("Format waktu tidak valid. Gunakan format HH:MM.")
        return TIME

# Fungsi untuk mencatat pair
async def pair_handler(update: Update, context: CallbackContext) -> int:
    context.user_data['pair'] = update.message.text.upper()
    await update.message.reply_text("Apakah hasilnya Win atau Loss?")
    return WIN_LOSS

# Fungsi untuk mencatat win/loss
async def win_loss_handler(update: Update, context: CallbackContext) -> int:
    win_loss = update.message.text.lower()
    if win_loss in ['win', 'loss']:
        context.user_data['win_loss'] = win_loss
        await update.message.reply_text("Masukkan posisi (Long/Short):")
        return POSITION
    else:
        await update.message.reply_text("Masukkan Win atau Loss.")
        return WIN_LOSS

# Fungsi untuk mencatat posisi (long/short)
async def position_handler(update: Update, context: CallbackContext) -> int:
    position = update.message.text.lower()
    if position in ['long', 'short']:
        context.user_data['position'] = position
        await update.message.reply_text("Masukkan harga entry:")
        return ENTRY
    else:
        await update.message.reply_text("Masukkan Long atau Short.")
        return POSITION

# Fungsi untuk mencatat entry price
async def entry_handler(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['entry'] = float(update.message.text)
        await update.message.reply_text("Masukkan harga stoploss:")
        return STOPLOSS
    except ValueError:
        await update.message.reply_text("Masukkan angka yang valid.")
        return ENTRY

# Fungsi untuk mencatat stoploss
async def stoploss_handler(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['stoploss'] = float(update.message.text)
        await update.message.reply_text("Masukkan harga takeprofit:")
        return TAKEPROFIT
    except ValueError:
        await update.message.reply_text("Masukkan angka yang valid.")
        return STOPLOSS

# Fungsi untuk mencatat takeprofit
async def takeprofit_handler(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['takeprofit'] = float(update.message.text)
        await update.message.reply_text("Masukkan RR:")
        return RR
    except ValueError:
        await update.message.reply_text("Masukkan angka yang valid.")
        return TAKEPROFIT

# Fungsi untuk mencatat RR
async def rr_handler(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['rr'] = float(update.message.text)
        await update.message.reply_text("Masukkan PnL:")
        return PNL
    except ValueError:
        await update.message.reply_text("Masukkan angka yang valid.")
        return RR

# Fungsi untuk mencatat PnL
async def pnl_handler(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['pnl'] = float(update.message.text)
        await update.message.reply_text("Masukkan strategi (Opsional):")
        return STRATEGY
    except ValueError:
        await update.message.reply_text("Masukkan angka yang valid.")
        return PNL

# Fungsi untuk mencatat strategi
async def strategy_handler(update: Update, context: CallbackContext) -> int:
    context.user_data['strategy'] = update.message.text
    await update.message.reply_text("Masukkan link TradingView (Opsional):")
    return LINK_TRADINGVIEW

# Fungsi untuk mencatat link TradingView
async def link_tradingview_handler(update: Update, context: CallbackContext) -> int:
    context.user_data['link_tradingview'] = update.message.text
    user_id = update.message.from_user.id
    conn = connect_db(user_id)
    cursor = conn.cursor()

    # Simpan data ke database
    cursor.execute('''
        INSERT INTO trades (date, time, pair, win_loss, position, entry, stoploss, takeprofit, rr, pnl, strategy, link_tradingview)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        context.user_data['date'],
        context.user_data['time'],
        context.user_data['pair'],
        context.user_data['win_loss'],
        context.user_data['position'],
        context.user_data['entry'],
        context.user_data['stoploss'],
        context.user_data['takeprofit'],
        context.user_data['rr'],
        context.user_data['pnl'],
        context.user_data.get('strategy', ''),
        context.user_data.get('link_tradingview', '')
    ))
    conn.commit()
    conn.close()

    await update.message.reply_text("Data trading berhasil disimpan!")
    return ConversationHandler.END

# Fungsi utama untuk menjalankan bot
async def main():
    application = Application.builder().token('YOUR_TELEGRAM_BOT_TOKEN').build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, date_handler)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_handler)],
            PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair_handler)],
            WIN_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, win_loss_handler)],
            POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, position_handler)],
            ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, entry_handler)],
            STOPLOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, stoploss_handler)],
            TAKEPROFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, takeprofit_handler)],
            RR: [MessageHandler(filters.TEXT & ~filters.COMMAND, rr_handler)],
            PNL: [MessageHandler(filters.TEXT & ~filters.COMMAND, pnl_handler)],
            STRATEGY: [MessageHandler(filters.TEXT & ~filters.COMMAND, strategy_handler)],
            LINK_TRADINGVIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, link_tradingview_handler)],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)

    # Jalankan bot
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
