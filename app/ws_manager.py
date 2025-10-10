from typing import Set, Dict, Any
from fastapi import WebSocket
import asyncio


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._serial_port_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def connect_serial_ports(self, websocket: WebSocket) -> None:
        """连接串口监听 WebSocket"""
        await websocket.accept()
        async with self._lock:
            self._serial_port_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
            if websocket in self._serial_port_connections:
                self._serial_port_connections.remove(websocket)
        try:
            await websocket.close()
        except Exception:
            pass

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """广播消息给所有连接"""
        async with self._lock:
            targets = list(self._connections)
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                # 发送失败则尝试断开
                await self.disconnect(ws)

    async def broadcast_serial_ports(self, message: Dict[str, Any]) -> None:
        """广播串口更新消息给串口监听连接"""
        async with self._lock:
            targets = list(self._serial_port_connections)
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                # 发送失败则尝试断开
                await self.disconnect(ws)

    async def receive_from_client(self, websocket: WebSocket) -> None:
        """接收客户端消息，转为写串口的指令格式：
        约定客户端发送 JSON：{"type":"write", "payload":"text", "appendNewline":false}
        非 write 类型可忽略或扩展
        由外层协程处理写串口逻辑（此示例简化为回显/广播）
        """
        while True:
            data = await websocket.receive_json()
            await self.broadcast({"type": "echo", "payload": data})
