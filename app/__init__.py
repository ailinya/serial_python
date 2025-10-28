'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 15:48:15
Description: 
'''
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import argparse
import sys
import os
import logging

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

# 全局实例
serial_helper = SerialHelper()
ws_manager = WebSocketManager()
port_monitor = PortMonitor(ws_manager)
from fastapi.responses import HTMLResponse

# --- 配置静态文件服务 ---

def should_serve_static_files():
    """
    决定是否应提供静态文件，并在需要时自动创建配置文件。
    优先级: config.json > 环境变量 > 默认禁用
    """
    try:
        is_frozen = getattr(sys, 'frozen', False)
        
        # 确定基础路径
        if is_frozen:
            # 打包后的应用，config.json 与 exe 同级
            base_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境，config.json 在项目根目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
        config_path = os.path.join(base_dir, 'config.json')

        # 如果配置文件存在，则读取它
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config.get('serve_static', False)

        # --- 自动生成 config.json 的逻辑 ---
        # 仅在打包后的应用首次运行时，且环境变量未设置时，自动创建
        if is_frozen and "SERVE_STATIC" not in os.environ:
            try:
                default_config = {"serve_static": True}
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                # 既然我们创建了它，就直接返回 True
                return True
            except Exception:
                # 如果创建失败，则继续执行后续逻辑
                pass

    except Exception:
        # 忽略任何文件处理或 JSON 解析错误
        pass

    # 如果以上逻辑都未返回，则回退到环境变量
    return os.getenv("SERVE_STATIC", "false").lower() == "true"

# SERVE_STATIC 的值将在 on_startup 事件中确定
SERVE_STATIC = False

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

app.include_router(v1_router)

@app.on_event("startup")
async def on_startup() -> None:
    global SERVE_STATIC
    SERVE_STATIC = should_serve_static_files()

    # --- 动态挂载静态文件 ---
    if SERVE_STATIC:
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        static_files_path = os.path.join(base_path, "serial_vue", "dist")

        if os.path.exists(static_files_path):
            app.mount("/assets", StaticFiles(directory=os.path.join(static_files_path, "assets")), name="assets")
            
            @app.get("/", include_in_schema=False)
            async def read_index():
                return FileResponse(os.path.join(static_files_path, 'index.html'))

            @app.get("/{catchall:path}", include_in_schema=False)
            async def read_spa(catchall: str):
                return FileResponse(os.path.join(static_files_path, 'index.html'))
            
            # 日志已在主进程中打印，此处不再重复
            # logging.info("静态文件服务已启用")
        else:
            logging.warning(f"静态文件路径不存在: {static_files_path}")
    # else:
        # 日志已在主进程中打印，此处不再重复
        # logging.info("静态文件服务已禁用")

    # 在应用启动时创建数据库表
    Base.metadata.create_all(bind=engine)
    
    # 初始化时无需打开串口，按需通过 API 打开
    # 启动串口监听
    port_monitor.start_monitoring()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    # 停止串口监听
    port_monitor.stop_monitoring()


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
          window.ui = SwaggerUIBundle({{
            url: '{app.openapi_url}',
            dom_id: '#swagger-ui',
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
            layout: 'BaseLayout',
          }});
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
                # 解析JSON消息
                try:
                    message = json.loads(data)
                    if message.get("type") == "get_ports":
                        # 客户端请求获取串口列表
                        current_ports = port_monitor.get_current_ports()
                        await websocket.send_json({
                            "type": "ports_update",
                            "ports": current_ports
                        })
                except json.JSONDecodeError:
                    # 处理非JSON消息（如心跳）
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
