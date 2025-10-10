'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 16:00:00
Description: 串口控制器
'''
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.serial_config import SerialConfig
from app.schemas.serial_schemas import (
    SerialConfigCreate, SerialConfigUpdate, SerialConfigResponse,
    SerialConfigList, SerialOpenRequest, SerialWriteRequest, SerialStatusResponse
)
from app.utils.serial_helper import SerialHelper


class SerialController:
    """串口控制器"""
    
    def __init__(self):
        self.serial_helper = SerialHelper()

    def list_ports(self) -> List[str]:
        """列出可用串口"""
        try:
            return self.serial_helper.list_available_ports()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def create_config(self, db: Session, config: SerialConfigCreate) -> SerialConfigResponse:
        """创建串口配置"""
        db_config = SerialConfig(**config.dict())
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return SerialConfigResponse.from_orm(db_config)

    def get_config(self, db: Session, config_id: int) -> SerialConfigResponse:
        """获取串口配置"""
        config = db.query(SerialConfig).filter(SerialConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        return SerialConfigResponse.from_orm(config)

    def list_configs(self, db: Session, skip: int = 0, limit: int = 100) -> SerialConfigList:
        """列出串口配置"""
        configs = db.query(SerialConfig).offset(skip).limit(limit).all()
        total = db.query(SerialConfig).count()
        return SerialConfigList(
            items=[SerialConfigResponse.from_orm(config) for config in configs],
            total=total
        )

    def update_config(self, db: Session, config_id: int, config_update: SerialConfigUpdate) -> SerialConfigResponse:
        """更新串口配置"""
        config = db.query(SerialConfig).filter(SerialConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        
        db.commit()
        db.refresh(config)
        return SerialConfigResponse.from_orm(config)

    def delete_config(self, db: Session, config_id: int) -> dict:
        """删除串口配置"""
        config = db.query(SerialConfig).filter(SerialConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        db.delete(config)
        db.commit()
        return {"status": "ok", "message": "配置已删除"}

    def open_port(self, db: Session, request: SerialOpenRequest) -> dict:
        """打开串口"""
        config = db.query(SerialConfig).filter(SerialConfig.id == request.config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")
        
        try:
            self.serial_helper.open_port(
                port=config.port,
                baudrate=config.baudrate,
                bytesize=config.bytesize,
                parity=config.parity,
                stopbits=config.stopbits,
                timeout=config.timeout
            )
            self.serial_helper.set_active_config_id(request.config_id)
            
            # 更新配置为激活状态
            config.is_active = True
            db.commit()
            
            return {"status": "ok", "message": f"串口 {config.port} 已打开"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def close_port(self, db: Session) -> dict:
        """关闭串口"""
        try:
            self.serial_helper.close_port()
            
            # 更新所有配置为非激活状态
            db.query(SerialConfig).update({"is_active": False})
            db.commit()
            
            return {"status": "ok", "message": "串口已关闭"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_status(self) -> SerialStatusResponse:
        """获取串口状态"""
        status = self.serial_helper.get_status()
        return SerialStatusResponse(**status)

    def write_data(self, request: SerialWriteRequest) -> dict:
        """写入数据"""
        try:
            bytes_written = self.serial_helper.write_data(
                data=request.data,
                append_newline=request.append_newline
            )
            return {"status": "ok", "bytes_written": bytes_written}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
