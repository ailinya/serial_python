'''
Author: nll
Date: 2025-10-10
Description: 保存的寄存器API路由
'''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.settings.database import get_db
from app.schemas.register_schemas import (
    SavedRegisterCreate, SavedRegisterUpdate, SavedRegisterResponse, SavedRegisterList,
    BatchDeleteRequest, BatchDeleteResponse
)
from app.controllers.saved_register_controller import SavedRegisterController

router = APIRouter()
saved_register_controller = SavedRegisterController()


@router.post("/save", response_model=SavedRegisterResponse)
def create_saved_register(register: SavedRegisterCreate, db: Session = Depends(get_db)):
    """保存寄存器到数据库"""
    return saved_register_controller.create_saved_register(db, register)


@router.get("/list", response_model=SavedRegisterList)
def get_saved_registers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取所有保存的寄存器列表"""
    return saved_register_controller.get_saved_registers(db, skip, limit)


@router.get("/{register_id}", response_model=SavedRegisterResponse)
def get_saved_register(register_id: int, db: Session = Depends(get_db)):
    """获取单个保存的寄存器"""
    return saved_register_controller.get_saved_register(db, register_id)


@router.put("/{register_id}", response_model=SavedRegisterResponse)
def update_saved_register(register_id: int, register: SavedRegisterUpdate, db: Session = Depends(get_db)):
    """更新保存的寄存器"""
    return saved_register_controller.update_saved_register(db, register_id, register)


@router.delete("/{register_id}")
def delete_saved_register(register_id: int, db: Session = Depends(get_db)):
    """删除保存的寄存器"""
    saved_register_controller.delete_saved_register(db, register_id)
    return {
        "success": True,
        "message": "保存的寄存器已删除",
        "data": {"register_id": register_id}
    }


@router.post("/batch-delete", response_model=BatchDeleteResponse)
def batch_delete_saved_registers(request: BatchDeleteRequest, db: Session = Depends(get_db)):
    """批量删除保存的寄存器"""
    return saved_register_controller.batch_delete_registers(db, request)
