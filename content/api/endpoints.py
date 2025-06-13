from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import RagRequest, User
from core.auth import get_current_user
from core.database import get_db
from core.embedding import embed_query
from core.rag_utils import (    
    search_docs_for_rag,
    search_docs_for_rekomendasi,
    generate_answer,
    get_latest_recommendations_for_user,
)

router = APIRouter()


@router.post("/inference/rag")
def generate_teks(
    input: RagRequest,
    conn=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        query_vec = embed_query(input.processed_text)
        docs = search_docs_for_rag(conn, query_vec, top_k=5)
        context = "\n\n".join([f"[{status}] {title}\n{desc}" for status, title, desc in docs])
        answer = generate_answer(context, input.processed_text, input.final_label_threshold)
        return {"jawaban": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inference/{history_id}/recommendations")
def create_recommendations(
    history_id: str,
    conn=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT processed_text FROM history WHERE history_id = %s AND user_id = %s",
            (history_id, current_user.id),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History not found")

        processed_teks = row["processed_text"]
        query_vec = embed_query(processed_teks)
        docs = search_docs_for_rekomendasi(conn, query_vec, top_k=8)

        recommendations = []
        for news_id, title, link, imageurl in docs:
            cursor.execute(
                """
                INSERT INTO recommendations (history_id, news_id, created_at)
                VALUES (%s, %s, now())
                RETURNING recom_id
                """,
                (history_id, news_id),
            )
            recom_id = cursor.fetchone()[0]
            recommendations.append({
                "recom_id": recom_id,
                "title": title,
                "link": link,
                "imageurl": imageurl,
            })
        conn.commit()
        cursor.close()
        return {"rekomendasi": recommendations}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/me/recommendations")
def ambil_rekomendasi(
    conn=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        rekom_data = get_latest_recommendations_for_user(conn, current_user.id)
        rekomendasi = [
            {
                "recom_id": recom_id,
                "title": title,
                "link": link,
                "imageurl": imageurl
            }
            for recom_id, title, link, imageurl in rekom_data
        ]
        return {"rekomendasi": rekomendasi}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))