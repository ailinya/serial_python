# 部署指南

## 概述

本文档详细说明了如何在不同环境中部署 Python 串口通信后端项目。

## 环境要求

### 系统要求
- **操作系统**: Windows 10+, Linux, macOS
- **Python版本**: 3.8 或更高版本
- **内存**: 最少 512MB，推荐 1GB+
- **磁盘空间**: 最少 100MB

### 软件依赖
- Python 3.8+
- pip 包管理器
- Git（用于版本控制）

## 本地开发部署

### 1. 环境准备

```bash
# 检查 Python 版本
python --version

# 检查 pip 版本
pip --version
```

### 2. 项目安装

```bash
# 克隆项目
git clone <repository-url>
cd python_back

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置数据库

```bash
# 数据库文件会自动创建在项目根目录
# 文件路径: ./app.db
```

### 4. 启动服务

```bash
# 开发模式（支持热重载）
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8008

# 或者使用项目提供的启动脚本
python app/main.py
```

### 5. 验证部署

```bash
# 测试服务是否正常运行
curl http://localhost:8008/api/ping

# 访问 API 文档
# 浏览器打开: http://localhost:8008/docs
```

## 生产环境部署

### 方法一: 使用 Gunicorn

#### 1. 安装 Gunicorn

```bash
pip install gunicorn
```

#### 2. 启动服务

```bash
# 单进程启动
gunicorn app.main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8008

# 多进程启动（推荐）
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8008 --timeout 120
```

#### 3. 使用配置文件

创建 `gunicorn.conf.py`:

```python
# Gunicorn 配置文件
bind = "0.0.0.0:8008"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

启动命令:
```bash
gunicorn app.main:app -c gunicorn.conf.py
```

### 方法二: 使用 Docker

#### 1. 创建 Dockerfile

```dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8008

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]
```

#### 2. 创建 .dockerignore

```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git/
.mypy_cache/
.pytest_cache/
.hypothesis/
```

#### 3. 构建和运行

```bash
# 构建镜像
docker build -t serial-backend .

# 运行容器
docker run -d -p 8008:8008 --name serial-backend serial-backend

# 查看日志
docker logs serial-backend

# 停止容器
docker stop serial-backend
```

#### 4. 使用 Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  serial-backend:
    build: .
    ports:
      - "8008:8008"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/api/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
```

启动服务:
```bash
docker-compose up -d
```

### 方法三: 使用 Nginx 反向代理

#### 1. 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

#### 2. 配置 Nginx

创建 `/etc/nginx/sites-available/serial-backend`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8008;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8008;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置:
```bash
sudo ln -s /etc/nginx/sites-available/serial-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 系统服务部署

### 1. 创建系统服务文件

创建 `/etc/systemd/system/serial-backend.service`:

```ini
[Unit]
Description=Serial Communication Backend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/python_back
Environment=PATH=/path/to/python_back/venv/bin
ExecStart=/path/to/python_back/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8008
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. 启动服务

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable serial-backend

# 启动服务
sudo systemctl start serial-backend

# 查看状态
sudo systemctl status serial-backend

# 查看日志
sudo journalctl -u serial-backend -f
```

## 环境变量配置

### 1. 创建环境配置文件

创建 `.env` 文件:

```bash
# 数据库配置
DATABASE_URL=sqlite:///./app.db

# 服务配置
HOST=0.0.0.0
PORT=8008
DEBUG=False

# 串口配置
DEFAULT_BAUDRATE=115200
DEFAULT_TIMEOUT=1

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 2. 修改应用配置

在 `app/__init__.py` 中加载环境变量:

```python
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 使用环境变量
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8008))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

## 监控和日志

### 1. 日志配置

创建 `logs/` 目录并配置日志:

```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### 2. 健康检查

```bash
# 创建健康检查脚本
#!/bin/bash
# health_check.sh

response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8008/api/ping)
if [ $response -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy"
    exit 1
fi
```

### 3. 监控脚本

```bash
# 创建监控脚本
#!/bin/bash
# monitor.sh

while true; do
    if ! curl -f http://localhost:8008/api/ping > /dev/null 2>&1; then
        echo "$(date): Service is down, restarting..."
        sudo systemctl restart serial-backend
    fi
    sleep 30
done
```

## 性能优化

### 1. 数据库优化

```python
# 在 database.py 中添加连接池配置
from sqlalchemy.pool import StaticPool

engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)
```

### 2. 内存优化

```python
# 在 uvicorn 启动时添加参数
uvicorn app.main:app --host 0.0.0.0 --port 8008 --workers 4 --limit-max-requests 1000
```

### 3. 缓存配置

```python
# 添加 Redis 缓存（可选）
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# 配置 Redis 缓存
redis = aioredis.from_url("redis://localhost")
FastAPICache.init(RedisBackend(redis), prefix="serial-cache")
```

## 安全配置

### 1. HTTPS 配置

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://127.0.0.1:8008;
        # ... 其他配置
    }
}
```

### 2. 防火墙配置

```bash
# 开放必要端口
sudo ufw allow 8008
sudo ufw allow 80
sudo ufw allow 443

# 限制访问来源（可选）
sudo ufw allow from 192.168.1.0/24 to any port 8008
```

### 3. 访问控制

```python
# 在 FastAPI 中添加认证中间件
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # 验证 token 逻辑
    if not is_valid_token(token.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.credentials
```

## 故障排除

### 1. 常见问题

**问题**: 端口被占用
```bash
# 查找占用端口的进程
sudo netstat -tulpn | grep :8008
sudo lsof -i :8008

# 杀死进程
sudo kill -9 <PID>
```

**问题**: 数据库连接失败
```bash
# 检查数据库文件权限
ls -la app.db
chmod 664 app.db
```

**问题**: 串口权限不足
```bash
# 添加用户到 dialout 组
sudo usermod -a -G dialout $USER
```

### 2. 日志分析

```bash
# 查看应用日志
tail -f logs/app.log

# 查看系统日志
sudo journalctl -u serial-backend -f

# 查看错误日志
grep -i error logs/app.log
```

### 3. 性能监控

```bash
# 监控 CPU 和内存使用
top -p $(pgrep -f "uvicorn")

# 监控网络连接
netstat -an | grep :8008

# 监控磁盘使用
df -h
```

## 备份和恢复

### 1. 数据库备份

```bash
# 备份 SQLite 数据库
cp app.db app.db.backup.$(date +%Y%m%d_%H%M%S)

# 定期备份脚本
#!/bin/bash
# backup.sh
BACKUP_DIR="/path/to/backups"
DB_FILE="/path/to/python_back/app.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp $DB_FILE $BACKUP_DIR/app.db.$DATE
```

### 2. 配置备份

```bash
# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz app/ requirements.txt .env
```

### 3. 恢复流程

```bash
# 恢复数据库
cp app.db.backup.20231010_120000 app.db

# 恢复配置
tar -xzf config_backup_20231010.tar.gz

# 重启服务
sudo systemctl restart serial-backend
```

---

**注意**: 在生产环境中部署前，请确保已经进行了充分的安全配置和性能测试。
