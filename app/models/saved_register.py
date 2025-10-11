'''
Author: nll
Date: 2025-10-10
Description: 保存的寄存器模型
'''
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.settings.database import Base


class SavedRegister(Base):
    __tablename__ = "saved_registers"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(20), nullable=False, index=True, comment="寄存器地址")
    data = Column(String(20), nullable=False, comment="寄存器数据")
    value32bit = Column(String(20), nullable=False, comment="32位值")
    description = Column(String(200), nullable=True, comment="描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<SavedRegister(id={self.id}, address='{self.address}', data='{self.data}')>"
