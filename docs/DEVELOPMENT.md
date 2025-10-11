# 开发指南

## 概述

本文档为开发者提供详细的开发指南，包括项目架构、代码规范、开发流程等。

## 项目架构

### 分层架构设计

```
┌─────────────────────────────────────┐
│              API Layer              │  ← FastAPI 路由层
├─────────────────────────────────────┤
│           Controller Layer          │  ← 业务逻辑层
├─────────────────────────────────────┤
│             Model Layer              │  ← 数据模型层
├─────────────────────────────────────┤
│            Database Layer           │  ← 数据库层
└─────────────────────────────────────┘
```

### 目录结构说明

```
app/
├── __init__.py              # 应用主配置
├── main.py                  # 应用入口点
├── api/                     # API 路由层
│   ├── __init__.py         # 路由汇总
│   ├── serial_settings/    # 串口设置 API
│   └── registers/          # 寄存器相关 API
├── controllers/            # 业务逻辑层
│   ├── register_controller.py
│   └── saved_register_controller.py
├── models/                 # 数据模型层
│   ├── serial_config.py
│   ├── register_log.py
│   └── saved_register.py
├── schemas/                # 数据验证层
│   └── register_schemas.py
├── settings/               # 配置层
│   └── database.py
└── utils/                  # 工具层
    ├── serial_helper.py
    └── port_monitor.py
```

## 开发环境设置

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd python_back

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 2. 开发依赖

创建 `requirements-dev.txt`:

```txt
# 开发工具
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=22.0.0
flake8>=5.0.0
mypy>=1.0.0
pre-commit>=2.20.0

# 调试工具
ipdb>=0.13.0
pdbpp>=0.10.0

# 文档工具
sphinx>=5.0.0
sphinx-rtd-theme>=1.0.0
```

### 3. 代码格式化配置

创建 `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.12.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 5.0.4
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

安装 pre-commit:
```bash
pre-commit install
```

## 代码规范

### 1. Python 代码规范

#### 命名规范
- **类名**: 使用 PascalCase，如 `SavedRegisterController`
- **函数名**: 使用 snake_case，如 `get_saved_registers`
- **变量名**: 使用 snake_case，如 `register_id`
- **常量**: 使用 UPPER_CASE，如 `DEFAULT_TIMEOUT`

#### 函数文档
```python
def create_saved_register(self, db: Session, register: SavedRegisterCreate) -> SavedRegisterResponse:
    """
    创建保存的寄存器
    
    Args:
        db: 数据库会话
        register: 寄存器创建请求
        
    Returns:
        SavedRegisterResponse: 创建的寄存器响应
        
    Raises:
        HTTPException: 当地址已存在或数据格式错误时
    """
```

#### 类型注解
```python
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

def batch_delete_registers(
    self, 
    db: Session, 
    request: BatchDeleteRequest
) -> BatchDeleteResponse:
    """批量删除保存的寄存器"""
    pass
```

### 2. API 设计规范

#### 路由命名
- 使用名词，避免动词
- 使用复数形式
- 使用小写和连字符

```python
# ✅ 正确
@router.get("/saved-registers")
@router.post("/batch-delete")

# ❌ 错误
@router.get("/getSavedRegisters")
@router.post("/deleteBatch")
```

#### 响应格式统一
```python
# 成功响应
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}

