'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 16:00:00
Description: 寄存器操作日志模型
'''
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.settings.database import Base


class RegisterLog(Base):
    """寄存器操作日志表"""
    __tablename__ = "register_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    serial_config_id = Column(Integer, ForeignKey("serial_configs.id"), comment="串口配置ID")
    operation_type = Column(String(20), nullable=False, comment="操作类型：read/write")
    address = Column(Integer, nullable=False, comment="寄存器地址")
    value = Column(String(255), comment="写入值")
    response = Column(Text, comment="设备响应")
    status = Column(String(20), default="pending", comment="状态：pending/success/failed")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="操作时间")
    
    # 关联关系
    serial_config = relationship("SerialConfig", back_populates="register_logs")


# 更新 SerialConfig 模型以包含关联
from app.models.serial_config import SerialConfig
SerialConfig.register_logs = relationship("RegisterLog", back_populates="serial_config")
