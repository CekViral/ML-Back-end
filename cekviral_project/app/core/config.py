# app/core/config.py
from pydantic_settings import BaseSettings
import os

# Khusus untuk lokal saja
if os.getenv("ENV", "local") == "local":
    from dotenv import load_dotenv
    load_dotenv()

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str

    PROJECT_NAME: str = "CekViral API"
    PROJECT_VERSION: str = "0.1.0"
    MODEL_PATH: str = "models/"
    YDL_TEMP_DIR: str = "temp_downloads/"
    GCP_CREDENTIALS_PATH: str | None = None

settings = Settings()