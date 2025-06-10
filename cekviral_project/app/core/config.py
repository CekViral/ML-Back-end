# cekviral_project/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CekViral API"
    PROJECT_VERSION: str = "0.1.0"
    MODEL_PATH: str = "models/"
    YDL_TEMP_DIR: str = "temp_downloads/"
    GCP_CREDENTIALS_PATH: str | None = None # Path ke file kredensial GCP

    # Variabel untuk kredensial Supabase
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()