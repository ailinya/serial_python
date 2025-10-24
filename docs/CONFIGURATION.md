# 配置说明

## 静态文件服务

本应用的静态文件服务（即前端页面的加载）由 `SERVE_STATIC` 环境变量控制。

### 如何启用静态文件服务

要启用静态文件服务，您需要在运行应用或打包之前，将 `SERVE_STATIC` 环境变量设置为 `true`。

#### Windows (CMD)

在命令提示符中，使用 `set` 命令：

```cmd
set SERVE_STATIC=true
python app/main.py
```

或者在打包时：

```cmd
set SERVE_STATIC=true
venv\Scripts\pyinstaller.exe ...
```

#### Windows (PowerShell)

在 PowerShell 中，使用 `$env:`：

```powershell
$env:SERVE_STATIC="true"
python app/main.py
```

或者在打包时：

```powershell
$env:SERVE_STATIC="true"
venv\Scripts\pyinstaller.exe ...
```

### 如何禁用静态文件服务

如果您不设置该环境变量，或者将其设置为 `false`，静态文件服务将保持禁用状态。这是默认行为。

```cmd
set SERVE_STATIC=false
python app/main.py
