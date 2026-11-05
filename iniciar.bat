@echo off
setlocal
cd /d "%~dp0"
set "FACTURACION_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "FACTURACION_PYTHON=%~dp0.venv\Scripts\python.exe"
if exist ".runtime\python.exe" set "FACTURACION_PYTHON=%~dp0.runtime\python.exe"
echo Abriendo el servidor en http://127.0.0.1:8000/
echo Mantenga esta ventana abierta. Para detenerlo, pulse Ctrl+C.
"%FACTURACION_PYTHON%" manage.py runserver 127.0.0.1:8000
if errorlevel 1 (
    echo.
    echo El servidor no pudo arrancar. Revise el error mostrado arriba.
    pause
)
endlocal
