'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 16:00:00
Description: 寄存器控制器
'''
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.register_log import RegisterLog
from app.models.serial_config import SerialConfig
from app.schemas.register_schemas import (
    RegisterReadRequest, RegisterWriteRequest, RegisterLogResponse,
    RegisterLogList, RegisterOperationResponse
)
from app.utils.serial_helper import SerialHelper


class RegisterController:
    """寄存器控制器"""
    
    def __init__(self, serial_helper: SerialHelper):
        self.serial_helper = serial_helper

    def read_register(self, db: Session, request: RegisterReadRequest) -> RegisterOperationResponse:
        """读取寄存器"""
        # 确定使用的配置ID
        config_id = request.config_id
        if not config_id:
            status = self.serial_helper.get_status()
            if not status["is_open"]:
                raise HTTPException(status_code=400, detail="串口未打开")
            config_id = status["active_config_id"]
            if not config_id:
                raise HTTPException(status_code=400, detail="未指定串口配置且无激活配置")
        
        # 验证配置存在
        config = db.query(SerialConfig).filter(SerialConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="串口配置不存在")
        
        # 创建操作日志
        log = RegisterLog(
            serial_config_id=config_id,
            operation_type="read",
            address=request.address,
            status="pending"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        try:
            # 构建命令并发送
            command = f"READ {request.address} {request.length}"
            self.serial_helper.write_data(command, append_newline=True)
            
            return RegisterOperationResponse(
                status="ok",
                message="读取命令已发送，响应请通过 WebSocket 接收",
                log_id=log.id,
                sent_command=command
            )
        except Exception as e:
            # 更新日志状态为失败
            log.status = "failed"
            log.response = str(e)
            db.commit()
            raise HTTPException(status_code=500, detail=str(e))

    def write_register(self, db: Session, request: RegisterWriteRequest) -> RegisterOperationResponse:
        """写入寄存器"""
        # 确定使用的配置ID
        config_id = request.config_id
        if not config_id:
            status = self.serial_helper.get_status()
            if not status["is_open"]:
                raise HTTPException(status_code=400, detail="串口未打开")
            config_id = status["active_config_id"]
            if not config_id:
                raise HTTPException(status_code=400, detail="未指定串口配置且无激活配置")
        
        # 验证配置存在
        config = db.query(SerialConfig).filter(SerialConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="串口配置不存在")
        
        # 创建操作日志
        log = RegisterLog(
            serial_config_id=config_id,
            operation_type="write",
            address=request.address,
            value=request.value,
            status="pending"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        try:
            # 构建命令并发送
            command = f"WRITE {request.address} {request.value}"
            self.serial_helper.write_data(command, append_newline=True)
            
            return RegisterOperationResponse(
                status="ok",
                message="写入命令已发送，响应请通过 WebSocket 接收",
                log_id=log.id,
                sent_command=command
            )
        except Exception as e:
            # 更新日志状态为失败
            log.status = "failed"
            log.response = str(e)
            db.commit()
            raise HTTPException(status_code=500, detail=str(e))

    def get_register_logs(self, db: Session, skip: int = 0, limit: int = 100, 
                         config_id: Optional[int] = None) -> RegisterLogList:
        """获取寄存器操作日志"""
        query = db.query(RegisterLog)
        if config_id:
            query = query.filter(RegisterLog.serial_config_id == config_id)
        
        logs = query.order_by(RegisterLog.created_at.desc()).offset(skip).limit(limit).all()
        total = query.count()
        
        return RegisterLogList(
            items=[RegisterLogResponse.from_orm(log) for log in logs],
            total=total
        )

    def update_log_response(self, db: Session, log_id: int, response: str, status: str = "success"):
        """更新日志响应（由 WebSocket 回调使用）"""
        log = db.query(RegisterLog).filter(RegisterLog.id == log_id).first()
        if log:
            log.response = response
            log.status = status
            db.commit()
