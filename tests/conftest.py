import pytest
import os
import sys
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from src.main import app
from src.models.error_history import init_db, engine
from sqlalchemy import text

# 添加專案根目錄到 Python 路徑
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

@pytest.fixture(scope="session")
def test_files_dir():
    """創建測試檔案目錄"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # 清理測試檔案
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)

@pytest.fixture(scope="session")
def test_db():
    """初始化測試資料庫"""
    # 初始化資料庫
    init_db()
    yield
    # 清理資料庫
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM correction_history"))
        conn.execute(text("DELETE FROM error_history"))
        conn.commit()

@pytest.fixture(scope="function")
def client(test_db):
    """創建測試客戶端"""
    return TestClient(app)

@pytest.fixture(scope="function")
def temp_file(test_files_dir):
    """創建臨時測試檔案"""
    temp_file = os.path.join(test_files_dir, "test_audio.wav")
    with open(temp_file, "wb") as f:
        f.write(b"test audio content")
    return temp_file 