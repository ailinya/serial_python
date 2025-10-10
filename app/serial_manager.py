import asyncio
import threading
from typing import Optional, List, Dict

try:
    import serial
    from serial.tools import list_ports
except Exception:  # pragma: no cover - 允许在未安装时导入失败，运行时需安装
    serial = None
    list_ports = None


class SerialManager:
    """串口管理：打开/关闭/写入，以及把串口收到的数据转发到 WebSocket"""

    def __init__(self) -> None:
        # type: ignore[name-defined]
        self._serial: Optional[serial.Serial] = None
        self._lock = threading.Lock()
        self._reader_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    def list_ports(self) -> List[str]:
        if list_ports is None:
            raise ValueError("pyserial 未安装，请先安装 pyserial")
        return [p.device for p in list_ports.comports()]

    def open(
        self,
        port: str,
        baudrate: int = 115200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: float = 1,
        timeout: float = 0.05,
    ) -> None:
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
            stopbits_map = {1: serial.STOPBITS_ONE,
                            1.5: serial.STOPBITS_ONE_POINT_FIVE, 2: serial.STOPBITS_TWO}

            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity_map.get(parity.upper(), serial.PARITY_NONE),
                stopbits=stopbits_map.get(stopbits, serial.STOPBITS_ONE),
                timeout=timeout,
            )
            self._stop_event = asyncio.Event()

    def close(self) -> None:
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

    def status(self) -> Dict[str, object]:
        with self._lock:
            is_open = bool(self._serial and self._serial.is_open)
            port = self._serial.port if self._serial else None
            baudrate = self._serial.baudrate if self._serial else None
        return {"is_open": is_open, "port": port, "baudrate": baudrate}

    def write(self, data: str, append_newline: bool = False) -> int:
        with self._lock:
            if not self._serial or not self._serial.is_open:
                raise ValueError("串口未打开")
            payload = (data + ("\n" if append_newline else "")).encode("utf-8")
            return self._serial.write(payload)

    async def forward_serial_to_ws(self, ws_manager: "WebSocketManager") -> None:
        """后台循环读取串口数据，并转发至所有 WebSocket 客户端。
        若串口未打开则等待，直到打开或任务取消。
        """
        try:
            while True:
                await asyncio.sleep(0)  # 让出事件循环
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
                    if text:
                        await ws_manager.broadcast({"type": "serial", "payload": text})
                else:
                    await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            return
