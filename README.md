# 串口 Python 后端

这是串口通信应用的 Python 后端。

## 安装

1.  创建虚拟环境: `python -m venv venv`
2.  激活虚拟环境: `.\venv\Scripts\activate`
3.  安装依赖: `pip install -r requirements.txt`

## 运行应用

### 调试模式
`python app/main.py`

### 部署模式
`python app/main.py --serve-static`

## 构建可执行文件

要将应用程序打包成单个可执行文件，您可以使用以下两种方法之一。

### 方法一：简单命令

此方法对于简单构建来说快速简便。

1.  **构建前端:**
    导航到 `serial_vue` 目录并运行：
    ```bash
    npm run build
    ```

2.  **打包应用:**
    在根目录中，运行以下命令：
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "serial_vue/dist;serial_vue/dist" serial_python/app/main.py
    ```

### 方法二：使用 `.spec` 文件 (推荐)

此方法更健壮，并对构建过程提供更强的控制，这对于本项目处理隐藏导入和其他复杂性是必需的。

1.  **构建前端:**
    导航到 `serial_vue` 目录并运行：
    ```bash
    npm run build
    ```

2.  **生成 `.spec` 文件 (只需执行一次):**
    在根目录中运行：
    ```bash
    pyi-makespec --onefile --windowed serial_python/app/main.py
    ```
    这将创建一个 `main.spec` 文件。

3.  **修改 `main.spec` 文件:**
    打开 `main.spec` 并将其修改为如下所示。这将添加前端 `dist` 文件夹，并包含 `uvicorn` 所需的隐藏导入。

    ```python
    # -*- mode: python ; coding: utf-8 -*-

    a = Analysis(
        ['serial_python\\app\\main.py'],
        pathex=[],
        binaries=[],
        datas=[('serial_vue/dist', 'serial_vue/dist')],
        hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off'],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
        optimize=0,
    )
    pyz = PYZ(a.pure)

    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='main',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True, # 设置为 False 以实现无窗口应用
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    ```

4.  **使用 `.spec` 文件构建可执行文件:**
    ```bash
    pyinstaller main.spec
    ```

最终的可执行文件将位于 `dist` 目录中。
