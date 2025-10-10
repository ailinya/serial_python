'''
Author: '艾琳爱' '2664840261@qq.com'
Date: 2025-09-29 16:55:45
LastEditors: '艾琳爱' '2664840261@qq.com'
LastEditTime: 2025-10-10 14:18:43
FilePath: \python_back\app\api\registers\registers.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.settings.database import get_db
from app.schemas.register_schemas import (
    RegisterReadRequest, RegisterWriteRequest, RegisterLogResponse,
    RegisterLogList, RegisterOperationResponse, SerialConnectionRequest
)
from app.controllers.register_controller import RegisterController
from app.utils.serial_helper import SerialHelper

router = APIRouter()
serial_helper = SerialHelper()
register_controller = RegisterController(serial_helper)


@router.post("/read", response_model=RegisterOperationResponse)
def read_register(request: RegisterReadRequest, db: Session = Depends(get_db)):
    """读取寄存器"""
    return register_controller.read_register(db, request)


@router.get("/test")
def test_system():
    """系统测试接口 - 简单测试结果"""
    return {
        "status": 200,
        "message": "系统运行正常",
        "timestamp": "2025-10-09T16:00:00Z",
        "version": "1.0.0"
    }


@router.post("/connect")
def connect_serial(request: SerialConnectionRequest):
    """串口连接接口 - 不涉及数据库操作"""
    try:
        # 直接使用串口工具类打开串口
        serial_helper.open_port(
            port=request.com_num,
            baudrate=request.baud
        )
        
        return {
            "status": 200,
            "message": f"串口 {request.com_num} 连接成功",
            "port": request.com_num,
            "baudrate": request.baud
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"串口连接失败: {str(exc)}")
@router.post("/write", response_model=RegisterOperationResponse)
def write_register(request: RegisterWriteRequest, db: Session = Depends(get_db)):
    """写入寄存器"""
    return register_controller.write_register(db, request)


@router.get("/logs", response_model=RegisterLogList)
def get_register_logs(skip: int = 0, limit: int = 100, config_id: Optional[int] = None, 
                     db: Session = Depends(get_db)):
    """获取寄存器操作日志"""
    return register_controller.get_register_logs(db, skip, limit, config_id)