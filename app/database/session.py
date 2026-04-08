from collections.abc import Generator
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from pymongo import ASCENDING, MongoClient, ReturnDocument

from app.core.config import get_settings

settings = get_settings()


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


class MongoSession:
    def __init__(self) -> None:
        self.client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[settings.mongo_db_name]

    def ping(self) -> None:
        self.client.admin.command("ping")

    def ensure_indexes(self) -> None:
        self.db.stores.create_index([("id", ASCENDING)], unique=True)
        self.db.stores.create_index([("name", ASCENDING)], unique=True)
        self.db.merchants.create_index([("id", ASCENDING)], unique=True)
        self.db.merchants.create_index([("store_id", ASCENDING), ("email", ASCENDING)], unique=True)
        self.db.logged_in_users.create_index([("id", ASCENDING)], unique=True)
        self.db.logged_in_users.create_index([("merchant_id", ASCENDING)])
        self.db.logged_in_users.create_index([("store_id", ASCENDING)])
        self.db.categories.create_index([("id", ASCENDING)], unique=True)
        self.db.categories.create_index([("store_id", ASCENDING), ("name", ASCENDING)], unique=True)
        self.db.products.create_index([("id", ASCENDING)], unique=True)
        self.db.products.create_index([("store_id", ASCENDING)])
        self.db.products.create_index([("store_id", ASCENDING), ("name", ASCENDING)])
        self.db.products.create_index([("category_id", ASCENDING)])

    def close(self) -> None:
        self.client.close()

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def _next_id(self, sequence_name: str) -> int:
        counter = self.db.counters.find_one_and_update(
            {"_id": sequence_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(counter["seq"])

    def _next_available_category_id(self) -> int:
        docs = self.db.categories.find({}, {"_id": 0, "id": 1}).sort("id", ASCENDING)
        used_ids = {int(doc["id"]) for doc in docs}
        category_id = 1
        while category_id in used_ids:
            category_id += 1
        return category_id

    def _namespace(self, doc: dict[str, Any] | None) -> SimpleNamespace | None:
        if not doc:
            return None
        data = dict(doc)
        data.pop("_id", None)
        if "price" in data:
            data["price"] = _to_decimal(data["price"])
        if "category" in data and isinstance(data["category"], dict):
            data["category"] = SimpleNamespace(**data["category"])
        return SimpleNamespace(**data)

    def _product_namespace(self, doc: dict[str, Any] | None) -> SimpleNamespace | None:
        if not doc:
            return None
        product = dict(doc)
        product.pop("_id", None)
        product["price"] = _to_decimal(product.get("price")) or Decimal("0")
        category = self.db.categories.find_one({"id": product["category_id"], "store_id": product["store_id"]})
        product["category"] = {"name": category["name"]} if category else {"name": ""}
        return self._namespace(product)

    def get_store_by_name(self, name: str) -> SimpleNamespace | None:
        return self._namespace(self.db.stores.find_one({"name": name}))

    def create_store(self, name: str, whatsapp_phone: str | None = None) -> SimpleNamespace:
        doc = {
            "id": self._next_id("stores"),
            "name": name,
            "whatsapp_phone": whatsapp_phone,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.db.stores.insert_one(doc)
        return self._namespace(doc)

    def get_merchant_by_email_and_store(self, email: str, store_id: int) -> SimpleNamespace | None:
        return self._namespace(self.db.merchants.find_one({"email": email, "store_id": store_id}))

    def create_merchant(self, store_id: int, name: str, email: str, password: str) -> SimpleNamespace:
        doc = {
            "id": self._next_id("merchants"),
            "store_id": store_id,
            "name": name,
            "email": email,
            "password": password,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.db.merchants.insert_one(doc)
        return self._namespace(doc)

    def create_logged_in_user(self, merchant: SimpleNamespace, store: SimpleNamespace) -> SimpleNamespace:
        now = datetime.now(timezone.utc)
        doc = {
            "id": self._next_id("logged_in_users"),
            "merchant_id": merchant.id,
            "merchant_name": merchant.name,
            "email": merchant.email,
            "store_id": store.id,
            "store_name": store.name,
            "logged_in_at": now,
            "created_at": now,
        }
        self.db.logged_in_users.insert_one(doc)
        return self._namespace(doc)

    def create_category(self, store_id: int, name: str) -> SimpleNamespace:
        doc = {
            "id": self._next_available_category_id(),
            "store_id": store_id,
            "name": name,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.db.categories.insert_one(doc)
        return self._namespace(doc)

    def list_categories_by_store(self, store_id: int) -> list[SimpleNamespace]:
        docs = self.db.categories.find({"store_id": store_id}).sort("name", ASCENDING)
        return [self._namespace(doc) for doc in docs]

    def get_category_by_id(self, store_id: int, category_id: int) -> SimpleNamespace | None:
        return self._namespace(self.db.categories.find_one({"id": category_id, "store_id": store_id}))

    def get_category_by_name(self, store_id: int, name: str) -> SimpleNamespace | None:
        return self._namespace(self.db.categories.find_one({"store_id": store_id, "name": name}))

    def category_has_products(self, store_id: int, category_id: int) -> bool:
        return self.db.products.find_one({"store_id": store_id, "category_id": category_id}, {"_id": 1}) is not None

    def delete_category(self, store_id: int, category_id: int) -> None:
        self.db.categories.delete_one({"id": category_id, "store_id": store_id})

    def create_product(self, **kwargs: Any) -> SimpleNamespace:
        doc = {
            "id": self._next_id("products"),
            "store_id": kwargs["store_id"],
            "category_id": kwargs["category_id"],
            "name": kwargs["name"],
            "description": kwargs["description"],
            "price": float(kwargs["price"]),
            "stock": kwargs["stock"],
            "image_url": str(kwargs["image_url"]) if kwargs.get("image_url") else None,
            "image_public_id": kwargs.get("image_public_id"),
            "is_active": kwargs.get("is_active", True),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.db.products.insert_one(doc)
        return self._product_namespace(doc)

    def get_product_by_id(self, store_id: int, product_id: int) -> SimpleNamespace | None:
        return self._product_namespace(self.db.products.find_one({"store_id": store_id, "id": product_id}))

    def list_products_by_store(self, store_id: int) -> list[SimpleNamespace]:
        docs = self.db.products.find({"store_id": store_id}).sort("name", ASCENDING)
        return [self._product_namespace(doc) for doc in docs]

    def delete_product(self, product_id: int) -> None:
        self.db.products.delete_one({"id": product_id})

    def update_product(self, product_id: int, updates: dict[str, Any]) -> SimpleNamespace | None:
        normalized = dict(updates)
        if "price" in normalized and normalized["price"] is not None:
            normalized["price"] = float(normalized["price"])
        if "image_url" in normalized and normalized["image_url"] is not None:
            normalized["image_url"] = str(normalized["image_url"])
        normalized["updated_at"] = datetime.now(timezone.utc)
        self.db.products.update_one({"id": product_id}, {"$set": normalized})
        doc = self.db.products.find_one({"id": product_id})
        return self._product_namespace(doc)

    def search_products(
        self,
        store_id: int,
        query: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        limit: int = 20,
        active_only: bool | None = None,
    ) -> list[SimpleNamespace]:
        filters: dict[str, Any] = {"store_id": store_id}
        if active_only is not None:
            filters["is_active"] = active_only
        if category_id:
            filters["category_id"] = category_id
        if min_price is not None or max_price is not None:
            filters["price"] = {}
            if min_price is not None:
                filters["price"]["$gte"] = float(min_price)
            if max_price is not None:
                filters["price"]["$lte"] = float(max_price)
        if query:
            filters["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]

        docs = self.db.products.find(filters).sort("name", ASCENDING).limit(min(limit, 100))
        return [self._product_namespace(doc) for doc in docs]


engine = None
SessionLocal = None


def get_db() -> Generator[MongoSession, None, None]:
    db = MongoSession()
    try:
        yield db
    finally:
        db.close()
