import pytest
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path

def test_audio_loading():
    """測試音頻文件加載功能"""
    # 創建一個測試用的音頻文件
    sample_rate = 22050
    duration = 1.0  # 1秒
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)  # 440Hz的正弦波
    
    # 保存為臨時文件
    temp_file = Path("test_audio.wav")
    sf.write(temp_file, audio, sample_rate)
    
    try:
        # 加載音頻文件
        loaded_audio, sr = librosa.load(temp_file, sr=None)
        
        # 驗證加載的音頻
        assert sr == sample_rate
        assert len(loaded_audio) == len(audio)
        assert np.allclose(loaded_audio, audio, atol=1e-3)
    finally:
        # 清理臨時文件
        if temp_file.exists():
            temp_file.unlink()

def test_audio_normalization():
    """測試音頻正規化功能"""
    # 創建測試音頻數據
    audio = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    
    # 正規化
    normalized = librosa.util.normalize(audio)
    
    # 驗證結果
    assert np.max(np.abs(normalized)) <= 1.0
    assert np.min(normalized) >= -1.0
    assert np.allclose(np.max(np.abs(normalized)), 1.0)

def test_audio_features():
    """測試音頻特徵提取"""
    # 創建測試音頻數據
    sample_rate = 22050
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = np.sin(2 * np.pi * 440 * t)
    
    # 提取梅爾頻譜圖
    mel_spec = librosa.feature.melspectrogram(y=audio, sr=sample_rate)
    
    # 驗證特徵
    assert mel_spec.shape[0] > 0  # 頻率維度
    assert mel_spec.shape[1] > 0  # 時間維度
    assert not np.any(np.isnan(mel_spec))  # 確保沒有NaN值 