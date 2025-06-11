import os
import pytest
import subprocess
import time
import signal
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fastapi.testclient import TestClient
from src.main import app
from src.utils.error_handler import ErrorHandler, ErrorType

class TestWebUI:
    @pytest.fixture(scope="class")
    def server(self):
        """啟動 FastAPI 服務器"""
        # 啟動服務器
        process = subprocess.Popen(
            ["uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待服務器啟動
        time.sleep(2)
        
        yield process
        
        # 關閉服務器
        process.send_signal(signal.SIGTERM)
        process.wait()

    @pytest.fixture(scope="class")
    def driver(self):
        """設置 Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 無頭模式
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        yield driver
        driver.quit()

    @pytest.fixture(scope="class")
    def client(self):
        """設置 FastAPI 測試客戶端"""
        return TestClient(app)

    @pytest.fixture(scope="class")
    def temp_file(self):
        """創建臨時測試檔案"""
        temp_file = "test_audio.wav"
        with open(temp_file, "wb") as f:
            f.write(b"x" * 1000)  # 創建一個小檔案
        yield temp_file
        if os.path.exists(temp_file):
            os.remove(temp_file)

    def test_upload_page_loads(self, driver, server):
        """測試上傳頁面是否正確載入"""
        driver.get("http://127.0.0.1:8000/upload")
        assert "Voice Clone Optimizer" in driver.title
        assert driver.find_element(By.ID, "file-upload").is_displayed()

    def test_file_upload_ui(self, driver, server, temp_file):
        """測試檔案上傳界面功能"""
        # 訪問上傳頁面
        driver.get("http://127.0.0.1:8000/upload")
        
        # 找到上傳按鈕並上傳檔案
        file_input = driver.find_element(By.ID, "file-upload")
        file_input.send_keys(os.path.abspath(temp_file))
        
        # 點擊上傳按鈕
        upload_button = driver.find_element(By.ID, "upload-button")
        upload_button.click()
        
        # 等待上傳完成提示
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "upload-success"))
        )
        
        # 驗證成功訊息
        success_message = driver.find_element(By.CLASS_NAME, "upload-success")
        assert "上傳成功" in success_message.text

    def test_error_display_ui(self, driver, server, temp_file, test_files_dir):
        """測試錯誤顯示界面"""
        # 創建一個過大的檔案
        large_file = os.path.join(test_files_dir, "large_test.wav")
        with open(large_file, "wb") as f:
            f.write(b"x" * (1024 * 1024 * 11))  # 11MB
        
        # 訪問上傳頁面
        driver.get("http://127.0.0.1:8000/upload")
        
        # 上傳過大的檔案
        file_input = driver.find_element(By.ID, "file-upload")
        file_input.send_keys(os.path.abspath(large_file))
        
        # 點擊上傳按鈕
        upload_button = driver.find_element(By.ID, "upload-button")
        upload_button.click()
        
        # 等待錯誤訊息顯示
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
        )
        
        # 驗證錯誤訊息
        error_message = driver.find_element(By.CLASS_NAME, "error-message")
        assert "檔案大小超過限制" in error_message.text
        
        # 清理測試檔案
        if os.path.exists(large_file):
            os.remove(large_file)

    def test_correction_flow_ui(self, driver, server, temp_file):
        """測試錯誤修正流程界面"""
        # 訪問上傳頁面
        driver.get("http://127.0.0.1:8000/upload")
        
        # 上傳檔案
        file_input = driver.find_element(By.ID, "file-upload")
        file_input.send_keys(os.path.abspath(temp_file))
        
        # 點擊上傳按鈕
        upload_button = driver.find_element(By.ID, "upload-button")
        upload_button.click()
        
        # 等待處理開始
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "processing-status"))
        )
        
        # 驗證處理狀態
        processing_status = driver.find_element(By.CLASS_NAME, "processing-status")
        assert "處理中" in processing_status.text
        
        # 等待處理完成
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "processing-complete"))
        )
        
        # 驗證處理結果
        result_message = driver.find_element(By.CLASS_NAME, "processing-complete")
        assert "處理完成" in result_message.text

    def test_error_history_ui(self, driver, server, test_files_dir):
        """測試錯誤歷史記錄界面"""
        # 先觸發一個錯誤（上傳超大檔案）
        large_file = os.path.join(test_files_dir, "large_test_for_history.wav")
        with open(large_file, "wb") as f:
            f.write(b"x" * (1024 * 1024 * 11))  # 11MB
        with open(large_file, "rb") as f:
            requests.post("http://127.0.0.1:8000/api/upload", files={"file": ("large_test_for_history.wav", f, "audio/wav")})
        time.sleep(1)  # 等待 server 寫入資料庫
        # 訪問錯誤歷史頁面
        driver.get("http://127.0.0.1:8000/error-history")
        
        # 等待錯誤歷史表格載入
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-history-table"))
        )
        
        # 驗證表格內容
        error_rows = driver.find_elements(By.CLASS_NAME, "error-row")
        assert len(error_rows) > 0
        
        # 驗證錯誤詳情
        first_error = error_rows[0]
        assert first_error.find_element(By.CLASS_NAME, "error-type").text in [
            "語法錯誤", "執行時錯誤", "邏輯錯誤", "資源錯誤", "未知錯誤"
        ]
        assert first_error.find_element(By.CLASS_NAME, "error-message").text is not None

    def test_correction_history_ui(self, driver, server, test_files_dir):
        """測試修正歷史記錄界面"""
        # 先觸發一個錯誤（上傳超大檔案）
        large_file = os.path.join(test_files_dir, "large_test_for_history.wav")
        with open(large_file, "wb") as f:
            f.write(b"x" * (1024 * 1024 * 11))  # 11MB
        with open(large_file, "rb") as f:
            requests.post("http://127.0.0.1:8000/api/upload", files={"file": ("large_test_for_history.wav", f, "audio/wav")})
        time.sleep(1)  # 等待 server 寫入資料庫
        # 訪問修正歷史頁面
        driver.get("http://127.0.0.1:8000/correction-history")
        
        # 等待修正歷史表格載入
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "correction-history-table"))
        )
        
        # 驗證表格內容
        correction_rows = driver.find_elements(By.CLASS_NAME, "correction-row")
        assert len(correction_rows) > 0
        
        # 驗證修正詳情
        first_correction = correction_rows[0]
        assert first_correction.find_element(By.CLASS_NAME, "correction-status").text == "成功"
        assert len(first_correction.find_elements(By.CLASS_NAME, "applied-fix")) > 0
        assert first_correction.find_element(By.CLASS_NAME, "verification-status").text == "成功" 