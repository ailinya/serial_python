'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 16:00:00
Description: 串口配置模型
'''
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.settings.database import Base


class SerialConfig(Base):
    """串口配置表"""
    __tablename__ = "serial_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    port = Column(String(50), nullable=False, comment="串口名称")
    baudrate = Column(Integer, default=115200, comment="波特率")
    bytesize = Column(Integer, default=8, comment="数据位")
    parity = Column(String(1), default="N", comment="校验位")
    stopbits = Column(Float, default=1.0, comment="停止位")
    timeout = Column(Float, default=0.05, comment="超时时间")
    is_active = Column(Boolean, default=False, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    description = Column(Text, comment="描述")
