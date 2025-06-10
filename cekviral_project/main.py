# cekviral_project/main.py
import os
import sys
import logging
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv

# ----------------- SETUP AWAL & KONFIGURASI -----------------

# 1. Tambahkan direktori root proyek ke sys.path
# Ini membantu Python menemukan modul di folder 'app' Anda.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 2. Load environment variables dari file .env
# Ini akan membaca variabel seperti GCP_CREDENTIALS_PATH
load_dotenv()

# 3. Import settings SETELAH .env di-load
from app.core.config import settings

# 4. Konfigurasi logging dasar untuk seluruh aplikasi
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 5. Atur environment variable untuk Google Cloud Credentials (JIKA ANDA MENGGUNAKAN GCP API)
# Ini langkah kunci agar library Google Cloud bisa menemukan file kunci JSON Anda secara otomatis.
# Pastikan Anda sudah membuat file .env dan mengisi GCP_CREDENTIALS_PATH="gcp-credentials.json"
if settings.GCP_CREDENTIALS_PATH:
    # Buat path absolut dari path relatif di .env
    credentials_path = os.path.join(current_dir, settings.GCP_CREDENTIALS_PATH)
    if os.path.exists(credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        logger.info("Kredensial Google Cloud (GOOGLE_APPLICATION_CREDENTIALS) berhasil diatur.")
    else:
        # Beri peringatan jika fitur ASR mungkin tidak berfungsi
        logger.warning(f"File kredensial GCP tidak ditemukan di path: '{credentials_path}'. Fitur ASR via GCP API mungkin tidak akan berfungsi.")
else:
    logger.info("GCP_CREDENTIALS_PATH tidak diatur di file .env. Melanjutkan tanpa setup kredensial GCP otomatis.")


# ----------------- INISIALISASI APLIKASI FASTAPI -----------------

# Impor router setelah semua setup path selesai
from app.api.endpoints import router as api_router

# Buat instance aplikasi FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="CekViral: Asisten Cerdas untuk Verifikasi Konten Viral"
)

# ----------------- EVENT HANDLERS (Fungsi saat Startup & Shutdown) -----------------

@app.on_event("startup")
async def startup_event():
    """
    Fungsi ini akan berjalan sekali saat aplikasi FastAPI pertama kali dinyalakan.
    Sangat cocok untuk memuat model dan dependensi.
    """
    logger.info("Aplikasi CekViral startup...")
    
    # 1. Download data NLTK yang diperlukan
    logger.info("Memeriksa/Mengunduh data NLTK...")
    import nltk
    try:
        # Cek apakah resource yang dibutuhkan sudah ada
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        logger.info("Data NLTK sudah tersedia.")
    except nltk.downloader.DownloadError:
        logger.warning("Data NLTK tidak ditemukan. Mengunduh...")
        nltk.download('punkt')
        nltk.download('stopwords')
        logger.info("Data NLTK berhasil diunduh.")

    # 2. Muat model ML untuk deteksi hoaks
    logger.info("Memuat model ML deteksi hoaks...")
    from app.services.ml_model import load_ml_model
    load_ml_model() # Fungsi ini akan mengisi variabel global_model dan global_tokenizer
    logger.info("Model ML deteksi hoaks berhasil dimuat.")


@app.on_event("shutdown")
async def shutdown_event():
    """Fungsi yang berjalan saat aplikasi dimatikan."""
    logger.info("Aplikasi CekViral shutdown.")

# ----------------- ROUTING DAN EKSEKUSI -----------------

# Sertakan router API
app.include_router(api_router)

@app.get("/", summary="Endpoint Root", tags=["Root"])
async def root():
    """Endpoint root untuk mengecek status API."""
    return {"message": f"Selamat datang di {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}. Kunjungi /docs untuk dokumentasi API."}

# Blok ini memungkinkan untuk menjalankan aplikasi langsung dengan 'python main.py'
if __name__ == "__main__":
    # Baca port dari environment variable 'PORT' yang diberikan oleh Cloud Run.
    # Jika tidak ada (misalnya saat development lokal), gunakan port 8000 sebagai default.
    port = int(os.environ.get("PORT", 8000))
    
    # Jalankan Uvicorn dari dalam Python.
    # --reload=True dihapus karena tidak boleh digunakan di production.
    uvicorn.run("main:app", host="0.0.0.0", port=port)
