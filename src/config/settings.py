from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "VoiceClone Optimizer"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # CORS Settings
    ALLOWED_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]
    
    # File Upload Settings
    UPLOAD_DIR: str = "data/raw"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [".wav", ".mp3", ".flac"]
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./voiceclone.db"
    
    # Model Settings
    MODEL_DIR: str = "data/models"
    DEFAULT_MODEL: str = "default_model.pth"
    
    # Processing Settings
    SAMPLE_RATE: int = 16000
    MAX_DURATION: int = 300  # seconds
    BATCH_SIZE: int = 32
    
    # Optimization Settings
    MAX_ITERATIONS: int = 100
    CONVERGENCE_THRESHOLD: float = 0.001
    OPTIMIZATION_TIMEOUT: int = 3600  # seconds
    
    # WebSocket Settings
    WS_PING_INTERVAL: int = 20  # seconds
    WS_PING_TIMEOUT: int = 20  # seconds
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/app.log"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
