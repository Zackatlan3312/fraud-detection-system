@echo off
REM Script de inicio rápido para Windows
echo ========================================
echo Sistema de Deteccion de Fraude
echo ========================================
echo.

REM Verificar si Cassandra está corriendo
echo [1/4] Verificando Cassandra...
docker ps | findstr cassandra-fraud >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Cassandra no está corriendo. Iniciando...
    docker start cassandra-fraud
    timeout /t 10 /nobreak >nul
) else (
    echo Cassandra ya está corriendo
)

REM Activar entorno virtual
echo.
echo [2/4] Activando entorno virtual...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Entorno virtual no encontrado.
    echo Ejecuta primero: python -m venv venv
    pause
    exit /b 1
)

REM Iniciar backend en una nueva ventana
echo.
echo [3/4] Iniciando backend...
start "Backend - API" cmd /k "venv\Scripts\activate.bat && python src\api.py"

REM Esperar un poco
timeout /t 3 /nobreak >nul

REM Iniciar frontend
echo.
echo [4/4] Iniciando frontend...
cd frontend
start "Frontend - React" cmd /k "npm start"

echo.
echo ========================================
echo Sistema iniciado correctamente!
echo ========================================
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo Documentacion: http://localhost:8000/docs
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
