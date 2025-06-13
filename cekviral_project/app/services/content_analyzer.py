# cekviral_project/app/services/content_analyzer.py
from bs4 import BeautifulSoup
import re
import os
import subprocess
import logging
import asyncio
from google.cloud import speech
from google.cloud import storage

from app.core.config import settings 

logger = logging.getLogger(__name__)

# Ganti dengan nama bucket GCS yang sudah dibuat
GCS_BUCKET_NAME = "cekviral-audio-uploads"

# --- FUNGSI EKSTRAKSI TEKS DARI HTML (MENGGUNAKAN BEAUTIFULSOUP) ---
def extract_text_from_html(html_content: str) -> str | None:
    """
    Mengekstrak teks utama dari konten HTML menggunakan BeautifulSoup.
    """
    if not html_content or not isinstance(html_content, str):
        logger.warning("Input html_content untuk extract_text_from_html kosong atau bukan string.")
        return None
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Hapus tag yang tidak diinginkan seperti script, style, nav, footer, dll.
        for tag_to_remove in soup(["script", "style", "nav", "header", "footer", "aside", "form", "button", "iframe", "img", "svg", "figcaption", "figure", "noscript"]):
            tag_to_remove.decompose()

        main_content_selectors = [
            'div[itemprop="articleBody"]', 'article[itemprop="articleBody"]', 'div.entry-content', 
            'div.td-post-content', 'div.post-content', 'div.article-content', 'div.story-content', 
            'div.content', 'article', 'main', 'div[role="main"]', 'div.read__content', 
            'div.detail-content', 'div.post-body', 'div.story-body', 'div.post-detail', 
            'div.body_artikel', 'div.section_detail_content', 'div[class*="article-body"]', 
            'div[class*="post-content"]', 'div[class*="entry-content"]', 'div[class*="main-content"]',
            'div[class*="text-content"]', 'div[class*="content__body"]'
        ]
        
        main_article_element = None
        for selector in main_content_selectors:
            main_article_element = soup.select_one(selector)
            if main_article_element:
                logger.debug(f"Main content found with selector: {selector}")
                break
        
        article_text_parts = []
        target_element = main_article_element if main_article_element else soup.body
        
        if target_element:
            text = target_element.get_text(separator=' ', strip=True)
            if text:
                article_text_parts.append(text)

        title_tag = soup.find('title')
        page_title = title_tag.get_text(strip=True) if title_tag else ''
        
        full_text_parts = [page_title] if page_title else []
        full_text_parts.extend(article_text_parts)
        
        final_text = ' '.join(part for part in full_text_parts if part)
        final_text = re.sub(r'\s+', ' ', final_text).strip()

        if final_text:
            logger.debug(f"Extracted text length: {len(final_text)}")
            return final_text
        else:
            logger.warning("No significant text could be extracted from HTML.")
            return None

    except Exception as e:
        logger.error(f"Gagal mengekstrak teks dari HTML: {e}", exc_info=True)
        return None


# --- FUNGSI TRANSKRIPSI VIDEO (MENGGUNAKAN GOOGLE CLOUD API) ---
async def convert_video_to_text(video_url: str) -> str | None:
    """
    Mengunduh audio dari URL video, mengonversinya ke format mono, mengunggahnya ke GCS, 
    dan mentranskripsinya menggunakan Google Cloud Speech-to-Text API.
    """
    temp_dir = settings.YDL_TEMP_DIR
    os.makedirs(temp_dir, exist_ok=True)
    audio_filename = f"temp_audio_{os.urandom(4).hex()}.wav"
    local_audio_path = os.path.join(temp_dir, audio_filename)
    
    try:
        logger.info(f"Memeriksa keberadaan yt-dlp dan ffmpeg...")
        await asyncio.to_thread(subprocess.run, ['yt-dlp', '--version'], check=True, capture_output=True, text=True, timeout=10)
        await asyncio.to_thread(subprocess.run, ['ffmpeg', '-version'], check=True, capture_output=True, text=True, timeout=10)
    except Exception as e:
        logger.error(f"Error saat memeriksa yt-dlp/FFmpeg: {e}")
        return "Maaf, fitur transkripsi suara tidak tersedia karena aplikasi tidak dapat menemukan alat bantu (yt-dlp/ffmpeg)."

    transcribed_text = None
    gcs_uri = None
    try:
        # 1. Unduh dan konversi audio ke WAV mono
        logger.info(f"Mulai mengunduh dan mengonversi audio dari {video_url} ke {local_audio_path}")
        process = await asyncio.to_thread(
            subprocess.run,
            [
                'yt-dlp', '-x', '--audio-format', 'wav', 
                '--ppa', 'ffmpeg:-ac 1', # Paksa output menjadi mono (1 channel audio)
                '-o', local_audio_path, video_url
            ],
            capture_output=True, text=True, check=False, timeout=900
        )
        if process.returncode != 0:
            logger.error(f"yt-dlp gagal mengunduh audio. Error: {process.stderr.strip()}")
            return "Maaf, gagal mengunduh audio dari video tersebut."

        if not os.path.exists(local_audio_path) or os.path.getsize(local_audio_path) == 0:
            logger.error(f"File audio tidak ditemukan atau kosong: {local_audio_path}.")
            return "Maaf, audio dari video tidak dapat diunduh."
        
        # 2. Upload ke GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(audio_filename)

        logger.info(f"Mengunggah {local_audio_path} ke GCS bucket '{GCS_BUCKET_NAME}'...")
        await asyncio.to_thread(blob.upload_from_filename, local_audio_path)
        gcs_uri = f"gs://{GCS_BUCKET_NAME}/{audio_filename}"
        
        # 3. Kirim request ke Google Speech-to-Text API
        speech_client = speech.SpeechClient()
        audio = speech.RecognitionAudio(uri=gcs_uri)
        config = speech.RecognitionConfig(
            language_code="id-ID",
            enable_automatic_punctuation=True
        )

        logger.info("Mengirim request long_running_recognize ke Google API...")
        operation = await asyncio.to_thread(speech_client.long_running_recognize, config=config, audio=audio)
        response = await asyncio.to_thread(operation.result, timeout=900)
        
        if response.results:
            transcribed_text = " ".join([result.alternatives[0].transcript for result in response.results])
        else:
            logger.warning(f"Google API tidak mengembalikan hasil untuk {video_url}")
            return "Maaf, tidak ada obrolan yang dapat dikenali dari audio ini."

    except Exception as e:
        logger.error(f"Error selama proses transkripsi: {e}", exc_info=True)
        return "Maaf, terjadi kesalahan pada layanan transkripsi suara."
    finally:
        # 4. Bersihkan file temporer di lokal dan GCS
        if os.path.exists(local_audio_path):
            os.remove(local_audio_path)
        
        if gcs_uri:
            try:
                storage_client = storage.Client()
                bucket = storage_client.bucket(GCS_BUCKET_NAME)
                blob = bucket.blob(audio_filename)
                blob.delete()
            except Exception as e:
                logger.error(f"Gagal membersihkan file dari GCS {gcs_uri}: {e}")
    
    return transcribed_text