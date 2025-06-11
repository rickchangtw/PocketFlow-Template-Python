from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # 基本設置
    PROJECT_NAME: str = "Voice Clone Optimizer"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    BASE_URL: str = "http://localhost:8000"
    
    # 文件設置
    UPLOAD_DIR: str = "uploads"
    PREVIEW_DIR: str = "previews"
    DOWNLOAD_DIR: str = "downloads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 日誌設置
    LOG_FILE: str = "logs/app.log"
    LOG_FORMAT: str = "%(asctime)s %(levelname)s %(name)s %(message)s"
    LOG_LEVEL: str = "INFO"
    
    # 數據庫設置
    DATABASE_URL: str = "sqlite:///./voice_clone.db"
    
    # 安全設置
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # 處理設置
    DEFAULT_QUALITY_LEVEL: str = "medium"
    DEFAULT_OUTPUT_FORMAT: str = "wav"
    MAX_CONCURRENT_TASKS: int = 5
    MIN_AUDIO_QUALITY: float = 0.5  # 新增，音質下限
    MAX_MEMORY_USAGE: int = 2 * 1024 * 1024 * 1024  # 新增，2GB
    
    # 清理設置
    CLEANUP_INTERVAL_HOURS: int = 24
    MAX_FILE_AGE_HOURS: int = 24
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# 確保必要的目錄存在
for directory in [settings.UPLOAD_DIR, settings.PREVIEW_DIR, settings.DOWNLOAD_DIR, os.path.dirname(settings.LOG_FILE)]:
    os.makedirs(directory, exist_ok=True) 