from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.config.logging import logger
from src.utils.file_manager import file_manager
from src.utils.error_handler import VoiceCloneError
from src.models.task import Task
from src.models.user import User
from src.models.base import get_db
from src.api.routes.upload import get_current_user

router = APIRouter()

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
