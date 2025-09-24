import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import time
import random
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

# --- SETUP ---
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/91.0.4472.124 Safari/537.36'
}

def build_page_url(base_url, page):
    if page == 1:
        return base_url
    parsed = urlparse(base_url)
    query = parse_qs(parsed.query)
    query['page'] = [str(page)]
    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

def get_list_berita(url):
    res = session.get(url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, 'html.parser')

    berita_blocks = soup.find_all("div", class_="card__post card__post-list card__post__transition mt-30")
    berita = []

    for block in berita_blocks:
        judul_tag = block.find("div", class_="card__post__title")
        a_tag = judul_tag.find("a") if judul_tag else None
        if a_tag and a_tag.get("href"):
            judul = a_tag.get_text(strip=True)
            link = urljoin(url, a_tag["href"])
            berita.append({
                "judul": judul,
                "link": link
            })

    return berita

def scrape_isi_berita(url):
    try:
        res = session.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')

        konten = soup.select_one('div.wrap_article-detail-content')
        if not konten:
            konten = soup.find('div', class_='post-content') or soup.find('article')

        if not konten:
            return ''

        paragraf = konten.find_all('p')
        teks = "\n".join(p.get_text(strip=True) for p in paragraf if p.get_text(strip=True))
        return teks
    except Exception as e:
        print(f"❌ Gagal ambil isi dari {url}: {e}")
        return ''

def baca_hal_terakhir(path="/Environment/information/data/halaman_terakhir.txt"):
    try:
        with open(path, 'r') as f:
            return int(f.read().strip())
    except:
        return 1

def simpan_hal_terakhir(no_halaman, path="/Environment/information/data/halaman_terakhir.txt"):
    with open(path, 'w') as f:
        f.write(str(no_halaman))

# --- PARAMETER ---
base_url = "https://www.antaranews.com/search?q=dokumentasi"
jumlah_halaman = 100
semua_berita = []
final_excel_path = "/Environment/information/data/dokumentasi.xlsx"
temp_excel_path = "/Environment/information/data/dokumentasi_temp.xlsx"

# Load data lama jika ada
if os.path.exists(temp_excel_path):
    df_existing = pd.read_excel(temp_excel_path)
    semua_berita = df_existing.to_dict(orient="records")
    print(f"📁 Memuat data sebelumnya: {len(semua_berita)} berita")
else:
    print("🆕 Memulai scraping dari awal")

start_page = baca_hal_terakhir()
save_interval = 500

# --- SCRAPING LOOP ---
for page in range(start_page, jumlah_halaman + 1):
    url = build_page_url(base_url, page)
    print(f"🔎 Scraping halaman {page} - {url}")

    try:
        daftar_berita = get_list_berita(url)
        if not daftar_berita:
            print("⚠️ Tidak ditemukan berita di halaman ini, hentikan scraping.")
            break

        for b in tqdm(daftar_berita, desc=f"📄 Halaman {page}", unit="berita"):
            isi = scrape_isi_berita(b['link'])
            semua_berita.append({
                "judul": b['judul'],
                "link": b['link'],
                "isi": isi
            })

            # Simpan progres temp
            pd.DataFrame(semua_berita).to_excel(temp_excel_path, index=False)
            time.sleep(random.uniform(1, 2))

        # Simpan progres halaman
        simpan_hal_terakhir(page)

        # Simpan ke file final tiap 500 halaman
        if page % save_interval == 0:
            pd.DataFrame(semua_berita).to_excel(final_excel_path, index=False)
            print(f"💾 Auto-save ke file final di halaman {page}")

    except requests.exceptions.ConnectionError as e:
        print(f"🔁 Koneksi putus, menunggu 10 detik dan coba lagi: {e}")
        time.sleep(10)
        continue

# Simpan hasil akhir
pd.DataFrame(semua_berita).to_excel(final_excel_path, index=False)
print("✅ Selesai. Total berita:", len(semua_berita))
