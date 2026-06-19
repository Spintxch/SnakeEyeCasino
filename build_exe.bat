@echo off
REM Build a one-file Windows executable with PyInstaller
REM Run this from the root of the snake_eye_casino package folder.

python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --clean --noconfirm snake_eye_gui.spec

set VERSION=0.1.0
if exist dist\snake_eye_gui.exe (
    copy /Y dist\snake_eye_gui.exe release\snake_eye_gui-%VERSION%.exe
    set "EXE_PATH=%CD%\release\snake_eye_gui-%VERSION%.exe"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$W=New-Object -ComObject WScript.Shell; $S=$W.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Snake Eye Casino.lnk'); $S.TargetPath='%EXE_PATH%'; $S.WorkingDirectory='%CD%\release'; $S.IconLocation='%EXE_PATH%,0'; $S.Save()"
    echo Build complete. Copied snake_eye_gui-%VERSION%.exe to release\
    echo Desktop shortcut refreshed: Snake Eye Casino.lnk
) else (
    echo Build failed or dist\snake_eye_gui.exe not found.
)

echo Release folder updated.
pause
