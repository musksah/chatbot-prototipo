# 📚 Cómo Agregar y Gestionar FAQs

## 🎯 Sistema de Carga desde Markdown

El chatbot ahora carga los FAQs desde un archivo **Markdown** en lugar de tener los datos hardcodeados en Python. Esto hace que sea mucho más fácil agregar, editar o eliminar FAQs sin tocar el código.

---

## 📁 Ubicación del Archivo

```
app/data/faqs_cootradecun.md
```

---

## 📝 Formato del Archivo

### Estructura General:

```markdown
# FAQs Cootradecun - Base de Conocimiento

## Título del FAQ

Contenido completo del FAQ. Puede tener múltiples párrafos.

Segunda parte del contenido si es necesario.

**Categoría**: nombre_categoria  
**Tema**: nombre_tema

---

## Siguiente FAQ

Contenido del siguiente FAQ...

**Categoría**: otra_categoria  
**Tema**: otro_tema

---
```

### Reglas Importantes:

1. **Cada FAQ debe empezar con `## ` (dos almohadillas)**
2. **Debe haber una línea en blanco después del título**
3. **El contenido va después de la línea en blanco**
4. **Los metadatos son opcionales pero recomendados:**
   - `**Categoría**: valor` (categoría principal)
   - `**Tema**: valor` (subtema)
5. **Cada FAQ debe terminar con `---` (tres guiones)**
6. **Debe haber una línea en blanco antes del separador `---`**

---

## ✨ Ejemplo Completo

```markdown
## Horarios de Atención

Cootradecun atiende de lunes a viernes de 8:00 AM a 5:00 PM, y los sábados de 8:00 AM a 12:00 PM. Horario de atención en oficinas principales.

**Categoría**: horarios  
**Tema**: atencion

---

## Beneficios de Afiliación

Los beneficios de ser afiliado a Cootradecun incluyen: acceso a créditos con tasas preferenciales, auxilios educativos, ahorro programado, seguros de vida, y acceso a convenios comerciales.

**Categoría**: beneficios  
**Tema**: afiliacion

---
```

---

## ➕ Cómo Agregar un Nuevo FAQ

### Paso 1: Abre el archivo
```bash
notepad app\data\faqs_cootradecun.md
```

### Paso 2: Ve al final del archivo

### Paso 3: Agrega tu FAQ siguiendo el formato:

```markdown
## Tu Nuevo Título

Tu contenido aquí. Explica claramente la información que los usuarios necesitan saber.

**Categoría**: categoria  
**Tema**: tema

---
```

### Paso 4: Guarda el archivo

### Paso 5: Reinicia el chatbot

El chatbot cargará automáticamente el nuevo FAQ al iniciar.

---

## ✏️ Cómo Editar un FAQ Existente

1. Abre `app\data\faqs_cootradecun.md`
2. Busca el FAQ que quieres editar
3. Modifica el contenido
4. Guarda el archivo
5. Reinicia el chatbot

---

## 🗑️ Cómo Eliminar un FAQ

1. Abre `app\data\faqs_cootradecun.md`
2. Encuentra el FAQ que quieres eliminar
3. Elimina desde `##` hasta el `---` (inclusive)
4. Guarda el archivo
5. Reinicia el chatbot

---

## 🏷️ Categorías y Temas Actuales

### Categorías Disponibles:
- `horarios` - Horarios de atención
- `beneficios` - Beneficios de afiliación
- `creditos` - Información sobre créditos
- `aportes` - Aportes y retiros
- `afiliacion` - Proceso de afiliación
- `consultas` - Consultas generales
- `seguros` - Seguros y protección

### Temas Comunes:
- `atencion` - Atención al cliente
- `requisitos` - Requisitos y condiciones
- `tipos` - Tipos de servicios
- `tasas` - Tasas e intereses
- `proceso` - Procesos y trámites
- `estado_cuenta` - Consulta de estado

Puedes crear nuevas categorías y temas según necesites.

---

## 🧪 Probar los Cambios

### Opción 1: Script de Prueba

```bash
python test_markdown_loader.py
```

Esto te mostrará cuántos FAQs se parsearon y sus detalles.

### Opción 2: Ejecutar el Chatbot

```bash
python run.py
```

En los logs verás:
```
✅ Parseados 11 FAQs desde faqs_cootradecun.md
✅ Cargados 11 documentos en ChromaDB
```

### Opción 3: Probar en la Interfaz

1. Abre http://localhost:8000
2. Haz una pregunta relacionada con el FAQ que agregaste/modificaste
3. Verifica que el chatbot responda correctamente

---

## 📊 FAQs Actuales (11 en total)

1. **Horarios de Atención** - horarios/atencion
2. **Beneficios de Afiliación** - beneficios/afiliacion
3. **Requisitos para Créditos** - creditos/requisitos
4. **Tipos de Crédito Disponibles** - creditos/tipos
5. **Aportes Mínimos** - aportes/requisitos
6. **Proceso de Afiliación** - afiliacion/requisitos
7. **Consulta de Estado de Cuenta** - consultas/estado_cuenta
8. **Auxilios Educativos** - beneficios/educacion
9. **Tasas de Interés** - creditos/tasas
10. **Seguros y Protección** - beneficios/seguros
11. **Retiro de Aportes** - aportes/retiro
12. **Convenios Comerciales** - beneficios/convenios

