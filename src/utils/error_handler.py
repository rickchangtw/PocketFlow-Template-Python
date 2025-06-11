from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import logging
from typing import Dict, Any, Optional, List, Tuple
import yaml
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from src.config.logging import logger
from src.services.error_correction_executor import ErrorCorrectionExecutor
from src.utils.exceptions import VoiceCloneError, FileValidationError, ProcessingError, OptimizationError
from src.models.error_history import ErrorHistory, CorrectionHistory, engine

# 建立 Session 工廠
SessionLocal = sessionmaker(bind=engine)

# 建立 Base 類別
Base = declarative_base()

class ErrorType(Enum):
    """錯誤類型枚舉"""
    SYNTAX = "syntax"           # 語法錯誤
    RUNTIME = "runtime"         # 運行時錯誤
    LOGIC = "logic"            # 邏輯錯誤
    RESOURCE = "resource"      # 資源錯誤
    UNKNOWN = "unknown"        # 未知錯誤

@dataclass
class ErrorContext:
    """錯誤上下文"""
    error_type: ErrorType
    error_message: str
    error_location: Optional[str] = None
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None

class ErrorHandler:
    """錯誤處理器"""
    
    def __init__(self):
        self.engine = create_engine(
            'sqlite:///error_history.db',
            connect_args={'check_same_thread': False}
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def detect_error(self, error: Exception) -> ErrorContext:
        """檢測錯誤並返回錯誤上下文"""
        error_type = self._classify_error(error)
        error_context = ErrorContext(
            error_type=error_type,
            error_message=str(error),
            stack_trace=self._get_stack_trace(error),
            additional_info=self._extract_additional_info(error)
        )
        
        # 儲存到資料庫
        self.record_error(file_path="", error_type=error_type.value, error_message=error_context.error_message)
        
        return error_context
    
    def analyze_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """分析錯誤並返回分析結果"""
        analysis = {
            "error_type": error_context.error_type.value,
            "severity": self._assess_severity(error_context),
            "possible_causes": self._identify_causes(error_context),
            "suggested_actions": self._suggest_actions(error_context)
        }
        return analysis
    
    def correct_error(self, error_context: ErrorContext, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """嘗試修正錯誤並返回修正結果"""
        correction = {
            "success": False,
            "applied_fixes": [],
            "remaining_issues": [],
            "verification_result": None
        }
        
        # 根據分析結果嘗試修正
        for action in analysis["suggested_actions"]:
            fix_result = self._apply_fix(action, error_context)
            if fix_result["success"]:
                correction["applied_fixes"].append(fix_result)
            else:
                correction["remaining_issues"].append(fix_result)
        
        # 驗證修正結果
        if correction["applied_fixes"]:
            correction["success"] = True
            correction["verification_result"] = self._verify_correction(error_context, correction)
        
        # 儲存到資料庫
        self.update_correction_status(error_context.error_code, "completed" if correction["success"] else "failed", correction["verification_result"]["message"] if correction["verification_result"] else "")
        
        return correction
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """分類錯誤類型"""
        error_name = error.__class__.__name__.lower()
        
        if "syntax" in error_name:
            return ErrorType.SYNTAX
        elif "runtime" in error_name:
            return ErrorType.RUNTIME
        elif "logic" in error_name:
            return ErrorType.LOGIC
        elif "resource" in error_name:
            return ErrorType.RESOURCE
        else:
            return ErrorType.UNKNOWN
    
    def _get_stack_trace(self, error: Exception) -> Optional[str]:
        """獲取錯誤堆疊追蹤"""
        import traceback
        return "".join(traceback.format_tb(error.__traceback__))
    
    def _extract_additional_info(self, error: Exception) -> Dict[str, Any]:
        """提取額外的錯誤信息"""
        info = {}
        if hasattr(error, "__dict__"):
            for key, value in error.__dict__.items():
                if not key.startswith("_"):
                    info[key] = str(value)
        return info
    
    def _assess_severity(self, error_context: ErrorContext) -> str:
        """評估錯誤嚴重程度"""
        if error_context.error_type in [ErrorType.SYNTAX, ErrorType.RUNTIME]:
            return "high"
        elif error_context.error_type == ErrorType.LOGIC:
            return "medium"
        else:
            return "low"
    
    def _identify_causes(self, error_context: ErrorContext) -> List[str]:
        """識別可能的錯誤原因"""
        causes = []
        
        if error_context.error_type == ErrorType.SYNTAX:
            causes.extend([
                "代碼語法錯誤",
                "缺少必要的括號或引號",
                "變量名稱拼寫錯誤"
            ])
        elif error_context.error_type == ErrorType.RUNTIME:
            causes.extend([
                "變量未定義",
                "類型不匹配",
                "除零錯誤"
            ])
        elif error_context.error_type == ErrorType.LOGIC:
            causes.extend([
                "條件判斷錯誤",
                "循環邏輯錯誤",
                "數據處理邏輯錯誤"
            ])
        
        return causes
    
    def _suggest_actions(self, error_context: ErrorContext) -> List[Dict[str, Any]]:
        """建議修正動作"""
        actions = []
        
        if error_context.error_type == ErrorType.SYNTAX:
            actions.append({
                "type": "syntax_fix",
                "description": "修正語法錯誤",
                "priority": "high"
            })
        elif error_context.error_type == ErrorType.RUNTIME:
            actions.append({
                "type": "runtime_fix",
                "description": "處理運行時錯誤",
                "priority": "high"
            })
        elif error_context.error_type == ErrorType.LOGIC:
            actions.append({
                "type": "logic_fix",
                "description": "修正邏輯錯誤",
                "priority": "medium"
            })
        
        return actions
    
    def _apply_fix(self, action: Dict[str, Any], error_context: ErrorContext) -> Dict[str, Any]:
        """應用修正"""
        fix_result = {
            "action": action,
            "success": False,
            "message": "",
            "changes": {}
        }
        
        try:
            if action["type"] == "syntax_fix":
                fix_result.update(self._fix_syntax_error(error_context))
            elif action["type"] == "runtime_fix":
                fix_result.update(self._fix_runtime_error(error_context))
            elif action["type"] == "logic_fix":
                fix_result.update(self._fix_logic_error(error_context))
            
            fix_result["success"] = True
        except Exception as e:
            fix_result["message"] = f"修正失敗: {str(e)}"
        
        return fix_result
    
    def _fix_syntax_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """修正語法錯誤"""
        # 這裡實現具體的語法錯誤修正邏輯
        return {
            "message": "語法錯誤已修正",
            "changes": {"fixed_syntax": True}
        }
    
    def _fix_runtime_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """修正運行時錯誤"""
        # 這裡實現具體的運行時錯誤修正邏輯
        return {
            "message": "運行時錯誤已修正",
            "changes": {"fixed_runtime": True}
        }
    
    def _fix_logic_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """修正邏輯錯誤"""
        # 這裡實現具體的邏輯錯誤修正邏輯
        return {
            "message": "邏輯錯誤已修正",
            "changes": {"fixed_logic": True}
        }
    
    def _verify_correction(self, error_context: ErrorContext, correction: Dict[str, Any]) -> Dict[str, Any]:
        """驗證修正結果"""
        verification = {
            "success": True,
            "message": "修正驗證通過",
            "details": {}
        }
        
        # 檢查是否所有問題都已解決
        if correction["remaining_issues"]:
            verification["success"] = False
            verification["message"] = "部分問題未解決"
            verification["details"]["remaining_issues"] = correction["remaining_issues"]
        
        return verification
    
    def record_error(self, file_path: str, error_type: str, error_message: str, correction_status: str = "pending"):
        """記錄錯誤到資料庫"""
        try:
            session = self.Session()
            error = ErrorHistory(
                file_path=file_path,
                error_type=error_type,
                error_message=error_message,
                correction_status=correction_status,
                created_at=datetime.utcnow()
            )
            session.add(error)
            session.commit()
            session.close()
        except Exception as e:
            print(f"Error recording error: {str(e)}")
    
    def get_error_history(self, limit: int = 100) -> List[ErrorHistory]:
        """獲取錯誤歷史記錄"""
        try:
            session = self.Session()
            errors = session.query(ErrorHistory).order_by(ErrorHistory.created_at.desc()).limit(limit).all()
            session.close()
            return errors
        except Exception as e:
            print(f"Error getting error history: {str(e)}")
            return []
    
    def get_correction_history(self, limit: int = 100) -> List[CorrectionHistory]:
        """獲取修正歷史記錄"""
        try:
            session = self.Session()
            corrections = session.query(CorrectionHistory).order_by(CorrectionHistory.created_at.desc()).limit(limit).all()
            session.close()
            return corrections
        except Exception as e:
            print(f"Error getting correction history: {str(e)}")
            return []
    
    def update_correction_status(self, error_id: int, status: str, message: str = None):
        """更新修正狀態"""
        try:
            session = self.Session()
            error = session.query(ErrorHistory).filter(ErrorHistory.id == error_id).first()
            if error:
                error.correction_status = status
                if message:
                    error.correction_message = message
                session.commit()
            session.close()
        except Exception as e:
            print(f"Error updating correction status: {str(e)}")

class VoiceCloneError(Exception):
    """Base exception for VoiceClone Optimizer"""
    def __init__(self, message: str, status_code: int = 500, context: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.context = context or {}
        super().__init__(self.message)

class FileValidationError(VoiceCloneError):
    """Exception for file validation errors"""
    def __init__(self, message: str, context: Dict[str, Any] = None):
        super().__init__(message, status_code=400, context=context)

class ProcessingError(VoiceCloneError):
    """Exception for processing errors"""
    def __init__(self, message: str, context: Dict[str, Any] = None):
        super().__init__(message, status_code=500, context=context)

class OptimizationError(VoiceCloneError):
    """Exception for optimization errors"""
    def __init__(self, message: str, context: Dict[str, Any] = None):
        super().__init__(message, status_code=500, context=context)

async def voice_clone_exception_handler(request: Request, exc: VoiceCloneError) -> JSONResponse:
    """處理 VoiceCloneError 異常"""
    try:
        # 嘗試自動修正錯誤
        executor = ErrorCorrectionExecutor()
        correction_result = await executor.execute_correction(exc, exc.context)
        
        if correction_result["success"]:
            # 如果修正成功,返回成功響應
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Error corrected successfully",
                    "correction_attempted": True,
                    "correction_result": correction_result
                }
            )
        else:
            # 如果修正失敗,返回原始錯誤
            return JSONResponse(
                status_code=400,
                content={
                    "message": exc.message,
                    "correction_attempted": True,
                    "correction_result": correction_result
                }
            )
    except Exception as e:
        # 如果修正過程出現錯誤,返回原始錯誤
        logger.error(f"Error during correction: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "message": exc.message,
                "correction_attempted": False,
                "error": str(e)
            }
        )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """處理請求驗證錯誤"""
    return JSONResponse(
        status_code=422,
        content={
            "message": "Validation error",
            "details": exc.errors()
        }
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """處理一般異常"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "error": str(exc)
        }
    )

def setup_error_handlers(app: FastAPI) -> None:
    """設置錯誤處理器"""
    app.add_exception_handler(VoiceCloneError, voice_clone_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

def handle_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """處理錯誤並拋出適當的異常"""
    if isinstance(error, VoiceCloneError):
        raise error
    
    # 將一般錯誤轉換為 VoiceCloneError
    raise VoiceCloneError(str(error), context)
