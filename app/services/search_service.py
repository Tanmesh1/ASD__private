import re
from decimal import Decimal, InvalidOperation
from typing import Any

import anyio

from app.repositories.category_repository import CategoryRepository
from app.schemas.ai import IntentExtraction, RecommendedProduct


class ProductSearchService:
    def __init__(self, db) -> None:
        self.db = db
        self.categories = CategoryRepository(db)

    async def search_products(
        self,
        store_id: int,
        intent: IntentExtraction,
        keywords: list[str],
        limit: int = 6,
    ) -> list[RecommendedProduct]:
        return await anyio.to_thread.run_sync(self._search_products_sync, store_id, intent, keywords, limit)

    def _search_products_sync(
        self,
        store_id: int,
        intent: IntentExtraction,
        keywords: list[str],
        limit: int,
    ) -> list[RecommendedProduct]:
        filters: dict[str, Any] = {"store_id": store_id, "is_active": True}

        category_id = self._resolve_category_id(store_id, intent)
        if category_id:
            filters["category_id"] = category_id

        price_filter = self._price_filter(intent)
        if price_filter:
            filters["price"] = price_filter

        terms = self._search_terms(intent, keywords)
        if terms:
            regexes = [{"$regex": re.escape(term), "$options": "i"} for term in terms]
            filters["$or"] = [
                {"name": regex}
                for regex in regexes
            ] + [
                {"description": regex}
                for regex in regexes
            ]

        docs = self.db.db.products.find(filters).sort("stock", -1).limit(max(1, min(limit, 10)))
        return [self._serialize(doc) for doc in docs]

    def _resolve_category_id(self, store_id: int, intent: IntentExtraction) -> int | None:
        categories = self.categories.list_by_store(store_id)
        wanted = [product.category for product in intent.products if product.category]
        wanted += [product.name for product in intent.products if product.name]
        for term in wanted:
            normalized = term.casefold()
            for category in categories:
                if normalized in category.name.casefold() or category.name.casefold() in normalized:
                    return int(category.id)
        return None

    def _price_filter(self, intent: IntentExtraction) -> dict[str, float]:
        price_range = intent.filters.price_range
        price_filter: dict[str, float] = {}
        minimum = self._decimal_or_none(price_range.min)
        maximum = self._decimal_or_none(price_range.max)
        if minimum is not None:
            price_filter["$gte"] = float(minimum)
        if maximum is not None:
            price_filter["$lte"] = float(maximum)
        return price_filter

    def _search_terms(self, intent: IntentExtraction, keywords: list[str]) -> list[str]:
        terms = []
        terms.extend(product.name for product in intent.products if product.name)
        terms.extend(product.category for product in intent.products if product.category)
        terms.extend(
            value
            for value in [
                intent.filters.color,
                intent.filters.brand,
                intent.filters.size,
                intent.filters.gender,
            ]
            if value
        )
        if not terms:
            terms.extend(keywords)
        return list(dict.fromkeys(term.strip() for term in terms if term and len(term.strip()) > 1))

    def _decimal_or_none(self, value: Any) -> Decimal | None:
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError):
            return None

    def _serialize(self, doc: dict[str, Any]) -> RecommendedProduct:
        category = self.db.db.categories.find_one({"id": doc.get("category_id"), "store_id": doc.get("store_id")})
        discount = doc.get("discount") or doc.get("offer") or doc.get("discount_text")
        return RecommendedProduct(
            id=int(doc["id"]),
            name=str(doc["name"]),
            price=Decimal(str(doc.get("price") or 0)),
            description=str(doc.get("description") or ""),
            image_url=str(doc["image_url"]) if doc.get("image_url") else None,
            discount=str(discount) if discount else None,
            category=str(category["name"]) if category else "",
            stock=int(doc.get("stock") or 0),
        )


async def searchProducts(query_json: dict, db, store_id: int, limit: int = 6) -> list[dict]:
    intent = IntentExtraction.model_validate(query_json)
    products = await ProductSearchService(db).search_products(store_id=store_id, intent=intent, keywords=[], limit=limit)
    return [product.model_dump(mode="json") for product in products]
