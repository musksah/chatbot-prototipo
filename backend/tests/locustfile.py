"""
Locust Webhook Stress Test — Chatbot COOTRADECUN
=================================================
Simulates Meta (WhatsApp) calling the webhook endpoint with real message payloads.

The webhook POST always returns 200 immediately. In production it enqueues
a Cloud Tasks job — the agent processing happens asynchronously.

Usage:
  # Web UI:
  locust -f tests/locustfile.py

  # Headless — 20 users, ramp 2/s, run 3 minutes:
  locust -f tests/locustfile.py --headless -u 20 -r 2 --run-time 3m \
         --csv=tests/results/webhook

  Open http://localhost:8089 to configure users & ramp-up.

⚠️  The "real" task triggers Cloud Tasks → real LLM processing → cost.
    Use --exclude-tags real to avoid it:
    locust -f tests/locustfile.py --exclude-tags real
"""

import uuid
import time
import random
import logging
from locust import HttpUser, task, between, tag, events

logger = logging.getLogger(__name__)

# ── Target ────────────────────────────────────────────────────────────
PRODUCTION_HOST = "https://chatbot-backend-cabzpqrleq-uc.a.run.app"

# ── Cootradecun tenant config ─────────────────────────────────────────
COOTRADECUN_PHONE_NUMBER_ID = "1040362502493753"
COOTRADECUN_VERIFY_TOKEN    = "explouse-webhook-verify-2024"
UNKNOWN_PHONE_NUMBER_ID     = "0000000000000000"  # no tenant → ignored, no LLM cost

# ── Simulated WhatsApp messages ───────────────────────────────────────
MESSAGES = [
    "Hola, buenos días",
    "Buenas tardes, necesito ayuda",
    "¿Qué proyectos de vivienda tienen disponibles?",
    "¿Cuánto cuesta un apartamento en El Pedregal?",
    "¿Qué requisitos necesito para crédito de vivienda?",
    "¿Cuáles son los requisitos para asociarme?",
    "¿Qué auxilios ofrecen?",
    "¿Cómo accedo al auxilio de estudios?",
    "¿Cómo puedo ver mi desprendible de pago?",
    "¿Qué tipos de crédito ofrecen?",
    "¿Qué medios de pago aceptan?",
    "¿Puedo pagar por PSE?",
    "Necesito mi certificado tributario",
    "¿Cómo obtengo un certificado de aportes?",
    "¿Qué convenios tienen disponibles?",
]


# ── Payload builder ───────────────────────────────────────────────────

def _whatsapp_payload(phone_number_id: str, sender: str, text: str, sender_name: str = "Locust Tester") -> dict:
    """Constructs a WhatsApp Cloud API webhook payload (same structure Meta sends)."""
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15550000000",
                        "phone_number_id": phone_number_id,
                    },
                    "contacts": [{
                        "profile": {"name": sender_name},
                        "wa_id": sender,
                    }],
                    "messages": [{
                        "from": sender,
                        "id": f"wamid.{uuid.uuid4().hex}",
                        "timestamp": str(int(time.time())),
                        "type": "text",
                        "text": {"body": text},
                    }],
                },
                "field": "messages",
            }],
        }],
    }


# ═══════════════════════════════════════════════════════════════════════
# Webhook User
# ═══════════════════════════════════════════════════════════════════════

class WhatsAppWebhookUser(HttpUser):
    """
    Simulates Meta calling the WhatsApp webhook.

    Task weights (out of 12 total):
      6 — POST message to unknown tenant  (no LLM cost, tests throughput)
      3 — POST message to real Cootradecun (triggers Cloud Tasks, has LLM cost)
      2 — GET webhook verification (correct token)
      1 — GET webhook verification (wrong token → expects 403)
    """
    host = PRODUCTION_HOST
    wait_time = between(1, 3)

    def on_start(self):
        # Each simulated user gets a unique phone number
        self.sender = f"57300{random.randint(1000000, 9999999)}"

    # ── POST: message to unknown tenant (no LLM cost) ─────────────────

    @tag("post", "no-cost")
    @task(6)
    def post_message_unknown_tenant(self):
        """
        POST with unknown phone_number_id.
        Webhook parses the payload, finds no matching tenant, returns 200 and ignores it.
        Useful for measuring raw webhook throughput without triggering agent processing.
        """
        payload = _whatsapp_payload(
            phone_number_id=UNKNOWN_PHONE_NUMBER_ID,
            sender=self.sender,
            text=random.choice(MESSAGES),
        )
        with self.client.post(
            "/webhook/whatsapp",
            json=payload,
            catch_response=True,
            name="POST /webhook/whatsapp [unknown tenant]",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Expected 200, got {resp.status_code}: {resp.text[:100]}")

    # ── POST: real Cootradecun message (triggers Cloud Tasks) ─────────

    @tag("post", "real")
    @task(3)
    def post_message_real(self):
        """
        POST with real Cootradecun phone_number_id.
        ⚠️  Triggers Cloud Tasks → real agent → LLM cost.
        Exclude with: --exclude-tags real
        """
        payload = _whatsapp_payload(
            phone_number_id=COOTRADECUN_PHONE_NUMBER_ID,
            sender=self.sender,
            text=random.choice(MESSAGES),
            sender_name="Locust Stress Test",
        )
        with self.client.post(
            "/webhook/whatsapp",
            json=payload,
            catch_response=True,
            name="POST /webhook/whatsapp [Cootradecun → Cloud Tasks]",
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Expected 200, got {resp.status_code}: {resp.text[:100]}")

    # ── GET: verification with correct token ──────────────────────────

    @tag("verify")
    @task(2)
    def get_verify_correct_token(self):
        """Meta's webhook verification — must echo the challenge."""
        challenge = uuid.uuid4().hex
        with self.client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": COOTRADECUN_VERIFY_TOKEN,
                "hub.challenge": challenge,
            },
            catch_response=True,
            name="GET /webhook/whatsapp [verify ✅]",
        ) as resp:
            if resp.status_code == 200 and resp.text.strip() == challenge:
                resp.success()
            else:
                resp.failure(f"Expected challenge '{challenge}', got {resp.status_code}: '{resp.text}'")

    # ── GET: verification with wrong token → 403 ──────────────────────

    @tag("verify")
    @task(1)
    def get_verify_wrong_token(self):
        """Verification with bad token — must return 403."""
        with self.client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "token-incorrecto",
                "hub.challenge": "irrelevant",
            },
            catch_response=True,
            name="GET /webhook/whatsapp [verify ❌ bad token]",
        ) as resp:
            if resp.status_code == 403:
                resp.success()
            else:
                resp.failure(f"Expected 403, got {resp.status_code}")


# ═══════════════════════════════════════════════════════════════════════
# Event hooks — summary stats
# ═══════════════════════════════════════════════════════════════════════

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("═" * 60)
    print("🔥  COOTRADECUN Webhook Stress Test — STARTED")
    print(f"    Target: {environment.host}")
    print("═" * 60)

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("═" * 60)
    print("🏁  Stress Test — FINISHED")
    stats = environment.stats
    print(f"    Total requests:  {stats.total.num_requests}")
    print(f"    Failures:        {stats.total.num_failures}")
    print(f"    Avg response:    {stats.total.avg_response_time:.0f}ms")
    if stats.total.num_requests > 0:
        fail_pct = (stats.total.num_failures / stats.total.num_requests) * 100
        print(f"    Failure rate:    {fail_pct:.1f}%")
    print("═" * 60)
