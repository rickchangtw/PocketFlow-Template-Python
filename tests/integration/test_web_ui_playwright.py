import os
import time
import pytest
import requests

@pytest.fixture(scope="session", autouse=True)
def start_server():
    import subprocess, signal
    process = subprocess.Popen(
        ["uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    time.sleep(2)
    yield
    process.send_signal(signal.SIGTERM)
    process.wait()

@pytest.fixture
def temp_file(tmp_path):
    temp_file = tmp_path / "test_audio.wav"
    temp_file.write_bytes(b"x" * 1000)
    return str(temp_file)

def test_upload_page_loads(page, start_server):
    page.goto("http://127.0.0.1:8000/upload")
    assert "Voice Clone Optimizer" in page.title()
    assert page.locator("#file-upload").is_visible()

def test_file_upload_ui(page, start_server, temp_file):
    page.goto("http://127.0.0.1:8000/upload")
    page.set_input_files("#file-upload", temp_file)
    page.click("#upload-button")
    page.wait_for_selector(".upload-success")
    assert "上傳成功" in page.inner_text(".upload-success")

def test_error_display_ui(page, start_server, tmp_path):
    large_file = tmp_path / "large_test.wav"
    large_file.write_bytes(b"x" * (1024 * 1024 * 11))
    page.goto("http://127.0.0.1:8000/upload")
    page.set_input_files("#file-upload", str(large_file))
    page.click("#upload-button")
    page.wait_for_selector(".error-message")
    assert "檔案大小超過限制" in page.inner_text(".error-message")

def test_correction_flow_ui(page, start_server, temp_file):
    page.goto("http://127.0.0.1:8000/upload")
    page.set_input_files("#file-upload", temp_file)
    page.click("#upload-button")
    page.wait_for_selector(".processing-status")
    assert "處理中" in page.inner_text(".processing-status")
    page.wait_for_selector(".processing-complete", timeout=20000)
    assert "處理完成" in page.inner_text(".processing-complete")

def test_error_history_ui(page, start_server, tmp_path):
    large_file = tmp_path / "large_test_for_history.wav"
    large_file.write_bytes(b"x" * (1024 * 1024 * 11))
    with open(large_file, "rb") as f:
        requests.post("http://127.0.0.1:8000/api/upload", files={"file": ("large_test_for_history.wav", f, "audio/wav")})
    time.sleep(1)
    page.goto("http://127.0.0.1:8000/error-history")
    page.wait_for_selector(".error-history-table")
    error_rows = page.locator(".error-row")
    assert error_rows.count() > 0
    first_error = error_rows.nth(0)
    assert first_error.locator(".error-type").inner_text() in [
        "語法錯誤", "執行時錯誤", "邏輯錯誤", "資源錯誤", "未知錯誤"
    ]
    assert first_error.locator(".error-message").inner_text() != ""

def test_correction_history_ui(page, start_server, tmp_path):
    large_file = tmp_path / "large_test_for_history.wav"
    large_file.write_bytes(b"x" * (1024 * 1024 * 11))
    with open(large_file, "rb") as f:
        requests.post("http://127.0.0.1:8000/api/upload", files={"file": ("large_test_for_history.wav", f, "audio/wav")})
    time.sleep(1)
    page.goto("http://127.0.0.1:8000/correction-history")
    page.wait_for_selector(".correction-history-table")
    correction_rows = page.locator(".correction-row")
    assert correction_rows.count() > 0
    first_correction = correction_rows.nth(0)
    assert first_correction.locator(".correction-status").inner_text() == "成功"
    assert first_correction.locator(".applied-fix").count() > 0
    assert first_correction.locator(".verification-status").inner_text() == "成功" 