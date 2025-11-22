'''
Author: nll
Date: 2025-09-29 15:58:53
LastEditors: nll
LastEditTime: 2025-10-09 16:00:00
Description: 数据库配置
'''
import os
import sys # 导入 sys 模块
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 动态确定数据库文件路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的应用，数据库文件放在可执行文件所在目录
    base_dir = os.path.dirname(sys.executable)
else:
    # 如果是开发环境，数据库文件放在项目根目录
    # 这里假设 serial_python 是项目根目录，或者再往上一层
    # 鉴于 main.py 在 app 目录下，project_root 是 serial_python
    base_dir = os.path.dirname(os.path.abspath(__file__)) # current dir: serial_python/app/settings
    base_dir = os.path.dirname(os.path.dirname(base_dir)) # project dir: serial_python
    
# 确保数据库文件所在目录存在
db_dir = os.path.join(base_dir, 'database') # 将数据库文件放到一个单独的database文件夹里
os.makedirs(db_dir, exist_ok=True)

db_path = os.path.join(db_dir, "serial_backend.db")
DATABASE_URL = f"sqlite:///{db_path}"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},  # SQLite 需要这个参数
    echo=True  # 开发时显示 SQL 语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 依赖注入：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
