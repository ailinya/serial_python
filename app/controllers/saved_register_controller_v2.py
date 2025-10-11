'''
Author: nll
Date: 2025-10-10
Description: 使用自定义异常的保存寄存器控制器
'''
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.saved_register import SavedRegister
from app.schemas.register_schemas import (
    SavedRegisterCreate, SavedRegisterUpdate, SavedRegisterResponse, SavedRegisterList
)
from app.utils.custom_exceptions import (
    AddressExistsException, InvalidHexFormatException, InvalidHexCharactersException,
    RegisterNotFoundException, InternalServerException
)


class SavedRegisterControllerV2:
    """保存的寄存器控制器V2（使用自定义异常）"""
    
    def create_saved_register(self, db: Session, register: SavedRegisterCreate) -> SavedRegisterResponse:
        """创建保存的寄存器"""
        try:
            # 检查地址是否已存在
            existing = db.query(SavedRegister).filter(SavedRegister.address == register.address).first()
            if existing:
                raise AddressExistsException(register.address)
            
            # 验证16进制格式
            self._validate_hex_format(register.address, "地址")
            self._validate_hex_format(register.data, "数据")
            self._validate_hex_format(register.value32bit, "32位值")
            
            db_register = SavedRegister(
                address=register.address,
                data=register.data,
                value32bit=register.value32bit,
                description=register.description
            )
            db.add(db_register)
            db.commit()
            db.refresh(db_register)
            
            return SavedRegisterResponse.from_orm(db_register)
            
        except (AddressExistsException, InvalidHexFormatException, InvalidHexCharactersException):
            # 重新抛出自定义异常
            raise
        except Exception as e:
            # 处理其他异常
            raise InternalServerException("保存寄存器", str(e))

    def get_saved_register(self, db: Session, register_id: int) -> SavedRegisterResponse:
        """获取单个保存的寄存器"""
        try:
            register = db.query(SavedRegister).filter(SavedRegister.id == register_id).first()
            if not register:
                raise RegisterNotFoundException(register_id)
            
            return SavedRegisterResponse.from_orm(register)
        except RegisterNotFoundException:
            raise
        except Exception as e:
            raise InternalServerException("获取寄存器", str(e))

    def _validate_hex_format(self, value: str, field_name: str) -> None:
        """验证16进制格式"""
        if not value.startswith('0x') and not value.startswith('0X'):
            raise InvalidHexFormatException(field_name, value)
        
        hex_part = value[2:] if value.startswith('0x') else value[2:]
        if not all(c in '0123456789ABCDEFabcdef' for c in hex_part):
            raise InvalidHexCharactersException(field_name, value)
