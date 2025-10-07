@echo off
REM ============================================================
REM    Script para crear archivo .env con codificación correcta
REM ============================================================

echo.
echo ============================================================
echo    Creando archivo .env con codificación UTF-8
echo ============================================================
echo.

REM Verificar si ya existe .env
if exist ".env" (
    echo ADVERTENCIA: Ya existe un archivo .env
    set /p OVERWRITE="¿Deseas sobrescribirlo? (S/N): "
    if /i not "%OVERWRITE%"=="S" (
        echo Operacion cancelada.
        pause
        exit /b 0
    )
    echo Eliminando archivo anterior...
    del .env
)

REM Crear nuevo archivo .env con codificación UTF-8
echo # OpenAI Configuration> .env
echo OPENAI_API_KEY=sk-your-api-key-here>> .env
echo.>> .env
echo # Application Configuration>> .env
echo ENVIRONMENT=development>> .env
echo LOG_LEVEL=INFO>> .env
echo.>> .env
echo # Server Configuration>> .env
echo HOST=0.0.0.0>> .env
echo PORT=8000>> .env

echo.
echo ============================================================
echo    Archivo .env creado exitosamente
echo ============================================================
echo.
echo IMPORTANTE: Ahora debes editar el archivo .env y agregar tu
echo OPENAI_API_KEY real.
echo.
echo ¿Deseas abrir el archivo en el Bloc de notas? (S/N)
set /p OPEN_FILE=
if /i "%OPEN_FILE%"=="S" (
    notepad .env
)

echo.
echo Archivo .env listo para usar.
echo.
pause

