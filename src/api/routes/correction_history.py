from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.utils.error_handler import ErrorHandler

router = APIRouter()
templates = Jinja2Templates(directory="templates")
error_handler = ErrorHandler()

@router.get("/correction-history", response_class=HTMLResponse)
async def correction_history_page(request: Request):
    """顯示修正歷史頁面"""
    corrections = error_handler.get_correction_history()
    print('[correction_history] 查詢結果:', corrections)
    return templates.TemplateResponse(
        "correction_history.html",
        {
            "request": request,
            "corrections": corrections
        }
    ) 