# 错误响应
{
    "detail": {
        "error": "ERROR_CODE",
        "message": "错误描述",
        "field": "字段名"
    }
}
```

### 3. 数据库设计规范

#### 模型定义
```python
class SavedRegister(Base):
    __tablename__ = "saved_registers"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 业务字段
    address = Column(String(50), unique=True, index=True, nullable=False)
    data = Column(String(255), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SavedRegister(id={self.id}, address='{self.address}')>"
```

#### 索引设计
- 主键自动创建索引
- 外键字段创建索引
- 查询频繁的字段创建索引
- 唯一约束字段创建索引

## 开发流程

### 1. 功能开发流程

#### 步骤 1: 需求分析
- 明确功能需求
- 设计 API 接口
- 确定数据模型

#### 步骤 2: 数据模型设计
```python
# 1. 在 models/ 中定义数据库模型
class NewModel(Base):
    __tablename__ = "new_models"
    # 字段定义...

# 2. 在 schemas/ 中定义 Pydantic 模型
class NewModelCreate(BaseModel):
    # 请求模型...

class NewModelResponse(BaseModel):
    # 响应模型...
```

#### 步骤 3: 业务逻辑实现
```python
# 在 controllers/ 中实现业务逻辑
class NewModelController:
    def create_model(self, db: Session, model: NewModelCreate) -> NewModelResponse:
        # 业务逻辑实现...
        pass
```

#### 步骤 4: API 接口实现
```python
# 在 api/ 中定义路由
@router.post("/new-models", response_model=NewModelResponse)
def create_new_model(model: NewModelCreate, db: Session = Depends(get_db)):
    return new_model_controller.create_model(db, model)
```

#### 步骤 5: 测试编写
```python
# 在 tests/ 中编写测试
def test_create_new_model():
    # 测试逻辑...
    pass
```

### 2. 代码审查流程

#### 提交前检查
```bash
# 运行代码格式化
black .

# 运行代码检查
flake8 .

# 运行类型检查
mypy .

# 运行测试
pytest
```

#### 代码审查要点
- 代码逻辑正确性
- 错误处理完整性
- 性能考虑
- 安全性检查
- 文档完整性

### 3. 测试策略

#### 单元测试
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_saved_register():
    response = client.post(
        "/api/registers/saved/save",
        json={
            "address": "0x20470c04",
            "data": "0XFDB25233",
            "value32bit": "0XFDB25233",
            "description": "Test Register"
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
```

#### 集成测试
```python
def test_register_workflow():
    # 1. 连接串口
    response = client.post("/api/registers/connect", json={
        "com_num": "COM3",
        "baud": 115200
    })
    assert response.status_code == 200
    
    # 2. 读取寄存器
    response = client.post("/api/registers/read", json={
        "address": "0x20470c04",
        "size": 4
    })
    assert response.status_code == 200
    
    # 3. 保存寄存器
    response = client.post("/api/registers/saved/save", json={
        "address": "0x20470c04",
        "data": "0XFDB25233",
        "value32bit": "0XFDB25233",
        "description": "Test Register"
    })
    assert response.status_code == 200
```

#### 性能测试
```python
import time

def test_batch_operation_performance():
    start_time = time.time()
    
    # 执行批量操作
    response = client.post("/api/registers/batch-read", json={
        "addresses": ["0x20470c04"] * 100,
        "size": 4
    })
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    assert response.status_code == 200
    assert execution_time < 10.0  # 10秒内完成
```

## 调试技巧

### 1. 日志调试

```python
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_function():
    logger.debug("调试信息")
    logger.info("一般信息")
    logger.warning("警告信息")
    logger.error("错误信息")
```

### 2. 断点调试

```python
import ipdb

def problematic_function():
    # 设置断点
    ipdb.set_trace()
    
    # 代码执行到这里会暂停
    result = some_calculation()
    return result
```

### 3. 异常处理

```python
try:
    # 可能出错的代码
    result = risky_operation()
except SpecificException as e:
    # 处理特定异常
    logger.error(f"特定错误: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    # 处理通用异常
    logger.error(f"未知错误: {e}")
    raise HTTPException(status_code=500, detail="内部服务器错误")
```

## 性能优化

### 1. 数据库优化

#### 查询优化
```python
# ❌ 避免 N+1 查询
def bad_query(db: Session):
    registers = db.query(SavedRegister).all()
    for register in registers:
        # 每个寄存器都会触发一次查询
        print(register.created_at)

# ✅ 使用预加载
def good_query(db: Session):
    registers = db.query(SavedRegister).options(
        joinedload(SavedRegister.created_at)
    ).all()
    for register in registers:
        print(register.created_at)
```

#### 批量操作
```python
# ❌ 逐个插入
def bad_batch_insert(db: Session, items: List[dict]):
    for item in items:
        register = SavedRegister(**item)
        db.add(register)
        db.commit()  # 每次提交

# ✅ 批量插入
def good_batch_insert(db: Session, items: List[dict]):
    registers = [SavedRegister(**item) for item in items]
    db.add_all(registers)
    db.commit()  # 只提交一次
```

### 2. 缓存优化

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(param: str) -> str:
    # 昂贵的计算
    return result

# 使用缓存
result = expensive_calculation("input")
```

### 3. 异步优化

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def async_batch_operation(items: List[str]) -> List[str]:
    with ThreadPoolExecutor(max_workers=4) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, process_item, item)
            for item in items
        ]
        results = await asyncio.gather(*tasks)
    return results
```

## 安全考虑

### 1. 输入验证

```python
from pydantic import BaseModel, validator

class RegisterRequest(BaseModel):
    address: str
    data: str
    
    @validator('address')
    def validate_address(cls, v):
        if not v.startswith('0x') and not v.startswith('0X'):
            raise ValueError('地址必须以0x或0X开头')
        return v
    
    @validator('data')
    def validate_data(cls, v):
        if not all(c in '0123456789ABCDEFabcdef' for c in v[2:]):
            raise ValueError('数据包含非法字符')
        return v
```

### 2. SQL 注入防护

```python
# ❌ 避免字符串拼接
def bad_query(db: Session, address: str):
    query = f"SELECT * FROM registers WHERE address = '{address}'"
    return db.execute(query)

# ✅ 使用参数化查询
def good_query(db: Session, address: str):
    return db.query(SavedRegister).filter(
        SavedRegister.address == address
    ).first()
```

### 3. 权限控制

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    if not is_valid_token(token.credentials):
        raise HTTPException(status_code=401, detail="无效的令牌")
    return token.credentials

# 在需要认证的接口中使用
@router.post("/protected-endpoint")
def protected_endpoint(token: str = Depends(verify_token)):
    # 受保护的接口
    pass
```

## 文档维护

### 1. API 文档更新

- 修改接口时同步更新文档
- 使用 Swagger 自动生成文档
- 提供完整的请求/响应示例

### 2. 代码注释

```python
def complex_algorithm(data: List[int]) -> int:
    """
    复杂的算法实现
    
    这个算法用于计算数据的加权平均值，考虑了以下因素：
    - 数据的权重分布
    - 异常值的处理
    - 边界条件的处理
    
    Args:
        data: 输入数据列表，必须为非空
        
    Returns:
        计算得到的加权平均值
        
    Raises:
        ValueError: 当输入数据为空时
        
    Example:
        >>> result = complex_algorithm([1, 2, 3, 4, 5])
        >>> print(result)
        3.0
    """
    if not data:
        raise ValueError("输入数据不能为空")
    
    # 算法实现...
    return result
```

### 3. 变更日志

维护 `CHANGELOG.md`:

```markdown
# 变更日志

## [1.1.0] - 2025-10-10

### 新增
- 批量删除寄存器功能
- 统一响应格式
- 性能优化

### 修复
- 修复 Pydantic V2 兼容性问题
- 修复字段名称不一致问题

### 变更
- 更新 API 响应格式
- 优化数据库查询性能
```

## 部署检查清单

### 部署前检查

- [ ] 代码审查完成
- [ ] 测试用例通过
- [ ] 性能测试通过
- [ ] 安全扫描通过
- [ ] 文档更新完成
- [ ] 版本号更新
- [ ] 变更日志更新

### 部署后验证

- [ ] 服务启动正常
- [ ] API 接口可访问
- [ ] 数据库连接正常
- [ ] 日志输出正常
- [ ] 监控指标正常

---

**注意**: 开发过程中请遵循代码规范，确保代码质量和可维护性。
