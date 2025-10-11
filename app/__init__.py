'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 15:48:15
Description: 
'''
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

import os
import sys
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.settings.database import engine, Base
# 导入所有模型以确保表被创建
from app.models.serial_config import SerialConfig
from app.models.register_log import RegisterLog
from app.models.saved_register import SavedRegister
from app.api import v1_router
from app.utils.serial_helper import SerialHelper
from app.utils.port_monitor import PortMonitor
from app.ws_manager import WebSocketManager

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 全局实例
serial_helper = SerialHelper()
ws_manager = WebSocketManager()
port_monitor = PortMonitor(ws_manager)
from fastapi.responses import HTMLResponse


tags_metadata = [
    {
        "name": "serial",
        "description": "串口端口管理、打开/关闭、参数设置与写入。",
    },
    {
        "name": "registers",
        "description": "寄存器读写示例接口，命令通过串口下发，回包经 WebSocket 获取。",
    },
]

app = FastAPI(
    title="Serial WebSocket Backend",
    version="1.0.0",
    description="提供串口通信与 WebSocket 长连接的后端服务，含串口管理与寄存器读写示例。",
    openapi_tags=tags_metadata,
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json",
)

# CORS（如不需要可按需调整）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可按需限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    # 初始化时无需打开串口，按需通过 API 打开
    # 启动串口监听
    port_monitor.start_monitoring()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    # 停止串口监听
    port_monitor.stop_monitoring()


app.include_router(v1_router)


@app.get("/api/ping")
def ping():
    return {"status": "ok"}


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html():
    html = f"""
    <!DOCTYPE html>
    <html lang=\"zh-CN\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>{app.title} - Swagger UI</title>
        <link rel=\"stylesheet\" href=\"https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.7/swagger-ui.min.css\" />
        <style>
          html, body, #swagger-ui {{ height: 100%; margin: 0; background: #fafafa; }}
        </style>
      </head>
      <body>
        <div id=\"swagger-ui\"></div>
        <script src=\"https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.7/swagger-ui-bundle.min.js\"></script>
        <script src=\"https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.11.7/swagger-ui-standalone-preset.min.js\"></script>
        <script>
          window.ui = SwaggerUIBundle({
            url: '{app.openapi_url}',
            dom_id: '#swagger-ui',
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
            layout: 'BaseLayout',
          });
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # 同时处理：
        # 1) 来自客户端的消息（写串口）
        # 2) 来自串口的消息（广播给所有 WS 客户端）
        recv_task = asyncio.create_task(
            ws_manager.receive_from_client(websocket))
        serial_task = asyncio.create_task(
            serial_helper.start_reading(ws_manager.broadcast))

        done, pending = await asyncio.wait(
            {recv_task, serial_task},
            return_when=asyncio.FIRST_EXCEPTION,
        )

        for task in pending:
            task.cancel()

    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket)


@app.websocket("/ws/serial-ports")
async def serial_ports_websocket(websocket: WebSocket):
    """串口插拔事件监听 WebSocket 端点"""
    await ws_manager.connect_serial_ports(websocket)
    
    # 发送当前可用串口列表
    current_ports = port_monitor.get_current_ports()
    await websocket.send_json({
        "type": "ports_update",
        "ports": current_ports
    })
    
    try:
        # 保持连接，等待串口变化事件
        while True:
            # 接收客户端心跳或其他消息
            try:
                data = await websocket.receive_text()
                # 可以处理客户端发送的心跳消息
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"串口监听 WebSocket 错误: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket)


def create_app() -> FastAPI:
    return app
