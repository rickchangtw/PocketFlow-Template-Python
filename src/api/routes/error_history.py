from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.utils.error_handler import ErrorHandler

router = APIRouter()
templates = Jinja2Templates(directory="templates")
error_handler = ErrorHandler()

@router.get("/error-history", response_class=HTMLResponse)
async def error_history_page(request: Request):
    """顯示錯誤歷史頁面"""
    errors = error_handler.get_error_history()
    print('[error_history] 查詢結果:', errors)
    return templates.TemplateResponse(
        "error_history.html",
        {
            "request": request,
            "errors": errors
        }
    ) 