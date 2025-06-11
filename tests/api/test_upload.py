import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models.task import TaskResponse, TaskStatus
from src.models.upload import UploadResponse
from src.core.config import settings
import os
import json

client = TestClient(app)

@pytest.fixture
def test_file():
    filename = 'test_audio.wav'
    # 建立測試檔案
    with open(filename, 'wb') as f:
        f.write(b'RIFF....WAVEfmt ')  # 寫入簡單 wav 標頭
    yield filename
    # 測試結束後刪除
    if os.path.exists(filename):
        os.remove(filename)

def test_upload_file_preview(test_file):
    """測試文件預覽功能"""
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/upload/preview",
            files={"file": ("test_audio.wav", f, "audio/wav")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "preview_url" in data
    assert data["preview_url"].startswith("http")

def test_upload_file_with_parameters(test_file):
    """測試帶參數的文件上傳"""
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test_audio.wav", f, "audio/wav")},
            data={
                "parameters": json.dumps({
                    "pitch_shift": 2,
                    "tempo_adjust": 1.2
                })
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert data["status"] == TaskStatus.PENDING

def test_batch_download():
    """測試批次下載功能"""
    # 創建測試任務
    task_ids = ["task1", "task2", "task3"]
    response = client.post(
        "/api/upload/batch-download",
        json={"task_ids": task_ids}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data
    assert data["download_url"].startswith("http")

def test_error_handling():
    """測試錯誤處理"""
    # 測試無效文件類型
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", b"invalid content", "text/plain")}
    )
    assert response.status_code == 400
    
    # 測試文件大小超限
    large_file = b"x" * (settings.MAX_FILE_SIZE + 1)
    response = client.post(
        "/api/upload",
        files={"file": ("large.wav", large_file, "audio/wav")}
    )
    assert response.status_code == 400
    
    # 測試無效的處理參數
    with open("test_audio.wav", "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test_audio.wav", f, "audio/wav")},
            data={"parameters": "invalid json"}
        )
    assert response.status_code == 400

def test_upload_with_invalid_parameters(test_file):
    """測試無效的處理參數"""
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test_audio.wav", f, "audio/wav")},
            data={
                "parameters": json.dumps({
                    "pitch_shift": "invalid",  # 應該是數字
                    "tempo_adjust": -1  # 應該是正數
                })
            }
        )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data 