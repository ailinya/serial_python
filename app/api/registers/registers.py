'''
Author: '艾琳爱' '2664840261@qq.com'
Date: 2025-09-29 16:55:45
LastEditors: '艾琳爱' '2664840261@qq.com'
LastEditTime: 2025-10-10 15:14:13
FilePath: \python_back\app\api\registers\registers.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
import openpyxl
import io
import base64

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
async def write_register(request: RegisterWriteRequest):
    """写入寄存器值"""
    return await register_controller.write_register_direct(request)


@router.post("/batch-read", response_model=BatchRegisterResponse)
async def batch_read_registers(request: dict):
    """批量读取寄存器 (手动验证)"""
    # 手动验证
    addresses = request.get("addresses")
    size = request.get("size")

    if not isinstance(addresses, list) or not all(isinstance(addr, str) for addr in addresses):
        raise HTTPException(status_code=422, detail="Invalid 'addresses' field. Expected a list of strings.")
    
    if not isinstance(size, int):
        raise HTTPException(status_code=422, detail="Invalid 'size' field. Expected an integer.")

    # 构造一个符合 Pydantic 模型的对象，然后传递给控制器
    validated_request = BatchRegisterReadRequest(addresses=addresses, size=size)
    return await register_controller.batch_read_registers(validated_request)


@router.post("/batch-write", response_model=BatchRegisterResponse)
async def batch_write_registers(request: BatchRegisterWriteRequest):
    """批量写入寄存器"""
    return await register_controller.batch_write_registers(request)


@router.post("/batch-write-v2", response_model=BatchRegisterResponse)
async def batch_write_registers_v2(request: BatchRegisterWriteRequestV2):
    """批量写入寄存器V2（使用嵌套模型验证）"""
    return await register_controller.batch_write_registers_v2(request)


@router.post("/send-command")
def send_command(request: dict):
    """发送串口命令"""
    try:
        command = request.get("command", "")
        if not command:
            raise HTTPException(status_code=400, detail="命令不能为空")
        
        # 检查串口是否已连接
        status = serial_helper.get_status()
        if not status["is_open"]:
            raise HTTPException(status_code=400, detail="串口未连接")
        
        # 发送命令到串口
        bytes_written = serial_helper.write_data(command, append_newline=True)
        
        return {
            "success": True,
            "message": f"命令发送成功，写入 {bytes_written} 字节"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送命令失败: {str(e)}")


class ExcelUploadRequest(BaseModel):
    file_content: str  # Base64 encoded string

@router.get("/definitions")
def get_definitions():
    """获取寄存器定义"""
    try:
        definitions = register_controller.get_register_definitions()
        return {
            "success": True,
            "data": definitions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取寄存器定义失败: {str(e)}")


@router.post("/upload-excel")
async def upload_excel(request: ExcelUploadRequest):
    """
    上传并解析寄存器定义的Excel文件 (Base64编码)
    """
    try:
        # 解码Base64字符串
        contents = base64.b64decode(request.file_content)
        
        # Use the controller to parse and cache the file
        parsed_data = register_controller.upload_and_parse_excel(contents)
        
        message = "Excel file parsed and definitions loaded successfully."
        if not parsed_data:
            message = "Excel file might be empty or in an unsupported format. No definitions were loaded."

        return {
            "success": True,
            "message": message,
            "data": parsed_data
        }
    except (base64.binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Invalid Base64 encoding.")
    except Exception as e:
        # Catch exceptions from the controller, including parsing errors
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the file: {e}")
