import logging

from app.core.config import get_settings
from app.database.session import MongoSession
from app.schemas.ai import AICommerceResult
from app.schemas.whatsapp import WhatsAppInboundMessage
from app.services.llm_service import LLMService
from app.services.preprocessing_service import PreprocessingService
from app.services.response_service import ResponseService
from app.services.search_service import ProductSearchService

logger = logging.getLogger(__name__)


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
        image_urls = [product.image_url for product in products if product.image_url][: self.settings.ai_max_images_per_reply]

        return AICommerceResult(
            text=text,
            products=products,
            image_urls=image_urls,
            intent=intent,
            preprocessing=preprocessed,
        )


async def handleIncomingMessage(message: WhatsAppInboundMessage, db: MongoSession) -> dict:
    return (await CommerceAIService().handle_incoming_message(message=message, db=db)).model_dump(mode="json")
