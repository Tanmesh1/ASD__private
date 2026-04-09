import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import anyio

from app.core.config import get_settings
from app.schemas.ai import IntentExtraction, PreprocessedMessage, RecommendedProduct
from app.services.ai_prompts import (
    INTENT_EXTRACTION_SYSTEM_PROMPT,
    INTENT_EXTRACTION_USER_PROMPT,
    SALES_RESPONSE_SYSTEM_PROMPT,
    SALES_RESPONSE_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class LLMServiceError(RuntimeError):
    pass


INTENT_JSON_SCHEMA: dict[str, Any] = {
    "name": "commerce_intent",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "intent": {"type": "string", "enum": ["buy", "browse", "compare", "ask_price", "casual"]},
            "products": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "category": {"type": "string"},
                    },
                    "required": ["name", "category"],
                },
            },
            "filters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "price_range": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "min": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                            "max": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                        },
                        "required": ["min", "max"],
                    },
                    "color": {"type": "string"},
                    "brand": {"type": "string"},
                    "size": {"type": "string"},
                    "gender": {"type": "string"},
                },
                "required": ["price_range", "color", "brand", "size", "gender"],
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["intent", "products", "filters", "confidence"],
    },
}


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def extract_user_intent(self, preprocessed: PreprocessedMessage) -> IntentExtraction:
        if not self.settings.openai_api_key:
            logger.warning("OPENAI_API_KEY is missing; using local fallback intent extraction.")
            return self._fallback_intent(preprocessed)

        messages = [
            {"role": "system", "content": INTENT_EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": INTENT_EXTRACTION_USER_PROMPT.format(
                    cleaned_text=preprocessed.cleaned_text,
                    detected_language=preprocessed.detected_language,
                    keywords=", ".join(preprocessed.keywords),
                ),
            },
        ]
        payload = {
            "model": self.settings.openai_intent_model,
            "messages": messages,
            "response_format": {"type": "json_schema", "json_schema": INTENT_JSON_SCHEMA},
        }
        body = await self._chat_completion(payload)
        content = self._message_content(body)
        return IntentExtraction.model_validate_json(content)

    async def generate_sales_response(
        self,
        user_input: str,
        intent: IntentExtraction,
        products: list[RecommendedProduct],
    ) -> str:
        if not products:
            return self._fallback_no_products(intent)
        if not self.settings.openai_api_key:
            return self._fallback_sales_response(products)

        product_payload = json.dumps(
            [product.model_dump(mode="json") for product in products],
            ensure_ascii=True,
            indent=2,
        )
        payload = {
            "model": self.settings.openai_response_model,
            "messages": [
                {"role": "system", "content": SALES_RESPONSE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": SALES_RESPONSE_USER_PROMPT.format(
                        user_input=user_input,
                        intent=intent.model_dump(mode="json"),
                        products=product_payload,
                    ),
                },
            ],
        }
        body = await self._chat_completion(payload)
        return self._message_content(body).strip()

    async def _chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await anyio.to_thread.run_sync(self._post_chat_completion, payload)

    def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            logger.error("OpenAI API rejected request: status=%s body=%s", exc.code, body)
            raise LLMServiceError("OpenAI API rejected request.") from exc
        except URLError as exc:
            logger.error("OpenAI API request failed: %s", exc)
            raise LLMServiceError("OpenAI API request failed.") from exc

        return json.loads(body)

    def _message_content(self, body: dict[str, Any]) -> str:
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMServiceError("OpenAI API response did not include message content.") from exc
        if not isinstance(content, str):
            raise LLMServiceError("OpenAI API message content was not text.")
        return content

    def _fallback_intent(self, preprocessed: PreprocessedMessage) -> IntentExtraction:
        price_max = None
        tokens = preprocessed.keywords
        if "under" in tokens:
            index = tokens.index("under")
            if index + 1 < len(tokens) and tokens[index + 1].isdigit():
                price_max = tokens[index + 1]
        non_product_tokens = {
            "affordable",
            "black",
            "blue",
            "cheap",
            "expensive",
            "good",
            "green",
            "kids",
            "men",
            "red",
            "show",
            "under",
            "want",
            "white",
            "women",
        }
        products = [
            {"name": token, "category": ""}
            for token in tokens
            if token not in non_product_tokens and not token.isdigit()
        ][:2]
        intent = "casual" if not products else "browse"
        return IntentExtraction.model_validate(
            {
                "intent": intent,
                "products": products,
                "filters": {
                    "price_range": {"min": None, "max": price_max},
                    "color": next((token for token in tokens if token in {"black", "white", "blue", "red", "green"}), ""),
                    "brand": "",
                    "size": "",
                    "gender": next((token for token in tokens if token in {"men", "women", "kids"}), ""),
                },
                "confidence": 0.45 if products else 0.2,
            }
        )

    def _fallback_no_products(self, intent: IntentExtraction) -> str:
        category = next((product.category or product.name for product in intent.products if product.category or product.name), "")
        if category:
            return f"I could not find a close match for {category} right now. Could you share your preferred budget, size, or color so I can narrow it down?"
        return "I can help you find the right product. What are you looking for, and do you have a budget or preferred color?"

    def _fallback_sales_response(self, products: list[RecommendedProduct]) -> str:
        lines = ["Hey! I found a few good options for you:"]
        for product in products[:5]:
            image = f" Image: {product.image_url}" if product.image_url else ""
            lines.append(f"- {product.name} at Rs. {product.price}: {product.description[:90]}{image}")
        lines.append("Which one should I help you order?")
        return "\n".join(lines)


async def extractUserIntent(cleaned_text: str) -> dict:
    preprocessed = PreprocessedMessage(cleaned_text=cleaned_text, detected_language="unknown", keywords=cleaned_text.split())
    return (await LLMService().extract_user_intent(preprocessed)).model_dump(mode="json")
