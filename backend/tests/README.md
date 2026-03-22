# Stress Tests — Chatbot COOTRADECUN

## Requisitos

```bash
pip install locust
```

## Ejecutar contra producción (Cloud Run)

```bash
cd backend
locust -f tests/locustfile.py
```

Abre **http://localhost:8089** y configura:

| Parámetro | Recomendado | Descripción |
|---|---|---|
| Number of users | 5-10 | Usuarios concurrentes simulados |
| Ramp up | 1-2 | Usuarios nuevos por segundo |

> La URL de producción (`https://chatbot-backend-cabzpqrleq-uc.a.run.app`) ya está configurada en el locustfile.

## Ejecutar contra local (Docker)

```bash
docker compose up -d backend
locust -f tests/locustfile.py --host=http://localhost:8000
```

## Headless (CI)

```bash
locust -f tests/locustfile.py \
       --headless -u 5 -r 1 --run-time 3m \
       --csv=tests/results/stress
```

## Perfiles de usuario

| Perfil | Peso | Comportamiento |
|---|---|---|
| **QuickBrowseUser** | 60% | Preguntas sueltas aleatorias, nuevo thread por request |
| **ConversationUser** | 40% | Conversaciones multi-turno, reutiliza thread |

## Async Polling (producción)

En producción `/chat` retorna `{status: "pending", task_id: "..."}`. El test automáticamente pollea `/chat/result/{task_id}` hasta obtener `completed` o `failed` (timeout: 120s).

## Notas

- ⚠️ **Gemini rate limits**: cada request genera múltiples llamadas a Gemini. Con 10+ usuarios podrías ver 429s.
- 📊 Resultados CSV en `tests/results/` con `--csv`.
