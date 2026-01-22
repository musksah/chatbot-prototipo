# Análisis de Costos Combinados: Modelo de Negocio (Tokens + WhatsApp)

Este documento expande la propuesta económica original para incluir un modelo de costos más realista que integra el consumo de **Tokens de Inteligencia Artificial (IA)** junto con las tarifas de **WhatsApp Business API**.

El objetivo es proyectar el Costo Total de Propiedad (TCO) mensual bajo diferentes escenarios de uso.

## 1. Variables del Modelo

### 1.1. Costos Unitarios (Inputs)

| Concepto | Costo Unitario | Notas |
|----------|---------------:|-------|
| **Costo por 1M Tokens** | **$25.00 USD** | Incluye input (prompts) y output (respuestas). |
| **WhatsApp Service** | **$0.00 USD** | Primeras 1,000 conversaciones/mes iniciadas por usuario son GRATIS. |
| **WhatsApp Service (Exceso)** | **$0.00** / Var | Depende del país, generalmente bajo o gratuito en ventanas 24h. |
| **WhatsApp Auth (OTP)** | **$0.0077 USD** | Mensajes de autenticación (fijos). |
| **WhatsApp Utility** | **$0.0009 USD** | Notificaciones transaccionales. |

### 1.2. Supuestos de Consumo (Estimaciones)

Para calcular el componente de IA, estimamos el volumen de tokens por tipo de conversación. 
*Nota: 1 token $\approx$ 4 caracteres o 0.75 palabras.*

| Tipo de Conversación | Promedio Mensajes/Conv. | Tokens Estimados/Conv. | Costo IA Estimado/Conv. |
|----------------------|------------------------:|-----------------------:|------------------------:|
| **Soporte (Service)** | 10 mensajes (5 in/5 out)| ~3,000 tokens | **$0.075 USD** |
| **Auth (OTP)** | 2 mensajes (1 in/1 out) | ~200 tokens | **$0.005 USD** |
| **Utilidad** | 1 mensaje (Unidireccional)| ~0 tokens | **$0.000 USD** |

> *El escenario de Soporte es intensivo en tokens porque incluye el contexto recuperado (RAG) en cada turno de conversación.*

---

## 2. Escenarios de Simulación Mensual

Proyectamos costos para un volumen total de **3,000 conversaciones/mes** (mismo volumen del ejemplo original), pero analizando el impacto de los tokens.

### Escenario A: Uso Mixto (Base)
*Distribución equilibrada entre soporte y transacciones.*

- **2,000 Conversaciones de Servicio** (Soporte IA)
- **500 Conversaciones de Autenticación** (OTP)
- **500 Conversaciones de Utilidad** (Notificaciones)

#### Cálculo Detallado

| Concepto | Cantidad | Costo Unitario WA | Costo Total WA | Costo Tokens IA (Est.) | Costo Total |
|:---|:---:|:---:|---:|---:|---:|
| **1. Servicio (IA)** | 2,000 | 1,000 Gratis / Remanente bajo | ~$0.00 | 2,000 x $0.075 = **$150.00** | **$150.00** |
| **2. Auth (OTP)** | 500 | $0.0077 | $3.85 | 500 x $0.005 = **$2.50** | **$6.35** |
| **3. Utilidad** | 500 | $0.0009 | $0.45 | $0.00 | **$0.45** |
| **TOTAL MES** | **3,000** | | **$4.30** | **$152.50** | **$156.80 USD** |

> **Observación:** El costo de IA ($152.50) es significativamente mayor que el costo de WhatsApp ($4.30). El modelo original ignoraba el 97% del costo real operativo.

---

### Escenario B: Alta Demanda de Soporte (Stress Test)
*Usuarios haciendo muchas preguntas complejas (RAG intensivo).*

- **2,800 Conversaciones de Servicio** (Soporte IA)
- **100 Conversaciones de Autenticación**
- **100 Conversaciones de Utilidad**

#### Cálculo Detallado

| Concepto | Cantidad | Costo WA | Costo IA (Tokens) | Costo Total |
|:---|:---:|---:|---:|---:|
| **1. Servicio (IA)** | 2,800 | ~$10.00 (Est. fuera de capa gratis) | 2,800 x $0.075 = **$210.00** | **$220.00** |
| **2. Auth** | 100 | $0.77 | $0.50 | **$1.27** |
| **3. Utilidad** | 100 | $0.09 | $0.00 | **$0.09** |
| **TOTAL MES** | **3,000** | **~$10.86** | **$210.50** | **~$221.36 USD** |

---

### Escenario C: Optimizado (Caché + Templates)
*Reducción de consumo de tokens mediante caché de respuestas frecuentes y uso de menús (botones) en lugar de texto libre.*

- **Supuesto:** Se reduce el consumo de tokens de Soporte a 1,500 tokens/conv (50% ahorro).
- **Volumen:** Igual al Escenario A.

| Concepto | Cantidad | Costo Unitario IA | Costo Total IA | Ahorro vs Esc. A |
|:---|:---:|---:|---:|---:|
| **1. Servicio (IA)** | 2,000 | $0.0375 | **$75.00** | $75.00 |
| **2. Auth + Util** | 1,000 | $0.0025 | **$2.50** | $0.00 |
| **TOTAL MES** | **3,000** | | **$77.50** | **Costos WA: $4.30** |
| **GRAN TOTAL** | | | **$81.80 USD** | |

---

## 3. Conclusiones y Recomendaciones

1.  **El Costo Real es la IA:** En todos los escenarios, el costo de los tokens representa entre el **90% y el 97%** del costo variable mensual.
2.  **Impacto del Contexto (RAG):** Cada vez que el bot "lee" documentos para responder, consume muchos tokens.
    *   *Recomendación:* Implementar "Context Caching" para documentos estáticos (normativas) si la plataforma lo permite, o optimizar los "chunks" de texto.
3.  **Presupuesto Sugerido:**
    *   Para un volumen de 3,000 conversaciones/mes, se recomienda presupuestar **~$160 - $200 USD mensuales** para cubrir holgadamente ambos conceptos, en lugar de los $17 USD que sugería el cálculo solo de WhatsApp.
4.  **Monitoreo:** Es vital implementar el **Módulo de Uso de Tokens** descrito en la propuesta técnica para detener o alertar si el consumo diario excede cierto umbral (ej. $10 USD/día).
