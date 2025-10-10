from fastapi import APIRouter
from .serial import router as _routes

serial_settings_router = APIRouter(prefix="/api/serial", tags=["serial"])
serial_settings_router.include_router(_routes)

__all__ = ["serial_settings_router"]
