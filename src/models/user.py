from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship

from src.models.base import Base

class User(Base):
    """User model for authentication and user management"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User preferences
    preferences = Column(JSON, nullable=True)
    
    # API key for programmatic access
    api_key = Column(String, unique=True, nullable=True)
    
    tasks = relationship("Task", back_populates="user")
    
    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        is_superuser: bool = False,
        preferences: Optional[Dict[str, Any]] = None
    ):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.is_superuser = is_superuser
        self.preferences = preferences or {}
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences"""
        current_prefs = self.preferences or {}
        current_prefs.update(preferences)
        self.preferences = current_prefs
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "preferences": self.preferences,
            "api_key": self.api_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create user from dictionary"""
        user = cls(
            username=data["username"],
            email=data["email"],
            hashed_password=data["hashed_password"],
            is_superuser=data.get("is_superuser", False),
            preferences=data.get("preferences")
        )
        
        if "id" in data:
            user.id = data["id"]
        
        if "is_active" in data:
            user.is_active = data["is_active"]
        
        if "api_key" in data:
            user.api_key = data["api_key"]
        
        return user
