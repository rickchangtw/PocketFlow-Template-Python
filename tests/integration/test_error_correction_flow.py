import pytest
from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient
import os
import tempfile
import json

from src.services.error_correction_service import ErrorCorrectionService
from src.services.error_correction_executor import ErrorCorrectionExecutor
from src.utils.error_handler import setup_error_handlers, ErrorHandler, ErrorType
from src.utils.file_manager import FileManager
from src.core.config import settings
from src.utils.exceptions import VoiceCloneError, FileValidationError, ProcessingError, OptimizationError

# 創建測試用的 FastAPI 應用
app = FastAPI()
setup_error_handlers(app)
client = TestClient(app)

@pytest.fixture
def file_manager():
    return FileManager()

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

class TestErrorCorrectionFlow:
    """測試錯誤修正流程"""
    
    @pytest.mark.asyncio
    async def test_file_upload_correction_flow(self, client, temp_file):
        """測試文件上傳錯誤修正流程"""
        # 創建一個測試路由
        @app.post("/upload")
        async def upload_file(file: UploadFile):
            # 模擬文件大小超限
            file.file.seek(0, os.SEEK_END)
            size = file.file.tell()
            file.file.seek(0)
            
            if size > settings.MAX_FILE_SIZE:
                raise FileValidationError(
                    "File size exceeds limit",
                    context={
                        "file_size": size,
                        "file_path": file.filename
                    }
                )
            return {"message": "File uploaded successfully"}
        
        # 創建一個大文件
        with open(temp_file, "wb") as f:
            f.write(b"x" * (settings.MAX_FILE_SIZE + 1000))
        
        # 上傳文件
        with open(temp_file, "rb") as f:
            response = client.post(
                "/upload",
                files={"file": ("test.wav", f, "audio/wav")}
            )
        
        # 驗證響應
        assert response.status_code in [200, 400]
        data = response.json()
        assert "correction_attempted" in data
        if response.status_code == 200:
            assert "correction_result" in data
            result = data["correction_result"]
            assert result["success"] is True
            assert isinstance(result["applied_fixes"], list)
            assert result["verification_result"]["success"] is True
        # 驗證錯誤歷史與修正歷史
        handler = ErrorHandler()
        error_history = handler.get_error_history()
        assert len(error_history) > 0
        assert error_history[0].error_type in [ErrorType.SYNTAX, ErrorType.RUNTIME, ErrorType.LOGIC, ErrorType.RESOURCE, ErrorType.UNKNOWN]
        assert error_history[0].error_message is not None
        correction_history = handler.get_correction_history()
        assert len(correction_history) > 0
        assert correction_history[0]["success"] is True
        assert len(correction_history[0]["applied_fixes"]) > 0
        assert correction_history[0]["verification_result"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_audio_processing_correction_flow(self, client, temp_file):
        """測試音頻處理錯誤修正流程"""
        # 創建一個測試路由
        @app.post("/process")
        async def process_audio(file: UploadFile):
            # 模擬音頻質量過低
            raise ProcessingError(
                "Audio quality too low",
                context={
                    "audio_quality": settings.MIN_AUDIO_QUALITY - 0.1,
                    "file_path": file.filename
                }
            )
        
        # 上傳文件
        with open(temp_file, "rb") as f:
            response = client.post(
                "/process",
                files={"file": ("test.wav", f, "audio/wav")}
            )
        
        # 驗證響應
        assert response.status_code in [200, 400]
        data = response.json()
        assert "correction_attempted" in data
        if response.status_code == 200:
            assert "correction_result" in data
            result = data["correction_result"]
            assert result["success"] is True
            assert isinstance(result["applied_fixes"], list)
            assert result["verification_result"]["success"] is True
        handler = ErrorHandler()
        error_history = handler.get_error_history()
        assert len(error_history) > 0
        assert error_history[0].error_type in [ErrorType.SYNTAX, ErrorType.RUNTIME, ErrorType.LOGIC, ErrorType.RESOURCE, ErrorType.UNKNOWN]
        assert error_history[0].error_message is not None
        correction_history = handler.get_correction_history()
        assert len(correction_history) > 0
        assert correction_history[0]["success"] is True
        assert len(correction_history[0]["applied_fixes"]) > 0
        assert correction_history[0]["verification_result"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_optimization_correction_flow(self, client):
        """測試優化錯誤修正流程"""
        # 創建一個測試路由
        @app.post("/optimize")
        async def optimize_model(params: dict):
            # 模擬參數錯誤
            raise OptimizationError(
                "Invalid model parameters",
                context={
                    "model_params": params
                }
            )
        
        # 發送請求
        response = client.post(
            "/optimize",
            json={"invalid": "params"}
        )
        
        # 驗證響應
        assert response.status_code in [200, 400]
        data = response.json()
        assert "correction_attempted" in data
        if response.status_code == 200:
            assert "correction_result" in data
            result = data["correction_result"]
            assert result["success"] is True
            assert isinstance(result["applied_fixes"], list)
            assert result["verification_result"]["success"] is True
        handler = ErrorHandler()
        error_history = handler.get_error_history()
        assert len(error_history) > 0
        assert error_history[0].error_type in [ErrorType.SYNTAX, ErrorType.RUNTIME, ErrorType.LOGIC, ErrorType.RESOURCE, ErrorType.UNKNOWN]
        assert error_history[0].error_message is not None
        correction_history = handler.get_correction_history()
        assert len(correction_history) > 0
        assert correction_history[0]["success"] is True
        assert len(correction_history[0]["applied_fixes"]) > 0
        assert correction_history[0]["verification_result"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_system_error_correction_flow(self, client):
        """測試系統錯誤修正流程"""
        # 創建一個測試路由
        @app.get("/system-status")
        async def check_system():
            # 模擬內存使用過高
            raise VoiceCloneError(
                "Memory usage too high",
                context={
                    "memory_usage": settings.MAX_MEMORY_USAGE + 1000
                }
            )
        
        # 發送請求
        response = client.get("/system-status")
        
        # 驗證響應
        assert response.status_code in [200, 400]
        data = response.json()
        assert "correction_attempted" in data
        if response.status_code == 200:
            assert "correction_result" in data
            result = data["correction_result"]
            assert result["success"] is True
            assert isinstance(result["applied_fixes"], list)
            assert result["verification_result"]["success"] is True
        handler = ErrorHandler()
        error_history = handler.get_error_history()
        assert len(error_history) > 0
        assert error_history[0].error_type in [ErrorType.SYNTAX, ErrorType.RUNTIME, ErrorType.LOGIC, ErrorType.RESOURCE, ErrorType.UNKNOWN]
        assert error_history[0].error_message is not None
        correction_history = handler.get_correction_history()
        assert len(correction_history) > 0
        assert correction_history[0]["success"] is True
        assert len(correction_history[0]["applied_fixes"]) > 0
        assert correction_history[0]["verification_result"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_e2e_error_correction_flow(self, client, temp_file):
        """端到端測試案例：上傳檔案、處理音訊、優化模型，並驗證錯誤修正與歷史記錄"""
        # 模擬上傳檔案
        @app.post("/upload")
        async def upload_file(file: UploadFile):
            file.file.seek(0, os.SEEK_END)
            size = file.file.tell()
            file.file.seek(0)
            if size > settings.MAX_FILE_SIZE:
                raise FileValidationError(
                    "File size exceeds limit",
                    context={
                        "file_size": size,
                        "file_path": file.filename
                    }
                )
            return {"message": "File uploaded successfully"}

        # 模擬處理音訊
        @app.post("/process")
        async def process_audio(file: UploadFile):
            raise ProcessingError(
                "Audio quality too low",
                context={
                    "audio_quality": settings.MIN_AUDIO_QUALITY - 0.1,
                    "file_path": file.filename
                }
            )

        # 模擬優化模型
        @app.post("/optimize")
        async def optimize_model(params: dict):
            raise OptimizationError(
                "Invalid model parameters",
                context={
                    "model_params": params
                }
            )

        # 上傳檔案
        with open(temp_file, "wb") as f:
            f.write(b"x" * (settings.MAX_FILE_SIZE + 1000))
        with open(temp_file, "rb") as f:
            upload_response = client.post(
                "/upload",
                files={"file": ("test.wav", f, "audio/wav")}
            )
        assert upload_response.status_code in [200, 400]
        upload_data = upload_response.json()
        assert "correction_attempted" in upload_data
        if upload_response.status_code == 200:
            assert "correction_result" in upload_data
            assert upload_data["correction_result"]["success"] is True

        # 處理音訊
        with open(temp_file, "rb") as f:
            process_response = client.post(
                "/process",
                files={"file": ("test.wav", f, "audio/wav")}
            )
        assert process_response.status_code in [200, 400]
        process_data = process_response.json()
        assert "correction_attempted" in process_data
        if process_response.status_code == 200:
            assert "correction_result" in process_data
            assert process_data["correction_result"]["success"] is True

        # 優化模型
        optimize_response = client.post(
            "/optimize",
            json={"invalid": "params"}
        )
        assert optimize_response.status_code in [200, 400]
        optimize_data = optimize_response.json()
        assert "correction_attempted" in optimize_data
        if optimize_response.status_code == 200:
            assert "correction_result" in optimize_data
            assert optimize_data["correction_result"]["success"] is True

        # 驗證錯誤歷史與修正歷史
        handler = ErrorHandler()
        error_history = handler.get_error_history()
        assert len(error_history) > 0
        assert error_history[0].error_type in [ErrorType.SYNTAX, ErrorType.RUNTIME, ErrorType.LOGIC, ErrorType.RESOURCE, ErrorType.UNKNOWN]
        assert error_history[0].error_message is not None
        correction_history = handler.get_correction_history()
        assert len(correction_history) > 0
        assert correction_history[0]["success"] is True
        assert len(correction_history[0]["applied_fixes"]) > 0
        assert correction_history[0]["verification_result"]["success"] is True 