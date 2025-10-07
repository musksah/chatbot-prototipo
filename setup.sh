#!/bin/bash

echo "============================================================"
echo "   Configuración Automática - Chatbot Cootradecun"
echo "============================================================"
echo

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python no está instalado"
    echo "Por favor instala Python 3.11 o superior"
    exit 1
fi

echo "[1/5] Verificando Python..."
python3 --version
echo

echo "[2/5] Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Entorno virtual creado"
else
    echo "Entorno virtual ya existe"
fi
echo

echo "[3/5] Activando entorno virtual..."
source venv/bin/activate
echo

echo "[4/5] Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt
echo

echo "[5/5] Verificando configuración..."
if [ ! -f ".env" ]; then
    echo
    echo "ATENCIÓN: No existe el archivo .env"
    echo "Debes crear un archivo .env con tu OPENAI_API_KEY"
    echo
    echo "Ejemplo:"
    echo "OPENAI_API_KEY=sk-tu-api-key-aqui"
    echo
    read -p "¿Quieres crear el archivo .env ahora? (s/n): " CREATE_ENV
    if [ "$CREATE_ENV" = "s" ] || [ "$CREATE_ENV" = "S" ]; then
        cat > .env << EOF
OPENAI_API_KEY=sk-your-api-key-here
# Application Configuration
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
EOF
        echo
        echo "Archivo .env creado. IMPORTANTE: Edita .env y agrega tu API key real"
        echo "Ejecuta: nano .env"
    fi
else
    echo "Archivo .env encontrado"
fi
echo

echo "============================================================"
echo "   Configuración Completada"
echo "============================================================"
echo
echo "Para ejecutar el chatbot:"
echo "  1. Asegúrate de que .env tenga tu OPENAI_API_KEY"
echo "  2. Ejecuta: python run.py"
echo "  3. Abre en navegador: http://localhost:8000"
echo
echo "============================================================"

