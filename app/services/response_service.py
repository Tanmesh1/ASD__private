from app.schemas.ai import IntentExtraction, RecommendedProduct
from app.services.llm_service import LLMService


class ResponseService:
    def __init__(self) -> None:
        self.llm = LLMService()

    async def generate_sales_response(
        self,
        user_input: str,
        intent: IntentExtraction,
        products: list[RecommendedProduct],
    ) -> str:
        return await self.llm.generate_sales_response(user_input=user_input, intent=intent, products=products)


async def generateSalesResponse(user_input: str, products: list[dict]) -> str:
    recommended = [RecommendedProduct.model_validate(product) for product in products]
    intent = IntentExtraction.model_validate(
        {
            "intent": "browse",
            "products": [],
            "filters": {"price_range": {"min": None, "max": None}, "color": "", "brand": "", "size": "", "gender": ""},
            "confidence": 0,
        }
    )
    return await ResponseService().generate_sales_response(user_input=user_input, intent=intent, products=recommended)
