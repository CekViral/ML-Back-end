from core.config import model
from core.embedding import embed_query


def get_label_threshold(conn, history_id: str) -> str:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT final_label_threshold 
        FROM history 
        WHERE history_id = %s
    """, (history_id,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None


def search_docs_for_rag(conn, query_vector, top_k=5):
    cursor = conn.cursor()
    vector_str = "[" + ",".join(map(str, query_vector)) + "]"
    cursor.execute(
        """
        SELECT status, title, description 
        FROM news
        ORDER BY vector <#> %s::vector
        LIMIT %s;
        """,
        (vector_str, top_k),
    )
    results = cursor.fetchall()
    cursor.close()
    return results


def search_docs_for_rekomendasi(conn, query_vector, top_k=8):
    cursor = conn.cursor()
    vector_str = "[" + ",".join(map(str, query_vector)) + "]"
    cursor.execute("""
        SELECT news_id, title, link, imageurl
        FROM news
        ORDER BY vector <#> %s::vector
        LIMIT %s
    """, (vector_str, top_k))
    results = cursor.fetchall()  # list of tuples (news_id, title, link, imageurl)
    cursor.close()
    return results
    

def get_latest_recommendations_for_user(conn, user_id: str, limit: int = 8):
    """
    Mengambil hingga `limit` rekomendasi terbaru (recom_id, title, link, imageurl)
    DARI session (history) terakhir user.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.recom_id, n.title, n.link, n.imageurl
        FROM recommendations r
        JOIN news n ON r.news_id = n.news_id
        WHERE r.history_id = (
            SELECT history_id
            FROM history
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        )
        ORDER BY r.created_at DESC
        LIMIT %s;
    """, (user_id, limit))
    results = cursor.fetchall()
    cursor.close()
    return results


def generate_answer(context: str, question: str, label_threshold: str) -> str:
    prompt = f"""
Berikut adalah informasi relevan:
{context}

Dan berikut adalah label akhir hasil prediksi:
{label_threshold.upper()}

Jadi Anda adalah seorang ahli yang diminta untuk menjelaskan apakah input dari user di bawah ini 
adalah konten asli atau hoax berdasarkan informasi yang tertera pada {context} dan {label_threshold.upper()}:
{question}
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return "Terjadi error saat memproses jawaban dari Gemini API."

