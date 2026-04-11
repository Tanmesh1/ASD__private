import logging
import re

from app.core.config import get_settings
from app.database.session import MongoSession
from app.schemas.ai import AICommerceResult, IntentExtraction
from app.schemas.whatsapp import WhatsAppInboundMessage
from app.services.llm_service import LLMService
from app.services.preprocessing_service import PreprocessingService
from app.services.response_service import ResponseService
from app.services.search_service import ProductSearchService

logger = logging.getLogger(__name__)
GREETING_ONLY_RE = re.compile(r"^(hi+|hello+|hey+|hii+|hlo+|namaste|hola)\s*$", re.IGNORECASE)
GREETING_PREFIX_RE = re.compile(r"^(hi+|hello+|hey+|hii+|hlo+|namaste)\b[\s,!.-]*", re.IGNORECASE)


class CommerceAIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.preprocessing = PreprocessingService()
        self.llm = LLMService()
        self.response = ResponseService()

    async def handle_incoming_message(
        self,
        message: WhatsAppInboundMessage,
        db: MongoSession,
    ) -> AICommerceResult:
        raw_text = message.text or ""
        preprocessed = self.preprocessing.preprocess_user_message(raw_text)

        if self._is_greeting_only(raw_text):
            intent = IntentExtraction.model_validate(
                {
                    "intent": "casual",
                    "products": [],
                    "filters": {"price_range": {"min": None, "max": None}, "color": "", "brand": "", "size": "", "gender": ""},
                    "confidence": 1,
                }
            )
            greeting_text = self._build_greeting(message, self.settings.ai_greeting_only_response)
            return AICommerceResult(
                text=greeting_text,
                products=[],
                image_urls=[],
                intent=intent,
                preprocessing=preprocessed,
            )

        intent = await self.llm.extract_user_intent(preprocessed)

        products = []
        if intent.intent != "casual" or intent.products or preprocessed.keywords:
            products = await ProductSearchService(db).search_products(
                store_id=self.settings.ai_default_store_id,
                intent=intent,
                keywords=preprocessed.keywords,
                limit=self.settings.ai_max_search_results,
            )

        text = await self.response.generate_sales_response(
            user_input=raw_text,
            intent=intent,
            products=products,
        )
        text = self._ensure_greeting(message, text)
        image_urls = [product.image_url for product in products if product.image_url][: self.settings.ai_max_images_per_reply]

        return AICommerceResult(
            text=text,
            products=products,
            image_urls=image_urls,
            intent=intent,
            preprocessing=preprocessed,
        )

    def _is_greeting_only(self, raw_text: str) -> bool:
        return bool(GREETING_ONLY_RE.match((raw_text or "").strip()))

    def _ensure_greeting(self, message: WhatsAppInboundMessage, text: str) -> str:
        normalized = (text or "").strip()
        if not normalized:
            return self._build_greeting(message, self.settings.ai_empty_reply_fallback)
        if GREETING_PREFIX_RE.match(normalized):
            return normalized
        return self._build_greeting(message, normalized)

    def _build_greeting(self, message: WhatsAppInboundMessage, body: str) -> str:
        first_name = (message.contact_name or "").strip().split(" ")[0]
        greeting_prefix = (self.settings.ai_reply_greeting_prefix or "Hi").strip().rstrip(",")
        salutation = f"{greeting_prefix} {first_name}," if first_name else f"{greeting_prefix},"
        return f"{salutation} {body.strip()}"


async def handleIncomingMessage(message: WhatsAppInboundMessage, db: MongoSession) -> dict:
    return (await CommerceAIService().handle_incoming_message(message=message, db=db)).model_dump(mode="json")
