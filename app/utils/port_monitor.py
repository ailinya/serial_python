'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 16:00:00
Description: 串口插拔事件监听工具
'''
import asyncio
import time
from typing import List, Set
from app.utils.serial_helper import SerialHelper


class PortMonitor:
    """串口插拔事件监听器"""
    
    def __init__(self, ws_manager):
        self.serial_helper = SerialHelper()
        self.ws_manager = ws_manager
        self._last_ports: Set[str] = set()
        self._monitoring = False
        self._monitor_task: asyncio.Task = None

    def start_monitoring(self):
        """开始监听串口插拔事件"""
        if not self._monitoring:
            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitor_ports())

    def stop_monitoring(self):
        """停止监听串口插拔事件"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()

    async def _monitor_ports(self):
        """监听串口变化的后台任务"""
        try:
            while self._monitoring:
                try:
                    # 获取当前可用串口
                    current_ports = set(self.serial_helper.list_available_ports())
                    
                    # 检查是否有变化
                    if current_ports != self._last_ports:
                        # 发送更新消息
                        await self.ws_manager.broadcast_serial_ports({
                            "type": "ports_update",
                            "ports": list(current_ports)
                        })
                        
                        # 更新上次的端口列表
                        self._last_ports = current_ports
                        
                        print(f"串口变化检测: {list(current_ports)}")
                    
                except Exception as e:
                    print(f"串口监听错误: {e}")
                
                # 每1秒检查一次
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            print("串口监听已停止")
        except Exception as e:
            print(f"串口监听异常: {e}")

    def get_current_ports(self) -> List[str]:
        """获取当前可用串口列表"""
        try:
            return self.serial_helper.list_available_ports()
        except Exception as e:
            print(f"获取串口列表失败: {e}")
            return []
