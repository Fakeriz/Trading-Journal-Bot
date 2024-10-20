# Gunakan image Python resmi
FROM python:3.10-slim

# Menetapkan direktori kerja di dalam container
WORKDIR /app

# Menyalin file requirements.txt ke dalam container
COPY requirements.txt requirements.txt

# Install dependencies dari requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh project ke dalam container
COPY . .

# Menjalankan bot
CMD ["python", "trading_journal_bot.py"]
