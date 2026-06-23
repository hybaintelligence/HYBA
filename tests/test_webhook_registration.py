from datetime import datetime

from hyba_genesis_api.api.webhooks import (
    WebhookEvent,
    WebhookEventType,
    webhook_service,
)


def test_webhook_registration_and_delivery_signature():
    secret = "x" * 32
    event = WebhookEvent(
        id="evt_1",
        event=WebhookEventType.WORKLOAD_COMPLETED,
        timestamp=datetime.utcnow(),
        data={"ok": True},
    )
    payload = event.json()
    ts = "1700000000"
    sig = webhook_service.generate_signature(secret, payload, ts)
    assert webhook_service.verify_signature(
        secret, payload, sig, ts, tolerance_seconds=10**10
    )
