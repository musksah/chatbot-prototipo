@echo off
REM ============================================================
REM    Script de Inicio - Chatbot Cootradecun
REM ============================================================

echo.
echo ============================================================
echo    Chatbot Cootradecun - Iniciando...
echo ============================================================
echo.

REM Verificar si Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Por favor instala Python 3.11 o superior
    echo.
    pause
    exit /b 1
)

REM Verificar si existe el entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo [*] Activando entorno virtual...
    call venv\Scripts\activate.bat
    echo.
) else (
    echo ADVERTENCIA: No se encontro el entorno virtual
    echo Se recomienda crear uno con: python -m venv venv
    echo.
    echo Ejecutando sin entorno virtual...
    echo.
)

REM Verificar si existe el archivo .env
if not exist ".env" (
    echo.
    echo ============================================================
    echo    ADVERTENCIA: Archivo .env no encontrado
    echo ============================================================
    echo.
    echo El chatbot requiere una API key de OpenAI.
    echo Por favor crea un archivo .env con:
    echo.
    echo OPENAI_API_KEY=sk-tu-api-key-aqui
    echo.
    echo ============================================================
    echo.
    set /p CONTINUE="¿Deseas continuar de todos modos? (S/N): "
    if /i not "%CONTINUE%"=="S" (
        echo.
        echo Ejecucion cancelada.
        pause
        exit /b 0
    )
)

REM Iniciar el servidor
echo.
echo ============================================================
echo    Iniciando Chatbot Cootradecun...
echo ============================================================
echo.
echo Servidor: http://localhost:8000
echo Documentacion API: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo.
echo Presiona Ctrl+C para detener el servidor
echo ============================================================
echo.

REM Ejecutar con python run.py (recomendado)
python run.py

REM Si falla, intentar con uvicorn directamente
if errorlevel 1 (
    echo.
    echo Error al ejecutar run.py, intentando con uvicorn...
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
)

REM Si el servidor se detiene
echo.
echo ============================================================
echo    Servidor detenido
echo ============================================================
echo.
pause

