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
    address: int = Field(..., ge=0, le=65535, description="寄存器地址")
    length: int = Field(1, ge=1, le=100, description="读取长度")
    config_id: Optional[int] = Field(None, description="串口配置ID，不指定则使用当前激活配置")


class RegisterWriteRequest(BaseModel):
    """寄存器写请求"""
    address: int = Field(..., ge=0, le=65535, description="寄存器地址")
    value: str = Field(..., min_length=1, max_length=255, description="写入值")
    config_id: Optional[int] = Field(None, description="串口配置ID，不指定则使用当前激活配置")


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


class RegisterOperationResponse(BaseModel):
    """寄存器操作响应"""
    status: str
    message: str
    log_id: Optional[int] = None
    sent_command: Optional[str] = None


class SerialConnectionRequest(BaseModel):
    """串口连接请求"""
    com_num: str = Field(..., min_length=1, max_length=20, description="串口编号，如 COM1, COM3")
    baud: int = Field(115200, ge=300, le=115200, description="波特率")
