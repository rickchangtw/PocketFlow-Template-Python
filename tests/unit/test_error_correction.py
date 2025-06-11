import pytest
from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient
import os
import tempfile

from src.services.error_correction_service import ErrorCorrectionService
from src.services.error_correction_executor import ErrorCorrectionExecutor
from src.utils.error_handler import (
    VoiceCloneError,
    FileValidationError,
    ProcessingError,
    OptimizationError
)
from src.core.config import settings

@pytest.fixture
def test_app():
    app = FastAPI()
    @app.get("/test-error")
    async def test_error():
        raise FileValidationError(
            "File size exceeds limit",
            context={
                "file_size": settings.MAX_FILE_SIZE + 1000,
                "file_path": "test.wav"
            }
        )
    return app

@pytest.fixture
def test_client(test_app):
    return TestClient(test_app)

@pytest.fixture
def error_correction_service():
    return ErrorCorrectionService()

@pytest.fixture
def error_correction_executor():
    return ErrorCorrectionExecutor()

@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
    yield f.name
    os.unlink(f.name)

class TestErrorCorrectionService:
    """測試錯誤修正服務"""
    
    @pytest.mark.asyncio
    async def test_file_validation_error_correction(self, error_correction_service, temp_file):
        """測試文件驗證錯誤修正"""
        # 創建文件大小超限錯誤
        error = FileValidationError(
            "File size exceeds limit",
            context={
                "file_size": settings.MAX_FILE_SIZE + 1000,
                "file_path": temp_file
            }
        )
        
        result = await error_correction_service.correct_error(error, error.context)
        assert result["success"] is True
        assert result["action"] == "compress_file"
        assert "target_size" in result["parameters"]
    
    @pytest.mark.asyncio
    async def test_processing_error_correction(self, error_correction_service, temp_file):
        """測試處理錯誤修正"""
        # 創建音頻質量過低錯誤
        error = ProcessingError(
            "Audio quality too low",
            context={
                "audio_quality": settings.MIN_AUDIO_QUALITY - 0.1,
                "file_path": temp_file
            }
        )
        
        result = await error_correction_service.correct_error(error, error.context)
        assert result["success"] is True
        assert result["action"] == "enhance_audio"
        assert "target_quality" in result["parameters"]
    
    @pytest.mark.asyncio
    async def test_optimization_error_correction(self, error_correction_service):
        """測試優化錯誤修正"""
        # 創建模型參數錯誤
        error = OptimizationError(
            "Invalid model parameters",
            context={
                "model_params": {"invalid": "params"}
            }
        )
        
        result = await error_correction_service.correct_error(error, error.context)
        assert result["success"] is True
        assert result["action"] == "adjust_parameters"
        assert "target_params" in result["parameters"]
    
    @pytest.mark.asyncio
    async def test_system_error_correction(self, error_correction_service):
        """測試系統錯誤修正"""
        # 創建內存使用過高錯誤
        error = VoiceCloneError(
            "Memory usage too high",
            context={
                "resource_usage": {
                    "memory_usage": settings.MAX_MEMORY_USAGE + 1000
                }
            }
        )
        
        result = await error_correction_service.correct_error(error, error.context)
        assert result["success"] is True
        assert result["action"] == "cleanup_resources"
        assert "target_memory" in result["parameters"]

class TestErrorCorrectionExecutor:
    """測試錯誤修正執行器"""
    
    @pytest.mark.asyncio
    async def test_compress_file_execution(self, error_correction_executor, temp_file):
        """測試文件壓縮執行"""
        error = FileValidationError(
            "File size exceeds limit",
            context={
                "file_size": settings.MAX_FILE_SIZE + 1000,
                "file_path": temp_file
            }
        )
        
        result = await error_correction_executor.execute_correction(error, error.context)
        assert result["success"] is True
        assert "compressed_size" in result["result"]
    
    @pytest.mark.asyncio
    async def test_enhance_audio_execution(self, error_correction_executor, temp_file):
        """測試音頻增強執行"""
        error = ProcessingError(
            "Audio quality too low",
            context={
                "audio_quality": settings.MIN_AUDIO_QUALITY - 0.1,
                "file_path": temp_file
            }
        )
        
        result = await error_correction_executor.execute_correction(error, error.context)
        assert result["success"] is True
        assert "enhanced_quality" in result["result"]
    
    @pytest.mark.asyncio
    async def test_adjust_parameters_execution(self, error_correction_executor):
        """測試參數調整執行"""
        error = OptimizationError(
            "Invalid model parameters",
            context={
                "model_params": {"invalid": "params"}
            }
        )
        
        result = await error_correction_executor.execute_correction(error, error.context)
        assert result["success"] is True
        assert "new_parameters" in result["result"]
    
    @pytest.mark.asyncio
    async def test_cleanup_resources_execution(self, error_correction_executor):
        """測試資源清理執行"""
        error = VoiceCloneError(
            "Memory usage too high",
            context={
                "resource_usage": {
                    "memory_usage": settings.MAX_MEMORY_USAGE + 1000
                }
            }
        )
        
        result = await error_correction_executor.execute_correction(error, error.context)
        assert result["success"] is True
        assert "memory_after_cleanup" in result["result"]

class TestErrorHandlerIntegration:
    """測試錯誤處理器集成"""
    
    @pytest.mark.asyncio
    async def test_error_handler_with_correction(self, test_client):
        """測試錯誤處理器與修正系統的集成"""
        response = test_client.get("/test-error")
        assert response.status_code in [200, 400]  # 200 if corrected, 400 if not
        data = response.json()
        assert "correction_attempted" in data
        if response.status_code == 200:
            assert "correction_result" in data 