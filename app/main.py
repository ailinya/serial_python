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
from app import app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9993)
