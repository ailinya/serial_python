'''
Author: nll
Date: 2025-09-29 16:55:36
LastEditors: '艾琳爱' '2664840261@qq.com'
LastEditTime: 2025-10-11 14:56:20
Description: 
'''
from fastapi import APIRouter
from .registers import router as _routes
from .saved_registers import router as _saved_routes

registers_router = APIRouter(prefix="/api/register", tags=["registers"])
registers_router.include_router(_routes)
registers_router.include_router(_saved_routes, prefix="/saved", tags=["saved-registers"])

__all__ = ["registers_router"]
