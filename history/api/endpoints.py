from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import User, HistoryItem, Response
from core.auth import get_current_user
from core.database import get_db
from core.item import get_last_history_for_user, delete_history_item  # pastikan ini diimpor

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/me", response_model=list[HistoryItem])
def list_user_history(
    conn=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the last 5 history records for the logged-in user.
    """
    try:
        rows = get_last_history_for_user(conn, current_user.id, limit=5)
        return rows
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Gagal mengambil riwayat. Silakan coba lagi nanti."
        )


@router.delete("/me/{history_id}", response_model=Response)
def delete_user_history(
    history_id: str,
    conn=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific history record for the logged-in user.
    """
    try:
        deleted = delete_history_item(conn, current_user.id, history_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data riwayat tidak ditemukan atau bukan milik Anda."
            )
        return {"detail": "Riwayat berhasil dihapus."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Gagal menghapus riwayat. Silakan coba lagi nanti."
        )
