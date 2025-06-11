from typing import Dict, Any, Optional

class VoiceCloneError(Exception):
    """基礎錯誤類"""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

class FileValidationError(VoiceCloneError):
    """文件驗證錯誤"""
    pass

class ProcessingError(VoiceCloneError):
    """處理錯誤"""
    pass

class OptimizationError(VoiceCloneError):
    """優化錯誤"""
    pass

class SystemError(VoiceCloneError):
    """系統錯誤"""
    pass 