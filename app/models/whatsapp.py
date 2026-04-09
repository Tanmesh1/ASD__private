from dataclasses import dataclass


@dataclass(frozen=True)
class WhatsAppCollections:
    messages: str = "whatsapp_messages"
    statuses: str = "whatsapp_message_statuses"
