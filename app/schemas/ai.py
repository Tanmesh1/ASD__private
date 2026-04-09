from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


IntentName = Literal["buy", "browse", "compare", "ask_price", "casual"]


class PreprocessedMessage(BaseModel):
    cleaned_text: str
    detected_language: str
    keywords: list[str] = Field(default_factory=list)


class PriceRange(BaseModel):
    min: Decimal | None = None
    max: Decimal | None = None


class IntentFilters(BaseModel):
    price_range: PriceRange = Field(default_factory=PriceRange)
    color: str = ""
    brand: str = ""
    size: str = ""
    gender: str = ""


class ExtractedProduct(BaseModel):
    name: str = ""
    category: str = ""


class IntentExtraction(BaseModel):
    intent: IntentName
    products: list[ExtractedProduct] = Field(default_factory=list)
    filters: IntentFilters = Field(default_factory=IntentFilters)
    confidence: float = Field(ge=0, le=1, default=0.0)


class RecommendedProduct(BaseModel):
    id: int
    name: str
    price: Decimal
    description: str
    image_url: str | None = None
    discount: str | None = None
    category: str = ""
    stock: int = 0


class AICommerceResult(BaseModel):
    text: str
    products: list[RecommendedProduct] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    intent: IntentExtraction
    preprocessing: PreprocessedMessage
