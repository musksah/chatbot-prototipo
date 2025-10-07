# 📁 Estructura del Proyecto

## 🌳 Árbol de Archivos Completo

```
mvp-chatbot-cootradecun/
│
├── 📄 README.md                                # 👈 EMPIEZA AQUÍ
├── 📄 requirements.txt                         # Dependencias Python
├── 📄 Prompt_Cursor_Chatbot_Cootradecun_CallModel.md  # Especificación original
│
├── 🔧 Scripts de Ejecución
│   ├── run.py                                  # Ejecutar con Python
│   ├── run.bat                                 # Ejecutar en Windows
│   ├── setup.bat                               # Instalación Windows
│   ├── setup.sh                                # Instalación Linux/Mac
│   ├── create_env.bat                          # Crear archivo .env
│   ├── test_chatbot.py                         # Tests del chatbot
│   └── test_markdown_loader.py                 # Test loader markdown
│
├── 🔒 Archivos de Configuración
│   ├── .env                                    # Variables de entorno (NO SUBIR)
│   ├── .gitignore                              # Git ignore
│   └── config.example.txt                      # Ejemplo de configuración
│
├── 📚 docs/                                    # 📚 TODA LA DOCUMENTACIÓN
│   ├── README.md                               # Índice de documentación
│   │
│   ├── 🚀 Guías de Inicio
│   │   ├── QUICKSTART.md                       # Inicio rápido (3 pasos)
│   │   └── INSTALL.md                          # Instalación detallada
│   │
│   ├── 📖 Guías de Usuario
│   │   └── COMO_AGREGAR_FAQS.md               # Gestión de FAQs
│   │
│   ├── 🔧 Documentación Técnica
│   │   ├── ARCHITECTURE.md                     # Arquitectura del sistema
│   │   ├── PROYECTO_COMPLETADO.md             # Resumen del proyecto
│   │   └── ESTADO_FINAL.md                    # Estado y guía de uso
│   │
│   ├── 🐛 Solución de Problemas
│   │   ├── TROUBLESHOOTING.md                 # Problemas comunes
│   │   └── SOLUCION_ERRORES.md                # Errores solucionados
│   │
│   ├── 📝 Historial de Cambios
│   │   ├── CAMBIOS_FINALES.md                 # Compatibilidad LangGraph
│   │   ├── MEJORA_MARKDOWN_LOADER.md          # Sistema Markdown
│   │   └── ORGANIZACION_DOCUMENTACION.md      # Esta reorganización
│   │
│   └── ESTRUCTURA_PROYECTO.md                  # Este archivo
│
└── 🐍 app/                                     # CÓDIGO FUENTE
    ├── __init__.py
    ├── main.py                                 # FastAPI app principal
    │
    ├── agents/                                 # 🤖 Agentes LangGraph
    │   ├── __init__.py
    │   ├── graph.py                            # Grafo principal
    │   │
    │   ├── nodes/                              # Nodos del grafo
    │   │   ├── __init__.py
    │   │   ├── router_node.py                  # Router de intenciones
    │   │   └── respond_node.py                 # Formateador de respuestas
    │   │
    │   └── tools/                              # Herramientas (Tools)
    │       ├── __init__.py
    │       ├── rag_tool.py                     # RAG con ChromaDB
    │       ├── linix_tools.py                  # Mock sistema Linix
    │       └── certificate_tool.py             # Generación de PDFs
    │
    ├── routers/                                # 🛣️ Rutas FastAPI
    │   ├── __init__.py
    │   └── chat.py                             # Endpoints del chat
    │
    ├── templates/                              # 🎨 Templates HTML
    │   └── chat.html                           # Interfaz del chatbot
    │
    ├── static/                                 # 📦 Archivos estáticos
    │   └── style.css
    │
    └── data/                                   # 💾 Datos
        ├── faqs_cootradecun.md                 # 👈 FAQs en Markdown
        └── generated/                          # PDFs generados
```

---

## 📊 Resumen por Categoría

### 📄 Documentación (12 archivos)
```
📁 docs/
├── README.md                    # Índice
├── QUICKSTART.md                # 🚀 Inicio rápido
├── INSTALL.md                   # 🚀 Instalación
├── COMO_AGREGAR_FAQS.md        # 📖 FAQs
├── ARCHITECTURE.md              # 🔧 Arquitectura
├── PROYECTO_COMPLETADO.md      # 🔧 Resumen
├── ESTADO_FINAL.md             # 🔧 Estado
├── TROUBLESHOOTING.md          # 🐛 Problemas
├── SOLUCION_ERRORES.md         # 🐛 Errores
├── CAMBIOS_FINALES.md          # 📝 Cambios
├── MEJORA_MARKDOWN_LOADER.md   # 📝 Mejoras
└── ORGANIZACION_DOCUMENTACION.md # 📝 Organización
```

### 🔧 Scripts (7 archivos)
```
run.py                           # Python execution
run.bat                          # Windows execution
setup.bat                        # Windows setup
setup.sh                         # Linux/Mac setup
create_env.bat                   # Environment config
test_chatbot.py                  # Chatbot tests
test_markdown_loader.py          # Markdown tests
```

