'''
Author: nll
Date: 2025-10-10
Description: 自定义异常类
'''
from fastapi import HTTPException
from typing import Dict, Any, Optional


class CustomHTTPException(HTTPException):
    """自定义HTTP异常，支持结构化错误信息"""
    
    def __init__(
        self, 
        status_code: int, 
        error_code: str, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[str] = None,
        **kwargs
    ):
        self.error_code = error_code
        self.field = field
        self.value = value
        
        # 构建响应数据
        response_data = {
            "error": error_code,
            "message": message
        }
        
        if field:
            response_data["field"] = field
        if value:
            response_data["value"] = value
        
        # 添加其他自定义字段
        response_data.update(kwargs)
        
        super().__init__(status_code=status_code, detail=response_data)


# 预定义的异常类
class AddressExistsException(CustomHTTPException):
    def __init__(self, address: str):
        super().__init__(
            status_code=400,
            error_code="ADDRESS_EXISTS",
            message=f"地址 {address} 已存在",
            field="address",
            value=address
        )


class InvalidHexFormatException(CustomHTTPException):
    def __init__(self, field_name: str, value: str):
        super().__init__(
            status_code=400,
            error_code="INVALID_HEX_FORMAT",
            message=f"{field_name}必须以0x或0X开头，当前值: {value}",
            field=field_name.lower(),
            value=value,
            expected_format="0x开头，如0x20470c04"
        )


class InvalidHexCharactersException(CustomHTTPException):
    def __init__(self, field_name: str, value: str):
        super().__init__(
            status_code=400,
            error_code="INVALID_HEX_CHARACTERS",
            message=f"{field_name}包含非法字符，当前值: {value}",
            field=field_name.lower(),
            value=value,
            allowed_characters="0-9, A-F, a-f"
        )


class RegisterNotFoundException(CustomHTTPException):
    def __init__(self, register_id: int):
        super().__init__(
            status_code=404,
            error_code="REGISTER_NOT_FOUND",
            message=f"ID为 {register_id} 的保存寄存器未找到",
            field="register_id",
            value=str(register_id)
        )


class InternalServerException(CustomHTTPException):
    def __init__(self, operation: str, error: str):
        super().__init__(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message=f"{operation}时发生内部错误: {error}",
            field="general"
        )
