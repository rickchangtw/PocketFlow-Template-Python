from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
import os
from pydantic import BaseModel, Field, field_validator
import json
from datetime import datetime
import uuid
from fastapi.responses import JSONResponse
from fastapi import Query

from src.config.logging import logger
from src.utils.file_manager import file_manager
from src.utils.error_handler import handle_error, ErrorHandler, FileValidationError
from src.models.task import Task, TaskResponse, TaskStatus
from src.models.user import User
from src.services.voice_service import voice_service
from src.models.base import get_db
from src.core.config import settings

from src.models.error_history import CorrectionHistory

router = APIRouter()

class DummyUser:
    def __init__(self):
        self.id = 1

def get_current_user():
    return DummyUser()

class ProcessingParams(BaseModel):
    """處理參數模型"""
    pitch_shift: float = Field(0.0, ge=-12.0, le=12.0)
    tempo_adjust: float = Field(1.0, ge=0.5, le=2.0)
    noise_reduction: float = Field(0.0, ge=0.0, le=1.0)
    quality_level: str = Field("medium", pattern="^(low|medium|high)$")
    output_format: str = Field("wav", pattern="^(wav|mp3|ogg)$")

    @field_validator('pitch_shift', 'tempo_adjust', 'noise_reduction')
    @classmethod
    def validate_numeric_params(cls, v: float, info) -> float:
        if info.field_name == 'pitch_shift' and not -12.0 <= v <= 12.0:
            raise ValueError("pitch_shift must be between -12.0 and 12.0")
        if info.field_name == 'tempo_adjust' and not 0.5 <= v <= 2.0:
            raise ValueError("tempo_adjust must be between 0.5 and 2.0")
        if info.field_name == 'noise_reduction' and not 0.0 <= v <= 1.0:
            raise ValueError("noise_reduction must be between 0.0 and 1.0")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "pitch_shift": 1.5,
                "tempo_adjust": 1.2,
                "noise_reduction": 0.5,
                "quality_level": "medium",
                "output_format": "wav"
            }
        }

class BatchDownloadRequest(BaseModel):
    task_ids: List[str]

# 假設有一個全域 dict 儲存進度（實際可用資料庫或 redis）
UPLOAD_PROGRESS = {}

@router.post("/upload/preview", response_model=dict)
async def preview_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """預覽上傳的文件"""
    try:
        # 驗證文件類型
        if not file.filename.lower().endswith(('.wav', '.mp3')):
            raise HTTPException(status_code=400, detail="Only WAV and MP3 files are allowed")
        
        # 驗證文件大小
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB
        while chunk := await file.read(chunk_size):
            file_size += len(chunk)
            if file_size > settings.MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"File size exceeds {settings.MAX_FILE_SIZE/1024/1024}MB limit")
        
        # 重置文件指針
        await file.seek(0)
        
        # 生成預覽URL
        preview_url = await file_manager.generate_preview_url(file)
        
        return {"preview_url": preview_url}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "Error during file preview")

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    form = await request.form()
    task_id = form.get('task_id')
    if task_id:
        UPLOAD_PROGRESS[task_id] = {"progress": 0, "status": "開始上傳…"}
    try:
        # 檢查檔案大小
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB
        while chunk := await file.read(chunk_size):
            file_size += len(chunk)
            if task_id:
                UPLOAD_PROGRESS[task_id] = {"progress": min(90, int(file_size / (1024*1024*10) * 90)), "status": "處理中…"}
            if file_size > settings.MAX_FILE_SIZE:
                error_handler = ErrorHandler()
                error_handler.record_error(
                    file_path=file.filename if file else None,
                    error_type="upload",
                    error_message="檔案大小超過限制",
                    correction_status="failed"
                )
                if task_id:
                    UPLOAD_PROGRESS[task_id] = {"progress": 100, "status": "檔案過大，失敗"}
                return {
                    "success": False,
                    "message": "檔案大小超過限制"
                }
        # 檢查檔案類型
        if not file.content_type.startswith('audio/'):
            error_handler = ErrorHandler()
            error_handler.record_error(
                file_path=file.filename if file else None,
                error_type="upload",
                error_message="只接受音訊檔案",
                correction_status="failed"
            )
            if task_id:
                UPLOAD_PROGRESS[task_id] = {"progress": 100, "status": "檔案類型錯誤"}
            return {
                "success": False,
                "message": "只接受音訊檔案"
            }
        # 儲存檔案
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        await file.seek(0)  # 重置檔案指標
        with open(file_path, "wb") as f:
            while chunk := await file.read(chunk_size):
                f.write(chunk)
        # 只記錄成功的 error history，不寫 correction history
        error_handler = ErrorHandler()
        error_handler.record_error(
            file_path=file_path,
            error_type="upload",
            error_message="檔案上傳成功",
            correction_status="成功"
        )
        if task_id:
            UPLOAD_PROGRESS[task_id] = {"progress": 100, "status": "處理完成！"}
        print('[API 回傳]', {"success": True, "message": "上傳成功！", "correction_message": "處理中..."})
        return {
            "success": True,
            "message": "上傳成功！",
            "correction_message": "處理中..."
        }
    except HTTPException as e:
        error_handler = ErrorHandler()
        error_handler.record_error(
            file_path=file.filename if file else None,
            error_type="upload",
            error_message=str(e.detail),
            correction_status="failed"
        )
        if task_id:
            UPLOAD_PROGRESS[task_id] = {"progress": 100, "status": "處理失敗"}
        raise HTTPException(
            status_code=e.status_code,
            detail=str(e.detail)
        )
    except Exception as e:
        error_handler = ErrorHandler()
        error_handler.record_error(
            file_path=file.filename if file else None,
            error_type="upload",
            error_message=str(e),
            correction_status="failed"
        )
        if task_id:
            UPLOAD_PROGRESS[task_id] = {"progress": 100, "status": "處理失敗"}
        raise HTTPException(
            status_code=500,
            detail="處理失敗"
        )

