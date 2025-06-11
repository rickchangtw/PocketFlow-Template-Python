from typing import Dict, Any
from src.utils.exceptions import VoiceCloneError, FileValidationError, ProcessingError, OptimizationError, SystemError
from src.config.logging import logger

class ErrorCorrectionService:
    """錯誤修正服務"""
    
    def __init__(self):
        self.correction_strategies = {
            FileValidationError: self._handle_file_validation_error,
            ProcessingError: self._handle_processing_error,
            OptimizationError: self._handle_optimization_error,
            VoiceCloneError: self._handle_system_error,
        }
    
    async def correct_error(self, error: VoiceCloneError, context: Dict[str, Any]) -> Dict[str, Any]:
        """嘗試修正錯誤"""
        try:
            error_type = self._get_error_type(error)
            if error_type in self.correction_strategies:
                return await self.correction_strategies[error_type](error, context)
            else:
                logger.warning(f"No correction strategy for error type: {error_type}")
                return {"success": False, "message": "No correction strategy available"}
        except Exception as e:
            logger.error(f"Error during correction: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _get_error_type(self, error: VoiceCloneError) -> type:
        """獲取錯誤類型"""
        for error_type in self.correction_strategies.keys():
            if isinstance(error, error_type):
                return error_type
        return type(error)
    
    async def _handle_file_validation_error(self, error: FileValidationError, context: Dict[str, Any]) -> Dict[str, Any]:
        """處理文件驗證錯誤"""
        try:
            # 檢查文件大小
            if "file_size" in context and context["file_size"] > 10 * 1024 * 1024:  # 10MB
                return {
                    "success": True,
                    "action": "compress_file",
                    "parameters": {
                        "target_size": 10 * 1024 * 1024
                    }
                }
            
            # 檢查文件格式
            if "file_extension" in context and context["file_extension"] not in [".wav", ".mp3"]:
                return {
                    "success": True,
                    "action": "convert_format",
                    "parameters": {
                        "target_format": ".wav"
                    }
                }
            
            return {"success": False, "message": "No applicable correction strategy"}
        except Exception as e:
            logger.error(f"Error handling file validation error: {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def _handle_processing_error(self, error: ProcessingError, context: Dict[str, Any]) -> Dict[str, Any]:
        """處理處理錯誤"""
        try:
            # 檢查音頻質量
            if "audio_quality" in context and context["audio_quality"] < 0.8:
                return {
                    "success": True,
                    "action": "enhance_audio",
                    "parameters": {
                        "target_quality": 0.8
                    }
                }
            
            # 檢查採樣率
            if "sample_rate" in context and context["sample_rate"] != 44100:
                return {
                    "success": True,
                    "action": "resample_audio",
                    "parameters": {
                        "target_rate": 44100
                    }
                }
            
            return {"success": False, "message": "No applicable correction strategy"}
        except Exception as e:
            logger.error(f"Error handling processing error: {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def _handle_optimization_error(self, error: OptimizationError, context: Dict[str, Any]) -> Dict[str, Any]:
        """處理優化錯誤"""
        try:
            # 檢查模型參數
            if "model_params" in context:
                return {
                    "success": True,
                    "action": "adjust_parameters",
                    "parameters": {
                        "target_params": {
                            "learning_rate": 0.001,
                            "batch_size": 32
                        }
                    }
                }
            
            return {"success": False, "message": "No applicable correction strategy"}
        except Exception as e:
            logger.error(f"Error handling optimization error: {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def _handle_system_error(self, error: VoiceCloneError, context: Dict[str, Any]) -> Dict[str, Any]:
        """處理系統錯誤"""
        try:
            # 檢查內存使用
            if "resource_usage" in context and context["resource_usage"].get("memory_usage", 0) > 1024 * 1024 * 1024:  # 1GB
                return {
                    "success": True,
                    "action": "cleanup_resources",
                    "parameters": {
                        "target_memory": 512 * 1024 * 1024  # 512MB
                    }
                }
            
            return {"success": False, "message": "No applicable correction strategy"}
        except Exception as e:
            logger.error(f"Error handling system error: {str(e)}")
            return {"success": False, "message": str(e)} 