"""
Cloud Tasks integration for async WhatsApp message processing.

Instead of processing messages synchronously in the webhook handler
(which must respond to Meta in <5 seconds), we enqueue a Cloud Task
that calls /internal/process-message asynchronously.

This gives us:
- Automatic retry logic (up to 5 attempts with exponential backoff)
- Decoupled processing (webhook returns immediately)
- Visibility in GCP console
- Dead-letter queue support
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

QUEUE_NAME = "whatsapp-messages"
LOCATION = "us-central1"
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "corvus-data-testing")
CLOUD_RUN_URL = os.getenv(
    "CLOUD_RUN_URL",
    "https://chatbot-backend-cabzpqrleq-uc.a.run.app",
)
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "")


def enqueue_chat(task_id: str, message: str, thread_id: str) -> bool:
    """
    Enqueue a chat request for async processing via Cloud Tasks.
    Called by the /chat endpoint in production.
    """
    try:
        from google.cloud import tasks_v2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(PROJECT_ID, LOCATION, QUEUE_NAME)

        payload = {
            "task_id": task_id,
            "message": message,
            "thread_id": thread_id,
        }

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{CLOUD_RUN_URL}/internal/process-chat",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Internal-Secret": INTERNAL_SECRET,
                },
                "body": json.dumps(payload).encode(),
            }
        }

        client.create_task(request={"parent": parent, "task": task})
        logger.info(f"📬 Chat task enqueued: task_id={task_id} thread_id={thread_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to enqueue chat Cloud Task: {e}")
        return False


def enqueue_message(parsed: dict, tenant_name: str) -> bool:
    """
    Enqueue a WhatsApp message for async processing via Cloud Tasks.

    Args:
        parsed:      Dict from parse_incoming_message()
        tenant_name: Name of the tenant (e.g. "Xplouse", "Cootradecun")

    Returns:
        True if enqueued successfully, False otherwise.
    """
    try:
        from google.cloud import tasks_v2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(PROJECT_ID, LOCATION, QUEUE_NAME)

        payload = {
            "sender": parsed["sender"],
            "text": parsed["text"],
            "message_id": parsed["message_id"],
            "name": parsed["name"],
            "phone_number_id": parsed["phone_number_id"],
            "tenant_name": tenant_name,
        }

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{CLOUD_RUN_URL}/internal/process-message",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Internal-Secret": INTERNAL_SECRET,
                },
                "body": json.dumps(payload).encode(),
            }
        }

        client.create_task(request={"parent": parent, "task": task})
        logger.info(
            f"📬 Task enqueued for tenant={tenant_name} "
            f"from=+{parsed['sender'][-4:].rjust(len(parsed['sender']), '*')}"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Failed to enqueue Cloud Task: {e}")
        return False