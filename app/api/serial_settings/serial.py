from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.settings.database import get_db
from app.schemas.serial_schemas import (
    SerialConfigCreate, SerialConfigUpdate, SerialConfigResponse,
    SerialConfigList, SerialOpenRequest, SerialWriteRequest, SerialStatusResponse
)
from app.controllers.serial_controller import SerialController

router = APIRouter()
serial_controller = SerialController()


@router.get("/ports", response_model=List[str])
def list_ports():
    """列出可用串口"""
    return serial_controller.list_ports()


@router.post("/configs", response_model=SerialConfigResponse)
def create_config(config: SerialConfigCreate, db: Session = Depends(get_db)):
    """创建串口配置"""
    return serial_controller.create_config(db, config)


@router.get("/configs", response_model=SerialConfigList)
def list_configs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """列出串口配置"""
    return serial_controller.list_configs(db, skip, limit)


@router.get("/configs/{config_id}", response_model=SerialConfigResponse)
def get_config(config_id: int, db: Session = Depends(get_db)):
    """获取串口配置"""
    return serial_controller.get_config(db, config_id)


@router.put("/configs/{config_id}", response_model=SerialConfigResponse)
def update_config(config_id: int, config_update: SerialConfigUpdate, db: Session = Depends(get_db)):
    """更新串口配置"""
    return serial_controller.update_config(db, config_id, config_update)


@router.delete("/configs/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    """删除串口配置"""
    return serial_controller.delete_config(db, config_id)


@router.post("/open")
def open_port(request: SerialOpenRequest, db: Session = Depends(get_db)):
    """打开串口"""
    return serial_controller.open_port(db, request)


@router.post("/close")
def close_port(db: Session = Depends(get_db)):
    """关闭串口"""
    return serial_controller.close_port(db)


@router.get("/status", response_model=SerialStatusResponse)
def get_status():
    """获取串口状态"""
    return serial_controller.get_status()


@router.post("/write")
def write_data(request: SerialWriteRequest):
    """写入数据"""
    return serial_controller.write_data(request)