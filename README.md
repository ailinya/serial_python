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

## 应用配置

本应用支持通过多种方式配置，主要用于控制前端静态文件服务的启用。

### 配置优先级

应用的配置加载遵循以下优先级顺序：

1.  **`config.json` 文件 (最高优先级)**: 在 `main.exe` 同级目录下放置 `config.json` 文件是**最推荐**的配置方式。
2.  **环境变量 (备用选项)**: 如果 `config.json` 不存在，应用会检查 `SERVE_STATIC` 环境变量。
3.  **默认禁用 (最低优先级)**: 如果以上两种配置均未设置，前端服务将保持禁用。

### 如何启用前端服务

#### 自动配置 (首次运行)

- **首次**运行 `main.exe` 时，应用会自动在 `.exe` 旁边创建一个 `config.json` 文件，并默认启用前端服务 (`"serve_static": true`)。
- 同时，应用会自动在浏览器中打开主页。

#### 手动配置

- 您可以随时手动编辑 `config.json` 文件。将 `serve_static` 的值修改为 `false` 即可在下次启动时禁用前端服务。
- 如果您删除了 `config.json`，应用在下次启动时会重新自动创建它。

#### 方法二: 使用环境变量

在运行 `.exe` 之前，在终端中设置环境变量：
```powershell
# PowerShell
$env:SERVE_STATIC="true"
dist\main.exe
```
```cmd
# CMD
set SERVE_STATIC=true
dist\main.exe
```

### 自动打开浏览器

- 当您运行打包后的 `main.exe` **并且**前端服务被成功启用时，应用会自动在您的默认浏览器中打开 `http://localhost:9993`。
- 在开发模式下（即直接运行 `python app/main.py`），此功能不会触发，以避免干扰开发流程。

## 构建可执行文件 (推荐方法)

为了确保打包过程的稳定性和可靠性，推荐使用以下基于 `.spec` 文件的专业方法。

### 步骤 1: 构建前端

前端项目必须首先被构建，以便其静态文件可以被打包到最终的可执行文件中。

```bash
# 进入前端项目目录
cd ../serial_vue/serial_vue_dev

# 安装依赖
npm install

# 构建项目
npm run build

# 返回后端项目根目录
cd ../../serial_python
```

### 步骤 2: 生成 .spec 配置文件 (仅需一次)

#### 方法一：直接打包
```bash
# 使用绝对路径来指定 --add-data 的源目录
# --windowed 打包应用不显示终端
venv\Scripts\pyinstaller.exe --noconfirm --onefile --windowed --add-data "c:\workspace\test_stuio_new\serial_vue\dist serial_vue/dist" app/main.py
```
#### 方法二：使用SPEC打包

PyInstaller 使用一个 `.spec` 文件来管理复杂的打包配置。这个文件只需要生成一次。

```bash
# 在虚拟环境中运行
venv\Scripts\pyinstaller.exe --noconfirm --onefile --console app/main.py
```
*   我们使用 `--console` 模式生成 `.spec` 文件，这有助于在最终应用出错时进行调试。
*   此命令会创建一个 `main.spec` 文件。

### 步骤 3: 修改 main.spec 文件

打开 `main.spec` 文件，找到 `datas` 列表，并添加前端构建产物的路径。这确保了前端文件被正确地包含进来。

```python
# main.spec

a = Analysis(
    ...
    datas=[('c:/workspace/test_stuio_new/serial_vue/dist', 'serial_vue/dist')],
    ...
)
```
*   **重要**: 请确保 `datas` 中的源路径 (`c:/workspace/test_stuio_new/serial_vue/dist`) 是您本地环境的**绝对路径**。

### 步骤 4: 使用 .spec 文件进行打包

现在，使用修改后的 `.spec` 文件来执行最终的打包。

```bash
# 在虚拟环境中运行
venv\Scripts\pyinstaller.exe --noconfirm main.spec
```

### 步骤 5: 运行可执行文件

打包完成后，最终的 `main.exe` 文件会位于 `dist` 目录中。

要配置应用（例如，启用前端服务），请参阅上面的 **应用配置** 部分。
