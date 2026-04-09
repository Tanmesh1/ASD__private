import logging
from typing import Any

import anyio

from app.core.config import get_settings
from app.database.session import MongoSession
from app.repositories.whatsapp_repository import WhatsAppRepository
from app.schemas.whatsapp import WhatsAppInboundMessage, WhatsAppParsedPayload, WhatsAppStatusUpdate
from app.services.commerce_ai_service import CommerceAIService
from app.services.whatsapp_cloud_api import WhatsAppCloudAPI, WhatsAppCloudAPIError
from app.services.whatsapp_payload import parse_whatsapp_payload

logger = logging.getLogger(__name__)


class WhatsAppWebhookService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = WhatsAppCloudAPI()
        self.ai = CommerceAIService()

    async def process_payload(self, payload: dict[str, Any]) -> None:
        parsed = parse_whatsapp_payload(payload)
        if not parsed.messages and not parsed.statuses:
            logger.info("WhatsApp webhook contained no supported messages or status updates.")
            return

        inserted_messages = await anyio.to_thread.run_sync(self._persist_payload, parsed)

        for message in inserted_messages:
            await self._send_auto_reply(message)

    def _persist_payload(self, parsed: WhatsAppParsedPayload) -> list[WhatsAppInboundMessage]:
        db = MongoSession()
        try:
            repository = WhatsAppRepository(db)
            inserted_messages = [
                message
                for message in parsed.messages
                if repository.create_incoming_message_if_absent(message)
            ]
            for status_update in parsed.statuses:
                repository.upsert_status(status_update)
            return inserted_messages
        finally:
            db.close()

    async def _send_auto_reply(self, message: WhatsAppInboundMessage) -> None:
        if message.message_type not in {"text", "image"}:
            logger.info("Skipping auto reply for unsupported WhatsApp message type=%s", message.message_type)
            return

        try:
            result = await self._build_ai_reply(message)
            await self.client.send_whatsapp_message(to=message.sender_phone, message=result.text)
            for image_url in result.image_urls:
                await self.client.send_whatsapp_image(to=message.sender_phone, image_url=image_url)
            logger.info("Sent WhatsApp auto reply for message_id=%s", message.message_id)
        except WhatsAppCloudAPIError:
            logger.exception("Failed to send WhatsApp auto reply for message_id=%s", message.message_id)
        except Exception:
            logger.exception("AI reply failed for message_id=%s; sending static fallback.", message.message_id)
            try:
                await self.client.send_whatsapp_message(
                    to=message.sender_phone,
                    message=self.settings.whatsapp_auto_reply_text,
                )
            except WhatsAppCloudAPIError:
                logger.exception("Failed to send fallback WhatsApp reply for message_id=%s", message.message_id)

    async def _build_ai_reply(self, message: WhatsAppInboundMessage):
        db = MongoSession()
        try:
            return await self.ai.handle_incoming_message(message=message, db=db)
        finally:
            db.close()
