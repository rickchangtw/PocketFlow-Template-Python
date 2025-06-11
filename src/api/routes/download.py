from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from typing import List
import zipfile
import io
import logging
import os

from src.config.logging import logger
from src.utils.file_manager import file_manager
from src.utils.error_handler import VoiceCloneError, handle_error
from src.models.task import Task
from src.models.user import User
from src.models.base import get_db
from src.api.routes.upload import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/download/{task_id}")
async def download_file(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download processed file"""
    try:
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        if task.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="File is not ready for download"
            )
            
        return await file_manager.get_file(task.file_path)
        
    except VoiceCloneError as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during download: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/batch")
async def download_batch(task_ids: List[int] = Query(..., min_items=1), current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """批次下載多個處理完成的檔案"""
    try:
        tasks = []
        for tid in task_ids:
            task = db.query(Task).filter(Task.id == tid, Task.user_id == current_user.id).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {tid} not found")
            if task.status != "completed":
                raise HTTPException(status_code=400, detail=f"Task {tid} is not completed")
            tasks.append(task)
        # 創建 ZIP 檔案
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for task in tasks:
                try:
                    file_path = file_manager.get_file(task.output_file)
                    zip_file.write(file_path, f"{task.id}_{os.path.basename(task.output_file)}")
                except Exception as e:
                    logger.error(f"Error adding file to zip: {str(e)}")
                    continue
        headers = {
            'Content-Disposition': 'attachment; filename=processed_files.zip',
            'Content-Type': 'application/zip'
        }
        return Response(content=zip_buffer.getvalue(), headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "Error during batch download")
