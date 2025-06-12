from fastapi import APIRouter, Depends
from pydantic import BaseModel
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

    if is_url(user_input):
        input_type = "url"
        url_type = classify_url(user_input)

        match url_type:
            case "direct_video":
                logger.info("Transkripsi video dimulai.")
                processed_text = await convert_video_to_text(user_input)
                if processed_text and not processed_text.lower().startswith("maaf,"):
                    processing_message = "Transkripsi video berhasil."
                else:
                    processing_message = processed_text or "Gagal mentranskripsi video."
                    processed_text = None

            case "web_article":
                logger.info("Ekstraksi artikel dimulai.")
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0"
                    }
                    response = await asyncio.to_thread(requests.get, user_input, headers=headers, timeout=20)
                    response.raise_for_status()
                    html_content = response.text
                    processed_text = await asyncio.to_thread(extract_text_from_html, html_content)
                    processing_message = (
                        "Teks dari halaman web berhasil diekstrak."
                        if processed_text else
                        "Gagal mengekstrak teks dari artikel."
                    )
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)
                    processing_message = "Gagal memproses URL."

            case "unsupported_social":
                processing_message = "Maaf, platform sosial ini belum didukung."
            case "academic":
                processing_message = "Konten ilmiah tidak diproses demi etika."
            case _:
                processing_message = "Jenis URL tidak dikenali atau belum didukung."

    elif user_input:
        processed_text = user_input
        processing_message = "Teks langsung diterima untuk verifikasi."
    else:
        processing_message = "Input kosong, tidak dapat diverifikasi."

    if processed_text:
        logger.info(f"Verifikasi ML untuk teks: {processed_text[:100]}...")
        ml_output = await asyncio.to_thread(predict_content_hoax_status, processed_text)
        if ml_output.get("status") == "success":
            prediction_details = MLPredictionOutput(**ml_output)
            processing_message += " Verifikasi selesai."
        else:
            processing_message = f"Verifikasi gagal: {ml_output.get('message', 'Terjadi kesalahan.')}"

    elif processing_message.startswith("Konten sedang diproses"):
        processing_message = "Tidak ada teks yang dapat diproses."

    final_result = VerificationResult(
        original_input=user_input,
        input_type=input_type,
        processed_text=processed_text or "",
        prediction=prediction_details,
        processing_message=processing_message,
        history_id="unsaved"
    )

    # Simpan hanya jika user login
    if user_id:
        history_id = await save_verification_result(result=final_result, user_id=user_id)
        final_result.history_id = history_id or "unsaved"

    return final_result