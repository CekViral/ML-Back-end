from fastapi import Request
from typing import Optional
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

# Load .env jika belum dilakukan sebelumnya
load_dotenv()

# Ambil dari environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # default HS256 kalau tidak ada

async def get_current_user(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # hapus 'Bearer '
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")  # misal 'sub' menyimpan user_id
        return user_id
    except JWTError:
        return None