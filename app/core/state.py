from app.serial_manager import SerialManager
from app.ws_manager import WebSocketManager

# 全局单例，供各模块导入使用（不改变原有逻辑，只抽离位置）
serial_manager = SerialManager()
ws_manager = WebSocketManager()