@router.post("/upload/batch-download", response_model=dict)
async def batch_download(
    request: BatchDownloadRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批次下載多個處理完成的檔案"""
    try:
        # 驗證任務是否存在且屬於當前用戶
        tasks = []
        for task_id in request.task_ids:
            task = db.query(Task).filter(Task.id==task_id).first()
            if not task or task.user_id != current_user.id:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            if task.status != TaskStatus.COMPLETED:
                raise HTTPException(status_code=400, detail=f"Task {task_id} is not completed")
            tasks.append(task)
        
        # 生成下載URL
        download_url = await file_manager.generate_batch_download_url(tasks)
        
        return {"download_url": download_url}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "Error during batch download")

@router.post("/upload/batch", response_model=List[TaskResponse])
async def upload_batch(
    files: List[UploadFile] = File(...),
    parameters: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批次上傳多個檔案進行處理"""
    try:
        # 解析處理參數
        try:
            params = ProcessingParams(**json.loads(parameters)) if parameters else ProcessingParams()
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid parameters format")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        tasks = []
        for file in files:
            # 驗證檔案類型
            if not file.filename.lower().endswith(('.wav', '.mp3')):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a valid audio file")
            
            # 驗證檔案大小
            file_size = 0
            chunk_size = 1024 * 1024  # 1MB
            while chunk := await file.read(chunk_size):
                file_size += len(chunk)
                if file_size > settings.MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds {settings.MAX_FILE_SIZE/1024/1024}MB limit")
            
            # 重置檔案指針
            await file.seek(0)
            
            # 保存檔案
            file_path = await file_manager.save_upload_file(file)
            
            # 創建任務
            task = Task(
                user_id=current_user.id,
                status=TaskStatus.PENDING,
                input_file=file_path,
                processing_params=params.model_dump(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=None
            )
            db.add(task)
            tasks.append(task)
            # 在背景處理檔案
            if background_tasks:
                background_tasks.add_task(voice_service.process_audio, file_path, params.model_dump())
        db.commit()
        for task in tasks:
            db.refresh(task)
        # 修正回傳格式
        return [TaskResponse.model_validate(task) for task in tasks]
    except HTTPException:
        raise
    except Exception as e:
        handle_error(e, "Error during batch upload")

@router.get("/upload_status")
def upload_status(task_id: str = Query(...)):
    # 這裡僅為範例，實際應根據 task_id 查詢進度
    progress = UPLOAD_PROGRESS.get(task_id, {"progress": 0, "status": "處理中…"})
    return JSONResponse(content=progress)
