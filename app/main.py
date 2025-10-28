'''
Author: nll
Date: 2025-09-29 15:43:15
LastEditors: nll
LastEditTime: 2025-10-09 13:59:54
Description: 
'''
import os
import sys
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app, SERVE_STATIC


import uvicorn
import webbrowser
import time
import socket
import ctypes
from multiprocessing import Process, freeze_support

def disable_quick_edit():
    """Disables QuickEdit Mode for the console to prevent pausing on click."""
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            h_stdin = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
            current_mode = ctypes.c_uint32()
            kernel32.GetConsoleMode(h_stdin, ctypes.byref(current_mode))
            
            # According to Windows API docs, to disable QuickEdit, we must
            # ensure ENABLE_EXTENDED_FLAGS (0x0080) is ON and
            # ENABLE_QUICK_EDIT_MODE (0x0040) is OFF.
            new_mode = (current_mode.value | 0x0080) & ~0x0040
            
            kernel32.SetConsoleMode(h_stdin, new_mode)
        except Exception as e:
            # This might fail if not running in a real console, which is fine.
            print(f"Could not disable QuickEdit Mode: {e}")

def run_server():
    # reload=False is crucial for packaged apps
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(message)s",
                "use_colors": False,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
                "use_colors": False,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
            "sqlalchemy.engine": {"handlers": ["default"], "level": "INFO", "propagate": False},
        },
    }
    uvicorn.run(app, host="0.0.0.0", port=9993, reload=False, workers=1, log_config=log_config)

if __name__ == "__main__":
    # Disable console QuickEdit mode to prevent pausing on click
    disable_quick_edit()

    # freeze_support() is necessary for multiprocessing to work in a frozen (PyInstaller) app
    freeze_support()

    # --- 在主进程中判断一次静态文件服务状态 ---
    from app import should_serve_static_files
    # 这个调用同时用于打印状态和决定是否打开浏览器
    serve_static_in_main = should_serve_static_files()

    if serve_static_in_main:
        print("静态文件服务已启用")
    else:
        print("静态文件服务已禁用")
    
    # Run the server in a separate process
    server_process = Process(target=run_server)
    server_process.start()

    # --- 智能等待服务器就绪 ---
    def wait_for_server(host: str, port: int, timeout: int = 10):
        """主动检测服务器端口，直到连接成功或超时。"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, port), timeout=0.1):
                    return True
            except (socket.timeout, ConnectionRefusedError):
                time.sleep(0.1)
        return False

    # --- 智能自动打开浏览器 ---
    # 仅在打包后的应用中，并且前端服务已启用时，才自动打开浏览器
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen and serve_static_in_main:
        if wait_for_server("localhost", 9993):
            webbrowser.open("http://localhost:9993")
        else:
            print("警告: 服务器在10秒内未能启动，无法自动打开浏览器。")

    # Wait for the server process to finish (e.g., by closing the console window)
    server_process.join()
