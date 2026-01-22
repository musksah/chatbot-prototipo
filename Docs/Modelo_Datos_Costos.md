# Modelo de Datos para Control de Costos (Tokens + WhatsApp API)

Este documento describe el modelo de datos propuesto para realizar el seguimiento de los costos asociados al chatbot "Cootradecun Inteligente", según la estructura de costos definida en la propuesta económica.

## 1. Resumen de Variables de Costo

| Variable | Tipo de Costo | Unidad | Valor Base (USD) | Notas |
|----------|---------------|--------|------------------|-------|
| **Tokens LLM** | Variable | 1M Tokens | $25.00 | Se debe medir input (baja) y output (alta) token count. |
| **WhatsApp Service** | Servicio | Ventana 24h | $0.00 | Primeras 1000/mes gratis. |
| **WhatsApp Utility** | Utilidad | Ventana 24h | $0.0009 | Confirmaciones, alertas. |
| **WhatsApp Auth** | Autenticación| Ventana 24h | $0.0077 | OTPs. |
| **WhatsApp Marketing** | Marketing | Ventana 24h | $0.0144 | Promociones. |

## 2. Diagrama Entidad-Relación (Propuesto)

El modelo se basa en un esquema relacional (PostgreSQL en Google Cloud SQL) que permite cruzar la actividad transaccional con las tarifas vigentes.

### Tablas Principales

#### 2.1. `cost_rates` (Tarifas)
Almacena los costos unitarios para permitir cambios de precios en el tiempo (ej. ajuste anual de Meta).

```sql
CREATE TABLE cost_rates (
    id SERIAL PRIMARY KEY,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP, -- NULL indica tarifa actual
    rate_type VARCHAR(50) NOT NULL, -- 'TOKEN_1M', 'WA_SERVICE', 'WA_UTILITY', 'WA_AUTH', 'WA_MARKETING'
    cost_usd DECIMAL(10, 6) NOT NULL, -- Costo en dólares con alta precisión
    description TEXT
);
```

#### 2.2. `exchange_rates` (Tasa de Cambio)
Almacena la TRM diaria para convertir los costos de USD a COP para facturación local.

```sql
CREATE TABLE exchange_rates (
    rate_date DATE PRIMARY KEY,
    source_currency VARCHAR(3) DEFAULT 'USD',
    target_currency VARCHAR(3) DEFAULT 'COP',
    rate DECIMAL(10, 2) NOT NULL -- Valor del dólar en pesos
);
```

#### 2.3. `conversations` (Sesiones de WhatsApp)
Registra cada ventana de conversación de 24 horas y su categoría de cobro.

```sql
CREATE TABLE conversations (
    conversation_id VARCHAR(100) PRIMARY KEY, -- ID único de la sesión de WhatsApp
    user_phone VARCHAR(20) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP, -- Cierre de la ventana de 24h
    category VARCHAR(20) NOT NULL, -- 'SERVICE', 'UTILITY', 'AUTHENTICATION', 'MARKETING'
    is_free_tier BOOLEAN DEFAULT FALSE, -- Flag para las primeras 1000 de servicio
    wa_cost_usd DECIMAL(10, 6) DEFAULT 0, -- Costo calculado basado en category y rates
    status VARCHAR(20) -- 'ACTIVE', 'CLOSED'
);
```

#### 2.4. `messages` (Detalle de Tokens)
Registra cada interacción individual para calcular el consumo de IA.

```sql
CREATE TABLE messages (
    message_id VARCHAR(100) PRIMARY KEY,
    conversation_id VARCHAR(100) REFERENCES conversations(conversation_id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sender VARCHAR(10) CHECK (sender IN ('USER', 'BOT')),
    content_type VARCHAR(20), -- 'TEXT', 'IMAGE', 'AUDIO'
    input_tokens INTEGER DEFAULT 0, -- Tokens de entrada (prompt)
    output_tokens INTEGER DEFAULT 0, -- Tokens de salida (completion)
    total_tokens INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    token_cost_usd DECIMAL(10, 6) DEFAULT 0 -- (total_tokens / 1,000,000) * Rate
);
```

## 3. Lógica de Cálculo

### Cálculo de Costo de Tokens
Para cada mensaje procesado por el LLM:
1. Se obtienen los `usage_metadata` de la respuesta del modelo (Gemini/Vertex AI).
2. Se consulta la tarifa vigente en `cost_rates` donde `rate_type = 'TOKEN_1M'`.
3. Fórmula:
   $$ Costo_{Mensaje} = \frac{(Input + Output)}{1,000,000} \times Precio_{1M} $$

### Cálculo de Costo WhatsApp
Al iniciar o categorizar una conversación (Conversation Start):
1. Se determina la categoría (iniciada por usuario vs. template de negocio).
2. Se consulta la tarifa vigente en `cost_rates` para esa categoría.
3. Se verifica si aplica la capa gratuita (para categoría Service, si el conteo mensual < 1000).
4. Se guarda el costo en `conversations.wa_cost_usd`.

## 4. Vista de Reporte Unificado

Para el Dashboard, se recomienda una vista que consolide ambos costos y los convierta a pesos.

```sql
CREATE VIEW daily_cost_summary AS
SELECT 
    DATE(c.start_time) as report_date,
    COUNT(DISTINCT c.conversation_id) as total_conversations,
    SUM(c.wa_cost_usd) as whatsapp_cost_usd,
    SUM(m.token_cost_usd) as ai_token_cost_usd,
    (SUM(c.wa_cost_usd) + SUM(m.token_cost_usd)) as total_cost_usd,
    -- Conversión a COP usando la TRM del día (join con exchange_rates)
    ((SUM(c.wa_cost_usd) + SUM(m.token_cost_usd)) * COALESCE(er.rate, 4000)) as total_cost_cop_est
FROM conversations c
LEFT JOIN messages m ON c.conversation_id = m.conversation_id
LEFT JOIN exchange_rates er ON DATE(c.start_time) = er.rate_date
GROUP BY DATE(c.start_time), er.rate;
```
