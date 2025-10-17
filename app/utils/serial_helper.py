'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: '艾琳爱' '2664840261@qq.com'
LastEditTime: 2025-10-10 14:29:05
Description: 串口工具类
'''
import asyncio
import threading
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy.orm import Session

# For runtime, to handle cases where pyserial is not installed
_serial_module = None
_list_ports_func = None

try:
    import serial as _serial_module
    from serial.tools import list_ports as _list_ports_func
except ImportError:
    pass  # Modules will remain None, handled in the methods

# For type checking, to allow static analysis without runtime errors
if TYPE_CHECKING:
    import serial
    from serial.tools import list_ports


class SerialHelper:
    """串口操作工具类"""
    
    def __init__(self):
        self._serial: Optional["serial.Serial"] = None
        self._lock = threading.Lock()
        self._reader_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._active_config_id: Optional[int] = None

    def list_available_ports(self) -> List[str]:
        """列出可用串口"""
        if _list_ports_func is None:
            raise ValueError("pyserial 未安装，请先安装 pyserial")
        return [p.device for p in _list_ports_func.comports()]

    def open_port(self, port: str, baudrate: int = 115200, bytesize: int = 8, 
                  parity: str = "N", stopbits: float = 1, timeout: float = 0.05) -> None:
        """打开串口"""
        if _serial_module is None:
            raise ValueError("pyserial 未安装，请先安装 pyserial")
        
        with self._lock:
            if self._serial and self._serial.is_open:
                raise ValueError("串口已打开，请先关闭")
            
            parity_map = {
                "N": _serial_module.PARITY_NONE,
                "E": _serial_module.PARITY_EVEN,
                "O": _serial_module.PARITY_ODD,
                "M": _serial_module.PARITY_MARK,
                "S": _serial_module.PARITY_SPACE,
            }
            stopbits_map = {
                1: _serial_module.STOPBITS_ONE,
                1.5: _serial_module.STOPBITS_ONE_POINT_FIVE,
                2: _serial_module.STOPBITS_TWO
            }
            
            self._serial = _serial_module.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity_map.get(parity.upper(), _serial_module.PARITY_NONE),
                stopbits=stopbits_map.get(stopbits, _serial_module.STOPBITS_ONE),
                timeout=timeout,
            )
            print(self._serial)
            self._stop_event = asyncio.Event()

    def close_port(self) -> None:
        """关闭串口"""
        with self._lock:
            if self._serial:
                try:
                    self._serial.close()
                finally:
                    self._serial = None
            if self._reader_task:
                self._reader_task.cancel()
                self._reader_task = None
            if not self._stop_event.is_set():
                self._stop_event.set()
            self._active_config_id = None

    def get_status(self) -> dict:
        """获取串口状态"""
        with self._lock:
            is_open = bool(self._serial and self._serial.is_open)
            port = self._serial.port if self._serial else None
            baudrate = self._serial.baudrate if self._serial else None
        return {
            "is_open": is_open,
            "port": port,
            "baudrate": baudrate,
            "active_config_id": self._active_config_id
        }

    def write_data(self, data: str, append_newline: bool = True) -> int:
        """写入数据"""
        with self._lock:
            if not self._serial or not self._serial.is_open:
                raise ValueError("串口未打开")
            payload = (data + ("\r\n" if append_newline else "")).encode("utf-8")
            return self._serial.write(payload)

    async def async_write(self, data: str, append_newline: bool = True) -> int:
        """异步写入数据"""
        if not self._serial or not self._serial.is_open:
            raise ValueError("串口未打开")
        
        payload = (data + ("\r\n" if append_newline else "")).encode("utf-8")
        
        # 在线程池中运行阻塞的写入操作
        return await asyncio.to_thread(self._serial.write, payload)

    async def async_read(self, size: int) -> bytes:
        """异步读取数据"""
        if not self._serial or not self._serial.is_open:
            raise ValueError("串口未打开")
        
        # 在线程池中运行阻塞的读取操作
        return await asyncio.to_thread(self._serial.read, size)

    async def async_flush_input(self):
        """异步清空输入缓冲区"""
        if not self._serial or not self._serial.is_open:
            raise ValueError("串口未打开")
        
        # 在线程池中运行阻塞的清空操作
        await asyncio.to_thread(self._serial.reset_input_buffer)

    async def start_reading(self, callback_func):
        """开始读取串口数据"""
        try:
            while True:
                await asyncio.sleep(0)
                with self._lock:
                    ser = self._serial
                
                if not ser or not ser.is_open:
                    await asyncio.sleep(0.1)
                    continue
                
                try:
                    data = ser.read(1024)
                except Exception:
                    await asyncio.sleep(0.05)
                    continue
                
                if data:
                    try:
                        text = data.decode("utf-8", errors="ignore")
                    except Exception:
                        text = ""
                    if text and callback_func:
                        await callback_func(text)
                else:
                    await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            return

    def set_active_config_id(self, config_id: Optional[int]):
        """设置当前激活的配置ID"""
        self._active_config_id = config_id
