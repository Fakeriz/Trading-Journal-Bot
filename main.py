import os
import sqlite3
import csv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters, ConversationHandler

# Koneksi database SQLite
def create_connection():
    conn = sqlite3.connect("trading_journal.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS journal (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        date_time TEXT,
                        pair TEXT,
                        order_type TEXT,
                        entry_price REAL,
                        take_profit REAL,
                        stop_loss REAL,
                        exit_price REAL,
                        profit_loss REAL,
                        notes TEXT,
                        trader_view_link TEXT)''')
    conn.commit()
    return conn

# Fungsi untuk menyimpan data ke database
def insert_journal_entry(user_id, date_time, pair, order_type, entry_price, take_profit, stop_loss, exit_price, profit_loss, notes, trader_view_link):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO journal (user_id, date_time, pair, order_type, entry_price, take_profit, stop_loss, exit_price, profit_loss, notes, trader_view_link)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (user_id, date_time, pair, order_type, entry_price, take_profit, stop_loss, exit_price, profit_loss, notes, trader_view_link))
    conn.commit()
    conn.close()

# Fungsi untuk menampilkan jurnal trading pribadi
def view_journal(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM journal WHERE user_id = ?''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# Fungsi untuk menghapus entri berdasarkan ID
def delete_entry(entry_id, user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM journal WHERE id = ? AND user_id = ?''', (entry_id, user_id))
    conn.commit()
    conn.close()

# Fungsi untuk menghapus seluruh entri jurnal pengguna
def clear_journal(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM journal WHERE user_id = ?''', (user_id,))
    conn.commit()
    conn.close()

# Fungsi untuk export data ke CSV
def export_to_csv(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM journal WHERE user_id = ?''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    filename = f"trading_journal_{user_id}.csv"
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'User ID', 'Tanggal dan Waktu', 'Pair', 'Order Type', 'Entry Price', 'Take Profit', 'Stop Loss', 'Exit Price', 'Profit/Loss', 'Catatan', 'Link TraderView'])
        writer.writerows(rows)

    return filename

# Fungsi /start untuk bot Telegram
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Selamat datang di Trading Journal Bot. Anda bisa menambahkan trading, melihat jurnal, atau mengelola entri trading Anda. Gunakan /help untuk informasi lebih lanjut.")

# Fungsi untuk menambahkan entri trading
async def add_entry(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    args = context.args
    if len(args) < 8:
        await update.message.reply_text("Format tidak lengkap! Harap masukkan data dalam format berikut:\n\nTanggal & Waktu, Pair, Order Type, Entry Price, TP, SL, Exit Price, Profit/Loss, [Catatan Tambahan], [Link TraderView]")
        return

    date_time, pair, order_type, entry_price, take_profit, stop_loss, exit_price, profit_loss = args[:8]
    notes = args[8] if len(args) > 8 else ""
    trader_view_link = args[9] if len(args) > 9 else ""

    insert_journal_entry(user_id, date_time, pair, order_type, float(entry_price), float(take_profit), float(stop_loss), float(exit_price), float(profit_loss), notes, trader_view_link)

    await update.message.reply_text("Entry jurnal trading berhasil ditambahkan!")

# Fungsi untuk melihat jurnal trading pribadi
async def view_entries(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    rows = view_journal(user_id)
    if rows:
        response = "Jurnal Trading Anda:\n\n"
        for row in rows:
            response += f"ID: {row[0]}\nTanggal & Waktu: {row[2]}\nPair: {row[3]}\nOrder Type: {row[4]}\nEntry Price: {row[5]}\nTake Profit: {row[6]}\nStop Loss: {row[7]}\nExit Price: {row[8]}\nProfit/Loss: {row[9]}\nCatatan: {row[10]}\nTraderView Link: {row[11]}\n\n"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Jurnal Anda kosong!")

# Fungsi untuk menghapus entri berdasarkan ID
async def delete_entry_cmd(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    entry_id = int(context.args[0])
    delete_entry(entry_id, user_id)
    await update.message.reply_text(f"Entri dengan ID {entry_id} berhasil dihapus.")

# Fungsi untuk menghapus seluruh entri jurnal pengguna
async def clear_journal_cmd(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    clear_journal(user_id)
    await update.message.reply_text("Seluruh entri jurnal Anda telah dihapus.")

# Fungsi untuk export jurnal ke CSV
async def export_journal(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    filename = export_to_csv(user_id)
    await update.message.reply_document(open(filename, 'rb'))

# Fungsi /cancel untuk membatalkan operasi
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Operasi dibatalkan.")
    return ConversationHandler.END

# Fungsi /help untuk bot Telegram
async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text("""
    Perintah yang tersedia:
    /start - Memulai bot
    /add_entry - Menambahkan entri trading baru (Format: Tanggal & Waktu, Pair, Order Type, Entry Price, TP, SL, Exit Price, Profit/Loss, [Catatan], [Link TraderView])
    /view_entries - Melihat jurnal trading pribadi
    /delete_entry <ID> - Menghapus entri berdasarkan ID
    /clear_journal - Menghapus seluruh jurnal trading
    /export - Mengekspor jurnal ke file CSV
    /cancel - Membatalkan operasi
    /help - Melihat perintah yang tersedia
    """)

# Setup bot dan command handler
async def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.getenv("PORT", "8443"))

    # Membuat tabel jika belum ada
    create_connection()

    application = Application.builder().token(TOKEN).build()

    # Menambahkan handler untuk command
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_entry", add_entry))
    application.add_handler(CommandHandler("view_entries", view_entries))
    application.add_handler(CommandHandler("delete_entry", delete_entry_cmd))
    application.add_handler(CommandHandler("clear_journal", clear_journal_cmd))
    application.add_handler(CommandHandler("export", export_journal))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("help", help_command))

    # Set webhook secara manual
    await application.bot.set_webhook(url=WEBHOOK_URL)

    # Menjalankan webhook
    await application.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=WEBHOOK_URL
    )

    await application.wait_until_shutdown()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
