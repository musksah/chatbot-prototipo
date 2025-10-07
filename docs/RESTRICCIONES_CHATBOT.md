# 🔒 Restricciones del Chatbot - Cootradecun

## 📋 Descripción General

El chatbot de Cootradecun está **restringido exclusivamente** a responder preguntas relacionadas con la Cooperativa de Trabajadores de Cundinamarca. El bot rechaza cortésmente cualquier consulta fuera de este alcance.

---

## ✅ Temas Permitidos

El chatbot SOLO puede ayudar con:

### 1. **Servicios y Beneficios**
- Horarios de atención
- Beneficios de afiliación
- Convenios comerciales
- Seguros y protección
- Auxilios educativos

### 2. **Afiliación y Aportes**
- Proceso de afiliación
- Requisitos para ser afiliado
- Aportes mínimos
- Consulta de estado de cuenta
- Retiro de aportes

### 3. **Créditos**
- Tipos de crédito disponibles
- Requisitos para créditos
- Simulación de créditos
- Tasas de interés
- Verificación de elegibilidad

### 4. **Documentos**
- Generación de certificados
- Certificados de afiliación
- Constancias

### 5. **Información General**
- Datos de contacto
- Ubicación de oficinas
- Canales de atención

---

## ❌ Temas NO Permitidos

El chatbot NO responderá preguntas sobre:

- 🍳 **Recetas de cocina** (ej: "¿Cómo hacer un flan?")
- ⚽ **Deportes** (ej: "¿Quién ganó el mundial?")
- 🎬 **Entretenimiento** (ej: "¿Qué película me recomiendas?")
- 🏥 **Consejos de salud** (ej: "¿Cómo perder peso?")
- ✈️ **Turismo** (ej: "¿Dónde viajar en vacaciones?")
- 📚 **Tareas escolares** (ej: "Ayúdame con mi tarea de matemáticas")
- 🌍 **Cultura general** (ej: "¿Cuál es la capital de Francia?")
- 🔧 **Reparaciones** (ej: "¿Cómo arreglar mi computadora?")
- 💻 **Programación general** (ej: "¿Cómo programar en Python?")
- 🎨 **Arte y diseño** (ej: "¿Cómo dibujar un paisaje?")

---

## 💬 Respuesta Estándar a Preguntas Fuera de Contexto

Cuando se le pregunta algo fuera del alcance, el bot responde:

```
Lo siento, soy un asistente especializado en la Cooperativa de 
Trabajadores de Cundinamarca (Cootradecun). Solo puedo ayudarte 
con consultas sobre:

- Servicios y beneficios de la cooperativa
- Estado de afiliación y aportes
- Créditos y simulaciones
- Certificados y documentos
- Horarios y requisitos

¿En qué tema relacionado con Cootradecun puedo ayudarte?
```

---

## 🧪 Ejemplos de Uso

### ✅ Ejemplo 1: Pregunta Válida

**Usuario:** "¿Cuáles son los horarios de atención?"

**Bot:** "🤖 Cootradecun atiende de lunes a viernes de 8:00 AM a 5:00 PM, y los sábados de 8:00 AM a 12:00 PM."

---

### ✅ Ejemplo 2: Pregunta Válida sobre Créditos

**Usuario:** "Quiero simular un crédito de 10 millones"

**Bot:** "🤖 Claro, puedo ayudarte con la simulación. ¿A cuántos meses deseas el crédito?"

---

### ❌ Ejemplo 3: Pregunta Rechazada - Receta

**Usuario:** "¿Cuál es la receta para hacer un flan?"

**Bot:** "🤖 Lo siento, soy un asistente especializado en la Cooperativa de Trabajadores de Cundinamarca (Cootradecun). Solo puedo ayudarte con consultas sobre servicios y beneficios de la cooperativa, estado de afiliación y aportes, créditos y simulaciones..."

---

### ❌ Ejemplo 4: Pregunta Rechazada - Deportes

**Usuario:** "¿Quién ganó el mundial de fútbol?"

**Bot:** "🤖 Lo siento, solo puedo ayudarte con temas relacionados a Cootradecun..."

---

## 🔧 Implementación Técnica

### System Prompt

El comportamiento restrictivo se implementa mediante el `SYSTEM_PROMPT` en `app/agents/graph.py`:

```python
SYSTEM_PROMPT = """Eres un asistente virtual de Cootradecun, la Cooperativa de 
Trabajadores de Cundinamarca.

ALCANCE DE TU FUNCIÓN:
Tu ÚNICA función es ayudar a los afiliados con temas relacionados a Cootradecun:
- Consultas sobre servicios y beneficios de la cooperativa
- Horarios de atención y requisitos
- Verificación de estado de afiliación y aportes
- Simulación y solicitud de créditos
- Generación de certificados
...

RESTRICCIONES IMPORTANTES:
- NO respondas preguntas que NO estén relacionadas con Cootradecun
- NO proporciones información sobre: recetas, deportes, entretenimiento...
- Si te preguntan algo fuera del alcance, responde cortésmente indicando 
  que solo puedes ayudar con temas de Cootradecun
...
"""
```

### Características del Sistema de Restricción

1. **Instrucciones Claras**: El prompt especifica explícitamente qué temas están permitidos
2. **Ejemplos de Restricción**: Lista específica de temas prohibidos
3. **Respuesta Estándar**: Plantilla de respuesta para rechazar preguntas
4. **Tono Cortés**: Las restricciones se comunican de manera amable y profesional

---

## 🧪 Pruebas de Restricción

### Script de Prueba Automatizado

Ejecuta el script de pruebas para verificar las restricciones:

```bash
# Terminal 1: Iniciar el servidor
python run.py

# Terminal 2: Ejecutar pruebas de restricción
python test_restricciones.py
```

