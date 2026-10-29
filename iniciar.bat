@echo off
REM ============================================================================
REM  EXODUS Contable - inicio rapido en Windows
REM  Crea el entorno virtual la primera vez, instala dependencias y arranca
REM  la aplicacion completa (contabilidad, inventario, nomina y configuracion).
REM ============================================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creando entorno virtual...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if errorlevel 1 (
        echo ERROR: no se encontro Python 3. Instala Python desde python.org
        pause
        exit /b 1
    )
)

echo [2/3] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo ERROR: no se pudieron instalar las dependencias.
    pause
    exit /b 1
)

echo [3/3] Iniciando EXODUS Contable en http://127.0.0.1:5000
echo.
echo Recuerda que MySQL/MariaDB debe estar encendido y configurado.
echo La primera vez se crean usuarios de demostracion (admin / admin123).
echo.
".venv\Scripts\python.exe" run.py

echo.
echo La aplicacion se detuvo.
pause
