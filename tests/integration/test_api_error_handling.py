import pytest
from fastapi.testclient import TestClient
from src.main import app
import time

client = TestClient(app)

def test_invalid_file_type():
    # 測試上傳無效的檔案類型
    invalid_bytes = b"invalid file content"
    files = {"file": ("test.txt", invalid_bytes, "text/plain")}
    
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "file type" in data["error"].lower()

def test_file_too_large():
    # 測試上傳過大的檔案
    large_bytes = b"0" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
    files = {"file": ("large.wav", large_bytes, "audio/wav")}
    
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "file size" in data["error"].lower()

def test_task_not_found():
    # 測試查詢不存在的任務
    response = client.get("/api/tasks/999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()

def test_cancel_nonexistent_task():
    # 測試取消不存在的任務
    response = client.post("/api/tasks/999/cancel")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "not found" in data["error"].lower()

def test_cancel_completed_task():
    # 準備測試檔案
    wav_bytes = b"RIFF....WAVEfmt "
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}
    
    # 上傳檔案
    upload_response = client.post("/api/upload", files=files)
    assert upload_response.status_code == 200
    task = upload_response.json()
    
    # 等待任務完成（加入超時機制）
    max_wait_time = 5  # 最多等待5秒
    start_time = time.time()
    
    while True:
        if time.time() - start_time > max_wait_time:
            pytest.fail("等待任務完成超時")
            
        response = client.get(f"/api/tasks/{task['id']}")
        if response.json()["status"] == "completed":
            break
        time.sleep(0.1)
    
    # 嘗試取消已完成的任務
    response = client.post(f"/api/tasks/{task['id']}/cancel")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "already completed" in data["error"].lower()

def test_invalid_processing_params():
    # 測試無效的處理參數
    wav_bytes = b"RIFF....WAVEfmt "
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}
    params = {
        "noise_reduction": -1.0,  # 無效值
        "quality_level": "invalid",
        "output_format": "invalid"
    }
    
    response = client.post("/api/upload", files=files, json=params)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data 