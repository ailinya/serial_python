'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 16:00:00
Description: 寄存器相关校验模式
'''
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RegisterReadRequest(BaseModel):
    """寄存器读请求"""
    address: str = Field(..., description="寄存器地址（16进制）", example="0x20470c04")
    size: int = Field(4, ge=1, le=8, description="读取字节数，默认4字节", example=4)


class RegisterWriteRequest(BaseModel):
    """寄存器写请求"""
    address: str = Field(..., description="寄存器地址（16进制）", example="0x20470c04")
    value: str = Field(..., description="要写入的值（16进制）", example="0x31335233")


class RegisterAccessResponse(BaseModel):
    """寄存器访问响应"""
    success: bool
    message: str
    address: str
    value: Optional[str] = None
    access_type: str
    timestamp: str


class RegisterLogResponse(BaseModel):
    """寄存器操作日志响应"""
    id: int
    operation_type: str
    address: int
    value: Optional[str]
    response: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class RegisterLogList(BaseModel):
    """寄存器日志列表响应"""
    items: List[RegisterLogResponse]
    total: int




class SerialConnectionRequest(BaseModel):
    """串口连接请求"""
    com_num: str = Field(..., min_length=1, max_length=20, description="串口编号，如 COM1, COM3")
    baud: int = Field(115200, ge=300, le=115200, description="波特率")


class BatchRegisterReadRequest(BaseModel):
    """批量寄存器读请求"""
    addresses: List[str] = Field(..., min_items=1, max_items=20, description="寄存器地址列表，最多20个")
    size: int = Field(4, ge=1, le=8, description="每个地址的读取字节数，默认4字节")


class BatchRegisterWriteRequest(BaseModel):
    """批量寄存器写请求"""
    operations: List[dict] = Field(..., min_items=1, max_items=20, description="写入操作列表，最多20个")
    
    class Config:
        schema_extra = {
            "example": {
                "operations": [
                    {"address": "0x20470c04", "value": "0xFFB25233"},
                    {"address": "0x20470c08", "value": "0x12345678"}
                ]
            }
        }


class BatchRegisterWriteRequestV2(BaseModel):
    """批量寄存器写请求V2（使用嵌套模型）"""
    operations: List['BatchOperationItem'] = Field(..., min_items=1, max_items=20, description="写入操作列表")
    
    class Config:
        schema_extra = {
            "example": {
                "operations": [
                    {"address": "0x20470c04", "value": "0xFFB25233"},
                    {"address": "0x20470c08", "value": "0x12345678"}
                ]
            }
        }


class BatchOperationItem(BaseModel):
    """批量操作项"""
    address: str = Field(..., description="寄存器地址（16进制）", example="0x20470c04")
    value: str = Field(..., description="要写入的值（16进制）", example="0xFFB25233")


class BatchRegisterResponse(BaseModel):
    """批量寄存器操作响应"""
    success: bool
    message: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    results: List[dict] = Field(..., description="每个操作的结果")
    timestamp: str


class SavedRegisterCreate(BaseModel):
    """保存寄存器请求"""
    address: str = Field(..., description="寄存器地址（16进制）", example="0x20470c04")
    data: str = Field(..., description="寄存器数据（16进制）", example="0XFDB25233")
    value32bit: str = Field(..., description="32位值（16进制）", example="0XFDB25233")
    description: str = Field(None, max_length=200, description="描述", example="GPIO配置寄存器")


class SavedRegisterUpdate(BaseModel):
    """更新保存的寄存器请求"""
    data: str = Field(None, description="寄存器数据（16进制）", example="0XFDB25233")
    value32bit: str = Field(None, description="32位值（16进制）", example="0XFDB25233")
    description: str = Field(None, max_length=200, description="描述", example="GPIO配置寄存器")


class SavedRegisterResponse(BaseModel):
    """保存的寄存器响应"""
    success: bool = True
    message: str = "操作成功"
    data: dict = Field(..., description="寄存器数据")
    
    class Config:
        from_attributes = True


class SavedRegisterData(BaseModel):
    """保存的寄存器数据"""
    id: int
    address: str
    data: str
    value32bit: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SavedRegisterList(BaseModel):
    """保存的寄存器列表响应"""
    success: bool = True
    message: str = "获取成功"
    data: dict = Field(..., description="列表数据")
    total: int


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    register_ids: List[int] = Field(..., description="要删除的寄存器ID列表", example=[1, 2, 3])


class BatchDeleteResponse(BaseModel):
    """批量删除响应"""
    success: bool = True
    message: str = "批量删除完成"
    data: dict = Field(..., description="删除结果数据")
    total_operations: int
    successful_operations: int
    failed_operations: int
    deleted_count: int = Field(..., description="实际删除的数量")
    results: List[dict]
