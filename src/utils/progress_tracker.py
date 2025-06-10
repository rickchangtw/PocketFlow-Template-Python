from typing import Dict, Any, Optional
from datetime import datetime
import json
from fastapi import WebSocket
import asyncio

from src.config.logging import logger

class ProgressTracker:
    """Utility class for tracking task progress"""
    
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._websockets: Dict[str, WebSocket] = {}
    
    async def create_task(self, task_id: str, total_steps: int) -> None:
        """Create a new task with progress tracking"""
        self._tasks[task_id] = {
            "total_steps": total_steps,
            "current_step": 0,
            "status": "pending",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "progress": 0.0,
            "details": {}
        }
        logger.info(f"Created task {task_id} with {total_steps} steps")
    
    async def update_progress(
        self,
        task_id: str,
        step: int,
        status: str = "in_progress",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update task progress"""
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")
        
        task = self._tasks[task_id]
        task["current_step"] = step
        task["status"] = status
        task["progress"] = (step / task["total_steps"]) * 100
        
        if details:
            task["details"].update(details)
        
        # Notify websocket clients if connected
        if task_id in self._websockets:
            await self._notify_progress(task_id)
        
        logger.info(f"Updated progress for task {task_id}: {task['progress']}%")
    
    async def complete_task(
        self,
        task_id: str,
        status: str = "completed",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark task as completed"""
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")
        
        task = self._tasks[task_id]
        task["status"] = status
        task["current_step"] = task["total_steps"]
        task["progress"] = 100.0
        task["end_time"] = datetime.now().isoformat()
        
        if details:
            task["details"].update(details)
        
        # Notify websocket clients if connected
        if task_id in self._websockets:
            await self._notify_progress(task_id)
        
        logger.info(f"Completed task {task_id} with status: {status}")
    
    async def register_websocket(self, task_id: str, websocket: WebSocket) -> None:
        """Register websocket for real-time progress updates"""
        self._websockets[task_id] = websocket
        logger.info(f"Registered websocket for task {task_id}")
    
    async def unregister_websocket(self, task_id: str) -> None:
        """Unregister websocket"""
        if task_id in self._websockets:
            del self._websockets[task_id]
            logger.info(f"Unregistered websocket for task {task_id}")
    
    async def _notify_progress(self, task_id: str) -> None:
        """Send progress update to websocket client"""
        if task_id not in self._websockets:
            return
        
        websocket = self._websockets[task_id]
        try:
            await websocket.send_json(self._tasks[task_id])
        except Exception as e:
            logger.error(f"Error sending progress update: {str(e)}")
            await self.unregister_websocket(task_id)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get current task status"""
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")
        return self._tasks[task_id]
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tasks"""
        return self._tasks
    
    def clear_completed_tasks(self, max_age_hours: int = 24) -> None:
        """Clear completed tasks older than max_age_hours"""
        current_time = datetime.now()
        tasks_to_remove = []
        
        for task_id, task in self._tasks.items():
            if task["status"] in ["completed", "failed"]:
                end_time = datetime.fromisoformat(task["end_time"])
                age_hours = (current_time - end_time).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self._tasks[task_id]
            logger.info(f"Cleared completed task {task_id}")

# Create global instance
progress_tracker = ProgressTracker()
