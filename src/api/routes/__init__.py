from .upload import router as upload_router
from .process import router as process_router
from .download import router as download_router
from .error_history import router as error_history_router
from .correction_history import router as correction_history_router

__all__ = [
    'upload_router',
    'process_router',
    'download_router',
    'error_history_router',
    'correction_history_router'
]
