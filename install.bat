@echo off
echo Installing dependencies from requirements.txt...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Installation failed.
    exit /b %errorlevel%
) else (
    echo Installation completed successfully.
)

pause
