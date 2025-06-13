def get_last_history_for_user(conn, user_id: str, limit: int = 5):
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT history_id, original_input, processed_text, predicted_label,
                   prob_hoax, prob_fakta, final_label_threshold, inference_time_ms, created_at
            FROM history
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows  # bisa [] jika belum ada riwayat
    except Exception as e:
        raise RuntimeError("Gagal mengambil data riwayat dari database.") from e



def delete_history_item(conn, user_id: str, history_id: str) -> bool:
    """
    Delete a history record if it belongs to the user.
    Returns True if deleted, False if not found.
    """
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM history WHERE history_id = %s AND user_id = %s RETURNING history_id;",
        (history_id, user_id),
    )
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    return bool(result)