### Pruebas Incluidas

El script `test_restricciones.py` verifica:

1. **Preguntas fuera de contexto** (6 casos)
   - Recetas de cocina
   - Deportes
   - Salud general
   - Turismo
   - Geografía
   - Ciencia

2. **Preguntas válidas** (4 casos)
   - Horarios
   - Beneficios
   - Requisitos de créditos
   - Consulta de estado

3. **Casos límite** (3 casos)
   - Saludos
   - Preguntas sobre capacidades
   - Tareas escolares

---

## 📊 Métricas Esperadas

### Tasa de Restricción Objetivo

- **Preguntas fuera de contexto**: 100% rechazadas
- **Preguntas válidas**: 100% respondidas
- **Casos límite**: >90% manejados correctamente

### Indicadores de Éxito

✅ **Restricción efectiva**: El bot NO responde recetas, deportes, etc.  
✅ **Respuesta cortés**: Siempre rechaza amablemente y ofrece alternativas  
✅ **No afecta funcionalidad**: Las preguntas válidas se responden normalmente  

---

## 🎯 Casos Especiales

### Preguntas Ambiguas

Si una pregunta es ambigua o podría interpretarse de múltiples formas:

**Usuario:** "¿Cómo puedo ahorrar?"

**Bot esperado:** Debe interpretarse en el contexto de la cooperativa y responder sobre opciones de ahorro en Cootradecun.

### Saludos y Conversación Casual

Los saludos y conversación casual relacionados con la interacción SÍ están permitidos:

**Usuario:** "Hola, ¿cómo estás?"

**Bot:** "🤖 ¡Hola! Estoy aquí para ayudarte con temas relacionados a Cootradecun. ¿En qué puedo ayudarte hoy?"

### Preguntas sobre las Capacidades del Bot

**Usuario:** "¿Qué puedes hacer?"

**Bot:** "🤖 Puedo ayudarte con:
- Consultas sobre servicios y beneficios de Cootradecun
- Estado de afiliación y aportes
- Simulación de créditos
- Generación de certificados
..."

---

## 🔄 Ajustes y Personalización

### Modificar las Restricciones

Si necesitas ajustar qué temas están permitidos o restringidos:

1. Edita el archivo `app/agents/graph.py`
2. Modifica la variable `SYSTEM_PROMPT`
3. Actualiza las secciones:
   - `ALCANCE DE TU FUNCIÓN`: Agrega o quita temas permitidos
   - `RESTRICCIONES IMPORTANTES`: Agrega o quita restricciones
   - `RESPUESTAS A PREGUNTAS FUERA DE TEMA`: Ajusta el mensaje

### Cambiar el Mensaje de Rechazo

Para personalizar cómo el bot rechaza preguntas:

```python
RESPUESTAS A PREGUNTAS FUERA DE TEMA:
Si te preguntan algo NO relacionado con Cootradecun, responde:
"[Tu mensaje personalizado aquí]"
```

---

## 💡 Mejores Prácticas

### Para Usuarios

1. **Sé específico**: Pregunta directamente sobre temas de Cootradecun
2. **Usa términos claros**: "crédito", "aportes", "certificado", etc.
3. **Si el bot rechaza tu pregunta**: Reformúlala enfocándola en la cooperativa

### Para Administradores

1. **Monitorea las restricciones**: Revisa los logs para ver qué preguntas se rechazan
2. **Ajusta según necesidad**: Si muchos usuarios preguntan algo legítimo que se rechaza, ajusta el prompt
3. **Mantén coherencia**: Asegúrate de que el prompt y la documentación estén alineados

---

## 🐛 Solución de Problemas

### El bot responde preguntas que debería rechazar

**Solución:**
1. Verifica el `SYSTEM_PROMPT` en `app/agents/graph.py`
2. Asegúrate de reiniciar el servidor después de cambios
3. Sé más explícito en las restricciones del prompt

### El bot rechaza preguntas válidas

**Solución:**
1. Revisa si la pregunta está claramente relacionada con Cootradecun
2. Reformula la pregunta para ser más específica
3. Ajusta el `SYSTEM_PROMPT` si es necesario incluir más temas

### Mensajes de rechazo inconsistentes

**Solución:**
1. Asegúrate de que el `SYSTEM_PROMPT` incluya la respuesta estándar
2. Verifica la temperatura del modelo (0.3 es óptimo para consistencia)
3. Prueba con el script `test_restricciones.py`

---

## 📈 Beneficios de las Restricciones

### ✅ Para Usuarios
- **Experiencia enfocada**: El bot no se distrae con temas irrelevantes
- **Respuestas precisas**: Especialización en el dominio de la cooperativa
- **Claridad de propósito**: Los usuarios saben exactamente qué esperar

### ✅ Para la Organización
- **Imagen profesional**: El bot se mantiene en su rol de asistente cooperativo
- **Recursos optimizados**: No se gastan tokens en respuestas fuera de alcance
- **Cumplimiento**: Evita responder sobre temas sensibles o legales fuera de competencia

---

## 📚 Referencias

- Archivo de configuración: `app/agents/graph.py` (líneas 71-113)
- Script de pruebas: `test_restricciones.py`
- Documentación general: `README.md`

---

## ✨ Resumen

El chatbot de Cootradecun está configurado para:

✅ **Responder SOLO** sobre temas de la cooperativa  
❌ **Rechazar cortésmente** preguntas fuera de contexto  
🤖 **Mantener profesionalismo** en todas las interacciones  
📊 **Ser consistente** en sus restricciones  

**Estado**: ✅ Implementado y funcional  
**Script de pruebas**: ✅ Disponible (`test_restricciones.py`)  
**Última actualización**: Octubre 2025

---

*Para más información, consulta el README principal o contacta al equipo de desarrollo.*

