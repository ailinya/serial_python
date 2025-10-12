# Python 串口通信后端项目

## 项目简介

这是一个基于 FastAPI 的串口通信后端项目，提供串口管理、寄存器读写、WebSocket 长连接等功能。项目采用 SQLite 数据库存储配置信息，支持 RESTful API 和 WebSocket 实时通信。

## 技术栈

- **后端框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy ORM
- **数据验证**: Pydantic V2
- **串口通信**: pyserial
- **WebSocket**: FastAPI WebSocket
- **API文档**: Swagger UI
- **项目结构**: 分层架构 (Models, Schemas, Controllers, Utils)

## 项目结构

```
python_back/
├── app/
│   ├── __init__.py              # 主应用配置
│   ├── main.py                  # 应用入口
│   ├── api/                     # API路由
│   │   ├── __init__.py          # API路由汇总
│   │   ├── serial_settings/     # 串口设置API
│   │   └── registers/           # 寄存器相关API
│   │       ├── __init__.py      # 寄存器路由汇总
│   │       ├── registers.py     # 寄存器读写API
│   │       └── saved_registers.py # 保存的寄存器API
│   ├── controllers/             # 业务逻辑控制器
│   │   ├── register_controller.py      # 寄存器控制器
│   │   └── saved_register_controller.py # 保存寄存器控制器
│   ├── models/                  # 数据库模型
│   │   ├── serial_config.py     # 串口配置模型
│   │   ├── register_log.py      # 寄存器日志模型
│   │   └── saved_register.py    # 保存的寄存器模型
│   ├── schemas/                 # Pydantic数据模型
│   │   └── register_schemas.py  # 寄存器相关数据模型
│   ├── settings/                # 配置设置
│   │   └── database.py          # 数据库配置
│   ├── utils/                   # 工具类
│   │   ├── serial_helper.py    # 串口助手
│   │   └── port_monitor.py      # 端口监听器
│   ├── ws_manager.py            # WebSocket管理器
│   └── writeAndRead.md          # 寄存器读写文档
├── requirements.txt             # 项目依赖
└── README.md                   # 项目说明文档
```

## 功能特性

### 🔌 串口管理
- 串口列表获取
- 串口连接/断开
- 串口参数配置
- 实时串口状态监控

### 📡 WebSocket 通信
- 长连接支持
- 实时数据推送
- 串口插拔事件监听
- 双向通信支持

### 💾 寄存器操作
- 单个寄存器读写
- 批量寄存器操作
- 寄存器数据持久化
- 操作日志记录

### 🗄️ 数据管理
- 保存的寄存器管理
- 批量删除操作
- 数据验证和错误处理
- 统一响应格式

## 快速开始

### 1. 环境要求

- Python 3.13+ (推荐使用 conda 管理环境)
- pip 包管理器

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd python_back

# 创建 conda 虚拟环境（推荐）
conda create -n serial_backend python=3.13 -y
conda activate serial_backend

# 或者使用 venv
python -m venv venv
# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装基础依赖
pip install -r requirements.txt

# 安装开发依赖（可选）
pip install -r requirements-dev.txt

# 安装生产环境依赖（可选）
pip install -r requirements-prod.txt
```

### 3. 启动服务

```bash
# 开发模式启动（支持热重载）
python app/main.py

# 或者使用 uvicorn 命令
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 9993

# 生产模式启动
python -m uvicorn app.main:app --host 0.0.0.0 --port 9993
```

### 4. 访问服务

- **API文档**: http://localhost:9993/docs
- **服务状态**: http://localhost:9993/api/ping
- **WebSocket**: ws://localhost:9993/ws

## API 接口文档

### 基础接口

#### 系统测试
```http
GET /api/ping
```
**响应**:
```json
{
  "status": "ok"
}
```

### 串口管理接口

#### 获取串口列表
```http
GET /api/serial/ports
```

#### 打开串口
```http
POST /api/serial/open
Content-Type: application/json

{
  "port": "COM3",
  "baudrate": 115200,
  "timeout": 1
}
```

#### 关闭串口
```http
POST /api/serial/close
```

#### 获取串口状态
```http
GET /api/serial/status
```

### 寄存器操作接口

#### 连接串口
```http
POST /api/registers/connect
Content-Type: application/json

{
  "com_num": "COM3",
  "baud": 115200
}
```

#### 读取寄存器
```http
POST /api/registers/read
Content-Type: application/json

{
  "address": "0x20470c04",
  "size": 4
}
```

#### 写入寄存器
```http
POST /api/registers/write
Content-Type: application/json

