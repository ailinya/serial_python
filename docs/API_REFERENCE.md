# API 接口参考文档

## 概述

本文档详细描述了 Python 串口通信后端项目的所有 API 接口。

## 基础信息

- **基础URL**: `http://localhost:8008`
- **API版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    // 具体数据内容
  }
}
```

### 错误响应
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

## 系统接口

### 系统测试
```http
GET /api/ping
```

**描述**: 测试系统是否正常运行

**响应**:
```json
{
  "status": "ok"
}
```

## 串口管理接口

### 获取串口列表
```http
GET /api/serial/ports
```

**描述**: 获取当前系统可用的串口列表

**响应**:
```json
{
  "success": true,
  "message": "获取串口列表成功",
  "data": {
    "ports": ["COM1", "COM3", "COM5"]
  }
}
```

### 打开串口
```http
POST /api/serial/open
```

**请求体**:
```json
{
  "port": "COM3",
  "baudrate": 115200,
  "timeout": 1
}
```

**响应**:
```json
{
  "success": true,
  "message": "串口打开成功",
  "data": {
    "port": "COM3",
    "baudrate": 115200,
    "is_open": true
  }
}
```

### 关闭串口
```http
POST /api/serial/close
```

**响应**:
```json
{
  "success": true,
  "message": "串口已关闭"
}
```

### 获取串口状态
```http
GET /api/serial/status
```

**响应**:
```json
{
  "success": true,
  "message": "获取状态成功",
  "data": {
    "is_open": true,
    "port": "COM3",
    "baudrate": 115200
  }
}
```

## 寄存器操作接口

### 连接串口
```http
POST /api/registers/connect
```

**请求体**:
```json
{
  "com_num": "COM3",
  "baud": 115200
}
```

**响应**:
```json
{
  "status": 200,
  "message": "串口 COM3 连接成功",
  "port": "COM3",
  "baudrate": 115200
}
```

### 断开串口连接
```http
POST /api/registers/disconnect
```

**响应**:
```json
{
  "status": 200,
  "message": "串口已断开连接"
}
```

### 读取寄存器
```http
POST /api/registers/read
```

**请求体**:
```json
{
  "address": "0x20470c04",
  "size": 4
}
```

**响应**:
```json
{
  "success": true,
  "message": "寄存器读取成功，读取4字节",
  "address": "0x20470c04",
  "value": "0XFFB25233",
  "access_type": "READ",
  "timestamp": "2025-10-10T16:00:00Z"
}
```

### 写入寄存器
```http
POST /api/registers/write
```

**请求体**:
```json
{
  "address": "0x20470c04",
  "value": "0x31335233"
}
```

**响应**:
```json
{
  "success": true,
  "message": "寄存器写入成功",
  "address": "0x20470c04",
  "value": "0x31335233",
  "access_type": "WRITE",
  "timestamp": "2025-10-10T16:00:00Z"
}
```

### 批量读取寄存器
```http
POST /api/registers/batch-read
```

**请求体**:
```json
{
  "addresses": ["0x20470c04", "0x20470c08"],
  "size": 4
}
```

**响应**:
```json
{
  "success": true,
  "message": "批量读取完成，成功 2 个，失败 0 个",
  "total_operations": 2,
  "successful_operations": 2,
  "failed_operations": 0,
  "results": [
    {
      "address": "0x20470c04",
      "status": "success",
      "value": "0XFFB25233",
      "message": "寄存器读取成功，读取4字节",
      "timestamp": "2025-10-10T16:00:00Z"
    }
  ],
  "timestamp": "2025-10-10T16:00:00Z"
}
```

### 批量写入寄存器
```http
POST /api/registers/batch-write
```

**请求体**:
```json
{
  "operations": [
    {"address": "0x20470c04", "value": "0x31335233"},
    {"address": "0x20470c08", "value": "0x31335234"}
  ]
}
```

**响应**:
```json
{
  "success": true,
  "message": "批量写入完成，成功 2 个，失败 0 个",
  "total_operations": 2,
  "successful_operations": 2,
  "failed_operations": 0,
  "results": [
    {
      "address": "0x20470c04",
      "value": "0x31335233",
      "status": "success",
      "message": "寄存器写入成功",
      "timestamp": "2025-10-10T16:00:00Z"
    }
  ],
  "timestamp": "2025-10-10T16:00:00Z"
}
```

## 保存的寄存器管理接口

### 保存寄存器
```http
POST /api/registers/saved/save
```

**请求体**:
```json
{
  "address": "0x20470c04",
  "data": "0XFDB25233",
  "value32bit": "0XFDB25233",
  "description": "GPIO配置寄存器"
}
```

**响应**:
```json
{
  "success": true,
  "message": "寄存器保存成功",
  "data": {
    "id": 1,
    "address": "0x20470c04",
    "data": "0XFDB25233",
    "value32bit": "0XFDB25233",
    "description": "GPIO配置寄存器",
    "created_at": "2025-10-10T16:00:00Z",
    "updated_at": "2025-10-10T16:00:00Z"
  }
}
```

### 获取寄存器列表
```http
GET /api/registers/saved/list?skip=0&limit=10
```

**查询参数**:
- `skip`: 跳过的记录数（默认: 0）
- `limit`: 返回的记录数（默认: 100）

**响应**:
```json
{
  "success": true,
  "message": "获取寄存器列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "address": "0x20470c04",
        "data": "0XFDB25233",
        "value32bit": "0XFDB25233",
        "description": "GPIO配置寄存器",
        "created_at": "2025-10-10T16:00:00Z",
        "updated_at": "2025-10-10T16:00:00Z"
      }
    ]
  },
  "total": 1
}
```

### 获取单个寄存器
```http
GET /api/registers/saved/{id}
```

**路径参数**:
- `id`: 寄存器ID

**响应**:
```json
{
  "success": true,
  "message": "获取寄存器成功",
  "data": {
    "id": 1,
    "address": "0x20470c04",
    "data": "0XFDB25233",
    "value32bit": "0XFDB25233",
    "description": "GPIO配置寄存器",
    "created_at": "2025-10-10T16:00:00Z",
    "updated_at": "2025-10-10T16:00:00Z"
  }
}
```

### 更新寄存器
```http
PUT /api/registers/saved/{id}
```

**路径参数**:
- `id`: 寄存器ID

**请求体**:
```json
{
  "data": "0XFDB25234",
  "value32bit": "0XFDB25234",
  "description": "更新后的描述"
}
```

**响应**:
```json
{
  "success": true,
  "message": "寄存器更新成功",
  "data": {
    "id": 1,
    "address": "0x20470c04",
    "data": "0XFDB25234",
    "value32bit": "0XFDB25234",
    "description": "更新后的描述",
    "created_at": "2025-10-10T16:00:00Z",
    "updated_at": "2025-10-10T16:00:00Z"
  }
}
```

### 删除单个寄存器
```http
DELETE /api/registers/saved/{id}
```

**路径参数**:
- `id`: 寄存器ID

**响应**:
```json
{
  "success": true,
  "message": "保存的寄存器已删除",
  "data": {
    "register_id": 1
  }
}
```

### 批量删除寄存器
```http
POST /api/registers/saved/batch-delete
```

**请求体**:
```json
{
  "register_ids": [1, 2, 3]
}
```

**响应**:
```json
{
  "success": true,
  "message": "批量删除完成，成功 2 个，失败 1 个",
  "data": {
    "deleted_ids": [1, 2]
  },
  "total_operations": 3,
  "successful_operations": 2,
  "failed_operations": 1,
  "deleted_count": 2,
  "results": [
    {
      "id": 1,
      "status": "success",
      "message": "删除成功",
      "timestamp": "2025-10-10T16:00:00Z"
    },
    {
      "id": 2,
      "status": "success",
      "message": "删除成功",
      "timestamp": "2025-10-10T16:00:00Z"
    },
    {
      "id": 3,
      "status": "failed",
      "message": "ID为 3 的寄存器未找到",
      "timestamp": "2025-10-10T16:00:00Z"
    }
  ]
}
```

## WebSocket 接口

### 通用 WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8008/ws');
```

