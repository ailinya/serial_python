'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 16:00:00
Description: 串口相关校验模式
'''
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SerialConfigBase(BaseModel):
    """串口配置基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    port: str = Field(..., min_length=1, max_length=50, description="串口名称")
    baudrate: int = Field(115200, ge=300, le=115200, description="波特率")
    bytesize: int = Field(8, ge=5, le=8, description="数据位")
    parity: str = Field("N", pattern="^[NEO]$", description="校验位：N-无校验，E-偶校验，O-奇校验")
    stopbits: float = Field(1.0, ge=1.0, le=2.0, description="停止位")
    timeout: float = Field(0.05, ge=0.01, le=10.0, description="超时时间")
    description: Optional[str] = Field(None, max_length=500, description="描述")


class SerialConfigCreate(SerialConfigBase):
    """创建串口配置"""
    pass


class SerialConfigUpdate(BaseModel):
    """更新串口配置"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    port: Optional[str] = Field(None, min_length=1, max_length=50)
    baudrate: Optional[int] = Field(None, ge=300, le=115200)
    bytesize: Optional[int] = Field(None, ge=5, le=8)
    parity: Optional[str] = Field(None, pattern="^[NEO]$")
    stopbits: Optional[float] = Field(None, ge=1.0, le=2.0)
    timeout: Optional[float] = Field(None, ge=0.01, le=10.0)
    description: Optional[str] = Field(None, max_length=500)


class SerialConfigResponse(SerialConfigBase):
    """串口配置响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SerialConfigList(BaseModel):
    """串口配置列表响应"""
    items: List[SerialConfigResponse]
    total: int


class SerialOpenRequest(BaseModel):
    """打开串口请求"""
    config_id: int = Field(..., description="配置ID")


class SerialWriteRequest(BaseModel):
    """串口写入请求"""
    data: str = Field(..., min_length=1, max_length=1000, description="写入数据")
    append_newline: bool = Field(False, description="是否追加换行符")


class SerialStatusResponse(BaseModel):
    """串口状态响应"""
    is_open: bool
    port: Optional[str]
    baudrate: Optional[int]
    active_config_id: Optional[int]
