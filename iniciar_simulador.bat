@echo off
cd /d "%~dp0"

:: Verifica si el puerto 8002 ya está escuchando para no duplicar el servidor
netstat -ano | findstr ":8002 " | findstr "LISTENING" >nul
if %errorlevel%==0 (
    start "" "http://127.0.0.1:8002/"
    exit /b 0
)

:: Levanta Uvicorn en segundo plano usando el Python del entorno virtual
start /b "" ".venv\Scripts\pythonw.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8002

:: Espera 2 segundos a que levante FastAPI y abre el navegador
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8002/"
exit /b 0