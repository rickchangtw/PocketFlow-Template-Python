import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_preview_file():
    # 先上傳一個檔案
    wav_bytes = b"RIFF....WAVEfmt "  # 模擬的 WAV 檔案內容
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}
    upload_response = client.post("/api/upload", files=files)
    assert upload_response.status_code == 200
    task_id = upload_response.json()["id"]

    # 測試預覽功能
    preview_response = client.get(f"/api/preview/{task_id}")
    assert preview_response.status_code == 200
    assert preview_response.headers["content-type"] == "audio/wav"

def test_preview_nonexistent_file():
    # 測試不存在的檔案
    response = client.get("/api/preview/99999")
    assert response.status_code == 404

def test_preview_uncompleted_task():
    # 先上傳一個檔案
    wav_bytes = b"RIFF....WAVEfmt "
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}
    upload_response = client.post("/api/upload", files=files)
    assert upload_response.status_code == 200
    task_id = upload_response.json()["id"]

    # 立即嘗試預覽（任務應該還在處理中）
    preview_response = client.get(f"/api/preview/{task_id}")
    assert preview_response.status_code == 400
    assert "not ready for preview" in preview_response.json()["detail"].lower() 