from .auth import router as auth_router
from .complaints import router as complaints_router
from .notifications import router as notifications_router
from .admin import router as admin_router
from .chat import router as chat_router
from .impact import impact_router

__all__ = [
    "auth_router",
    "complaints_router",
    "notifications_router",
    "admin_router",
    "chat_router",
    "impact_router",
]
