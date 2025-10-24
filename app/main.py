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
from multiprocessing import Process, freeze_support

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
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    }
    uvicorn.run(app, host="0.0.0.0", port=9993, reload=False, workers=1, log_config=log_config)

if __name__ == "__main__":
    # freeze_support() is necessary for multiprocessing to work in a frozen (PyInstaller) app
    freeze_support()
    
    # Run the server in a separate process
    server_process = Process(target=run_server)
    server_process.start()

    # Give the server a moment to start up
    time.sleep(5)

    # --- 智能自动打开浏览器 ---
    # 仅在打包后的应用中，并且前端服务已启用时，才自动打开浏览器
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen and SERVE_STATIC:
        webbrowser.open("http://localhost:9993")

    # Wait for the server process to finish (e.g., by closing the console window)
    server_process.join()
