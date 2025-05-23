from pydantic_settings import BaseSettings
import os
class Settings(BaseSettings):
    PROJECT_NAME: str = "Taleified AI Engine"
    BASE_URL: str = "http://127.0.0.1:8000"
    HOST: str = BASE_URL.split("://")[1].split(":")[0]
    PORT: int = int(BASE_URL.split("://")[1].split(":")[1])
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", False)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PROXY_HEADERS: bool = True
    KEEP_ALIVE_TIMEOUT: int = 5
    STORAGE_PATH: str = "storage"
    
    class Config:
        env_file = ".env"
        
settings = Settings()
