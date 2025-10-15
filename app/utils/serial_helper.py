'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: '艾琳爱' '2664840261@qq.com'
LastEditTime: 2025-10-10 14:29:05
Description: 串口工具类
'''
import asyncio
import threading
from typing import Optional, List
from sqlalchemy.orm import Session

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None


class SerialHelper:
    """串口操作工具类"""
    
    def __init__(self):
        self._serial: Optional[serial.Serial] = None
        self._lock = threading.Lock()
        self._reader_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._active_config_id: Optional[int] = None

    def list_available_ports(self) -> List[str]:
        """列出可用串口"""
        if list_ports is None:
            raise ValueError("pyserial 未安装，请先安装 pyserial")
        return [p.device for p in list_ports.comports()]

    def open_port(self, port: str, baudrate: int = 115200, bytesize: int = 8, 
                  parity: str = "N", stopbits: float = 1, timeout: float = 0.05) -> None:
        """打开串口"""
        if serial is None:
            raise ValueError("pyserial 未安装，请先安装 pyserial")
        
        with self._lock:
            if self._serial and self._serial.is_open:
                raise ValueError("串口已打开，请先关闭")
            
            parity_map = {
                "N": serial.PARITY_NONE,
                "E": serial.PARITY_EVEN,
                "O": serial.PARITY_ODD,
                "M": serial.PARITY_MARK,
                "S": serial.PARITY_SPACE,
            }
            stopbits_map = {
                1: serial.STOPBITS_ONE,
                1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2: serial.STOPBITS_TWO
            }
            
            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity_map.get(parity.upper(), serial.PARITY_NONE),
                stopbits=stopbits_map.get(stopbits, serial.STOPBITS_ONE),
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