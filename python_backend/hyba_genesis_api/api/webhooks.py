"""
HYBA Webhooks API - Event delivery and subscription management
Enterprise-grade webhook system with retry logic and signature verification
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Body
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime, timedelta
import json
import hashlib
import hmac
import httpx
import asyncio
from enum import Enum

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


class WebhookEventType(str, Enum):
    """Supported webhook event types"""
    SERVICE_PROVISIONED = "service.provisioned"
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"
    SERVICE_DELETED = "service.deleted"
    WORKLOAD_STARTED = "workload.started"
    WORKLOAD_COMPLETED = "workload.completed"
    WORKLOAD_FAILED = "workload.failed"
    QUOTA_EXCEEDED = "quota.exceeded"
    SERVICE_ERROR = "service.error"


class WebhookSubscription(BaseModel):
    """Webhook subscription configuration"""
    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    events: List[WebhookEventType] = Field(
        ...,
        description="List of events to subscribe to",
        min_items=1
    )
    secret: str = Field(
        ...,
        description="Secret for signature verification (HMAC-SHA256)",
        min_length=32
    )
    active: bool = Field(default=True, description="Whether webhook is active")
    retry_max_attempts: int = Field(
        default=5,
        description="Maximum retry attempts",
        ge=1,
        le=10
    )
    retry_backoff_seconds: int = Field(
        default=60,
        description="Backoff duration in seconds between retries",
        ge=5,
        le=600
    )
    timeout_seconds: int = Field(
        default=30,
        description="Timeout for webhook delivery",
        ge=5,
        le=300
    )


class WebhookEvent(BaseModel):
    """Webhook event payload"""
    id: str = Field(..., description="Unique event ID")
    event: WebhookEventType
    timestamp: datetime
    data: Dict[str, Any] = Field(..., description="Event-specific data")


class WebhookDeliveryLog(BaseModel):
    """Webhook delivery attempt log"""
    webhook_id: str
    event_id: str
    event_type: WebhookEventType
    attempt: int
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime
    next_retry: Optional[datetime] = None


class WebhookDeliveryService:
    """Service for delivering webhooks with retry logic"""
    
    def __init__(self):
        self.delivery_logs: Dict[str, List[WebhookDeliveryLog]] = {}
        self.subscriptions: Dict[str, WebhookSubscription] = {}
    
    def generate_signature(
        self,
        secret: str,
        payload: str,
        timestamp: str
    ) -> str:
        """
        Generate HMAC-SHA256 signature for webhook verification
        
        Format: v1=<signature>
        Computed over: {timestamp}.{payload}
        """
        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"v1={signature}"
    
    def verify_signature(
        self,
        secret: str,
        payload: str,
        signature: str,
        timestamp: str,
        tolerance_seconds: int = 300
    ) -> bool:
        """
        Verify webhook signature
        
        Args:
            secret: Webhook secret
            payload: Request body
            signature: X-HYBA-Signature header value
            timestamp: X-HYBA-Timestamp header value
            tolerance_seconds: Allow timestamp within this range
            
        Returns:
            True if signature is valid
        """
        try:
            # Check timestamp tolerance
            event_timestamp = int(timestamp)
            now = int(datetime.utcnow().timestamp())
            
            if abs(now - event_timestamp) > tolerance_seconds:
                return False
            
            # Verify signature
            expected_signature = self.generate_signature(secret, payload, timestamp)
            return hmac.compare_digest(signature, expected_signature)
        except:
            return False
    
    async def deliver_webhook(
        self,
        subscription: WebhookSubscription,
        event: WebhookEvent,
        attempt: int = 1
    ) -> WebhookDeliveryLog:
        """
        Deliver webhook with exponential backoff retry
        
        Returns:
            WebhookDeliveryLog with delivery status
        """
        payload = event.json()
        timestamp = str(int(datetime.utcnow().timestamp()))
        signature = self.generate_signature(
            subscription.secret,
            payload,
            timestamp
        )
        
        headers = {
            "X-HYBA-Event": event.event.value,
            "X-HYBA-Event-ID": event.id,
            "X-HYBA-Timestamp": timestamp,
            "X-HYBA-Signature": signature,
            "Content-Type": "application/json",
            "User-Agent": "HYBA-Webhook/1.0"
        }
        
        log = WebhookDeliveryLog(
            webhook_id=str(subscription.url),
            event_id=event.id,
            event_type=event.event,
            attempt=attempt,
            timestamp=datetime.utcnow()
        )
        
        try:
            async with httpx.AsyncClient(
                timeout=subscription.timeout_seconds
            ) as client:
                response = await client.post(
                    str(subscription.url),
                    headers=headers,
                    content=payload
                )
                
                log.status_code = response.status_code
                log.response_body = response.text[:500]  # Truncate long responses
                
                # Success if 2xx status code
                if 200 <= response.status_code < 300:
                    return log
                
                # Retry on server errors or rate limits
                if response.status_code >= 500 or response.status_code == 429:
                    if attempt < subscription.retry_max_attempts:
                        backoff = subscription.retry_backoff_seconds * (2 ** (attempt - 1))
                        log.next_retry = datetime.utcnow() + timedelta(seconds=backoff)
                    return log
                
                # Don't retry client errors (4xx, except 429)
                log.error = f"HTTP {response.status_code}: {response.text[:100]}"
                return log
        
        except httpx.TimeoutException as e:
            log.error = f"Timeout after {subscription.timeout_seconds}s"
            if attempt < subscription.retry_max_attempts:
                backoff = subscription.retry_backoff_seconds * (2 ** (attempt - 1))
                log.next_retry = datetime.utcnow() + timedelta(seconds=backoff)
            return log
        
        except Exception as e:
            log.error = str(e)
            if attempt < subscription.retry_max_attempts:
                backoff = subscription.retry_backoff_seconds * (2 ** (attempt - 1))
                log.next_retry = datetime.utcnow() + timedelta(seconds=backoff)
            return log
    
    async def broadcast_event(
        self,
        event: WebhookEvent,
        subscriptions: List[WebhookSubscription]
    ):
        """
        Broadcast event to all relevant subscriptions
        """
        tasks = []
        
        for sub in subscriptions:
            # Check if subscription is active and interested in this event
            if not sub.active or event.event not in sub.events:
                continue
            
            # Fire-and-forget delivery (don't wait)
            task = asyncio.create_task(
                self.deliver_webhook(sub, event)
            )
            tasks.append(task)
        
        # Don't wait for delivery to complete
        if tasks:
            asyncio.gather(*tasks, return_exceptions=True)


# Global webhook service
webhook_service = WebhookDeliveryService()


@router.post("/subscriptions", response_model=Dict[str, Any])
async def create_webhook_subscription(
    subscription: WebhookSubscription,
    customer_id: str = Header(..., description="Customer ID from API key")
) -> Dict[str, Any]:
    """
    Create a new webhook subscription
    
    Example:
    ```json
    {
      "url": "https://acme.com/webhooks/hyba",
      "events": ["service.provisioned", "workload.completed"],
      "secret": "whsec_abc123xyz789abc123xyz789abc123xyz789"
    }
    ```
    """
    webhook_id = f"whk_{customer_id}_{len(webhook_service.subscriptions)}"
    webhook_service.subscriptions[webhook_id] = subscription
    
    return {
        "webhook_id": webhook_id,
        "url": str(subscription.url),
        "events": [e.value for e in subscription.events],
        "active": subscription.active,
        "created_at": datetime.utcnow().isoformat(),
        "test_url": f"https://api.hyba.ai/v1/webhooks/{webhook_id}/test"
    }


@router.get("/subscriptions", response_model=List[Dict[str, Any]])
async def list_webhook_subscriptions(
    customer_id: str = Header(..., description="Customer ID from API key")
) -> List[Dict[str, Any]]:
    """
    List all webhook subscriptions for customer
    """
    return [
        {
            "webhook_id": wid,
            "url": str(sub.url),
            "events": [e.value for e in sub.events],
            "active": sub.active,
            "retry_max_attempts": sub.retry_max_attempts,
        }
        for wid, sub in webhook_service.subscriptions.items()
    ]


@router.get("/subscriptions/{webhook_id}", response_model=Dict[str, Any])
async def get_webhook_subscription(webhook_id: str):
    """
    Get webhook subscription details
    """
    if webhook_id not in webhook_service.subscriptions:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    sub = webhook_service.subscriptions[webhook_id]
    return {
        "webhook_id": webhook_id,
        "url": str(sub.url),
        "events": [e.value for e in sub.events],
        "active": sub.active,
        "retry_max_attempts": sub.retry_max_attempts,
        "timeout_seconds": sub.timeout_seconds,
    }


@router.post("/subscriptions/{webhook_id}/test", response_model=Dict[str, Any])
async def test_webhook(webhook_id: str):
    """
    Test webhook delivery with sample event
    """
    if webhook_id not in webhook_service.subscriptions:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    sub = webhook_service.subscriptions[webhook_id]
    
    # Create test event
    test_event = WebhookEvent(
        id="evt_test_123",
        event=WebhookEventType.SERVICE_PROVISIONED,
        timestamp=datetime.utcnow(),
        data={
            "service_id": "hyba-ciaas-test-001",
            "name": "Test Service",
            "test": True
        }
    )
    
    # Attempt delivery
    log = await webhook_service.deliver_webhook(sub, test_event)
    
    return {
        "test_id": "evt_test_123",
        "status_code": log.status_code,
        "error": log.error,
        "response_body": log.response_body,
        "success": log.status_code is not None and 200 <= log.status_code < 300
    }


@router.delete("/subscriptions/{webhook_id}", response_model=Dict[str, Any])
async def delete_webhook_subscription(webhook_id: str):
    """
    Delete a webhook subscription
    """
    if webhook_id not in webhook_service.subscriptions:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    del webhook_service.subscriptions[webhook_id]
    
    return {"deleted": True, "webhook_id": webhook_id}


@router.get("/deliveries", response_model=List[Dict[str, Any]])
async def get_webhook_deliveries(
    webhook_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get webhook delivery logs
    """
    logs = []
    for wid, delivery_logs in webhook_service.delivery_logs.items():
        if webhook_id and wid != webhook_id:
            continue
        
        for log in delivery_logs[-limit:]:
            if event_type and log.event_type != event_type:
                continue
            
            logs.append({
                "webhook_id": log.webhook_id,
                "event_id": log.event_id,
                "event_type": log.event_type.value,
                "attempt": log.attempt,
                "status_code": log.status_code,
                "error": log.error,
                "timestamp": log.timestamp.isoformat(),
                "next_retry": log.next_retry.isoformat() if log.next_retry else None
            })
    
    return logs
