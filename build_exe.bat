@echo off
REM Build a one-file Windows executable with PyInstaller
REM Run this from the root of the snake_eye_casino package folder.

pip install pyinstaller
pyinstaller --onefile --noconsole frontend\snake_eye_gui.py

set VERSION=0.1.0
if exist dist\snake_eye_gui.exe (
    copy /Y dist\snake_eye_gui.exe release\snake_eye_gui-%VERSION%.exe
    echo Build complete. Copied snake_eye_gui-%VERSION%.exe to release\
) else (
    echo Build failed or dist\snake_eye_gui.exe not found.
)

echo Release folder updated.
pause
