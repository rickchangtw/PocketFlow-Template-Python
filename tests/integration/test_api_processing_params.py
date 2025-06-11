import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_upload_with_params():
    # 準備測試檔案和參數
    wav_bytes = b"RIFF....WAVEfmt "
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}
    params = {
        "noise_reduction": 0.8,
        "quality_level": "high",
        "output_format": "wav"
    }
    
    # 上傳檔案並設定參數
    response = client.post("/api/upload", files=files, json=params)
    assert response.status_code == 200
    data = response.json()
    
    # 驗證參數是否正確保存
    assert data["processing_params"]["noise_reduction"] == 0.8
    assert data["processing_params"]["quality_level"] == "high"
    assert data["processing_params"]["output_format"] == "wav"

def test_upload_with_invalid_params():
    # 準備測試檔案和無效參數
    wav_bytes = b"RIFF....WAVEfmt "
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}
    params = {
        "noise_reduction": 2.0,  # 超出範圍
        "quality_level": "invalid",  # 無效值
        "output_format": "invalid"  # 無效值
    }
    
    # 上傳檔案並設定無效參數
    response = client.post("/api/upload", files=files, json=params)
    assert response.status_code == 422  # 參數驗證錯誤

def test_batch_upload_with_params():
    # 準備多個測試檔案和參數
    wav_bytes = b"RIFF....WAVEfmt "
    files = [
        ("files", ("test1.wav", wav_bytes, "audio/wav")),
        ("files", ("test2.wav", wav_bytes, "audio/wav"))
    ]
    params = {
        "noise_reduction": 0.5,
        "quality_level": "medium",
        "output_format": "wav"
    }
    
    # 批次上傳檔案並設定參數
    response = client.post("/api/upload/batch", files=files, json=params)
    assert response.status_code == 200
    data = response.json()
    
    # 驗證每個任務的參數是否正確保存
    for task in data:
        assert task["processing_params"]["noise_reduction"] == 0.5
        assert task["processing_params"]["quality_level"] == "medium"
        assert task["processing_params"]["output_format"] == "wav" 