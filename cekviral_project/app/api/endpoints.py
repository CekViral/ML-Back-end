# cekviral_project/app/api/endpoints.py
from fastapi import APIRouter
from pydantic import BaseModel, Field
import requests
import asyncio
import logging

# Impor model Pydantic dari schemas.py
from app.schemas import ContentInput, MLPredictionOutput, VerificationResult

# Impor fungsi-fungsi dari modul lain
from app.utils.helpers import is_url, classify_url
from app.services.content_analyzer import extract_text_from_html, convert_video_to_text
from app.services.ml_model import predict_content_hoax_status
from app.services.database import save_verification_result

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/verify", response_model=VerificationResult)
async def verify_content(input_data: ContentInput):
    user_input = input_data.content.strip()
    user_id = input_data.user_id  # Ambil user_id (boleh None)
    processed_text: str | None = None
    input_type = "text"
    processing_message = "Konten sedang diproses..."

    default_ml_output = MLPredictionOutput(
        status="error",
        message="Tidak ada teks yang dapat diproses atau diverifikasi oleh model ML.",
        probabilities={"HOAKS": 0.0, "FAKTA": 0.0},
        predicted_label_model="N/A",
        highest_confidence=0.0,
        final_label_thresholded="BELUM DIVERIFIKASI",
        inference_time_ms=0.0
    )
    prediction_details = default_ml_output

    if is_url(user_input):
        input_type = "url"
        url_type = classify_url(user_input)

        if url_type == "direct_video":
            logger.info(f"URL classified as 'direct_video'. Starting transcription.")
            processed_text = await convert_video_to_text(user_input)
            if processed_text and not processed_text.lower().startswith("maaf,"):
                processing_message = "Transkripsi video berhasil."
            else:
                processing_message = processed_text or "Gagal mentranskripsi video. Konten mungkin tidak memiliki audio."
                processed_text = None

        elif url_type == "web_article":
            logger.info(f"URL classified as 'web_article'. Fetching HTML and extracting text.")
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                }
                response = await asyncio.to_thread(requests.get, user_input, headers=headers, timeout=20)
                response.raise_for_status()
                html_content = response.text
                processed_text = await asyncio.to_thread(extract_text_from_html, html_content)
                if not processed_text:
                    processing_message = "Gagal mengekstrak teks dari artikel. Halaman mungkin tidak berisi konten teks yang jelas."
                else:
                    processing_message = "Teks dari halaman web berhasil diekstrak."

            except requests.RequestException as e:
                processing_message = "Gagal mengakses atau membaca konten dari URL yang diberikan."
                processed_text = None
                logger.error(f"Error fetching article URL {user_input}: {e}", exc_info=True)
            except Exception as e:
                processing_message = f"Terjadi kesalahan saat mencoba mengekstrak artikel dari URL."
                processed_text = None
                logger.error(f"Error extracting article from {user_input}: {e}", exc_info=True)

        elif url_type == "unsupported_social":
            processing_message = "Maaf, input yang Anda berikan tidak valid atau merupakan jenis konten yang belum kami dukung untuk verifikasi."
            logger.warning(f"Unsupported social media link detected: {user_input}")

        elif url_type == "academic":
            processing_message = "Untuk menghormati hak cipta dan kode etik, sistem kami tidak memproses link yang terdeteksi sebagai jurnal ilmiah atau karya penelitian."
            logger.warning(f"Academic site link detected: {user_input}")

        else:
            processing_message = "Maaf, input yang Anda berikan tidak valid atau merupakan jenis konten yang belum kami dukung untuk verifikasi."
            logger.warning(f"Unknown or invalid URL type: {user_input}")

    else:
        if not user_input:
            processing_message = "Input teks kosong, tidak ada yang dapat diverifikasi."
        else:
            processed_text = user_input
            processing_message = "Teks murni diterima untuk verifikasi."

    if processed_text and processed_text.strip():
        logger.info(f"Sending text to ML model: {processed_text[:100]}...")
        ml_output = await asyncio.to_thread(predict_content_hoax_status, processed_text)

        if ml_output.get("status") == "success":
            prediction_details = MLPredictionOutput(**ml_output)
            if "berhasil" in processing_message:
                processing_message += " Verifikasi oleh model ML selesai."
            else:
                processing_message = "Verifikasi konten oleh model ML selesai."
        else:
            prediction_details = default_ml_output
            processing_message = f"Verifikasi ML gagal: {ml_output.get('message', 'Error tidak diketahui')}"
    else:
        if processing_message.startswith("Konten sedang diproses"):
            processing_message = "Tidak ada teks yang dapat diekstrak atau diproses dari input."

    final_result = VerificationResult(
        original_input=user_input,
        input_type=input_type,
        processed_text=processed_text or "",
        prediction=prediction_details,
        processing_message=processing_message,
        history_id="temp"
    )

    # Simpan hanya jika user login (ada user_id)
    if user_id:
        history_id = await save_verification_result(result=final_result, user_id=user_id)
        final_result.history_id = history_id or "unsaved"
    else:
        final_result.history_id = "unsaved"

    return final_result