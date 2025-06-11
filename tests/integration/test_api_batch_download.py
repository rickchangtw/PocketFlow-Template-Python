import pytest
from fastapi.testclient import TestClient
from src.main import app
import time

client = TestClient(app)

def test_batch_download():
    # 準備多個測試檔案
    wav_bytes = b"RIFF....WAVEfmt "
    files = [
        ("files", ("test1.wav", wav_bytes, "audio/wav")),
        ("files", ("test2.wav", wav_bytes, "audio/wav"))
    ]
    
    # 批次上傳檔案
    upload_response = client.post("/api/upload/batch", files=files)
    assert upload_response.status_code == 200
    tasks = upload_response.json()
    
    # 等待任務完成（加入超時機制）
    task_ids = [task["id"] for task in tasks]
    max_wait_time = 5  # 最多等待5秒
    start_time = time.time()
    
    for task_id in task_ids:
        while True:
            if time.time() - start_time > max_wait_time:
                pytest.fail("等待任務完成超時")
            
            response = client.get(f"/api/tasks/{task_id}")
            if response.status_code == 404:
                pytest.fail(f"查無任務 {task_id}，回傳 404: {response.json()}")
            if response.json().get("status") == "completed":
                break
            time.sleep(0.1)
    
    # 測試批次下載
    params = [("task_ids", int(tid)) for tid in task_ids]
    response = client.get("/api/download/batch", params=params)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    
    # 驗證下載的檔案內容
    content = response.content
    assert len(content) > 0  # 確保下載的檔案不為空

def test_batch_download_with_invalid_ids():
    # 測試使用無效的任務ID
    params = [("task_ids", 999), ("task_ids", 1000)]
    response = client.get("/api/download/batch", params=params)
    assert response.status_code == 404
    data = response.json()
    assert "error" in data

def test_batch_download_with_uncompleted_tasks():
    # 準備測試檔案
    wav_bytes = b"RIFF....WAVEfmt "
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}
    
    # 上傳檔案
    upload_response = client.post("/api/upload", files=files)
    assert upload_response.status_code == 200
    task = upload_response.json()
    
    # 立即嘗試下載（任務尚未完成）
    params = [("task_ids", int(task["id"]))]
    response = client.get("/api/download/batch", params=params)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "not completed" in data["error"].lower() 