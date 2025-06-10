from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.config.logging import logger
from src.utils.error_handler import VoiceCloneError
from src.models.task import Task, TaskResponse
from src.models.user import User
from src.models.base import get_db
from src.api.routes.upload import get_current_user
from src.services.voice_service import voice_service
from src.services.analysis_service import analysis_service
from src.services.optimization_service import optimization_service

router = APIRouter()

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Task]:
    """Get list of tasks with optional filtering"""
    try:
        query = db.query(Task).filter(Task.user_id == current_user.id)
        
        if status:
            query = query.filter(Task.status == status)
        if task_type:
            query = query.filter(Task.task_type == task_type)
            
        return query.offset(skip).limit(limit).all()
        
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Task:
    """Get task details by ID"""
    try:
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Cancel a running task"""
    try:
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        if task.status not in ["pending", "processing"]:
            raise HTTPException(
                status_code=400,
                detail="Can only cancel pending or processing tasks"
            )
            
        # Cancel task processing
        await voice_service.cancel_task(task_id)
        
        # Update task status
        task.status = "cancelled"
        db.commit()
        
        return {"message": "Task cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/tasks/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Task:
    """Retry a failed task"""
    try:
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        if task.status != "failed":
            raise HTTPException(
                status_code=400,
                detail="Can only retry failed tasks"
            )
            
        # Reset task status
        task.status = "pending"
        task.error_message = None
        task.error_details = None
        db.commit()
        
        # Start processing
        await voice_service.process_file(task.id, task.input_file)
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