{
  "address": "0x20470c04",
  "value": "0x31335233"
}
```

#### 批量读取寄存器
```http
POST /api/registers/batch-read
Content-Type: application/json

{
  "addresses": ["0x20470c04", "0x20470c08"],
  "size": 4
}
```

#### 批量写入寄存器
```http
POST /api/registers/batch-write
Content-Type: application/json

{
  "operations": [
    {"address": "0x20470c04", "value": "0x31335233"},
    {"address": "0x20470c08", "value": "0x31335234"}
  ]
}
```

### 保存的寄存器管理接口

#### 保存寄存器
```http
POST /api/registers/saved/save
Content-Type: application/json

{
  "address": "0x20470c04",
  "data": "0XFDB25233",
  "value32bit": "0XFDB25233",
  "description": "GPIO配置寄存器"
}
```

#### 获取寄存器列表
```http
GET /api/registers/saved/list?skip=0&limit=10
```

#### 获取单个寄存器
```http
GET /api/registers/saved/{id}
```

#### 更新寄存器
```http
PUT /api/registers/saved/{id}
Content-Type: application/json

{
  "data": "0XFDB25234",
  "value32bit": "0XFDB25234",
  "description": "更新后的描述"
}
```

#### 删除单个寄存器
```http
DELETE /api/registers/saved/{id}
```

#### 批量删除寄存器
```http
POST /api/registers/saved/batch-delete
Content-Type: application/json

{
  "register_ids": [1, 2, 3]
}
```

## WebSocket 接口

### 通用 WebSocket
```javascript
const ws = new WebSocket('ws://localhost:9993/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到数据:', data);
};
```

### 串口插拔监听
```javascript
const ws = new WebSocket('ws://localhost:9993/ws/serial-ports');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'ports_update') {
    console.log('可用串口:', data.ports);
  }
};
```

## 数据模型

### 统一响应格式

所有API接口都使用统一的响应格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    // 具体数据内容
  }
}
```

### 错误响应格式

```json
{
  "detail": {
    "error": "ERROR_CODE",
    "message": "错误描述",
    "field": "字段名",
    "value": "字段值"
  }
}
```

## 配置说明

### 数据库配置
- 使用 SQLite 数据库
- 自动创建表结构
- 支持数据持久化

### 串口配置
- 支持多种波特率
- 可配置超时时间
- 自动检测串口状态

### CORS 配置
- 允许所有来源访问
- 支持跨域请求
- 可配置允许的方法和头部

## 开发指南

### 添加新的API接口

1. 在 `app/schemas/` 中定义数据模型
2. 在 `app/controllers/` 中实现业务逻辑
3. 在 `app/api/` 中定义路由
4. 更新路由汇总文件

### 数据库操作

```python
from app.settings.database import get_db
from app.models.saved_register import SavedRegister

# 在控制器中使用
def some_function(db: Session = Depends(get_db)):
    registers = db.query(SavedRegister).all()
    return registers
```

### 错误处理

```python
from fastapi import HTTPException

# 抛出HTTP异常
raise HTTPException(
    status_code=400,
    detail={
        "error": "INVALID_FORMAT",
        "message": "数据格式错误",
        "field": "address"
    }
)
```

## 部署说明

### 生产环境部署

1. **使用 Gunicorn**:
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:9993
```

2. **使用 Docker**:
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9993"]
```

### 环境变量配置

```bash
# 数据库配置
DATABASE_URL=sqlite:///./app.db

# 服务配置
HOST=0.0.0.0
PORT=9993
DEBUG=False
```

## 常见问题

### Q: 串口连接失败怎么办？
A: 检查串口是否被其他程序占用，确认串口参数是否正确。

### Q: WebSocket 连接断开怎么办？
A: 检查网络连接，重新建立WebSocket连接。

### Q: 数据库操作失败怎么办？
A: 检查数据库文件权限，确认表结构是否正确创建。

### Q: 如何添加新的串口设备支持？
A: 在 `serial_helper.py` 中添加设备特定的通信协议。

## 更新日志

### v1.1.0 (2025-10-12)
- ✅ 升级到 Python 3.13
- ✅ 更新依赖包版本
- ✅ 优化 conda 环境管理
- ✅ 修复 Pydantic V2 兼容性
- ✅ 改进错误处理和响应格式

### v1.0.0 (2025-10-10)
- ✅ 基础串口通信功能
- ✅ WebSocket 长连接支持
- ✅ 寄存器读写操作
- ✅ 数据持久化存储
- ✅ 批量操作支持
- ✅ 统一响应格式
- ✅ API 文档自动生成

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request



**注意**: 本项目仅供学习和开发使用，请根据实际需求进行配置和部署。
