# cekviral_project/app/services/database.py
import logging
from supabase import create_client, Client
from app.core.config import settings

# --- Impor dari file schemas.py ---
from app.schemas import VerificationResult

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

async def save_verification_result(result: VerificationResult, user_id: str | None = None) -> str | None:
    """
    Menyimpan hasil verifikasi lengkap ke dalam tabel 'history' di Supabase dan mengembalikan ID-nya.
    """
    if not supabase:
        logger.warning("Klien Supabase tidak tersedia. Melewatkan penyimpanan ke database.")
        return None

    try:
        data_to_insert = {
            "original_input":        result.original_input,
            "processed_text":        result.processed_text,
            "prob_hoax":             result.prediction.probabilities.HOAKS,
            "prob_fakta":            result.prediction.probabilities.FAKTA,
            "final_label_threshold": result.prediction.final_label_thresholded,
            "inference_time_ms":     result.prediction.inference_time_ms,
            "predicted_label":       result.prediction.predicted_label_model,
            "user_id":               user_id
        }

        logger.info(f"Menyimpan hasil verifikasi ke Supabase: {data_to_insert}")
        response = supabase.table("history").insert(data_to_insert, returning="representation").execute()

        if response.data and len(response.data) > 0:
            history_id = response.data[0].get("history_id")
            logger.info(f"Data berhasil disimpan ke Supabase dengan ID: {history_id}")
            return history_id
        else:
            logger.warning("Data berhasil disimpan tetapi tidak ada ID yang dikembalikan.")
            return None

    except Exception as e:
        logger.error(f"Gagal menyimpan data ke Supabase: {e}", exc_info=True)
        return None