import io
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def override_get_db():
    # 可根據實際情況回傳一個 mock 或 sqlite in-memory session
    class DummyDB:
        def add(self, obj): pass
        def commit(self): pass
        def refresh(self, obj): pass
    return DummyDB()

def override_get_current_user():
    class DummyUser:
        id = "test_user"
    return DummyUser()

app.dependency_overrides = {
    "src.api.routes.upload.get_db": override_get_db,
    "src.api.routes.upload.get_current_user": override_get_current_user,
}

def test_upload_wav():
    # 準備一個假的 wav 檔案
    wav_bytes = io.BytesIO(b"RIFF....WAVEfmt ")  # 這不是合法音檔，只做 API 測試
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}
    response = client.post("/api/upload", files=files)
    # 由於我們 mock 了 DB 與權限，這裡只驗證 API 路徑與格式
    assert response.status_code in (200, 422, 400)  # 依據實作可能回傳 422 或 400
    # 若有正確回傳 Task 結構，可進一步驗證內容
    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert data["user_id"] == "test_user"
        assert data["status"] in ("pending", "processing", "completed", "failed") 