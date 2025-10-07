# 🔒 Implementación de Restricciones de Contexto - Resumen de Cambios

## 📅 Fecha de Implementación
Octubre 7, 2025

## 🎯 Objetivo
Restringir el chatbot para que SOLO responda preguntas relacionadas con la Cooperativa de Trabajadores de Cundinamarca (Cootradecun), rechazando cortésmente cualquier consulta fuera de este contexto (recetas, deportes, consejos generales, etc.).

---

## ✅ Cambios Implementados

### 1. **app/agents/graph.py**

#### System Prompt Mejorado

**Antes:**
```python
SYSTEM_PROMPT = """Eres un asistente virtual de Cootradecun...

Tu objetivo es ayudar a los afiliados con:
- Consultas sobre servicios y beneficios
- Verificación de estado de afiliación
...

Responde de forma conversacional y útil."""
```

**Después:**
```python
SYSTEM_PROMPT = """Eres un asistente virtual de Cootradecun...

ALCANCE DE TU FUNCIÓN:
Tu ÚNICA función es ayudar a los afiliados con temas relacionados a Cootradecun:
[Lista detallada de temas permitidos]

RESTRICCIONES IMPORTANTES:
- NO respondas preguntas que NO estén relacionadas con Cootradecun
- NO proporciones información sobre: recetas, deportes, entretenimiento...
- Si te preguntan algo fuera del alcance, responde cortésmente...

RESPUESTAS A PREGUNTAS FUERA DE TEMA:
Si te preguntan algo NO relacionado con Cootradecun, responde:
"Lo siento, soy un asistente especializado en la Cooperativa de 
Trabajadores de Cundinamarca (Cootradecun). Solo puedo ayudarte con..."
"""
```

#### Características del Nuevo Prompt

1. **Sección "ALCANCE DE TU FUNCIÓN"**
   - Lista explícita de temas permitidos
   - Enfoque claro en servicios cooperativos

2. **Sección "RESTRICCIONES IMPORTANTES"**
   - Lista explícita de temas prohibidos con ejemplos
   - Instrucción clara de rechazar preguntas fuera de contexto

3. **Sección "RESPUESTAS A PREGUNTAS FUERA DE TEMA"**
   - Plantilla de respuesta estándar para rechazos
   - Tono cortés y profesional
   - Ofrece alternativas válidas

### 2. **app/main.py**

#### Endpoint /api/info

Agregada información sobre restricciones:

```python
"features": {
    ...
    "context_restrictions": {
        "enabled": True,
        "description": "El bot solo responde preguntas relacionadas con Cootradecun",
        "scope": "Servicios cooperativos, créditos, afiliación, certificados",
        "rejects": "Preguntas fuera de contexto (recetas, deportes, etc.)"
    }
}
```

### 3. **Documentación Nueva**

#### docs/RESTRICCIONES_CHATBOT.md (NUEVO)

Documentación completa de 10+ páginas sobre:
- ✅ Temas permitidos (lista detallada)
- ❌ Temas NO permitidos (lista con ejemplos)
- 💬 Respuesta estándar a preguntas fuera de contexto
- 🧪 Ejemplos de uso (válidos e inválidos)
- 🔧 Implementación técnica
- 🐛 Solución de problemas
- 📈 Beneficios del sistema de restricción

### 4. **Script de Pruebas**

#### test_restricciones.py (NUEVO)

Script automatizado de pruebas con 3 categorías:

**Test 1: Preguntas Fuera de Contexto (6 casos)**
- ❌ Recetas de cocina (flan)
- ❌ Deportes (mundial de fútbol)
- ❌ Salud general (perder peso)
- ❌ Turismo (viajar a Europa)
- ❌ Geografía (capital de Francia)
- ❌ Ciencia (fotosíntesis)

**Test 2: Preguntas Válidas (4 casos)**
- ✅ Horarios de atención
- ✅ Beneficios de afiliación
- ✅ Requisitos para créditos
- ✅ Consulta de estado

**Test 3: Casos Límite (3 casos)**
- ✅ Saludos simples
- ✅ Preguntas sobre capacidades
- ❌ Tareas escolares

### 5. **Actualizaciones de Documentación**

