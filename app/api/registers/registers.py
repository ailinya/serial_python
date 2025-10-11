'''
Author: '艾琳爱' '2664840261@qq.com'
Date: 2025-09-29 16:55:45
LastEditors: '艾琳爱' '2664840261@qq.com'
LastEditTime: 2025-10-10 15:14:13
FilePath: \python_back\app\api\registers\registers.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.schemas.register_schemas import (
    RegisterReadRequest, RegisterWriteRequest, SerialConnectionRequest, RegisterAccessResponse,
    BatchRegisterReadRequest, BatchRegisterWriteRequest, BatchRegisterWriteRequestV2, BatchRegisterResponse
)
from app.utils.serial_helper import SerialHelper
from app.controllers.register_controller import RegisterController

router = APIRouter()
serial_helper = SerialHelper()
register_controller = RegisterController(serial_helper)


@router.post("/read", response_model=RegisterAccessResponse)
def read_register(request: RegisterReadRequest):
    """读取寄存器值"""
    return register_controller.read_register_direct(request)


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
        # 先检查串口状态，如果已打开则先关闭
        status = serial_helper.get_status()
        if status["is_open"]:
            serial_helper.close_port()
        
        # 打开新串口
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


@router.post("/disconnect")
def disconnect_serial():
    """串口断开连接接口"""
    try:
        serial_helper.close_port()
        return {
            "status": 200,
            "message": "串口已断开连接"
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"串口断开失败: {str(exc)}")
@router.post("/write", response_model=RegisterAccessResponse)
def write_register(request: RegisterWriteRequest):
    """写入寄存器值"""
    return register_controller.write_register_direct(request)


@router.post("/batch-read", response_model=BatchRegisterResponse)
def batch_read_registers(request: BatchRegisterReadRequest):
    """批量读取寄存器"""
    return register_controller.batch_read_registers(request)


@router.post("/batch-write", response_model=BatchRegisterResponse)
def batch_write_registers(request: BatchRegisterWriteRequest):
    """批量写入寄存器"""
    return register_controller.batch_write_registers(request)


@router.post("/batch-write-v2", response_model=BatchRegisterResponse)
def batch_write_registers_v2(request: BatchRegisterWriteRequestV2):
    """批量写入寄存器V2（使用嵌套模型验证）"""
    return register_controller.batch_write_registers_v2(request)

