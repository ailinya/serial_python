# Serial Python Backend

This is the Python backend for the serial communication application.

## Setup

1.  Create a virtual environment: `python -m venv venv`
2.  Activate the virtual environment: `.\venv\Scripts\activate`
3.  Install dependencies: `pip install -r requirements.txt`

## Running the application

`python app/main.py`

## Building the Executable

To package the application into a single executable, you can use one of two methods.

### Method 1: Simple Command

This method is quick and easy for simple builds.

1.  **Build the frontend:**
    Navigate to the `serial_vue` directory and run:
    ```bash
    npm run build
    ```

2.  **Package the application:**
    From the root directory, run the following command:
    ```bash
    pyinstaller --noconfirm --onefile --windowed --add-data "serial_vue/dist;serial_vue/dist" serial_python/app/main.py
    ```

### Method 2: Using a `.spec` File (Recommended)

This method is more robust and provides greater control over the build process, which is necessary for this project to handle hidden imports and other complexities.

1.  **Build the frontend:**
    Navigate to the `serial_vue` directory and run:
    ```bash
    npm run build
    ```

2.  **Generate the `.spec` file (only needs to be done once):**
    From the root directory, run:
    ```bash
    pyi-makespec --onefile --windowed serial_python/app/main.py
    ```
    This will create a `main.spec` file.

3.  **Modify the `main.spec` file:**
    Open `main.spec` and modify it to look like this. This adds the frontend `dist` folder and includes necessary hidden imports for `uvicorn`.

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
        console=True, # Set to False for a windowless application
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    ```

4.  **Build the executable using the `.spec` file:**
    ```bash
    pyinstaller main.spec
    ```

The final executable will be located in the `dist` directory.
