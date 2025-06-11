from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import Base, engine

class ErrorHistory(Base):
    """錯誤歷史記錄"""
    __tablename__ = "error_history"

    id = Column(Integer, primary_key=True)
    file_path = Column(String)
    error_type = Column(String, nullable=False)
    error_message = Column(String, nullable=False)
    correction_status = Column(String)
    error_location = Column(String)
    error_code = Column(String)
    stack_trace = Column(String)
    additional_info = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯到修正歷史
    corrections = relationship("CorrectionHistory", back_populates="error")

class CorrectionHistory(Base):
    """修正歷史記錄"""
    __tablename__ = "correction_history"

    id = Column(Integer, primary_key=True)
    error_id = Column(Integer, ForeignKey("error_history.id"))
    success = Column(Integer, nullable=False)  # 0 或 1
    applied_fixes = Column(JSON)
    remaining_issues = Column(JSON)
    verification_result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯到錯誤歷史
    error = relationship("ErrorHistory", back_populates="corrections")

# 建立所有表格
def init_db():
    Base.metadata.create_all(bind=engine) 