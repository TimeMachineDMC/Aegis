@echo off
setlocal
cd /d "%~dp0"

echo Aegis 债优盾 backend for Windows
echo This starts the local API at http://127.0.0.1:8080
echo Same PC test: https://timemachinedmc.github.io/Aegis/?api=http://127.0.0.1:8080
echo Other devices use the cpolar URL configured in config.js.
echo.

if "%AEGIS_PORT%"=="" set AEGIS_PORT=8080
if not exist ".runtime" mkdir .runtime

if /I "%~1"=="stop" (
    powershell -NoProfile -Command "$p=(Get-NetTCPConnection -LocalPort %AEGIS_PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique); if($p){$p | ForEach-Object { Stop-Process -Id $_ -Force }; Write-Host 'Stopped Aegis backend on port %AEGIS_PORT%.'} else {Write-Host 'No Aegis backend is listening on port %AEGIS_PORT%.'}"
    exit /b 0
)

powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://127.0.0.1:%AEGIS_PORT%/api/health | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
if "%ERRORLEVEL%"=="0" (
    echo Aegis 债优盾 backend is already running at http://127.0.0.1:%AEGIS_PORT%
    echo Same PC test: https://timemachinedmc.github.io/Aegis/?api=http://127.0.0.1:%AEGIS_PORT%
    echo.
    echo Showing live backend logs. Press Ctrl-C to stop watching logs; backend keeps running.
    if exist ".runtime\backend-live.log" (
        powershell -NoProfile -Command "Get-Content .runtime\backend-live.log -Tail 80 -Wait"
    ) else (
        echo No log file found yet. Trigger one request in the browser, then rerun run_local.bat.
    )
    exit /b 0
)

if not exist "Code\.env" if not exist ".env" (
    echo Missing DeepSeek config.
    echo Run this once first: copy .env.example Code\.env
    echo Then edit Code\.env and fill DEEPSEEK_API_KEY.
    exit /b 1
)

if not exist ".venv" (
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if exist "Model\chroma_db" if not exist ".runtime\chroma_db" (
    mkdir .runtime
    xcopy /E /I /Q Model\chroma_db .runtime\chroma_db >nul
)

if "%CHROMA_DB_PATH%"=="" set CHROMA_DB_PATH=.runtime\chroma_db
if "%AEGIS_HOST%"=="" set AEGIS_HOST=127.0.0.1
set PYTHONUNBUFFERED=1

python -u Code\dual_api_server.py
