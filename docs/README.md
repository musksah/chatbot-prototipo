# 📚 Documentación del Chatbot Cootradecun

Bienvenido a la documentación completa del proyecto. Aquí encontrarás todas las guías y documentos técnicos.

---

## 🚀 Inicio Rápido

Para empezar rápidamente con el proyecto:

1. **[QUICKSTART.md](QUICKSTART.md)** - Guía de inicio rápido (3 pasos)
   - Configuración básica
   - Instalación rápida
   - Primeras pruebas

---

## 📖 Guías de Usuario

### Instalación y Configuración
- **[INSTALL.md](INSTALL.md)** - Guía detallada de instalación
  - Requisitos del sistema
  - Instalación paso a paso
  - Configuración completa
  - Solución de problemas de instalación

### Gestión de Contenido
- **[COMO_AGREGAR_FAQS.md](COMO_AGREGAR_FAQS.md)** - Cómo agregar y editar FAQs
  - Formato del archivo markdown
  - Ejemplos prácticos
  - Categorías y temas
  - Mejores prácticas

### Funcionalidades Avanzadas
- **[MEMORIA_CONVERSACIONES.md](MEMORIA_CONVERSACIONES.md)** - Sistema de memoria persistente
  - Cómo funciona el checkpointing
  - Gestión de sesiones
  - APIs de historial
  - Configuración avanzada (SQLite/PostgreSQL)

- **[RESTRICCIONES_CHATBOT.md](RESTRICCIONES_CHATBOT.md)** - Restricciones de contexto
  - Temas permitidos y prohibidos
  - Sistema de restricción
  - Ejemplos de uso
  - Script de pruebas automatizado

- **[MEJORAS_RAG.md](MEJORAS_RAG.md)** - Mejoras del sistema RAG ✨ NUEVO
  - Indexación mejorada (título + contenido)
  - Logging detallado para debugging
  - Scripts de diagnóstico
  - Guía de troubleshooting

---

## 🔧 Documentación Técnica

### Arquitectura del Sistema
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitectura completa del chatbot
  - Diagramas de flujo
  - Componentes principales
  - Stack tecnológico
  - Decisiones de diseño

### Estado del Proyecto
- **[PROYECTO_COMPLETADO.md](PROYECTO_COMPLETADO.md)** - Resumen completo del proyecto
  - Funcionalidades implementadas
  - Archivos creados
  - Métricas del proyecto
  - Estado final

- **[ESTADO_FINAL.md](ESTADO_FINAL.md)** - Guía de uso y estado actual
  - Cómo ejecutar el chatbot
  - Pruebas recomendadas
  - URLs importantes
  - Datos de prueba

---

## 🐛 Solución de Problemas

### Errores y Soluciones
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Guía completa de problemas comunes
  - UnicodeDecodeError
  - Errores de módulos
  - Puerto en uso
  - Problemas con ChromaDB y WeasyPrint
  - Modo debug

- **[SOLUCION_ERRORES.md](SOLUCION_ERRORES.md)** - Errores solucionados en el desarrollo
  - Error de codificación .env
  - Errores de importación de LangGraph
  - Soluciones aplicadas
  - Estado de compatibilidad

---

## 📝 Historial de Cambios

### Actualizaciones y Mejoras
- **[CAMBIOS_FINALES.md](CAMBIOS_FINALES.md)** - Compatibilidad con LangGraph 0.6.8
  - Cambios de API
  - Archivos modificados
  - Próximos pasos

- **[MEJORA_MARKDOWN_LOADER.md](MEJORA_MARKDOWN_LOADER.md)** - Sistema de carga desde Markdown
  - Comparación antes/después
  - Detalles de implementación
  - Beneficios del cambio
  - Estadísticas

---

## 📑 Estructura de la Documentación

```
docs/
├── README.md (este archivo)           # Índice de documentación
│
├── 🚀 Inicio Rápido
│   ├── QUICKSTART.md                  # 3 pasos para empezar
│   └── INSTALL.md                     # Instalación detallada
│
├── 📖 Guías de Usuario
│   └── COMO_AGREGAR_FAQS.md          # Gestión de FAQs
│
├── 🔧 Documentación Técnica
│   ├── ARCHITECTURE.md                # Arquitectura del sistema
│   ├── PROYECTO_COMPLETADO.md        # Resumen del proyecto
│   └── ESTADO_FINAL.md               # Estado y guía de uso
│
├── 🐛 Solución de Problemas
│   ├── TROUBLESHOOTING.md            # Problemas comunes
│   └── SOLUCION_ERRORES.md           # Errores solucionados
│
└── 📝 Historial
    ├── CAMBIOS_FINALES.md            # Compatibilidad LangGraph
    └── MEJORA_MARKDOWN_LOADER.md     # Sistema Markdown
```

---

## 🎯 ¿Qué Documento Leer?

### Si eres nuevo en el proyecto:
1. **QUICKSTART.md** - Empieza aquí
2. **INSTALL.md** - Si tienes problemas instalando
3. **ESTADO_FINAL.md** - Para ver todas las funcionalidades

### Si quieres agregar/editar contenido:
1. **COMO_AGREGAR_FAQS.md** - Guía completa de FAQs

### Si eres desarrollador:
1. **ARCHITECTURE.md** - Entender la arquitectura
2. **PROYECTO_COMPLETADO.md** - Ver todo lo implementado
3. **CAMBIOS_FINALES.md** - Cambios de compatibilidad

### Si tienes un error:
1. **TROUBLESHOOTING.md** - Problemas comunes
2. **SOLUCION_ERRORES.md** - Errores ya solucionados

### Si quieres saber qué cambió:
1. **MEJORA_MARKDOWN_LOADER.md** - Sistema de carga de FAQs
2. **CAMBIOS_FINALES.md** - Compatibilidad con LangGraph 0.6.8

---

## 📊 Resumen de Documentos

| Documento | Páginas | Audiencia | Prioridad |
|-----------|---------|-----------|-----------|
| QUICKSTART.md | 5 | Todos | 🔴 Alta |
| INSTALL.md | 6 | Todos | 🟡 Media |
| COMO_AGREGAR_FAQS.md | 8 | Editores | 🔴 Alta |
| TROUBLESHOOTING.md | 7 | Todos | 🟡 Media |
| ARCHITECTURE.md | 12 | Desarrolladores | 🟢 Baja |
| PROYECTO_COMPLETADO.md | 10 | Gestores | 🟡 Media |
| ESTADO_FINAL.md | 9 | Todos | 🟡 Media |
| SOLUCION_ERRORES.md | 6 | Desarrolladores | 🟢 Baja |
| CAMBIOS_FINALES.md | 6 | Desarrolladores | 🟢 Baja |
| MEJORA_MARKDOWN_LOADER.md | 7 | Desarrolladores | 🟢 Baja |

---

## 🔗 Enlaces Rápidos

- [README Principal del Proyecto](../README.md)
- [Especificación Original](../Prompt_Cursor_Chatbot_Cootradecun_CallModel.md)
- [Archivo de FAQs](../app/data/faqs_cootradecun.md)

---

## 📞 Ayuda

Si no encuentras lo que buscas:
1. Usa la búsqueda de archivos en tu editor
2. Busca palabras clave en esta página
3. Consulta el README principal

---

## ✨ Documentación Actualizada

Toda la documentación está actualizada a:
- **Fecha**: Octubre 2025
- **Versión LangGraph**: 0.6.8
- **Versión Python**: 3.12
- **Estado**: ✅ Completo y Funcional

---

*Última actualización: Octubre 2025*

