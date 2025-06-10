from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from pydantic import BaseModel
from src.models.base import Base

class TaskBase(BaseModel):
    """Base Pydantic model for Task"""
    user_id: str
    status: str = "pending"
    input_file: str
    output_file: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    total_steps: int = 1
    current_step: int = 0
    progress: int = 0
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

class TaskCreate(TaskBase):
    """Pydantic model for creating a Task"""
    pass

class TaskResponse(TaskBase):
    """Pydantic model for Task response"""
    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Task(Base):
    """SQLAlchemy model for Task"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    input_file = Column(String, nullable=False)
    output_file = Column(String, nullable=True)
    parameters = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    total_steps = Column(Integer, default=1)
    current_step = Column(Integer, default=0)
    progress = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    error_details = Column(JSON, nullable=True)
