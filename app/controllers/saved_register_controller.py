'''
Author: nll
Date: 2025-10-10
Description: 保存的寄存器控制器
'''
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.saved_register import SavedRegister
from app.schemas.register_schemas import (
    SavedRegisterCreate, SavedRegisterUpdate, SavedRegisterResponse, SavedRegisterList, SavedRegisterData,
    BatchDeleteRequest, BatchDeleteResponse
)


class SavedRegisterController:
    """保存的寄存器控制器"""
    
    def create_saved_register(self, db: Session, register: SavedRegisterCreate) -> SavedRegisterResponse:
        """创建保存的寄存器"""
        try:
            # 检查地址是否已存在
            existing = db.query(SavedRegister).filter(SavedRegister.address == register.address).first()
            if existing:
                raise HTTPException(
                    status_code=400, 
                    detail={
                        "error": "ADDRESS_EXISTS",
                        "message": f"地址 {register.address} 已存在",
                        "field": "address",
                        "value": register.address
                    }
                )
            
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
            
            register_data = SavedRegisterData.model_validate(db_register)
            return SavedRegisterResponse(
                success=True,
                message="寄存器保存成功",
                data=register_data.model_dump()
            )
            
        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            # 处理其他异常
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "INTERNAL_ERROR",
                    "message": f"保存寄存器时发生内部错误: {str(e)}",
                    "field": "general"
                }
            )

    def get_saved_registers(self, db: Session, skip: int = 0, limit: int = 100) -> SavedRegisterList:
        """获取所有保存的寄存器"""
        try:
            registers = db.query(SavedRegister).offset(skip).limit(limit).all()
            total = db.query(SavedRegister).count()
            
            register_items = [SavedRegisterData.model_validate(register).model_dump() for register in registers]
            
            return SavedRegisterList(
                success=True,
                message="获取寄存器列表成功",
                data={"items": register_items},
                total=total
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "INTERNAL_ERROR",
                    "message": f"获取寄存器列表时发生内部错误: {str(e)}",
                    "field": "general"
                }
            )

    def get_saved_register(self, db: Session, register_id: int) -> SavedRegisterResponse:
        """获取单个保存的寄存器"""
        try:
            register = db.query(SavedRegister).filter(SavedRegister.id == register_id).first()
            if not register:
                raise HTTPException(
                    status_code=404, 
                    detail={
                        "error": "REGISTER_NOT_FOUND",
                        "message": f"ID为 {register_id} 的保存寄存器未找到",
                        "field": "register_id",
                        "value": register_id
                    }
                )
            
            register_data = SavedRegisterData.model_validate(register)
            return SavedRegisterResponse(
                success=True,
                message="获取寄存器成功",
                data=register_data.model_dump()
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "INTERNAL_ERROR",
                    "message": f"获取寄存器时发生内部错误: {str(e)}",
                    "field": "general"
                }
            )

    def update_saved_register(self, db: Session, register_id: int, register: SavedRegisterUpdate) -> SavedRegisterResponse:
        """更新保存的寄存器"""
        try:
            db_register = db.query(SavedRegister).filter(SavedRegister.id == register_id).first()
            if not db_register:
                raise HTTPException(
                    status_code=404, 
                    detail={
                        "error": "REGISTER_NOT_FOUND",
                        "message": f"ID为 {register_id} 的保存寄存器未找到",
                        "field": "register_id",
                        "value": register_id
                    }
                )
            
            update_data = register.model_dump(exclude_unset=True)
            
            # 验证16进制格式
            if "data" in update_data:
                self._validate_hex_format(update_data["data"], "数据")
            if "value32bit" in update_data:
                self._validate_hex_format(update_data["value32bit"], "32位值")
            
            for key, value in update_data.items():
                setattr(db_register, key, value)
            
            db.commit()
            db.refresh(db_register)
            
            register_data = SavedRegisterData.model_validate(db_register)
            return SavedRegisterResponse(
                success=True,
                message="寄存器更新成功",
                data=register_data.model_dump()
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "INTERNAL_ERROR",
                    "message": f"更新寄存器时发生内部错误: {str(e)}",
                    "field": "general"
                }
            )

    def delete_saved_register(self, db: Session, register_id: int) -> None:
        """删除保存的寄存器"""
        try:
            db_register = db.query(SavedRegister).filter(SavedRegister.id == register_id).first()
            if not db_register:
                raise HTTPException(
                    status_code=404, 
                    detail={
                        "error": "REGISTER_NOT_FOUND",
                        "message": f"ID为 {register_id} 的保存寄存器未找到",
                        "field": "register_id",
                        "value": register_id
                    }
                )
            
            db.delete(db_register)
            db.commit()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "INTERNAL_ERROR",
                    "message": f"删除寄存器时发生内部错误: {str(e)}",
                    "field": "general"
                }
            )

    def _validate_hex_format(self, value: str, field_name: str) -> None:
        """验证16进制格式"""
        if not value.startswith('0x') and not value.startswith('0X'):
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "INVALID_HEX_FORMAT",
                    "message": f"{field_name}必须以0x或0X开头，当前值: {value}",
                    "field": field_name.lower(),
                    "value": value,
                    "expected_format": "0x开头，如0x20470c04"
                }
            )
        
        hex_part = value[2:] if value.startswith('0x') else value[2:]
        if not all(c in '0123456789ABCDEFabcdef' for c in hex_part):
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "INVALID_HEX_CHARACTERS",
                    "message": f"{field_name}包含非法字符，当前值: {value}",
                    "field": field_name.lower(),
                    "value": value,
                    "allowed_characters": "0-9, A-F, a-f"
                }
            )

    def batch_delete_registers(self, db: Session, request: BatchDeleteRequest) -> BatchDeleteResponse:
        """批量删除保存的寄存器"""
        try:
            results = []
            successful_count = 0
            failed_count = 0
            
            for register_id in request.register_ids:
                try:
                    # 查找寄存器
                    db_register = db.query(SavedRegister).filter(SavedRegister.id == register_id).first()
                    
                    if not db_register:
                        results.append({
                            "id": register_id,
                            "status": "failed",
                            "message": f"ID为 {register_id} 的寄存器未找到",
                            "timestamp": datetime.now().isoformat()
                        })
                        failed_count += 1
                        continue
                    
                    # 删除寄存器
                    db.delete(db_register)
                    db.commit()
                    
                    results.append({
                        "id": register_id,
                        "status": "success",
                        "message": "删除成功",
                        "timestamp": datetime.now().isoformat()
                    })
                    successful_count += 1
                    
                except Exception as e:
                    results.append({
                        "id": register_id,
                        "status": "failed",
                        "message": f"删除失败: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })
                    failed_count += 1
            
            return BatchDeleteResponse(
                success=True,
                message=f"批量删除完成，成功 {successful_count} 个，失败 {failed_count} 个",
                data={"deleted_ids": [r["id"] for r in results if r["status"] == "success"]},
                total_operations=len(request.register_ids),
                successful_operations=successful_count,
                failed_operations=failed_count,
                deleted_count=successful_count,
                results=results
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "INTERNAL_ERROR",
                    "message": f"批量删除寄存器时发生内部错误: {str(e)}",
                    "field": "general"
                }
            )
