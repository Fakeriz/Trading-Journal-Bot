import os
import csv
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, filters

# Konfigurasi
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
PORT = int(os.environ.get('PORT', 8443))

# States untuk ConversationHandler
(PAIR, ORDER_TYPE, ENTRY_PRICE, TAKE_PROFIT, STOP_LOSS, EXIT_PRICE, PROFIT_LOSS, NOTES, TRADINGVIEW_LINK) = range(9)

# Fungsi untuk menginisialisasi database
def init_db():
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_id INTEGER,
     date TEXT,
     pair TEXT,
     order_type TEXT,
     entry_price REAL,
     take_profit REAL,
     stop_loss REAL,
     exit_price REAL,
     profit_loss REAL,
     notes TEXT,
     tradingview_link TEXT)
    ''')
    conn.commit()
    conn.close()

# Fungsi untuk menambahkan entri baru
async def add_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    context.user_data['trade'] = {'user_id': user_id, 'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    await update.message.reply_text("Masukkan pair (instrumen):")
    return PAIR

async def pair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['trade']['pair'] = update.message.text
    await update.message.reply_text("Masukkan jenis order (Buy/Sell):")
    return ORDER_TYPE

async def order_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['trade']['order_type'] = update.message.text
    await update.message.reply_text("Masukkan harga entry:")
    return ENTRY_PRICE

async def entry_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['trade']['entry_price'] = float(update.message.text)
    await update.message.reply_text("Masukkan Take Profit (TP):")
    return TAKE_PROFIT

async def take_profit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['trade']['take_profit'] = float(update.message.text)
    await update.message.reply_text("Masukkan Stop Loss (SL):")
    return STOP_LOSS

async def stop_loss(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['trade']['stop_loss'] = float(update.message.text)
    await update.message.reply_text("Masukkan harga exit:")
    return EXIT_PRICE

async def exit_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['trade']['exit_price'] = float(update.message.text)
    await update.message.reply_text("Masukkan Profit/Loss:")
    return PROFIT_LOSS

async def profit_loss(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['trade']['profit_loss'] = float(update.message.text)
    await update.message.reply_text("Masukkan catatan tambahan (opsional) atau ketik 'skip':")
    return NOTES

async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() != 'skip':
        context.user_data['trade']['notes'] = update.message.text
    await update.message.reply_text("Masukkan link TradingView (opsional) atau ketik 'skip':")
    return TRADINGVIEW_LINK

async def tradingview_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() != 'skip':
        context.user_data['trade']['tradingview_link'] = update.message.text
    
    # Simpan data ke database
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO trades (user_id, date, pair, order_type, entry_price, take_profit, stop_loss, exit_price, profit_loss, notes, tradingview_link)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        context.user_data['trade']['user_id'],
        context.user_data['trade']['date'],
        context.user_data['trade']['pair'],
        context.user_data['trade']['order_type'],
        context.user_data['trade']['entry_price'],
        context.user_data['trade']['take_profit'],
        context.user_data['trade']['stop_loss'],
        context.user_data['trade']['exit_price'],
        context.user_data['trade']['profit_loss'],
        context.user_data['trade'].get('notes', ''),
        context.user_data['trade'].get('tradingview_link', '')
    ))
    conn.commit()
    conn.close()

    await update.message.reply_text("Entri trading berhasil ditambahkan ke jurnal Anda!")
    return ConversationHandler.END

# Fungsi untuk melihat jurnal trading
async def view_journal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trades WHERE user_id = ?', (user_id,))
    trades = cursor.fetchall()
    conn.close()

    if not trades:
        await update.message.reply_text("Jurnal trading Anda masih kosong.")
        return

    response = "Jurnal Trading Anda:\n\n"
    for trade in trades:
        response += f"Tanggal: {trade[2]}\n"
        response += f"Pair: {trade[3]}\n"
        response += f"Jenis Order: {trade[4]}\n"
        response += f"Harga Entry: {trade[5]}\n"
        response += f"Take Profit: {trade[6]}\n"
        response += f"Stop Loss: {trade[7]}\n"
        response += f"Harga Exit: {trade[8]}\n"
        response += f"Profit/Loss: {trade[9]}\n"
        if trade[10]:
            response += f"Catatan: {trade[10]}\n"
        if trade[11]:
            response += f"Link TradingView: {trade[11]}\n"
        response += "\n"

    await update.message.reply_text(response)

# Fungsi untuk menghapus entri spesifik
async def delete_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, date, pair FROM trades WHERE user_id = ?', (user_id,))
    trades = cursor.fetchall()

    if not trades:
        await update.message.reply_text("Tidak ada entri untuk dihapus.")
        return

    keyboard = []
    for trade in trades:
        keyboard.append([InlineKeyboardButton(f"{trade[1]} - {trade[2]}", callback_data=f"delete_{trade[0]}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Pilih entri yang ingin dihapus:", reply_markup=reply_markup)

async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    trade_id = int(query.data.split('_')[1])
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM trades WHERE id = ?', (trade_id,))
    conn.commit()
    conn.close()

    await query.edit_message_text(text="Entri berhasil dihapus.")

# Fungsi untuk mengosongkan seluruh jurnal
async def clear_journal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM trades WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text("Seluruh jurnal trading Anda telah dikosongkan.")

# Fungsi untuk mengekspor ke CSV
async def export_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trades WHERE user_id = ?', (user_id,))
    trades = cursor.fetchall()
    conn.close()

    if not trades:
        await update.message.reply_text("Tidak ada data untuk diekspor.")
        return

    filename = f"trading_journal_{user_id}.csv"
    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Tanggal', 'Pair', 'Jenis Order', 'Harga Entry', 'Take Profit', 'Stop Loss', 'Harga Exit', 'Profit/Loss', 'Catatan', 'Link TradingView'])
        for trade in trades:
            csv_writer.writerow(trade[2:])

    with open(filename, 'rb') as file:
        await update.message.reply_document(document=file, filename=filename)

    os.remove(filename)

# Fungsi untuk membatalkan operasi
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operasi dibatalkan.")
    return ConversationHandler.END

# Fungsi utama
def main():
    init_db()

    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_trade', add_trade)],
        states={
            PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, pair)],
            ORDER_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_type)],
            ENTRY_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, entry_price)],
            TAKE_PROFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_profit)],
            STOP_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, stop_loss)],
            EXIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, exit_price)],
            PROFIT_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, profit_loss)],
            NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, notes)],
            TRADINGVIEW_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, tradingview_link)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('view_journal', view_journal))
    application.add_handler(CommandHandler('delete_entry', delete_entry))
    application.add_handler(CommandHandler('clear_journal', clear_journal))
    application.add_handler(CommandHandler('export_csv', export_csv))
    application.add_handler(CallbackQueryHandler(delete_callback, pattern='^delete_'))

    # Menggunakan webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

if __name__ == '__main__':
    main()