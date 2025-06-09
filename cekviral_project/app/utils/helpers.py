# cekviral_project/app/utils/helpers.py
import re
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# --- Pola-pola URL ---

# Platform video yang didukung oleh yt-dlp
DIRECT_VIDEO_PATTERNS = [
    re.compile(r"https://(www\.|m\.)?youtube\.com/(watch\?v=|embed/|shorts/|live/)"),
    re.compile(r"https://youtu\.be/"),
    re.compile(r"https://(www\.|m\.)?tiktok\.com/(@[^/]+)?/video/"),
    re.compile(r"https://(www\.)?instagram\.com/(reel|reels|tv)/[^/]+/?"),
    re.compile(r"https://(www\.)?(twitter|x)\.com/[^/]+/status/\d+"), # Tweet bisa berisi video
    re.compile(r"https://(www\.)?dailymotion\.com/video/"), # <-- DIKEMBALIKAN
    re.compile(r"https://(www\.)?vimeo\.com/\d+"), # <-- DIKEMBALIKAN
    re.compile(r"https://(www\.|m\.)?facebook\.com/([^/]+/videos/|watch/?\?v=|video\.php\?v=)"), # <-- DIKEMBALIKAN
    re.compile(r"https://fb\.watch/") # <-- DIKEMBALIKAN
]

# Platform sosial media yang kontennya sulit/tidak didukung untuk diekstrak (dinamis/membutuhkan login)
UNSUPPORTED_SOCIAL_PATTERNS = [
    re.compile(r"https://(www\.|m\.)?instagram\.com/p/"), # Postingan Instagram (foto/carousel)
    re.compile(r"https://(www\.|m\.)?youtube\.com/post/"),
    re.compile(r"https://(www\.|m\.)?facebook\.com/(story\.php|photo)"),
]

# Kata kunci untuk mendeteksi situs jurnal/akademik yang tidak akan kita proses
ACADEMIC_KEYWORDS = [
    'journal', 'jurnal', 'doi.org', 'arxiv.org', 'researchgate.net', 
    'academia.edu', 'ieee.org', 'acm.org', 'springer.com', 'sciencedirect.com'
]

# --- Fungsi-fungsi Helper ---

def is_url(input_string: str) -> bool:
    if not isinstance(input_string, str):
        return False
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(input_string))


def classify_url(url: str) -> str:
    """
    Mengklasifikasikan URL ke dalam beberapa kategori untuk diproses lebih lanjut.
    Returns: 'direct_video', 'unsupported_social', 'academic', 'web_article', 'unknown'
    """
    if not url or not isinstance(url, str):
        return 'unknown'
        
    try:
        # Cek jika ini adalah link video langsung
        for pattern in DIRECT_VIDEO_PATTERNS:
            if pattern.match(url):
                logger.info(f"URL classified as 'direct_video': {url}")
                return "direct_video"

        # Cek jika ini adalah link dari platform sosial yang tidak didukung
        for pattern in UNSUPPORTED_SOCIAL_PATTERNS:
            if pattern.match(url):
                logger.warning(f"URL classified as 'unsupported_social': {url}")
                return "unsupported_social"
        
        # Cek jika ini adalah link dari situs akademik/jurnal
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname or ""
        path = parsed_url.path or ""
        for keyword in ACADEMIC_KEYWORDS:
            if keyword in hostname or keyword in path:
                logger.warning(f"URL classified as 'academic': {url}")
                return "academic"

        # Jika lolos semua pengecekan di atas, anggap sebagai artikel web umum
        logger.info(f"URL classified as 'web_article': {url}")
        return "web_article"

    except Exception as e:
        logger.error(f"Error classifying URL {url}: {e}", exc_info=True)
        return "unknown"