#### README.md
- Agregada sección "Restricciones de Contexto"
- Enlace a documentación detallada

#### docs/README.md
- Agregada entrada en "Funcionalidades Avanzadas"
- Referencia a RESTRICCIONES_CHATBOT.md

---

## 🎯 Comportamiento Esperado

### ✅ Preguntas Válidas - El Bot RESPONDE

**Ejemplo 1:**
```
Usuario: "¿Cuáles son los horarios de atención?"
Bot: "🤖 Cootradecun atiende de lunes a viernes de 8:00 AM a 5:00 PM..."
```

**Ejemplo 2:**
```
Usuario: "Quiero simular un crédito de 5 millones"
Bot: "🤖 Claro, puedo ayudarte con la simulación. ¿A cuántos meses...?"
```

### ❌ Preguntas Fuera de Contexto - El Bot RECHAZA

**Ejemplo 1:**
```
Usuario: "¿Cuál es la receta para hacer un flan?"
Bot: "🤖 Lo siento, soy un asistente especializado en la Cooperativa de 
Trabajadores de Cundinamarca (Cootradecun). Solo puedo ayudarte con 
consultas sobre servicios y beneficios de la cooperativa..."
```

**Ejemplo 2:**
```
Usuario: "¿Quién ganó el mundial de fútbol?"
Bot: "🤖 Lo siento, solo puedo ayudarte con temas relacionados a Cootradecun.
¿En qué tema sobre la cooperativa puedo ayudarte?"
```

---

## 🧪 Cómo Probar

### Opción 1: Script Automatizado

```bash
# Terminal 1: Iniciar servidor
python run.py

# Terminal 2: Ejecutar pruebas
python test_restricciones.py
```

**Salida esperada:**
```
🧪 TEST: Restricciones - Preguntas Fuera de Contexto
=====================================================

📝 Categoría: Recetas de cocina
👤 Usuario: ¿Cuál es la receta para hacer un flan?
🤖 Bot: Lo siento, soy un asistente especializado...
✅ CORRECTO: El bot rechazó la pregunta fuera de contexto

[... más pruebas ...]

📊 RESUMEN GENERAL
==================
   Test 1 - Restricciones: ✅ PASÓ
   Test 2 - Preguntas válidas: ✅ PASÓ
   Test 3 - Casos límite: ✅ PASÓ

🎉 ¡TODAS LAS PRUEBAS PASARON!
```

### Opción 2: Prueba Manual (Interfaz Web)

1. Iniciar servidor: `python run.py`
2. Abrir http://localhost:8000
3. Probar preguntas:
   - ✅ "¿Cuáles son los horarios?" → Debe responder
   - ❌ "¿Cómo hacer un flan?" → Debe rechazar
   - ❌ "¿Quién ganó el mundial?" → Debe rechazar

### Opción 3: API Directa

```bash
# Pregunta válida
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Cuáles son los horarios?", "session_id": "test"}'

# Pregunta inválida
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Cómo hacer un flan?", "session_id": "test"}'
```

---

## 📊 Métricas de Restricción

### Objetivo de Precisión

| Categoría | Objetivo | Descripción |
|-----------|----------|-------------|
| Preguntas fuera de contexto | 100% rechazadas | No responder recetas, deportes, etc. |
| Preguntas válidas | 100% respondidas | Responder todo sobre Cootradecun |
| Casos límite | >90% correctos | Saludos y preguntas ambiguas |

### Indicadores de Éxito

✅ **El bot NO responde recetas de cocina**  
✅ **El bot NO responde sobre deportes**  
✅ **El bot NO responde consejos generales**  
✅ **El bot SÍ responde todo sobre Cootradecun**  
✅ **Los rechazos son corteses y ofrecen alternativas**  

---

## 📈 Beneficios

### Para Usuarios

1. **Expectativas claras**: Los usuarios saben qué esperar del bot
2. **Experiencia enfocada**: No hay respuestas confusas fuera de tema
3. **Respuestas precisas**: El bot se especializa en su dominio

### Para la Organización

1. **Imagen profesional**: El bot mantiene su rol específico
2. **Optimización de recursos**: No se gastan tokens en respuestas irrelevantes
3. **Cumplimiento**: Evita responder temas fuera de competencia
4. **Mejor experiencia**: Usuarios reciben ayuda relevante

