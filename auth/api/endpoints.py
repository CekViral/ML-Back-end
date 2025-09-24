from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from core.database import connect_db, create_user, get_user_by_email, update_user_password, get_user_by_id, update_user_name
from core.auth_utils import create_access_token, verify_password, get_hash_password
from datetime import timedelta
from datetime import datetime
from models.schemas import UserRegister, LoginRequest, ChangePasswordRequest, LoginResponse
import logging
import traceback


router = APIRouter()


@router.post("/signup")
def signup(user: UserRegister):
    try:
        if get_user_by_email(user.email):
            raise HTTPException(status_code=400, detail="Email sudah terdaftar")

        hashed_password = get_hash_password(user.password)
        create_user(user.name, user.email, hashed_password)
        return {"message": "Pendaftaran pengguna berhasil"}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal mendaftarkan pengguna: {str(e)}")




@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, password FROM "users" WHERE email = %s', (request.email,))
        user = cursor.fetchone()
        conn.close()

        if not user or not verify_password(request.password, user["password"]):
            raise HTTPException(status_code=401, detail="Email atau kata sandi tidak valid")

        access_token = create_access_token(
            data={"sub": str(user["id"])},
            expires_delta=timedelta(minutes=60)
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
            }
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal melakukan login: {str(e)}")



@router.put("/change-name")
def change_name(
    new_name: str,
    user_id: str = Header(..., alias="X-User-Id")  # user_id dikirim dari frontend via header
):
    try:
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")

        update_user_name(user_id, new_name)

        return {"message": "Nama berhasil diperbarui"}
    
    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Terjadi kesalahan saat memperbarui nama pengguna")




@router.post("/change-password")
def change_password(request: ChangePasswordRequest):
    try:
        user = get_user_by_email(request.email)
        if not user or not verify_password(request.old_password, user["password"]):
            raise HTTPException(status_code=401, detail="Kata sandi lama tidak sesuai atau pengguna tidak ditemukan")

        new_hashed_password = get_hash_password(request.new_password)
        update_user_password(request.email, new_hashed_password)
        return {"message": "Kata sandi berhasil diperbarui"}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui kata sandi: {str(e)}")