from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from src.models.base import Base

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskBase(BaseModel):
    """Base Pydantic model for Task"""
    user_id: int
    status: Optional[str] = None
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    processing_params: Optional[Dict[str, Any]] = None
    progress: Optional[float] = 0.0
    error_message: Optional[str] = None

class TaskCreate(TaskBase):
    """Pydantic model for creating a Task"""
    pass

class TaskResponse(TaskBase):
    """Pydantic model for Task response"""
    id: int
    task_id: int = Field(..., alias="id")
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class Task(Base):
    """SQLAlchemy model for Task"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String)
    status = Column(String, default=TaskStatus.PENDING)
    parameters = Column(JSON)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    input_file = Column(String, nullable=False)
    output_file = Column(String, nullable=True)
    progress = Column(Float, default=0.0)
    error_message = Column(String, nullable=True)
    processing_params = Column(JSON, nullable=True)

    user = relationship("User", back_populates="tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "input_file": self.input_file,
            "output_file": self.output_file,
            "status": self.status,
            "progress": self.progress,
            "error_message": self.error_message,
            "processing_params": self.processing_params,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
