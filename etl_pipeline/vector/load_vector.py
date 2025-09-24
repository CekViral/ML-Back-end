import pandas as pd
from typing import List, Tuple
import re
import unicodedata
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import execute_batch
import sys
import os
from dotenv import load_dotenv

tqdm.pandas()

# ===================
# Fungsi Utilitas
# ===================

def clean_text(text: str) -> str:
    """Membersihkan teks deskripsi untuk IR."""
    if not isinstance(text, str):
        return ''
    text = text.lower()
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'^\s*[a-z\s\[\]_-]{2,}:\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'=+', ' ', text)
    text = re.sub(r'[^\w\s.,;:\'\-()"]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_and_clean_data(file_path: str) -> pd.DataFrame:
    """Memuat file Excel dan membersihkan data."""
    print(f"Memuat data dari {file_path}...")
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.lower()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    print("Membersihkan teks deskripsi...")
    df['cleaned_description'] = df['description'].progress_apply(clean_text)
    return df

def encode_texts(texts: List[str], model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2') -> List:
    """Menyandikan teks menjadi vektor embedding."""
    print("Menyandikan teks menjadi vektor...")
    model = SentenceTransformer(model_name, cache_folder='./model_cache')
    vectors = model.encode(texts, show_progress_bar=True, batch_size=32)
    print(f"Dimensi embedding: {model.get_sentence_embedding_dimension()}")
    return vectors.tolist()

def connect_db():
    """Koneksi ke database PostgreSQL (Supabase) menggunakan .env."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        print("✅ Berhasil terhubung ke database Supabase.")
        return conn
    except Exception as e:
        print(f"❌ Gagal koneksi database: {e}")
        sys.exit(1)

def insert_data_to_db(conn, table_name: str, records: List[Tuple], columns: List[str], batch_size: int = 500):
    """Menyisipkan beberapa data ke PostgreSQL dengan proses batch."""
    with conn.cursor() as cursor:
        cols = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        
        print(f"Mengunggah {len(records)} data ke tabel '{table_name}'...")
        execute_batch(cursor, query, records, page_size=batch_size)
        conn.commit()

# ===================
# Fungsi Utama
# ===================

def main():
    """
    Menjalankan pipeline ETL: Load, Clean, Encode, dan Upload.
    """
    # Muat variabel environment dari file .env
    load_dotenv()

    try:
        # Konfigurasi
        FILE_PATH = 'data/fact_news.xlsx' # Menggunakan path relatif
        TABLE_NAME = 'news_data'
        COLUMNS = ['date', 'status', 'title', 'description', 'link', 'imageurl', 'cleaned_description', 'vector']

        # 1. Load dan proses data
        df = load_and_clean_data(FILE_PATH)
        
        # 2. Encode deskripsi menjadi vektor
        df['vector'] = encode_texts(df['cleaned_description'].tolist())

        # 3. Siapkan data untuk diunggah
        records_to_upload = [tuple(row) for row in df[COLUMNS].itertuples(index=False)]

        # 4. Koneksi ke database dan unggah data
        conn = connect_db()
        try:
            insert_data_to_db(conn, TABLE_NAME, records_to_upload, COLUMNS)
            print("🎉 Semua data berhasil dimasukkan ke Supabase.")
        except Exception as e:
            print(f"❌ Gagal saat memasukkan data: {e}")
            conn.rollback() # Batalkan transaksi jika terjadi error
        finally:
            if conn:
                conn.close()
                print("Koneksi database ditutup.")

    except FileNotFoundError:
        print(f"❌ File tidak ditemukan di path: {FILE_PATH}")
    except Exception as e:
        print(f"❌ Terjadi error tak terduga dalam proses: {e}")

if __name__ == "__main__":
    main()