@echo off
rmdir /s /q build dist
CALL venv\Scripts\pyinstaller.exe main.spec --noconfirm
