from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UploadResponse(BaseModel):
    """上傳響應模型"""
    task_id: str
    status: str
    message: Optional[str] = None
    created_at: datetime
    preview_url: Optional[str] = None
    id: Optional[int] = None
    model_config = {"from_attributes": True} 