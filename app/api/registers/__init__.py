'''
Author: nll
Date: 2025-09-29 16:55:36
LastEditors: nll
LastEditTime: 2025-10-09 15:17:56
Description: 
'''
from fastapi import APIRouter
from .registers import router as _routes

registers_router = APIRouter(prefix="/api/register", tags=["registers"])
registers_router.include_router(_routes)

__all__ = ["registers_router"]