### Técnicos

1. **Menor probabilidad de errores**: El bot no intenta responder lo que no sabe
2. **Costos optimizados**: Menos tokens gastados en respuestas largas fuera de tema
3. **Mejor control**: Comportamiento predecible y consistente

---

## 🔧 Configuración Técnica

### Ubicación del System Prompt

**Archivo:** `app/agents/graph.py`  
**Líneas:** 71-113  
**Variable:** `SYSTEM_PROMPT`

### Estructura del Prompt

```
1. Introducción (rol del asistente)
2. ALCANCE DE TU FUNCIÓN (temas permitidos)
3. RESTRICCIONES IMPORTANTES (temas prohibidos)
4. COMPORTAMIENTO (cómo actuar)
5. RESPUESTAS A PREGUNTAS FUERA DE TEMA (plantilla de rechazo)
6. INFORMACIÓN REQUERIDA (datos necesarios para consultas)
7. Cierre (refuerzo del contexto)
```

### Parámetros del Modelo

```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,  # Baja temperatura para mayor consistencia
    api_key=api_key
)
```

---

## ⚠️ Limitaciones Conocidas

### Casos Difíciles

1. **Preguntas ambiguas**: 
   - "¿Cómo puedo ahorrar?" → Podría interpretarse como ahorro general o ahorro en Cootradecun
   - Solución: El modelo generalmente interpreta en contexto de Cootradecun

2. **Preguntas relacionadas indirectamente**:
   - "¿Cómo llego a sus oficinas?" → Es válida pero requiere información de ubicación
   - Solución: El bot responde con la dirección de Cootradecun

3. **Sensibilidad del modelo**:
   - A veces el modelo puede ser demasiado restrictivo o permisivo
   - Solución: Ajustar el prompt o la temperatura según sea necesario

---

## 🔄 Mantenimiento y Ajustes

### Cuando Ajustar las Restricciones

1. **Usuarios preguntan temas legítimos que se rechazan**: Ampliar alcance
2. **Bot responde preguntas que no debería**: Reforzar restricciones
3. **Mensajes de rechazo muy frecuentes**: Revisar FAQs y agregar contenido

### Cómo Hacer Ajustes

```python
# app/agents/graph.py

# 1. Agregar tema permitido
ALCANCE DE TU FUNCIÓN:
- [Nuevo tema aquí]

# 2. Agregar restricción
RESTRICCIONES IMPORTANTES:
- NO respondas sobre [nuevo tema prohibido]

# 3. Modificar mensaje de rechazo
RESPUESTAS A PREGUNTAS FUERA DE TEMA:
"[Nuevo mensaje personalizado]"
```

### Después de Cambios

1. Reiniciar el servidor: `python run.py`
2. Ejecutar pruebas: `python test_restricciones.py`
3. Probar casos específicos manualmente
4. Monitorear logs para verificar comportamiento

---

## 📚 Referencias

- **Archivo modificado**: `app/agents/graph.py` (líneas 71-113)
- **Documentación**: `docs/RESTRICCIONES_CHATBOT.md`
- **Script de pruebas**: `test_restricciones.py`
- **Actualización en README**: Sección "Restricciones de Contexto"

---

## ✨ Resumen

Se implementó un **sistema robusto de restricciones** que:

✅ **Limita el alcance** del bot a temas de Cootradecun  
✅ **Rechaza cortésmente** preguntas fuera de contexto  
✅ **Mantiene profesionalismo** en todas las interacciones  
✅ **Incluye pruebas automatizadas** para verificar funcionamiento  
✅ **Proporciona documentación completa** para usuarios y administradores  

**Resultado esperado:**
- El bot ya NO responderá recetas de cocina, preguntas sobre deportes, consejos generales, etc.
- El bot SOLO responderá sobre servicios, créditos, aportes, y otros temas de Cootradecun
- Los usuarios recibirán mensajes claros cuando hagan preguntas fuera de alcance

**Estado**: ✅ Implementado y probado  
**Versión**: 1.2.0  
**Última actualización**: Octubre 2025

---

*Implementado siguiendo mejores prácticas de diseño de prompts y restricciones de LLM*

