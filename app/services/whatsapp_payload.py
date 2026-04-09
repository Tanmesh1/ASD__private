import logging
from typing import Any

from pydantic import ValidationError

from app.schemas.whatsapp import (
    WhatsAppImage,
    WhatsAppInboundMessage,
    WhatsAppParsedPayload,
    WhatsAppStatusUpdate,
)

logger = logging.getLogger(__name__)


def parse_whatsapp_payload(payload: dict[str, Any]) -> WhatsAppParsedPayload:
    messages: list[WhatsAppInboundMessage] = []
    statuses: list[WhatsAppStatusUpdate] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            metadata = value.get("metadata") or {}
            phone_number_id = metadata.get("phone_number_id")
            contacts_by_phone = _contacts_by_phone(value.get("contacts", []))

            for raw_message in value.get("messages", []):
                try:
                    messages.append(_parse_message(raw_message, phone_number_id, contacts_by_phone))
                except (TypeError, ValidationError) as exc:
                    logger.warning("Skipping invalid WhatsApp message payload: %s", exc)

            for raw_status in value.get("statuses", []):
                try:
                    statuses.append(_parse_status(raw_status, phone_number_id))
                except (TypeError, ValidationError) as exc:
                    logger.warning("Skipping invalid WhatsApp status payload: %s", exc)

    return WhatsAppParsedPayload(messages=messages, statuses=statuses)


def _contacts_by_phone(contacts: list[dict[str, Any]]) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for contact in contacts:
        phone = contact.get("wa_id")
        profile = contact.get("profile") or {}
        name = profile.get("name")
        if phone and name:
            mapped[str(phone)] = str(name)
    return mapped


def _parse_message(
    raw_message: dict[str, Any],
    phone_number_id: str | None,
    contacts_by_phone: dict[str, str],
) -> WhatsAppInboundMessage:
    sender_phone = raw_message.get("from")
    message_id = raw_message.get("id")
    message_type = raw_message.get("type")

    if not sender_phone or not message_id or not message_type:
        raise TypeError("message payload must include from, id, and type")

    image = None
    if message_type == "image":
        image_payload = raw_message.get("image") or {}
        image = WhatsAppImage(
            id=image_payload["id"],
            mime_type=image_payload.get("mime_type"),
            sha256=image_payload.get("sha256"),
            caption=image_payload.get("caption"),
        )

    text = None
    if message_type == "text":
        text = (raw_message.get("text") or {}).get("body")
    elif image and image.caption:
        text = image.caption

    return WhatsAppInboundMessage(
        message_id=str(message_id),
        sender_phone=str(sender_phone),
        phone_number_id=phone_number_id,
        message_type=str(message_type),
        text=text,
        image=image,
        whatsapp_timestamp=_parse_timestamp(raw_message.get("timestamp")),
        contact_name=contacts_by_phone.get(str(sender_phone)),
        raw_message=raw_message,
    )


def _parse_status(raw_status: dict[str, Any], phone_number_id: str | None) -> WhatsAppStatusUpdate:
    message_id = raw_status.get("id")
    status = raw_status.get("status")
    if not message_id or not status:
        raise TypeError("status payload must include id and status")

    return WhatsAppStatusUpdate(
        message_id=str(message_id),
        recipient_phone=raw_status.get("recipient_id"),
        phone_number_id=phone_number_id,
        status=str(status),
        whatsapp_timestamp=_parse_timestamp(raw_status.get("timestamp")),
        raw_status=raw_status,
    )


def _parse_timestamp(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