### 🐍 Código Python (11 archivos)
```
app/
├── main.py                      # FastAPI main
├── agents/
│   ├── graph.py                 # LangGraph
│   ├── nodes/
│   │   ├── router_node.py       # Router
│   │   └── respond_node.py      # Responder
│   └── tools/
│       ├── rag_tool.py          # RAG
│       ├── linix_tools.py       # Linix
│       └── certificate_tool.py  # Certs
└── routers/
    └── chat.py                  # API endpoints
```

### 🎨 Frontend (2 archivos)
```
app/
├── templates/
│   └── chat.html                # UI
└── static/
    └── style.css                # Styles
```

### 💾 Datos (1 archivo + carpeta)
```
app/data/
├── faqs_cootradecun.md          # FAQs source
└── generated/                   # PDF output
```

---

## 🎯 Archivos Importantes

### Para Empezar:
1. **README.md** - Punto de entrada
2. **docs/QUICKSTART.md** - Inicio en 3 pasos
3. **requirements.txt** - Instalar dependencias

### Para Ejecutar:
1. **run.bat** (Windows) o **run.py** (multiplataforma)
2. **.env** - Configurar API key

### Para Desarrollar:
1. **app/main.py** - FastAPI app
2. **app/agents/graph.py** - LangGraph core
3. **app/agents/tools/** - Herramientas

### Para Documentación:
1. **docs/README.md** - Índice completo
2. **docs/ARCHITECTURE.md** - Entender sistema
3. **docs/COMO_AGREGAR_FAQS.md** - Editar contenido

---

## 📈 Estadísticas del Proyecto

| Categoría | Cantidad |
|-----------|----------|
| **Total de archivos** | ~40 |
| **Documentación (.md)** | 12 |
| **Scripts (.py, .bat, .sh)** | 7 |
| **Código Python (.py)** | 11 |
| **Templates HTML** | 1 |
| **Archivos de config** | 4 |

---

## 🔑 Archivos Clave por Función

### Configuración Inicial:
```
1. requirements.txt        → Instalar dependencias
2. .env                    → Configurar API key
3. setup.bat / setup.sh    → Auto-instalación
```

### Ejecución:
```
1. run.bat / run.py        → Iniciar servidor
2. app/main.py             → FastAPI app
3. app/agents/graph.py     → LangGraph engine
```

### Contenido:
```
1. app/data/faqs_cootradecun.md  → Editar FAQs
2. app/agents/tools/rag_tool.py  → Loader de FAQs
```

### Interfaz:
```
1. app/templates/chat.html       → UI del chatbot
2. app/static/style.css          → Estilos
```

### Documentación:
```
1. README.md                     → Entrada principal
2. docs/README.md                → Índice de docs
3. docs/QUICKSTART.md            → Guía rápida
```

---

## 🗺️ Mapa de Navegación

```
START
  ↓
README.md (raíz)
  ↓
  ├─→ ¿Quieres empezar?          → docs/QUICKSTART.md
  ├─→ ¿Problemas instalando?      → docs/INSTALL.md
  ├─→ ¿Agregar FAQs?              → docs/COMO_AGREGAR_FAQS.md
  ├─→ ¿Entender arquitectura?     → docs/ARCHITECTURE.md
  ├─→ ¿Tienes un error?           → docs/TROUBLESHOOTING.md
  └─→ ¿Ver todo?                  → docs/README.md (índice)
```

---

## 💡 Tips de Navegación

### En VS Code / Cursor:
- Usa `Ctrl+P` y escribe el nombre del archivo
- Explora la carpeta `docs/` en el sidebar
- Usa `Ctrl+Shift+F` para buscar en todos los archivos

### En Terminal:
```bash
# Ver estructura
tree /f

# Buscar en documentación
findstr /s /i "palabra" docs\*.md

# Abrir archivo
notepad docs\QUICKSTART.md
```

### En GitHub:
- La carpeta `docs/` tiene su propio README
- Todos los links funcionan correctamente
- Fácil navegar entre documentos

---

## 🎨 Convenciones de Nombres

### Archivos Markdown:
- **MAYÚSCULAS.md** - Documentación importante
- **snake_case.md** - Scripts o configs
- **README.md** - Índices

### Archivos Python:
- **snake_case.py** - Módulos
- **__init__.py** - Paquetes

### Scripts:
- **run.*** - Ejecución
- **setup.*** - Instalación
- **test_*** - Pruebas

---

## ✅ Checklist de Archivos Esenciales

Para que el proyecto funcione, necesitas:

- [x] README.md
- [x] requirements.txt
- [x] .env (con tu API key)
- [x] app/main.py
- [x] app/agents/graph.py
- [x] app/templates/chat.html
- [x] app/data/faqs_cootradecun.md
- [x] docs/ (completo)

---

## 🚀 Próxima Actualización

Si el proyecto crece, considera:
- Separar `app/agents/` por funcionalidad
- Crear `app/models/` para modelos de datos
- Agregar `tests/` para pruebas unitarias
- Crear `scripts/` para utilidades

---

*Estructura documentada: Octubre 2025*  
*Total de archivos: ~40*  
*Estado: ✅ Organizado y Completo*

