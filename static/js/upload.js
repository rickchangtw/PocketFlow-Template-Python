document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('file-upload');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('請選擇檔案');
        return;
    }
    
    // 顯示處理中狀態
    showProcessingStatus();
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        console.log('API 回傳', data);
        
        if (!response.ok || data.success === false) {
            // 優先顯示 message，再顯示 detail
            let msg = data.message || data.detail || '處理失敗';
            if (data.message && data.detail && data.message !== data.detail) {
                msg = data.message + ' ' + data.detail;
            }
            showError(msg);
            return;
        }
        
        if (data.success) {
            // 顯示成功訊息
            showSuccess(data.message);
            
            // 如果有修正訊息，顯示處理中狀態
            if (data.correction_message) {
                showProcessingStatus(data.correction_message);
                
                // 等待處理完成
                setTimeout(() => {
                    showProcessingComplete('處理完成');
                }, 2000);
            }
        } else {
            showError(data.message || '處理失敗');
        }
        
    } catch (error) {
        showError('處理失敗');
    }
});

function showError(message) {
    console.log('[showError]', message);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    const container = document.querySelector('.upload-container');
    container.appendChild(errorDiv);
    
    // 3秒後移除錯誤訊息
    setTimeout(() => {
        errorDiv.remove();
    }, 3000);
}

function showSuccess(message) {
    console.log('[showSuccess]', message);
    const successDiv = document.createElement('div');
    successDiv.className = 'upload-success';
    successDiv.textContent = message;
    
    const container = document.querySelector('.upload-container');
    container.appendChild(successDiv);
    
    // 3秒後移除成功訊息
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

function showProcessingStatus(message = '處理中...') {
    console.log('[showProcessingStatus]', message);
    const statusDiv = document.createElement('div');
    statusDiv.className = 'processing-status';
    statusDiv.textContent = message;
    
    const container = document.querySelector('.upload-container');
    container.appendChild(statusDiv);
}

function showProcessingComplete(message) {
    console.log('[showProcessingComplete]', message);
    const completeDiv = document.createElement('div');
    completeDiv.className = 'processing-complete';
    completeDiv.textContent = message;
    
    const container = document.querySelector('.upload-container');
    container.appendChild(completeDiv);
    
    // 3秒後移除完成訊息
    setTimeout(() => {
        completeDiv.remove();
    }, 3000);
}

function generateTaskId() {
    return 'task_' + Math.random().toString(36).substr(2, 9);
}

const uploadButton = document.getElementById('upload-button');
const fileInput = document.getElementById('file-upload');

uploadButton.addEventListener('click', function() {
    const file = fileInput.files[0];
    if (!file) return;
    const task_id = generateTaskId();
    // 初始化進度條
    document.getElementById('progress-container').style.display = 'block';
    document.getElementById('progress-bar').value = 0;
    document.getElementById('progress-status').innerText = '處理中…';
    // 準備 form data
    const formData = new FormData();
    formData.append('file', file);
    formData.append('task_id', task_id);
    // 發送上傳請求
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            onUploadSuccess(task_id);
        } else {
            document.getElementById('progress-status').innerText = data.message || '上傳失敗';
        }
    });
}); 