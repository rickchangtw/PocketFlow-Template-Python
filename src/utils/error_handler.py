from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.config.logging import logger

class VoiceCloneError(Exception):
    """Base exception for VoiceClone Optimizer"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class FileValidationError(VoiceCloneError):
    """Exception for file validation errors"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class ProcessingError(VoiceCloneError):
    """Exception for processing errors"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

class OptimizationError(VoiceCloneError):
    """Exception for optimization errors"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

def setup_error_handlers(app: FastAPI):
    """Setup custom exception handlers"""
    
    @app.exception_handler(VoiceCloneError)
    async def voice_clone_exception_handler(request: Request, exc: VoiceCloneError):
        """Handle VoiceCloneError exceptions"""
        logger.error(f"VoiceCloneError: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message}
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.error(f"ValidationError: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={"error": "Validation error", "details": exc.errors()}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
