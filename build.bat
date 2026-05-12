@echo off
echo ========================================
echo   APITokenWatcher Build Script
echo ========================================
echo.

echo [1/2] Building frontend...
cd frontend
call npm run build
cd ..
if %errorlevel% neq 0 (
    echo Frontend build failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Building exe with PyInstaller...
pyinstaller APITokenWatcher.spec --noconfirm
if %errorlevel% neq 0 (
    echo PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build complete!
echo   Output: dist\APITokenWatcher\APITokenWatcher.exe
echo ========================================
pause
