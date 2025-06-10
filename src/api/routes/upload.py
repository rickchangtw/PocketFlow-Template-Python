from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os

from src.config.logging import logger
from src.utils.file_manager import file_manager
from src.utils.error_handler import VoiceCloneError
from src.models.task import Task, TaskResponse
from src.models.user import User
from src.services.voice_service import voice_service
from src.models.base import get_db

router = APIRouter()

# Mock user for testing
class DummyUser:
    def __init__(self):
        self.id = "test_user"

def get_current_user():
    return DummyUser()

@router.post("/upload", response_model=TaskResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: DummyUser = Depends(get_current_user)
):
    """Upload a single voice file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.wav', '.mp3')):
            raise HTTPException(status_code=400, detail="Only WAV and MP3 files are allowed")

        # Save file
        file_path = await file_manager.save_upload_file(file)

        # Create task in database
        task = Task(
            user_id=current_user.id,
            status="pending",
            input_file=file_path
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Start processing
        await voice_service.process_audio(file_path)

        return task

    except VoiceCloneError as e:
        logger.error(f"Voice clone error during upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/upload/batch", response_model=List[TaskResponse])
async def upload_batch(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: DummyUser = Depends(get_current_user)
):
    """Upload multiple voice files"""
    try:
        tasks = []
        for file in files:
            # Validate file type
            if not file.filename.endswith(('.wav', '.mp3')):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a WAV or MP3 file")

            # Save file
            file_path = await file_manager.save_upload_file(file)

            # Create task in database
            task = Task(
                user_id=current_user.id,
                status="pending",
                input_file=file_path
            )
            db.add(task)
            tasks.append(task)

        db.commit()

        # Start processing all tasks
        for task in tasks:
            await voice_service.process_audio(task.input_file)

        return tasks

    except VoiceCloneError as e:
        logger.error(f"Voice clone error during batch upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during batch upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
