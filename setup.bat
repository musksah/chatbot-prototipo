@echo off
echo ============================================================
echo    Configuracion Automatica - Chatbot Cootradecun
echo ============================================================
echo.

REM Verificar si Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Por favor instala Python 3.11 o superior
    pause
    exit /b 1
)

echo [1/5] Verificando Python...
python --version
echo.

echo [2/5] Creando entorno virtual...
if not exist "venv" (
    python -m venv venv
    echo Entorno virtual creado
) else (
    echo Entorno virtual ya existe
)
echo.

echo [3/5] Activando entorno virtual...
call venv\Scripts\activate.bat
echo.

echo [4/5] Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt
echo.

echo [5/5] Verificando configuracion...
if not exist ".env" (
    echo.
    echo ATENCION: No existe el archivo .env
    echo Debes crear un archivo .env con tu OPENAI_API_KEY
    echo.
    echo Ejemplo:
    echo OPENAI_API_KEY=sk-tu-api-key-aqui
    echo.
    echo ¿Quieres crear el archivo .env ahora? (S/N)
    set /p CREATE_ENV=
    if /i "%CREATE_ENV%"=="S" (
        echo OPENAI_API_KEY=sk-your-api-key-here > .env
        echo # Application Configuration >> .env
        echo ENVIRONMENT=development >> .env
        echo HOST=0.0.0.0 >> .env
        echo PORT=8000 >> .env
        echo.
        echo Archivo .env creado. IMPORTANTE: Edita .env y agrega tu API key real
        notepad .env
    )
) else (
    echo Archivo .env encontrado
)
echo.

echo ============================================================
echo    Configuracion Completada
echo ============================================================
echo.
echo Para ejecutar el chatbot:
echo   1. Asegurate de que .env tenga tu OPENAI_API_KEY
echo   2. Ejecuta: python run.py
echo   3. Abre en navegador: http://localhost:8000
echo.
echo ============================================================
pause

