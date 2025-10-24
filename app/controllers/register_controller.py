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
import pandas as pd
import os
import asyncio
import io

from app.models.register_log import RegisterLog
from app.models.serial_config import SerialConfig
from app.schemas.register_schemas import (
    RegisterLogResponse, RegisterLogList, RegisterReadRequest, 
    RegisterWriteRequest, RegisterAccessResponse, BatchRegisterReadRequest,
    BatchRegisterWriteRequest, BatchRegisterWriteRequestV2, BatchRegisterResponse
)
from app.utils.serial_helper import SerialHelper


def _group_contiguous_addresses(addresses: List[str], size: int, max_regs_per_block: int = 32) -> List[dict]:
    """
    将地址列表分组为连续的内存块，并遵守每个块的最大寄存器数量限制。
    """
    if not addresses:
        return []

    int_addresses = sorted([int(addr, 16) for addr in addresses])

    groups = []
    if not int_addresses:
        return []
        
    current_group = [int_addresses[0]]

    for i in range(1, len(int_addresses)):
        # 检查连续性和块大小限制
        if int_addresses[i] == current_group[-1] + size and len(current_group) < max_regs_per_block:
            current_group.append(int_addresses[i])
        else:
            groups.append(current_group)
            current_group = [int_addresses[i]]
    
    groups.append(current_group)

    blocks = []
    for group in groups:
        if not group: continue
        start_address = group[0]
        length = len(group) * size
        original_addrs_in_block = [f"0x{addr:08X}" for addr in group]
        blocks.append({
            "start_address": f"0x{start_address:08X}",
            "length": length,
            "original_addresses": original_addrs_in_block
        })
        
    return blocks


