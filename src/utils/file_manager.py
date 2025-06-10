import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile

from src.config.settings import Settings
from src.utils.error_handler import FileValidationError
from src.config.logging import logger

settings = Settings()

class FileManager:
    """Utility class for managing file operations"""
    
    @staticmethod
    def validate_file(file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file size
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
        
        if size > settings.MAX_UPLOAD_SIZE:
            raise FileValidationError(
                f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        # Check file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"File extension {ext} not allowed. Allowed extensions: {settings.ALLOWED_EXTENSIONS}"
            )
    
    @staticmethod
    async def save_upload_file(file: UploadFile, destination: Optional[str] = None) -> str:
        """Save uploaded file to destination"""
        try:
            # Validate file
            FileManager.validate_file(file)
            
            # Create destination directory if it doesn't exist
            if destination is None:
                destination = settings.UPLOAD_DIR
            os.makedirs(destination, exist_ok=True)
            
            # Generate unique filename
            file_path = os.path.join(destination, file.filename)
            file_path = FileManager._get_unique_path(file_path)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            logger.info(f"File saved successfully: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise FileValidationError(f"Error saving file: {str(e)}")
    
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
            raise FileValidationError(f"Error deleting file: {str(e)}")
    
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
            raise FileValidationError(f"Error listing files: {str(e)}")
    
    @staticmethod
    def create_directory(directory: str) -> None:
        """Create directory if it doesn't exist"""
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory created/verified: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory: {str(e)}")
            raise FileValidationError(f"Error creating directory: {str(e)}")
    
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

# Create a singleton instance
file_manager = FileManager()
