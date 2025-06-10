from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import HTMLResponse

from src.config.settings import settings
from src.config.logging import logger
from src.api.routes import upload, process, download
from src.api.websocket import handle_websocket
from src.models.base import init_db

# Create FastAPI application
app = FastAPI(
    title="VoiceClone Optimizer",
    description="An application for optimizing voice cloning quality",
    version="1.0.0"
)

# Initialize database
init_db()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="src/web/templates")

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(process.router, prefix="/api", tags=["process"])
app.include_router(download.router, prefix="/api", tags=["download"])

# WebSocket 路由
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await handle_websocket(websocket, client_id)

# 首頁（可選，展示前端頁面）
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
