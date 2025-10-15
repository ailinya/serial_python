'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 16:00:00
Description: 寄存器控制器
'''
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
import time
import time

from app.models.register_log import RegisterLog
from app.models.serial_config import SerialConfig
from app.schemas.register_schemas import (
    RegisterLogResponse, RegisterLogList, RegisterReadRequest, 
    RegisterWriteRequest, RegisterAccessResponse, BatchRegisterReadRequest,
    BatchRegisterWriteRequest, BatchRegisterWriteRequestV2, BatchRegisterResponse
)
from app.utils.serial_helper import SerialHelper


class RegisterController:
    """寄存器控制器"""
    
    def __init__(self, serial_helper: SerialHelper):
        self.serial_helper = serial_helper


    def get_register_logs(self, db: Session, skip: int = 0, limit: int = 100, 
                         config_id: Optional[int] = None) -> RegisterLogList:
        """获取寄存器操作日志"""
        query = db.query(RegisterLog)
        if config_id:
            query = query.filter(RegisterLog.serial_config_id == config_id)
        
        logs = query.order_by(RegisterLog.created_at.desc()).offset(skip).limit(limit).all()
        total = query.count()
        
        return RegisterLogList(
            items=[RegisterLogResponse.from_orm(log) for log in logs],
            total=total
        )

    def read_register_direct(self, request: RegisterReadRequest) -> RegisterAccessResponse:
        """直接读取寄存器值（不涉及数据库）"""
        try:
            # 验证16进制地址格式
            if not request.address.startswith('0x') and not request.address.startswith('0X'):
                raise ValueError(f"地址必须以0x或0X开头，当前地址: {request.address}")
            
            # 移除0x前缀进行验证
            hex_part = request.address[2:] if request.address.startswith('0x') else request.address[2:]
            
            # 验证是否为有效的16进制字符
            if not all(c in '0123456789ABCDEFabcdef' for c in hex_part):
                raise ValueError(f"地址包含非法字符，当前地址: {request.address}")
            
            address = int(request.address, 16)
            
            # # 在读取寄存器前，先清空串口缓冲区中的缓存数据
            # if self.serial_helper._serial and self.serial_helper._serial.is_open:
            #     print("读取寄存器前清空串口缓冲区...")
            #     # 清空输入缓冲区，确保不会读取到之前的残留数据
            #     self.serial_helper._serial.reset_input_buffer()
            #     # 清空输出缓冲区，确保命令发送不会受到之前数据的影响
            #     self.serial_helper._serial.reset_output_buffer()
            #     # 短暂等待，确保缓冲区完全清空
            #     time.sleep(0.02)
            
            # 构建读取命令，包含字节数
            command = f"read {request.address} {request.size}"
            # 刷新串口输入缓存区，防止读取到旧数据
            self.serial_helper._serial.flushInput()
            # 发送命令到串口
            self.serial_helper.write_data(command, append_newline=True)
            # 等待设备响应
            time.sleep(0.1)  # 增加等待时间到0.1秒

            # 尝试读取响应数据
            try:
                if self.serial_helper._serial and self.serial_helper._serial.is_open:
                    response_data = self.serial_helper._serial.read(1024)
                    print(f"读取到{response_data}")  # 调试信息
                    if response_data:
                        response_text = response_data.decode("utf-8", errors="ignore").strip()
                        print(f":串口原始内容 {response_text}")  # 调试信息
                        
                        # 处理4字节的16进制返回值
                        processed_value = self._process_hex_response(response_text, request.size)
                        print(f":处理后值 {processed_value}")  # 调试信息
                        
                        return RegisterAccessResponse(
                            success=True,
                            message=f"寄存器读取成功，读取{request.size}字节",
                            address=request.address,
                            value=processed_value,
                            access_type="READ",
                            timestamp=datetime.now().isoformat()
                        )
            except Exception as e:
                print(f"读取响应时出错: {e}")  # 调试信息
                pass
            
            # 如果没有读取到响应，返回默认值
            return RegisterAccessResponse(
                success=True,
                message="寄存器读取命令已发送，但未收到响应",
                address=request.address,
                value=None,
                access_type="READ",
                timestamp=datetime.now().isoformat()
            )
        
        except ValueError:
            raise HTTPException(status_code=400, detail="地址格式错误，请使用16进制格式")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取寄存器失败: {str(e)}")

    def _process_hex_response(self, response_text: str, size: int) -> str:
        """处理16进制响应数据"""
        if not response_text:
            return None
        start_index = response_text.find(':') + 1
        end_index = response_text.find('\r\nOK')
        value = response_text[start_index:end_index]
        value = '0x' + value.strip().upper()
        print(f":匹配后的值 {value}")  # 调试信息
        return value

    def write_register_direct(self, request: RegisterWriteRequest) -> RegisterAccessResponse:
        """直接写入寄存器值（不涉及数据库）"""
        try:
            # 验证16进制地址和数据前缀格式
            if not request.address.startswith('0x') and not request.address.startswith('0X'):
                raise ValueError(f"地址必须以0x或0X开头，当前地址: {request.address}")
            
            if not request.value.startswith('0x') and not request.value.startswith('0X'):
                raise ValueError(f"值必须以0x或0X开头，当前值: {request.value}")
            
            # 验证地址格式
            hex_part = request.address[2:] if request.address.startswith('0x') else request.address[2:]
            if not all(c in '0123456789ABCDEFabcdef' for c in hex_part):
                raise ValueError(f"地址包含非法字符，当前地址: {request.address}")
            
            # 验证值格式
            value_hex_part = request.value[2:] if request.value.startswith('0x') else request.value[2:]
            if not all(c in '0123456789ABCDEFabcdef' for c in value_hex_part):
                raise ValueError(f"值包含非法字符，当前值: {request.value}")
            
            address = int(request.address, 16)
            value = int(request.value, 16)
            
            # 构建写入命令
            command = f"write {request.address} {request.value}"
            
            # 发送命令到串口
            self.serial_helper.write_data(command, append_newline=True)
            
            # 等待并读取响应
            time.sleep(0.1)  # 等待设备响应
            
            # 尝试读取响应数据
            try:
                if self.serial_helper._serial and self.serial_helper._serial.is_open:
                    response_data = self.serial_helper._serial.read(1024)
                    if response_data:
                        response_text = response_data.decode("utf-8", errors="ignore").strip()
                        # 处理响应格式，确保返回0X开头的格式
                        if response_text and not response_text.startswith('0X') and not response_text.startswith('0x'):
                            # 如果不是0X格式，尝试转换为0X格式
                            try:
                                # 如果响应是纯数字，转换为16进制
                                if response_text.isdigit():
                                    hex_value = hex(int(response_text))
                                    response_text = hex_value.upper().replace('0X', '0X')
                                else:
                                    # 如果已经是16进制格式，确保是0X开头
                                    if response_text.startswith('0x'):
                                        response_text = response_text.upper()
                                    elif not response_text.startswith('0X'):
                                        response_text = '0X' + response_text.upper()
                            except:
                                # 如果转换失败，保持原格式
                                pass
                        
                        return RegisterAccessResponse(
                            success=True,
                            message="寄存器写入成功",
                            address=request.address,
                            value=request.value,
                            access_type="WRITE",
                            timestamp=datetime.now().isoformat()
                        )
            except Exception:
                pass
            
            # 如果没有读取到响应，返回默认值
            return RegisterAccessResponse(
                success=True,
                message="寄存器写入命令已发送，但未收到响应",
                address=request.address,
                value=request.value,
                access_type="WRITE",
                timestamp=datetime.now().isoformat()
            )
        
        except ValueError:
            raise HTTPException(status_code=400, detail="地址或值格式错误，请使用16进制格式")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"写入寄存器失败: {str(e)}")

    def batch_read_registers(self, request: BatchRegisterReadRequest) -> BatchRegisterResponse:
        """批量读取寄存器"""
        results = []
        successful_count = 0
        failed_count = 0
        
        for address in request.addresses:
            try:
                # 创建单个读取请求
                read_request = RegisterReadRequest(
                    address=address,
                    size=request.size
                )
                
                # 添加小延迟避免串口通信冲突
                time.sleep(0.05)
                
                # 执行读取操作
                result = self.read_register_direct(read_request)
                
                results.append({
                    "address": address,
                    "success": True,  # 改为布尔值以匹配前端期望
                    "value": result.value,
                    "message": result.message,
                    "timestamp": result.timestamp
                })
                successful_count += 1
                
            except Exception as e:
                results.append({
                    "address": address,
                    "success": False,  # 改为布尔值以匹配前端期望
                    "value": None,
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                failed_count += 1
        
        return BatchRegisterResponse(
            success=True,
            message=f"批量读取完成，成功 {successful_count} 个，失败 {failed_count} 个",
            total_operations=len(request.addresses),
            successful_operations=successful_count,
            failed_operations=failed_count,
            results=results,
            timestamp=datetime.now().isoformat()
        )

    def batch_write_registers(self, request: BatchRegisterWriteRequest) -> BatchRegisterResponse:
        """批量写入寄存器"""
        results = []
        successful_count = 0
        failed_count = 0
        
        for operation in request.operations:
            try:
                # 验证操作数据
                address = operation.get("address")
                value = operation.get("value")
                
                if address is None or value is None:
                    raise ValueError("操作数据不完整，缺少 address 或 value")
                
                # 创建单个写入请求
                write_request = RegisterWriteRequest(
                    address=address,
                    value=value
                )
                
                # 添加小延迟避免串口通信冲突
                time.sleep(0.05)
                
                # 执行写入操作
                result = self.write_register_direct(write_request)
                
                results.append({
                    "address": address,
                    "value": value,
                    "success": True,  # 改为布尔值以匹配前端期望
                    "message": result.message,
                    "timestamp": result.timestamp
                })
                successful_count += 1
                
            except Exception as e:
                results.append({
                    "address": operation.get("address", "unknown"),
                    "value": operation.get("value", "unknown"),
                    "success": False,  # 改为布尔值以匹配前端期望
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                failed_count += 1
        
        return BatchRegisterResponse(
            success=True,
            message=f"批量写入完成，成功 {successful_count} 个，失败 {failed_count} 个",
            total_operations=len(request.operations),
            successful_operations=successful_count,
            failed_operations=failed_count,
            results=results,
            timestamp=datetime.now().isoformat()
        )

    def batch_write_registers_v2(self, request: BatchRegisterWriteRequestV2) -> BatchRegisterResponse:
        """批量写入寄存器V2（使用嵌套模型验证）"""
        results = []
        successful_count = 0
        failed_count = 0
        
        for operation in request.operations:
            try:
                # 创建单个写入请求
                write_request = RegisterWriteRequest(
                    address=operation.address,
                    value=operation.value
                )
                
                # 添加小延迟避免串口通信冲突
                time.sleep(0.05)
                
                # 执行写入操作
                result = self.write_register_direct(write_request)
                
                results.append({
                    "address": operation.address,
                    "value": operation.value,
                    "success": True,  # 改为布尔值以匹配前端期望
                    "message": result.message,
                    "timestamp": result.timestamp
                })
                successful_count += 1
                
            except Exception as e:
                results.append({
                    "address": operation.address,
                    "value": operation.value,
                    "success": False,  # 改为布尔值以匹配前端期望
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                failed_count += 1
        
        return BatchRegisterResponse(
            success=True,
            message=f"批量写入完成，成功 {successful_count} 个，失败 {failed_count} 个",
            total_operations=len(request.operations),
            successful_operations=successful_count,
            failed_operations=failed_count,
            results=results,
            timestamp=datetime.now().isoformat()
        )

    def update_log_response(self, db: Session, log_id: int, response: str, status: str = "success"):
        """更新日志响应（由 WebSocket 回调使用）"""
        log = db.query(RegisterLog).filter(RegisterLog.id == log_id).first()
        if log:
            log.response = response
            log.status = status
            db.commit()
