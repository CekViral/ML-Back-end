# Gunakan image yang ringan
FROM python:3.12-slim

# Tambahkan dependencies sistem (buat psycopg2 & bcrypt work)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements dulu (agar cache pip bisa dipakai)
COPY requirements.txt .

# Install dependencies Python
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy semua source code ke dalam container
COPY . .

# Jalankan server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port=${PORT:-8000}"]