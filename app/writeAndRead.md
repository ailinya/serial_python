# 独立的读和写端点
````
class RegisterReadRequest(BaseModel):
    address: str = Field(..., description="寄存器地址（16进制）", example="0x20470c04")

class RegisterWriteRequest(BaseModel):
    address: str = Field(..., description="寄存器地址（16进制）", example="0x20470c04")
    value: str = Field(..., description="要写入的值（16进制）", example="0x31335233")

@app.post("/register/read", response_model=RegisterAccessResponse)
async def read_register(request: RegisterReadRequest):
    """读取寄存器值"""
    try:
        address = int(request.address, 16)
        value = HardwareManager.read_register(address)
        
        return RegisterAccessResponse(
            success=True,
            message="寄存器读取成功",
            address=request.address,
            value=f"0x{value:08x}",
            access_type=RegisterAccessType.READ,
            timestamp=datetime.now().isoformat()
        )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="地址格式错误，请使用16进制格式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取寄存器失败: {str(e)}")

@app.post("/register/write", response_model=RegisterAccessResponse)
async def write_register(request: RegisterWriteRequest):
    """写入寄存器值"""
    try:
        address = int(request.address, 16)
        value = int(request.value, 16)
        
        success = HardwareManager.write_register(address, value)
        
        return RegisterAccessResponse(
            success=success,
            message="寄存器写入成功" if success else "寄存器写入失败",
            address=request.address,
            value=request.value,
            access_type=RegisterAccessType.WRITE,
            timestamp=datetime.now().isoformat()
        )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="地址或值格式错误，请使用16进制格式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入寄存器失败: {str(e)}")
````


# 批量读写
````


from typing import List

class BatchRegisterRequest(BaseModel):
    operations: List[RegisterAccessRequest]

class BatchRegisterResponse(BaseModel):
    success: bool
    message: str
    results: List[RegisterAccessResponse]
    timestamp: str

@app.post("/register/batch", response_model=BatchRegisterResponse)
async def batch_access_registers(request: BatchRegisterRequest):
    """批量寄存器操作"""
    results = []
    
    for op_request in request.operations:
        try:
            address = int(op_request.address, 16)
            
            if op_request.access_type == RegisterAccessType.READ:
                value = HardwareManager.read_register(address)
                result = RegisterAccessResponse(
                    success=True,
                    message="读取成功",
                    address=op_request.address,
                    value=f"0x{value:08x}",
                    access_type=op_request.access_type,
                    timestamp=datetime.now().isoformat()
                )
            else:
                if op_request.value is None:
                    result = RegisterAccessResponse(
                        success=False,
                        message="写操作缺少value参数",
                        address=op_request.address,
                        value=None,
                        access_type=op_request.access_type,
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    value = int(op_request.value, 16)
                    success = HardwareManager.write_register(address, value)
                    result = RegisterAccessResponse(
                        success=success,
                        message="写入成功" if success else "写入失败",
                        address=op_request.address,
                        value=op_request.value,
                        access_type=op_request.access_type,
                        timestamp=datetime.now().isoformat()
                    )
            
            results.append(result)
        
        except Exception as e:
            results.append(RegisterAccessResponse(
                success=False,
                message=f"操作失败: {str(e)}",
                address=op_request.address,
                value=None,
                access_type=op_request.access_type,
                timestamp=datetime.now().isoformat()
            ))
    
    return BatchRegisterResponse(
        success=all(r.success for r in results),
        message="批量操作完成",
        results=results,
        timestamp=datetime.now().isoformat()
    )
    ````
