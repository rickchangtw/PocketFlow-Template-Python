import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, Response
from fastapi.responses import FileResponse

from src.core.config import settings
from src.utils.error_handler import FileValidationError
from src.config.logging import logger

class FileManager:
    """Utility class for managing file operations"""
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.preview_dir = settings.PREVIEW_DIR
        self.download_dir = settings.DOWNLOAD_DIR
        self._ensure_directories()
    
    def _ensure_directories(self):
        """確保必要的目錄存在"""
        for directory in [self.upload_dir, self.preview_dir, self.download_dir]:
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file size
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
        
        if size > settings.MAX_UPLOAD_SIZE:
            raise FileValidationError(
                f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes",
                context={
                    "file_size": size,
                    "max_size": settings.MAX_UPLOAD_SIZE,
                    "file_name": file.filename
                }
            )
        
        # Check file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"File extension {ext} not allowed. Allowed extensions: {settings.ALLOWED_EXTENSIONS}",
                context={
                    "file_extension": ext,
                    "allowed_extensions": settings.ALLOWED_EXTENSIONS,
                    "file_name": file.filename
                }
            )
    
    async def save_upload_file(self, file: UploadFile) -> str:
        """保存上傳的文件"""
        try:
            # 生成唯一文件名
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(self.upload_dir, unique_filename)
            
            # 保存文件
            with open(file_path, "wb") as f:
                while chunk := await file.read(8192):
                    f.write(chunk)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise
    
    async def generate_preview_url(self, file: UploadFile) -> str:
        """生成文件預覽URL"""
        try:
            # 生成預覽文件名
            file_extension = os.path.splitext(file.filename)[1]
            preview_filename = f"preview_{uuid.uuid4()}{file_extension}"
            preview_path = os.path.join(self.preview_dir, preview_filename)
            
            # 保存預覽文件
            with open(preview_path, "wb") as f:
                while chunk := await file.read(8192):
                    f.write(chunk)
            
            # 生成預覽URL
            preview_url = f"{settings.BASE_URL}/preview/{preview_filename}"
            return preview_url
            
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}")
            raise
    
    async def generate_batch_download_url(self, tasks: list) -> str:
        """生成批次下載URL"""
        try:
            # 創建批次下載目錄
            batch_id = str(uuid.uuid4())
            batch_dir = os.path.join(self.download_dir, batch_id)
            os.makedirs(batch_dir, exist_ok=True)
            
            # 複製所有處理完成的文件到批次目錄
            for task in tasks:
                if task.output_file and os.path.exists(task.output_file):
                    filename = os.path.basename(task.output_file)
                    new_path = os.path.join(batch_dir, filename)
                    os.link(task.output_file, new_path)
            
            # 生成下載URL
            download_url = f"{settings.BASE_URL}/download/batch/{batch_id}"
            return download_url
            
        except Exception as e:
            logger.error(f"Error generating batch download: {str(e)}")
            raise
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """清理過期的文件"""
        try:
            import time
            current_time = time.time()
            
            for directory in [self.preview_dir, self.download_dir]:
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > (max_age_hours * 3600):
                        os.remove(file_path)
                        
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")
            raise
    
    @staticmethod
    def _get_unique_path(file_path: str) -> str:
        """Generate unique file path if file already exists"""
        path = Path(file_path)
        counter = 1
        
        while path.exists():
            new_name = f"{path.stem}_{counter}{path.suffix}"
            path = path.parent / new_name
            counter += 1
        
        return str(path)
    
    @staticmethod
    def delete_file(file_path: str) -> None:
        """Delete file if it exists"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted successfully: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            raise FileValidationError(
                f"Error deleting file: {str(e)}",
                context={
                    "file_path": file_path,
                    "error_type": type(e).__name__
                }
            )
    
    @staticmethod
    def list_files(directory: str, pattern: str = "*") -> List[str]:
        """List files in directory matching pattern"""
        try:
            files = []
            for file in Path(directory).glob(pattern):
                if file.is_file():
                    files.append(str(file))
            return files
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise FileValidationError(
                f"Error listing files: {str(e)}",
                context={
                    "directory": directory,
                    "pattern": pattern,
                    "error_type": type(e).__name__
                }
            )
    
    @staticmethod
    def create_directory(directory: str) -> None:
        """Create directory if it doesn't exist"""
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory created/verified: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory: {str(e)}")
            raise FileValidationError(
                f"Error creating directory: {str(e)}",
                context={
                    "directory": directory,
                    "error_type": type(e).__name__
                }
            )
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """Get file information"""
        try:
            stat = os.stat(file_path)
            return {
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "accessed": stat.st_atime
            }
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            raise FileValidationError(f"Error getting file info: {str(e)}")

    @staticmethod
    async def get_file(file_path: str) -> FileResponse:
        """Get file for download"""
        try:
            if not os.path.exists(file_path):
                raise FileValidationError("File not found")
            
            # 獲取檔案名稱
            filename = os.path.basename(file_path)
            
            # 使用 FileResponse 來處理檔案下載
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="audio/wav"  # 或根據檔案類型設置適當的 media_type
            )
            
        except Exception as e:
            logger.error(f"Error getting file: {str(e)}")
            raise FileValidationError(f"Error getting file: {str(e)}")

# Create a singleton instance
file_manager = FileManager()
