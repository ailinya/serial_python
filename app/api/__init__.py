from fastapi import APIRouter

from app.api.serial_settings import serial_settings_router
from app.api.registers import registers_router


# 汇总各模块路由
v1_router = APIRouter()

# 保持原有路径不变（各子路由已在自身定义了 prefix）
v1_router.include_router(serial_settings_router)
v1_router.include_router(registers_router)


__all__ = ["v1_router"]
