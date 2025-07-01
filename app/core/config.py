from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: Optional[str] = os.getenv("APP_NAME", "Test App")
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = APP_NAME+"API"
    VERSION: str = "1.0.0"
    API_KEY: Optional[str] = os.getenv("API_KEY")
    SEGMIND_API_KEY: Optional[str] = os.getenv("SEGMIND_API_KEY")
    SEGMIND_API_URL: str = "https://api.segmind.com/v1/faceswap-comic"
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    UPLOAD_DIR: str = "storage/uploads"
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 