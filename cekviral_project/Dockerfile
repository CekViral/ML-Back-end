# 1. Gunakan base image Python resmi (sesuaikan versi jika perlu, misal python:3.10-slim)
FROM python:3.10-slim-buster 

# 2. Set variabel environment
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive

# 3. Set working directory di dalam kontainer
WORKDIR /app

# 4. Update package list dan install ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 5. Salin file requirements.txt terlebih dahulu
COPY requirements.txt .

# 6. Install dependensi Python
RUN pip install --no-cache-dir -r requirements.txt

# 7. Download NLTK data saat build image
RUN python -m nltk.downloader punkt_tab stopwords 

# 8. Salin semua file dan folder dari direktori proyek Anda ke working directory di kontainer
COPY . .

# 9. Jalankan aplikasi melalui file main.py, bukan uvicorn langsung
CMD ["python", "main.py"]