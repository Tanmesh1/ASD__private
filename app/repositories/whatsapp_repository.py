from datetime import datetime, timezone

from app.schemas.whatsapp import WhatsAppInboundMessage, WhatsAppStatusUpdate


class WhatsAppRepository:
    def __init__(self, db) -> None:
        self.db = db

    def create_incoming_message_if_absent(self, message: WhatsAppInboundMessage) -> bool:
        now = datetime.now(timezone.utc)
        doc = message.model_dump(mode="python")
        doc["received_at"] = now
        doc["created_at"] = now
        doc["updated_at"] = now
        doc["direction"] = "incoming"
        return self.db.create_whatsapp_message_if_absent(doc)

    def upsert_status(self, status_update: WhatsAppStatusUpdate) -> None:
        now = datetime.now(timezone.utc)
        doc = status_update.model_dump(mode="python")
        doc["updated_at"] = now
        self.db.upsert_whatsapp_status(doc)
