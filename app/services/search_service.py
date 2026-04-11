import re
from difflib import SequenceMatcher
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

        candidate_limit = max(20, min(limit * 5, 50))
        docs = list(self.db.db.products.find(filters).sort("stock", -1).limit(candidate_limit))

        if terms and not docs:
            fallback_filters = {key: value for key, value in filters.items() if key != "$or"}
            docs = list(self.db.db.products.find(fallback_filters).sort("stock", -1).limit(100))

        ranked_docs = self._rank_products(docs, intent, keywords)
        return [self._serialize(doc) for doc in ranked_docs[: max(1, min(limit, 10))]]

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
        if intent.filters.brand:
            for product in intent.products:
                if product.name:
                    terms.append(f"{intent.filters.brand} {product.name}")
                if product.category:
                    terms.append(f"{intent.filters.brand} {product.category}")
        terms.extend(self._keyword_phrases(keywords))
        if not terms:
            terms.extend(keywords)
        return list(dict.fromkeys(term.strip() for term in terms if term and len(term.strip()) > 1))

    def _keyword_phrases(self, keywords: list[str]) -> list[str]:
        phrases: list[str] = []
        cleaned = [keyword.strip() for keyword in keywords if keyword and len(keyword.strip()) > 1]
        for size in (2, 3):
            for index in range(len(cleaned) - size + 1):
                phrase = " ".join(cleaned[index : index + size])
                if len(phrase) > 3:
                    phrases.append(phrase)
        return phrases

    def _rank_products(
        self,
        docs: list[dict[str, Any]],
        intent: IntentExtraction,
        keywords: list[str],
    ) -> list[dict[str, Any]]:
        if not docs:
            return []

        terms = self._search_terms(intent, keywords)
        scored = [
            (self._product_match_score(doc, terms), int(doc.get("stock") or 0), str(doc.get("name") or "").casefold(), doc)
            for doc in docs
        ]
        scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
        return [doc for score, _stock, _name, doc in scored if score > 0] or [item[3] for item in scored]

    def _product_match_score(self, doc: dict[str, Any], terms: list[str]) -> float:
        name = self._normalize_text(str(doc.get("name") or ""))
        description = self._normalize_text(str(doc.get("description") or ""))
        category = self._normalize_text(self._category_name(doc))
        haystack = " ".join(part for part in [name, description, category] if part)
        name_tokens = name.split()
        haystack_tokens = haystack.split()
        score = 0.0

        for term in terms:
            normalized = self._normalize_text(term)
            if not normalized:
                continue

            if normalized == name:
                score += 120
                continue
            if normalized in name:
                score += 75
            elif normalized in category:
                score += 45
            elif normalized in description:
                score += 25

            for token in normalized.split():
                if token in name_tokens:
                    score += 24
                elif token in haystack_tokens:
                    score += 10
                else:
                    score += self._best_fuzzy_token_score(token, name_tokens, haystack_tokens)

            ratio = SequenceMatcher(None, normalized, name).ratio() if name else 0.0
            if ratio >= 0.9:
                score += 40
            elif ratio >= 0.78:
                score += 18

        return score

    def _best_fuzzy_token_score(
        self,
        token: str,
        name_tokens: list[str],
        haystack_tokens: list[str],
    ) -> float:
        best_ratio = 0.0
        for candidate in name_tokens or haystack_tokens:
            ratio = SequenceMatcher(None, token, candidate).ratio()
            if ratio > best_ratio:
                best_ratio = ratio

        if best_ratio >= 0.9:
            return 20
        if best_ratio >= 0.8:
            return 8
        return 0.0

    def _normalize_text(self, value: str) -> str:
        return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))

    def _category_name(self, doc: dict[str, Any]) -> str:
        category = self.db.db.categories.find_one({"id": doc.get("category_id"), "store_id": doc.get("store_id")})
        return str(category["name"]) if category else ""

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
