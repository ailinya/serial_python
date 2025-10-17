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
import pandas as pd

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


def parse_register_excel(file_content: bytes) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    """
    解析寄存器Excel文件，返回表格数据、位域定义和调试信息。
    """
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(file_content))
        all_sheets_data = []
        all_definitions = {}
        debug_info = []

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            
            # 1. 获取基地址
            try:
                base_address_str = str(sheet.cell(row=2, column=2).value).replace('_', '')
                base_address = int(base_address_str, 16)
            except (ValueError, TypeError, AttributeError) as e:
                debug_info.append(f"Sheet '{sheet_name}': Skipped. Invalid base address. Error: {e}")
                continue

            # 2. 获取表头
            header = [str(cell.value).strip() if cell.value is not None else "" for cell in sheet[4]]
            required_cols = ['名称', '偏移地址', '成员变量', '位域', '类型', '初始值', '成员描述']
            if not all(col in header for col in required_cols):
                debug_info.append(f"Sheet '{sheet_name}': Skipped. Missing required columns.")
                continue
            
            col_map = {name: i for i, name in enumerate(header)}
            
            sheet_data = {"name": sheet_name, "rows": []}
            sheet_registers_def = {}
            current_reg_name = None

            # 3. 遍历数据行
            for row_idx, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), start=5):
                reg_name_val = row[col_map['名称']]
                offset_val = row[col_map['偏移地址']]

                # 新的寄存器定义行
                if pd.notna(reg_name_val) and pd.notna(offset_val) and str(offset_val).strip().lower().startswith('0x'):
                    current_reg_name = str(reg_name_val)
                    try:
                        offset = int(str(offset_val), 16)
                        absolute_address = base_address + offset
                        address_hex = f"0x{absolute_address:08X}"
                        
                        # 添加到表格数据
                        sheet_data["rows"].append({
                            "address": address_hex,
                            "data": str(row[col_map['初始值']]),
                            "description": current_reg_name
                        })
                        
                        # 添加到位域定义
                        sheet_registers_def[current_reg_name] = {
                            "address": address_hex,
                            "init_value": str(row[col_map['初始值']]),
                            "bit_fields": []
                        }
                    except (ValueError, TypeError):
                        current_reg_name = None
                        continue
                
                # 位域信息行
                member_val = row[col_map['成员变量']]
                bitfield_val = row[col_map['位域']]
                if current_reg_name and pd.notna(member_val) and pd.notna(bitfield_val):
                    try:
                        bit_range = str(bitfield_val)
                        start_bit, end_bit = (int(p) for p in bit_range.split(':')) if ':' in bit_range else (int(bit_range), int(bit_range))
                        
                        sheet_registers_def[current_reg_name]["bit_fields"].append({
                            "name": str(member_val),
                            "start_bit": start_bit,
                            "end_bit": end_bit,
                            "type": str(row[col_map['类型']]).strip(),
                            "description": str(row[col_map['成员描述']])
                        })
                    except (ValueError, TypeError):
                        continue

            if sheet_data["rows"]:
                all_sheets_data.append(sheet_data)
            if sheet_registers_def:
                all_definitions[sheet_name] = sheet_registers_def
        
        return all_sheets_data, all_definitions, debug_info

    except Exception as e:
        return [], {}, [f"Critical Excel parsing error: {e}"]


class ExcelUploadRequest(BaseModel):
    file_content: str  # Base64 encoded string

@router.post("/upload-excel")
async def upload_excel(request: ExcelUploadRequest):
    """
    上传并解析寄存器定义的Excel文件 (Base64编码)
    """
    try:
        # 解码Base64字符串
        contents = base64.b64decode(request.file_content)
        
        table_data, definitions, debug_info = parse_register_excel(contents)
        
        message = "Excel file parsing complete."
        if not table_data and not debug_info:
            message = "Excel file is empty or has an unsupported format."
        elif not table_data and debug_info:
            message = "Parsing finished with issues. See debug info for details."

        return {
            "success": True,
            "message": message,
            "data": {
                "tables": table_data,
                "definitions": definitions
            },
            "debug": debug_info
        }
    except (base64.binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="无效的Base64编码")
    except Exception as e:
        # 捕获其他意外错误
        raise HTTPException(status_code=500, detail=f"处理文件时发生未知错误: {e}")