**消息格式**:
```json
{
  "type": "message_type",
  "data": "message_content"
}
```

### 串口插拔监听 WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8008/ws/serial-ports');
```

**消息格式**:
```json
{
  "type": "ports_update",
  "ports": ["COM1", "COM3", "COM5"]
}
```

## 错误代码

| 错误代码 | 描述 |
|---------|------|
| `ADDRESS_EXISTS` | 地址已存在 |
| `INVALID_HEX_FORMAT` | 无效的16进制格式 |
| `INVALID_HEX_CHARACTERS` | 16进制字符无效 |
| `REGISTER_NOT_FOUND` | 寄存器未找到 |
| `INTERNAL_ERROR` | 内部服务器错误 |

## 状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |

## 数据验证规则

### 16进制地址格式
- 必须以 `0x` 或 `0X` 开头
- 只能包含 `0-9`, `A-F`, `a-f` 字符
- 示例: `0x20470c04`, `0X20470C04`

### 寄存器数据格式
- 必须是有效的16进制字符串
- 支持不同长度（4字节、8字节等）
- 示例: `0XFDB25233`, `0x31335233`

### 分页参数
- `skip`: 必须 >= 0
- `limit`: 必须在 1-1000 之间

## 使用示例

### JavaScript 示例

```javascript
// 连接串口
const connectSerial = async () => {
  const response = await fetch('/api/registers/connect', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      com_num: 'COM3',
      baud: 115200
    })
  });
  const result = await response.json();
  console.log(result);
};

// 读取寄存器
const readRegister = async () => {
  const response = await fetch('/api/registers/read', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      address: '0x20470c04',
      size: 4
    })
  });
  const result = await response.json();
  console.log(result);
};

// WebSocket 连接
const ws = new WebSocket('ws://localhost:8008/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('收到数据:', data);
};
```

### Python 示例

```python
import requests
import json

# 连接串口
def connect_serial():
    url = 'http://localhost:8008/api/registers/connect'
    data = {
        'com_num': 'COM3',
        'baud': 115200
    }
    response = requests.post(url, json=data)
    return response.json()

# 读取寄存器
def read_register():
    url = 'http://localhost:8008/api/registers/read'
    data = {
        'address': '0x20470c04',
        'size': 4
    }
    response = requests.post(url, json=data)
    return response.json()

# 保存寄存器
def save_register():
    url = 'http://localhost:8008/api/registers/saved/save'
    data = {
        'address': '0x20470c04',
        'data': '0XFDB25233',
        'value32bit': '0XFDB25233',
        'description': 'GPIO配置寄存器'
    }
    response = requests.post(url, json=data)
    return response.json()
```

---

**注意**: 所有时间戳都使用 ISO 8601 格式，所有16进制值都使用大写格式。
