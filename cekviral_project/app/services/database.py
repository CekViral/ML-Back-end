# cekviral_project/app/services/database.py
import logging
from supabase import create_client, Client
from app.core.config import settings

# --- PERUBAHAN UTAMA #2: Impor dari file schemas.py ---
from app.schemas import VerificationResult # Impor dari file baru

logger = logging.getLogger(__name__)

# Inisialisasi klien Supabase
supabase: Client | None = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Koneksi ke Supabase berhasil diinisialisasi.")
    except Exception as e:
        logger.error(f"Gagal menginisialisasi koneksi Supabase: {e}", exc_info=True)
else:
    logger.warning("SUPABASE_URL atau SUPABASE_KEY tidak ditemukan. Fitur database tidak akan aktif.")

async def save_verification_result(result: VerificationResult, user_id: str | None = None):
    """
    Menyimpan hasil verifikasi lengkap ke dalam tabel 'history' di Supabase.
    """
    if not supabase:
        logger.warning("Klien Supabase tidak tersedia. Melewatkan penyimpanan ke database.")
        return

    try:
        data_to_insert = {
            "original_input":        result.original_input,
            "processed_text":        result.processed_text,
            "prob_hoax":             result.prediction.probabilities.HOAX,
            "prob_fakta":            result.prediction.probabilities.FAKTA,
            "final_label_threshold": result.prediction.final_label_thresholded,
            "inference_time_ms":     result.prediction.inference_time_ms,
            "predicted_label":       result.prediction.predicted_label_model,
            "user_id":               user_id
        }

        logger.info(f"Menyimpan hasil verifikasi ke Supabase: {data_to_insert}")
        # Ganti 'history' dengan nama tabel Anda jika berbeda
        response = supabase.table("history").insert(data_to_insert).execute()
        
        logger.info("Data berhasil disimpan ke Supabase.")

    except Exception as e:
        logger.error(f"Gagal menyimpan data ke Supabase: {e}", exc_info=True)