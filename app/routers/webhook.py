import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.schemas.whatsapp import WhatsAppWebhookAck
from app.services.whatsapp_service import WhatsAppWebhookService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])


@router.get("", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    settings = get_settings()
    if (
        settings.verify_token
        and hub_mode == "subscribe"
        and hub_verify_token == settings.verify_token
        and hub_challenge
    ):
        logger.info("WhatsApp webhook verification succeeded.")
        return hub_challenge

    logger.warning("WhatsApp webhook verification failed.")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verify token.")


@router.post("", response_model=WhatsAppWebhookAck)
async def receive_webhook(request: Request, background_tasks: BackgroundTasks) -> dict[str, str]:
    try:
        payload: dict[str, Any] = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.") from exc

    background_tasks.add_task(WhatsAppWebhookService().process_payload, payload)
    return {"status": "accepted"}