---

## 🔧 Características Técnicas

### Parser de Markdown

El sistema utiliza un parser personalizado que:

- ✅ Lee archivos markdown con encoding UTF-8
- ✅ Extrae títulos de nivel 2 (`##`)
- ✅ Separa contenido por `---`
- ✅ Extrae metadatos (Categoría y Tema)
- ✅ Crea IDs automáticos (faq_1, faq_2, etc.)
- ✅ Maneja errores gracefully
- ✅ Tiene fallback a datos básicos si el archivo no existe

### Código Fuente

El parser está en: `app/agents/tools/rag_tool.py`

Funciones principales:
- `_parse_markdown_faqs()` - Parsea el archivo markdown
- `_load_sample_data()` - Carga los datos en ChromaDB
- `initialize_rag()` - Inicializa el sistema RAG

---

## 💡 Consejos y Buenas Prácticas

### 1. **Contenido Claro y Conciso**
- Escribe respuestas directas y fáciles de entender
- Evita jerga técnica innecesaria
- Usa ejemplos cuando sea apropiado

### 2. **Organización**
- Agrupa FAQs relacionados por categoría
- Usa temas para subdividir categorías grandes
- Mantén un orden lógico (de lo general a lo específico)

### 3. **Actualización**
- Revisa y actualiza los FAQs periódicamente
- Elimina información obsoleta
- Agrega FAQs basándote en preguntas frecuentes de usuarios

### 4. **Testing**
- Siempre prueba después de agregar/modificar FAQs
- Verifica que el chatbot encuentre la información
- Prueba con diferentes formas de preguntar

### 5. **Formato**
- Mantén el formato consistente
- No olvides los metadatos
- No olvides el separador `---` al final

---

## 🚨 Errores Comunes y Soluciones

### Error: "No se pudieron cargar FAQs"

**Causa:** Problema con el formato del markdown

**Solución:**
1. Verifica que cada FAQ empiece con `##`
2. Verifica que haya línea en blanco después del título
3. Verifica que cada FAQ termine con `---`
4. Verifica la codificación del archivo (debe ser UTF-8)

### Error: "Archivo de FAQs no encontrado"

**Causa:** El archivo no existe o está en la ubicación incorrecta

**Solución:**
1. Verifica que el archivo esté en `app/data/faqs_cootradecun.md`
2. Verifica que el nombre del archivo sea exacto
3. Verifica los permisos del archivo

### Error: Parser no encuentra algunos FAQs

**Causa:** Formato incorrecto en esos FAQs

**Solución:**
1. Ejecuta `python test_markdown_loader.py` para ver qué se parseó
2. Revisa el formato de los FAQs que no aparecen
3. Asegúrate de que sigan el formato exacto

---

## 📈 Expansión Futura

### Características Planeadas:

- [ ] Soporte para subsecciones (### )
- [ ] Imágenes en FAQs
- [ ] Links internos entre FAQs
- [ ] Versionado de FAQs
- [ ] Múltiples archivos markdown
- [ ] Sincronización automática (hot reload)
- [ ] Panel de administración web

---

## 🎓 Ejemplo: Agregar FAQ de "Préstamos de Calamidad"

```markdown
## Préstamos de Calamidad Doméstica

Cootradecun ofrece préstamos especiales para calamidades domésticas como enfermedades graves, daños en vivienda, o pérdidas materiales significativas. Estos préstamos tienen:

- Desembolso rápido (24-48 horas)
- Tasa de interés preferencial (8% anual)
- Plazo flexible hasta 36 meses
- Sin costos adicionales de estudio

Requisitos: Ser afiliado activo, tener mínimo 3 meses de antigüedad, presentar documentación que sustente la calamidad.

**Categoría**: creditos  
**Tema**: calamidad

---
```

Guarda, reinicia el chatbot, y prueba preguntando:
```
"¿Qué préstamos hay para calamidades?"
```

---

## ✅ Checklist de Verificación

Antes de hacer cambios en producción:

- [ ] El archivo tiene codificación UTF-8
- [ ] Cada FAQ tiene título con `##`
- [ ] Hay línea en blanco después del título
- [ ] El contenido es claro y útil
- [ ] Los metadatos están presentes
- [ ] Cada FAQ termina con `---`
- [ ] El archivo se parseó correctamente (test)
- [ ] El chatbot responde correctamente (prueba)
- [ ] Los logs muestran el número correcto de FAQs

---

## 📞 Soporte

Si tienes problemas:

1. Ejecuta `python test_markdown_loader.py` para diagnosticar
2. Revisa los logs del chatbot
3. Verifica el formato del markdown
4. Consulta la documentación de ChromaDB

---

*Última actualización: Octubre 2025*  
*Sistema de carga dinámica desde Markdown implementado ✅*

