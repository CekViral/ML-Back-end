import os
import sys
import psycopg2
import textwrap
import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Muat environment variables dari file .env
load_dotenv()

# ===================
# KONFIGURASI & KREDENSIAL
# ===================
# Mengambil kredensial dari environment variables untuk keamanan
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Nama model dipusatkan di sini agar mudah diganti
EMBEDDING_MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
GENERATIVE_MODEL_NAME = 'models/gemini-1.5-flash-latest'

# Konfigurasi API key Gemini
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY tidak ditemukan. Mohon set di file .env")
    sys.exit(1)
genai.configure(api_key=GEMINI_API_KEY)


# ===================
# Inisialisasi Model (dilakukan sekali saja untuk efisiensi)
# ===================
print("Memuat model embedding...")
embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
print("Model embedding siap.")

print("Memuat model generatif...")
generative_model = genai.GenerativeModel(model_name=GENERATIVE_MODEL_NAME)
print("Model generatif siap.")


# ===================
# Fungsi-Fungsi
# ===================
def connect_db():
    """
    Membuat koneksi ke database PostgreSQL.
    Koneksi akan berhenti jika gagal, dengan pesan error yang jelas.
    :return: Objek koneksi database atau None jika gagal.
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Koneksi ke database berhasil.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error: Gagal terhubung ke database.\nDetail: {e}")
        sys.exit(1) # Keluar dari program jika DB tidak bisa diakses

def embed_query(text: str) -> list:
    """
    Mengubah query teks menjadi vector embedding.
    :param text: Teks input dari user.
    :return: Sebuah list float yang merepresentasikan vector.
    """
    vector = embed_model.encode(text)
    return vector.tolist()

def search_similar_docs(conn, query_vector: list, top_k: int = 6):
    """
    Mencari dokumen yang paling mirip di database berdasarkan vector query.
    :param conn: Objek koneksi database.
    :param query_vector: Vector dari query user.
    :param top_k: Jumlah dokumen teratas yang ingin diambil.
    :return: List of tuples berisi (title, cleaned_description).
    """
    with conn.cursor() as cursor:
        # Menggunakan str() pada list akan menghasilkan format '[1.0, 2.0, ...]'
        # yang kompatibel dengan pgvector
        vector_str = str(query_vector)
        cursor.execute(
            """
            SELECT title, cleaned_description
            FROM news_data
            ORDER BY vector <#> %s::vector
            LIMIT %s;
            """,
            (vector_str, top_k)
        )
        results = cursor.fetchall()
    return results

def generate_answer(context: str, question: str) -> str:
    """
    Menghasilkan jawaban dari model generatif berdasarkan konteks dan pertanyaan.
    :param context: String berisi informasi yang diambil dari database.
    :param question: Pertanyaan asli dari user.
    :return: Jawaban yang dihasilkan oleh model dalam format string.
    """
    prompt = textwrap.dedent(f"""
        Anda adalah seorang ahli pemeriksa fakta yang objektif.
        Berdasarkan informasi relevan di bawah ini, jelaskan apakah input dari user adalah konten asli atau berpotensi hoaks.
        Berikan jawaban yang ringkas, jelas, dan hanya berdasarkan data yang diberikan.

        ---
        Informasi Relevan:
        {context}
        ---
        Pertanyaan User:
        {question}
        ---
        Analisis Anda:
    """)
    try:
        response = generative_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Terjadi error saat memproses jawaban dari Gemini API: {e}")
        return "Maaf, terjadi kendala saat mencoba menghasilkan jawaban."

def rag_pipeline(question: str, conn):
    """
    Menjalankan seluruh pipeline RAG: embed, search, dan generate.
    :param question: Pertanyaan dari user.
    :param conn: Objek koneksi database.
    :return: Jawaban final untuk user.
    """
    print("1. Mengubah pertanyaan menjadi vector...")
    query_vec = embed_query(question)
    
    print("2. Mencari dokumen relevan di database...")
    docs = search_similar_docs(conn, query_vec)
    
    if not docs:
        return "Maaf, tidak ditemukan informasi yang relevan dengan pertanyaan Anda di dalam database kami."
    
    print(f"3. Menemukan {len(docs)} dokumen relevan. Menyiapkan konteks...")
    context = "\n\n".join([f"Judul: {title}\nDeskripsi: {desc}" for title, desc in docs])
    
    print("4. Menghasilkan jawaban berdasarkan konteks...")
    answer = generate_answer(context, question)
    
    return answer

# ===================
# Fungsi Utama untuk Menjalankan Program via CLI
# ===================
def main():
    """
    Fungsi utama untuk menjalankan loop interaktif dengan user.
    """
    conn = connect_db()
    try:
        while True:
            question = input("\nMasukkan pertanyaan (ketik 'exit' untuk keluar): ")
            if question.lower() == "exit":
                print("Terima kasih, sampai jumpa!")
                break
            if not question.strip():
                continue

            answer = rag_pipeline(question, conn)
            print("\nJawaban:")
            print("="*40)
            print(answer)
            print("="*40)
    finally:
        if conn:
            conn.close()
            print("\nKoneksi ke database ditutup.")

if __name__ == "__main__":
    main()