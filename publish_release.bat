@echo off
REM Publish release using GitHub CLI
REM Usage: run this script locally where `gh` is installed and you're authenticated.

SET OWNER=Spintxch
SET REPO=SnakeEyeCasino
SET TAG=v0.1.0
SET ASSET=release\snake_eye_gui-0.1.0.exe
SET TITLE=v0.1.0

REM Prefer gh on PATH, otherwise fall back to known install location
SET GH=gh
where gh >nul 2>&1
IF ERRORLEVEL 1 (
    IF EXIST "C:\Program Files\GitHub CLI\gh.exe" (
        SET "GH=C:\Program Files\GitHub CLI\gh.exe"
    ) ELSE IF EXIST "%ProgramFiles(x86)%\GitHub CLI\gh.exe" (
        SET "GH=%ProgramFiles(x86)%\GitHub CLI\gh.exe"
    ) ELSE (
        echo gh CLI not found. Install from https://cli.github.com/ and re-run.
        pause
        exit /b 1
    )
)

echo Using: %GH%

REM Verify authentication; prompt to login if needed
"%GH%" auth status >nul 2>&1
IF ERRORLEVEL 1 (
    echo Not authenticated with GitHub. Starting web login...
    "%GH%" auth login --web
)

echo Creating release %TAG% on %OWNER%/%REPO%...
"%GH%" release create %TAG% %ASSET% --title "%TITLE%" --notes-file RELEASE_NOTE.md --repo %OWNER%/%REPO%
IF %ERRORLEVEL% EQU 0 (
    echo Release created successfully.
) ELSE (
    echo Release creation failed. Check gh auth status or run: %GH% auth login --web
)

pause
