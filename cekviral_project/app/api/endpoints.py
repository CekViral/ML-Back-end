# cekviral_project/app/api/endpoints.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging
import asyncio
import requests

from app.schemas import ContentInput, MLPredictionOutput, VerificationResult
from app.utils.helpers import is_url, classify_url
from app.services.content_analyzer import extract_text_from_html, convert_video_to_text
from app.services.ml_model import predict_content_hoax_status
from app.services.database import save_verification_result
from app.utils.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/verify", response_model=VerificationResult)
async def verify_content(
    input_data: ContentInput,
    user_id: Optional[str] = Depends(get_current_user)
):
    if not user_id:
        logger.warning("Akses ditolak: pengguna tidak terautentikasi.")
        raise HTTPException(status_code=401, detail="Akses ditolak. Silakan login untuk menggunakan layanan ini.")

    user_input = input_data.content.strip()
    processed_text: Optional[str] = None
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

    # --- Proses jika input berupa URL ---
    if is_url(user_input):
        input_type = "url"
        url_type = classify_url(user_input)

        match url_type:
            case "direct_video":
                logger.info(f"URL classified as 'direct_video'. Starting transcription.")
                processed_text = await convert_video_to_text(user_input)
                if processed_text and not processed_text.lower().startswith("maaf,"):
                    processing_message = "Transkripsi video berhasil."
                else:
                    processing_message = processed_text or "Gagal mentranskripsi video. Konten mungkin tidak memiliki audio."
                    processed_text = None

            case "web_article":
                logger.info(f"URL classified as 'web_article'. Fetching and extracting text.")
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/125.0.0.0 Safari/537.36",
                    }
                    response = await asyncio.to_thread(requests.get, user_input, headers=headers, timeout=20)
                    response.raise_for_status()
                    html_content = response.text
                    processed_text = await asyncio.to_thread(extract_text_from_html, html_content)
                    processing_message = (
                        "Teks dari halaman web berhasil diekstrak."
                        if processed_text else
                        "Gagal mengekstrak teks dari artikel. Halaman mungkin tidak berisi konten teks yang jelas."
                    )
                except requests.RequestException as e:
                    logger.error(f"Error fetching article URL {user_input}: {e}", exc_info=True)
                    processing_message = "Gagal mengakses atau membaca konten dari URL yang diberikan."
                except Exception as e:
                    logger.error(f"Error extracting article from {user_input}: {e}", exc_info=True)
                    processing_message = "Terjadi kesalahan saat mencoba mengekstrak artikel dari URL."
                finally:
                    if not processed_text:
                        processed_text = None

            case "unsupported_social":
                logger.warning(f"Unsupported social media link: {user_input}")
                processing_message = "Maaf, konten dari platform ini belum didukung untuk verifikasi."

            case "academic":
                logger.warning(f"Academic content detected: {user_input}")
                processing_message = "Konten dari jurnal atau situs ilmiah tidak diproses demi etika dan hak cipta."

            case _:
                logger.warning(f"Unknown URL type: {user_input}")
                processing_message = "Maaf, jenis URL ini tidak dikenali atau belum didukung."

    # --- Proses jika input berupa teks langsung ---
    elif user_input:
        processed_text = user_input
        processing_message = "Teks murni diterima untuk verifikasi."
    else:
        processing_message = "Input teks kosong, tidak ada yang dapat diverifikasi."

    # --- Verifikasi dengan model ML ---
    if processed_text and processed_text.strip():
        logger.info(f"Sending text to ML model: {processed_text[:100]}...")
        ml_output = await asyncio.to_thread(predict_content_hoax_status, processed_text)

        if ml_output.get("status") == "success":
            prediction_details = MLPredictionOutput(**ml_output)
            processing_message += " Verifikasi oleh model ML selesai."
        else:
            processing_message = f"Verifikasi ML gagal: {ml_output.get('message', 'Terjadi kesalahan.')}"

    elif processing_message.startswith("Konten sedang diproses"):
        processing_message = "Tidak ada teks yang dapat diekstrak atau diproses dari input."

    final_result = VerificationResult(
        original_input=user_input,
        input_type=input_type,
        processed_text=processed_text or "",
        prediction=prediction_details,
        processing_message=processing_message,
        history_id="unsaved"
    )

    # Simpan hasil ke database
    history_id = await save_verification_result(result=final_result, user_id=user_id)
    final_result.history_id = history_id or "unsaved"

    return final_result