from typing import Any

from pydantic import BaseModel, Field


class WhatsAppImage(BaseModel):
    id: str
    mime_type: str | None = None
    sha256: str | None = None
    caption: str | None = None


class WhatsAppInboundMessage(BaseModel):
    message_id: str
    sender_phone: str
    phone_number_id: str | None = None
    message_type: str
    text: str | None = None
    image: WhatsAppImage | None = None
    whatsapp_timestamp: int | None = None
    contact_name: str | None = None
    raw_message: dict[str, Any] = Field(default_factory=dict)


class WhatsAppStatusUpdate(BaseModel):
    message_id: str
    recipient_phone: str | None = None
    phone_number_id: str | None = None
    status: str
    whatsapp_timestamp: int | None = None
    raw_status: dict[str, Any] = Field(default_factory=dict)


class WhatsAppParsedPayload(BaseModel):
    messages: list[WhatsAppInboundMessage] = Field(default_factory=list)
    statuses: list[WhatsAppStatusUpdate] = Field(default_factory=list)


class WhatsAppWebhookAck(BaseModel):
    status: str
