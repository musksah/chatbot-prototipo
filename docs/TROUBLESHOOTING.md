# 🔧 Solución de Problemas - Chatbot Cootradecun

## ❌ Error: UnicodeDecodeError al cargar .env

### Síntoma:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte
```

### Causa:
El archivo `.env` tiene una codificación incorrecta (probablemente UTF-16 con BOM en lugar de UTF-8).

### Solución Rápida:

**Opción 1: Usar el script helper** (Recomendado)
```cmd
create_env.bat
```
Este script creará el archivo `.env` con la codificación correcta.

**Opción 2: Manual**
1. Elimina el archivo `.env` actual:
   ```cmd
   del .env
   ```

2. Crea uno nuevo con PowerShell:
   ```powershell
   @"
   # OpenAI Configuration
   OPENAI_API_KEY=sk-your-api-key-here
   
   # Application Configuration
   ENVIRONMENT=development
   LOG_LEVEL=INFO
   
   # Server Configuration
   HOST=0.0.0.0
   PORT=8000
   "@ | Out-File -FilePath .env -Encoding UTF8 -NoNewline
   ```

3. Edita el archivo y agrega tu API key real:
   ```cmd
   notepad .env
   ```

**Opción 3: Con VS Code**
1. Elimina el `.env` actual
2. En VS Code: File → New File
3. Pega el contenido de `.env.example`
4. Guarda como `.env`
5. Verifica que VS Code muestre "UTF-8" en la barra inferior
6. Si dice "UTF-16" o algo más, haz clic y cambia a "UTF-8"

---

## ❌ Error: OPENAI_API_KEY no configurada

### Síntoma:
```
⚠️  ADVERTENCIA: OPENAI_API_KEY no configurada
```

### Solución:
1. Verifica que el archivo `.env` exista
2. Abre el archivo `.env` y asegúrate de tener:
   ```
   OPENAI_API_KEY=sk-tu-api-key-real-aqui
   ```
3. Reemplaza `sk-tu-api-key-real-aqui` con tu API key de OpenAI
4. Guarda el archivo
5. Reinicia el servidor

---

## ❌ Error: Module not found

### Síntoma:
```
ModuleNotFoundError: No module named 'fastapi'
```

### Solución:
1. Verifica que el entorno virtual esté activado:
   ```cmd
   venv\Scripts\activate
   ```
   
2. Reinstala las dependencias:
   ```cmd
   pip install -r requirements.txt
   ```

3. Si persiste, elimina y recrea el entorno virtual:
   ```cmd
   rmdir /s /q venv
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## ❌ Error: Puerto 8000 ya en uso

### Síntoma:
```
OSError: [Errno 48] Address already in use
```

### Solución:

**Opción 1: Cambiar el puerto**
En el archivo `.env`:
```
PORT=8001
```

**Opción 2: Matar el proceso que usa el puerto**
```cmd
# Encontrar el proceso
netstat -ano | findstr :8000

# Matar el proceso (reemplaza <PID> con el número)
taskkill /PID <PID> /F
```

---

## ❌ Error: ChromaDB no se puede instalar

### Síntoma:
```
ERROR: Failed building wheel for chromadb
```

### Solución:
1. Actualiza pip:
   ```cmd
   pip install --upgrade pip
   ```

2. Instala herramientas de compilación:
   ```cmd
   pip install --upgrade setuptools wheel
   ```

3. Intenta de nuevo:
   ```cmd
   pip install chromadb==0.4.22
   ```

---

## ❌ Error: WeasyPrint no se instala en Windows

### Síntoma:
```
OSError: cannot load library 'gobject-2.0-0'
```

### Solución:
WeasyPrint requiere GTK3 en Windows. Tienes dos opciones:

**Opción 1: Omitir WeasyPrint** (Recomendado para desarrollo)
El chatbot funcionará sin WeasyPrint, generando certificados simulados:
```cmd
pip install -r requirements.txt --no-deps
pip install fastapi uvicorn langchain langchain-openai langgraph chromadb python-dotenv pydantic requests jinja2
```

**Opción 2: Instalar GTK3**
1. Descarga GTK3 Runtime:
   https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
2. Instala GTK3
3. Instala WeasyPrint:
   ```cmd
   pip install weasyprint
   ```

---

## ❌ Error: ImportError con LangGraph

### Síntoma:
```
ImportError: cannot import name 'MessagesState' from 'langgraph.graph'
```

### Solución:
Versión incorrecta de LangGraph. Instala la versión correcta:
```cmd
pip uninstall langgraph langchain langchain-openai -y
pip install langgraph==0.0.20 langchain==0.1.4 langchain-openai==0.0.5
```

---

## ⚠️ Advertencia: El chatbot no responde

### Posibles causas:

**1. OPENAI_API_KEY inválida**
- Verifica que tu API key sea correcta
- Verifica que tengas créditos en tu cuenta OpenAI
- Prueba la API key en: https://platform.openai.com/playground

**2. Problema de conexión**
- Verifica tu conexión a internet
- Si estás detrás de un proxy, configúralo

**3. El grafo no se inicializó**
- Revisa los logs en la consola
- Busca mensajes de error al iniciar

---

## 🐛 Modo Debug

Para obtener más información sobre errores:

1. **Activar logs detallados**
   En `.env`:
   ```
   LOG_LEVEL=DEBUG
   ```

2. **Ver el traceback completo**
   En la consola donde ejecutaste `run.bat` o `python run.py`

3. **Probar con el script de pruebas**
   ```cmd
   python test_chatbot.py
   ```
   Esto probará el chatbot sin la interfaz web

---

## 📊 Verificar instalación

Ejecuta estos comandos para verificar que todo esté instalado:

```cmd
# Verificar Python
python --version

# Verificar pip
pip --version

# Verificar paquetes instalados
pip list

# Verificar que el archivo .env existe
dir .env

# Verificar estructura del proyecto
dir /s /b app
```

---

## 🆘 Obtener ayuda

Si ninguna de estas soluciones funciona:

1. **Revisa los logs completos** en la consola
2. **Copia el error completo** incluyendo el traceback
3. **Verifica las versiones** de Python y paquetes
4. **Comprueba que tienes**:
   - Python 3.11 o superior
   - pip actualizado
   - Conexión a internet
   - API key de OpenAI válida

---

## 📝 Checklist de verificación

Antes de reportar un error, verifica:

- [ ] Python 3.11+ instalado
- [ ] Entorno virtual activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Archivo `.env` existe y tiene codificación UTF-8
- [ ] `OPENAI_API_KEY` configurada en `.env`
- [ ] Puerto 8000 disponible
- [ ] Conexión a internet activa
- [ ] API key de OpenAI válida y con créditos

---

## 🔄 Reinstalación limpia

Si todo lo demás falla, prueba una reinstalación limpia:

```cmd
# 1. Desactivar entorno virtual (si está activo)
deactivate

# 2. Eliminar entorno virtual
rmdir /s /q venv

# 3. Eliminar .env con problemas
del .env

# 4. Crear nuevo entorno virtual
python -m venv venv

# 5. Activar entorno virtual
venv\Scripts\activate

# 6. Actualizar pip
pip install --upgrade pip

# 7. Instalar dependencias
pip install -r requirements.txt

# 8. Crear .env con codificación correcta
create_env.bat

# 9. Editar .env con tu API key
notepad .env

# 10. Ejecutar
python run.py
```

---

*Última actualización: Octubre 2025*