class RegisterController:
    """寄存器控制器"""
    
    def __init__(self, serial_helper: SerialHelper):
        self.serial_helper = serial_helper
        self.register_definitions = {}  # In-memory storage for register definitions

    def get_register_definitions(self):
        """获取当前加载的寄存器定义"""
        # Simply return the definitions from memory.
        # The frontend can handle an empty object if nothing is loaded.
        return self.register_definitions

    def upload_and_parse_excel(self, file_content: bytes):
        """解析上传的Excel文件并将其存储在内存中"""
        try:
            xls = pd.ExcelFile(io.BytesIO(file_content))
            all_definitions = {}

            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                
                # 1. 获取基地址
                try:
                    base_address_str = df.iloc[1, 1] # B2
                    if isinstance(base_address_str, str):
                        base_address_str = base_address_str.replace('_', '')
                    base_address = int(str(base_address_str), 16)
                except (ValueError, TypeError, IndexError):
                    continue # 基地址无效或不存在，跳过此sheet

                # 2. 动态查找列索引
                header_row_index = 3
                if len(df) <= header_row_index:
                    continue # sheet太短，没有表头
                
                header_row = df.iloc[header_row_index]
                col_map = {str(col_name).strip(): i for i, col_name in enumerate(header_row) if pd.notna(col_name)}

                # 检查必需的列是否存在
                required_cols = ['名称', '偏移地址', '成员变量', '位域', '类型', '初始值', '成员描述']
                if not all(col in col_map for col in required_cols):
                    continue # 缺少关键列，跳过此sheet

                name_idx = col_map['名称']
                offset_idx = col_map['偏移地址']
                init_val_idx = col_map['初始值']
                member_idx = col_map['成员变量']
                bitfield_idx = col_map['位域']
                type_idx = col_map['类型']
                desc_idx = col_map['成员描述']

                # 3. 遍历数据行进行解析
                sheet_registers = {}
                current_reg_name = None
                
                for index, row in df.iterrows():
                    if index <= header_row_index: # 跳过表头及之前的行
                        continue

                    reg_name_val = row[name_idx]
                    offset_val = row[offset_idx]

                    # 步骤1: 检查是否为新的寄存器定义行
                    if pd.notna(reg_name_val) and pd.notna(offset_val) and str(offset_val).strip().lower().startswith('0x'):
                        current_reg_name = str(reg_name_val)
                        
                        try:
                            offset = int(str(offset_val), 16)
                            absolute_address = base_address + offset
                            address_hex = f"0x{absolute_address:08X}"

                            sheet_registers[current_reg_name] = {
                                "address": address_hex,
                                "init_value": row[init_val_idx],
                                "bit_fields": []
                            }
                        except (ValueError, TypeError):
                            current_reg_name = None
                            continue
                    
                    # 步骤2: 检查当前行是否有位域信息
                    member_val = row[member_idx]
                    bitfield_val = row[bitfield_idx]
                    if current_reg_name and pd.notna(member_val) and pd.notna(bitfield_val):
                        bit_field_name = str(member_val)
                        bit_range = str(bitfield_val)
                        field_type = str(row[type_idx]).strip()

                        if field_type.upper() == 'RO' or 'RESERVED' in bit_field_name.upper():
                            final_type = 'RO'
                        else:
                            final_type = field_type

                        try:
                            if ':' in bit_range:
                                parts = bit_range.split(':')
                                start_bit = int(parts[0])
                                end_bit = int(parts[1])
                            else:
                                start_bit = int(bit_range)
                                end_bit = int(bit_range)
                            
                            if current_reg_name in sheet_registers:
                                description = str(row[desc_idx]) if pd.notna(row[desc_idx]) else ''
                                sheet_registers[current_reg_name]["bit_fields"].append({
                                    "name": bit_field_name,
                                    "start_bit": start_bit,
                                    "end_bit": end_bit,
                                    "type": final_type,
                                    "description": description
                                })
                        except (ValueError, TypeError):
                            continue

                if sheet_registers:
                    all_definitions[sheet_name] = sheet_registers
            
            self.register_definitions = all_definitions  # Store parsed data in memory
            return all_definitions
        except Exception as e:
            # Clear definitions on failure to avoid serving stale/bad data
            self.register_definitions = {}
            raise HTTPException(status_code=500, detail=f"Failed to parse register file: {str(e)}")

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

    async def write_register_direct(self, request: RegisterWriteRequest, wait_for_ok: bool = True) -> RegisterAccessResponse:
        """(异步)直接写入寄存器值，可选是否等待OK"""
        try:
            if not request.address.startswith('0x') and not request.address.startswith('0X'):
                raise ValueError(f"地址必须以0x或0X开头，当前地址: {request.address}")
            if not request.value.startswith('0x') and not request.value.startswith('0X'):
                raise ValueError(f"值必须以0x或0X开头，当前值: {request.value}")

            command = f"write {request.address} {request.value}"

            if not self.serial_helper._serial or not self.serial_helper._serial.is_open:
                raise ConnectionError("Serial port is not open.")

            # 写入命令
            await self.serial_helper.async_write(command)

            if wait_for_ok:
                # 使用健壮的读取循环等待 "OK"
                response_buffer = bytearray()
                terminator = b"OK\r\n"
                start_time = time.time()
                timeout = 3.0

                while terminator not in response_buffer:
                    if time.time() - start_time > timeout:
                        raise TimeoutError("写入命令后等待OK响应超时")
                    
                    chunk = await self.serial_helper.async_read(64)
                    if chunk:
                        response_buffer.extend(chunk)
                    else:
                        await asyncio.sleep(0.01)
            
            return RegisterAccessResponse(
                success=True,
                message="寄存器写入命令已发送",
                address=request.address,
                value=request.value,
                access_type="WRITE",
                timestamp=datetime.now().isoformat()
            )
        
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=f"地址或值格式错误: {ve}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"写入寄存器失败: {str(e)}")

    async def batch_read_registers(self, request: BatchRegisterReadRequest) -> BatchRegisterResponse:
        """批量读取寄存器 (异步优化版)"""
        try:
            # The block size limit is now a safeguard, not the primary fix.
            address_blocks = _group_contiguous_addresses(request.addresses, request.size)
            
            all_results_map = {}
            successful_count = 0
            failed_count = 0

            for block in address_blocks:
                try:
                    command = f"read {block['start_address']} {block['length']}"
                    
                    if not self.serial_helper._serial or not self.serial_helper._serial.is_open:
                        raise ConnectionError("Serial port is not open.")

                    # --- CRITICAL FIX: Flush input buffer before writing ---
                    await self.serial_helper.async_flush_input()
                    
                    await self.serial_helper.async_write(command)
                    
                    # --- Robust reading loop with terminator and timeout ---
                    response_buffer = bytearray()
                    terminator = b"OK\r\n"
                    start_time = time.time()
                    timeout = 3.0  # 3-second timeout for the entire block read

                    while terminator not in response_buffer:
                        if time.time() - start_time > timeout:
                            raise TimeoutError(f"Timeout waiting for response terminator '{terminator.decode().strip()}'")
                        
                        chunk = await self.serial_helper.async_read(128)
                        if chunk:
                            response_buffer.extend(chunk)
                        else:
                            await asyncio.sleep(0.01)
                    
                    response_data = bytes(response_buffer)
                    # --- End of robust reading loop ---

                    if response_data:
                        response_text = response_data.decode("utf-8", errors="ignore").strip()
                        hex_body = self._process_merged_hex_response(response_text)
                        
                        expected_len = block['length'] * 2
                        if len(hex_body) >= expected_len:
                            hex_body = hex_body[:expected_len]
                            
                            for j, original_addr in enumerate(block['original_addresses']):
                                start_idx = j * request.size * 2
                                end_idx = start_idx + request.size * 2
                                value = "0x" + hex_body[start_idx:end_idx].upper()
                                
                                all_results_map[original_addr] = {
                                    "address": original_addr, "success": True, "value": value,
                                    "message": "读取成功", "timestamp": datetime.now().isoformat()
                                }
                                successful_count += 1
                        else:
                            raise ValueError(f"Merged read response length mismatch. Expected {expected_len}, got {len(hex_body)}.")
                    else:
                        raise ValueError("No response from merged read.")

                except Exception as e:
                    for addr in block['original_addresses']:
                        all_results_map[addr] = {
                            "address": addr, "success": False, "value": None,
                            "message": f"块读取失败: {str(e)}", "timestamp": datetime.now().isoformat()
                        }
                        failed_count += 1
            
            final_results = [all_results_map.get(addr) for addr in request.addresses if addr in all_results_map]

            return BatchRegisterResponse(
                success=True,
                message=f"批量读取完成，成功 {successful_count} 个，失败 {failed_count} 个",
                total_operations=len(request.addresses),
                successful_operations=successful_count,
                failed_operations=failed_count,
                results=final_results,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"批量读取时发生严重错误: {str(e)}")

    def _process_merged_hex_response(self, response_text: str) -> str:
        """从合并读取的多行响应中提取并拼接纯十六进制数据。"""
        if not response_text:
            return ""
        
        hex_parts = []
        lines = response_text.splitlines() # 按行分割
        
        for line in lines:
            line = line.strip()
            if ":" in line:
                # 提取冒号后面的部分
                try:
                    hex_value = line.split(":")[1].strip()
                    # 移除可能存在的'0x'前缀
                    if hex_value.lower().startswith('0x'):
                        hex_value = hex_value[2:]
                    hex_parts.append(hex_value)
                except IndexError:
                    continue # 忽略格式不正确的行
        
        # 将所有提取的十六进制部分拼接成一个长字符串
        return "".join(hex_parts)

    async def batch_write_registers(self, request: BatchRegisterWriteRequest) -> BatchRegisterResponse:
        """(异步优化, "火力全开"模式)批量写入寄存器"""
        
        # --- 清空一次缓冲区，为命令风暴做准备 ---
        if self.serial_helper._serial and self.serial_helper._serial.is_open:
            await self.serial_helper.async_flush_input()

        tasks = []
        for operation in request.operations:
            address = operation.get("address")
            value = operation.get("value")
            if address is None or value is None:
                continue # 跳过无效操作
            
            write_request = RegisterWriteRequest(address=address, value=value)
            # 创建一个不等待OK的任务
            task = self.write_register_direct(write_request, wait_for_ok=False)
            tasks.append(task)

        # --- 并发执行所有写入任务 ---
        await asyncio.gather(*tasks)

        # --- 由于我们没有等待确认，所以只能假设所有操作都已“成功”发送 ---
        results = [{
            "address": op.get("address"), "value": op.get("value"),
            "success": True, "message": "写入命令已发送",
            "timestamp": datetime.now().isoformat()
        } for op in request.operations]
        
        return BatchRegisterResponse(
            success=True,
            message=f"批量写入命令已全部发送 ({len(tasks)} 个)",
            total_operations=len(tasks),
            successful_operations=len(tasks),
            failed_operations=0,
            results=results,
            timestamp=datetime.now().isoformat()
        )

    async def batch_write_registers_v2(self, request: BatchRegisterWriteRequestV2) -> BatchRegisterResponse:
        """(异步优化)批量写入寄存器V2（使用嵌套模型验证）"""
        results = []
        successful_count = 0
        failed_count = 0
        
        for operation in request.operations:
            try:
                write_request = RegisterWriteRequest(
                    address=operation.address,
                    value=operation.value
                )
                
                await self.write_register_direct(write_request)
                
                results.append({
                    "address": operation.address,
                    "value": operation.value,
                    "success": True,
                    "message": "写入成功",
                    "timestamp": datetime.now().isoformat()
                })
                successful_count += 1
                
            except Exception as e:
                failed_count += 1
                results.append({
                    "address": operation.address,
                    "value": operation.value,
                    "success": False,
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
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
