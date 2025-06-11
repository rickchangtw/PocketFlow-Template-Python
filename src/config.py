from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 檔案上傳設置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {"wav", "mp3", "ogg"}
    
    # 音訊處理設置
    MIN_AUDIO_QUALITY: float = 0.7
    MAX_AUDIO_DURATION: int = 300  # 秒
    
    # 模型設置
    MODEL_PATH: str = "models/voice_clone"
    BATCH_SIZE: int = 32
    
    class Config:
        env_file = ".env"

settings = Settings() 