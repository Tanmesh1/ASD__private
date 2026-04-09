from decimal import Decimal

from fastapi import UploadFile

from app.core.exceptions import NotFoundError
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.cloudinary_service import CloudinaryService
from app.services.upload_service import UploadService


class ProductService:
    def __init__(self, db) -> None:
        self.db = db
        self.products = ProductRepository(db)
        self.categories = CategoryRepository(db)
        self.cloudinary = CloudinaryService()
        self.uploads = UploadService()

    def _get_category(self, store_id: int, category_id: int):
        category = self.categories.get_by_id(store_id=store_id, category_id=category_id)
        if not category:
            raise NotFoundError("Category not found for this store.")
        return category

    def _serialize(self, product) -> ProductResponse:
        return ProductResponse(
            id=product.id,
            store_id=product.store_id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock=product.stock,
            image_url=str(product.image_url) if product.image_url else None,
            is_active=product.is_active,
            category_id=product.category_id,
            category=product.category.name if product.category else "",
            image_public_id=getattr(product, "image_public_id", None),
        )

    def _delete_cloudinary_image(self, public_id: str | None) -> None:
        if public_id:
            self.cloudinary.delete_image(public_id)

    def create_product(self, store_id: int, payload: ProductCreate) -> ProductResponse:
        try:
            self._get_category(store_id, payload.category_id)
            product = self.products.create(store_id=store_id, **payload.model_dump())
            self.db.commit()
        except Exception:
            self._delete_cloudinary_image(payload.image_public_id)
            raise

        product = self.products.get_by_id(store_id=store_id, product_id=product.id)
        return self._serialize(product)

    def create_product_with_image(
        self,
        store_id: int,
        payload: ProductCreate,
        image: UploadFile,
    ) -> ProductResponse:
        self._get_category(store_id, payload.category_id)
        image_url, image_public_id = self.uploads.save_product_image(image)
        payload_with_image = ProductCreate(
            **payload.model_dump(exclude={"image_url", "image_public_id"}),
            image_url=image_url,
            image_public_id=image_public_id,
        )
        return self.create_product(store_id=store_id, payload=payload_with_image)

    def update_product(self, store_id: int, product_id: int, payload: ProductUpdate) -> ProductResponse:
        product = self.products.get_by_id(store_id=store_id, product_id=product_id)
        if not product:
            raise NotFoundError("Product not found for this store.")

        updates = payload.model_dump(exclude_unset=True)
        try:
            if "category_id" in updates and updates["category_id"] is not None:
                self._get_category(store_id, updates["category_id"])

            updated = self.products.update(product, updates)
            self.db.commit()
        except Exception:
            new_public_id = updates.get("image_public_id")
            old_public_id = getattr(product, "image_public_id", None)
            if new_public_id and new_public_id != old_public_id:
                self._delete_cloudinary_image(new_public_id)
            raise

        old_public_id = getattr(product, "image_public_id", None)
        if "image_public_id" in updates and updates["image_public_id"] != old_public_id:
            self._delete_cloudinary_image(old_public_id)

        updated = self.products.get_by_id(store_id=store_id, product_id=updated.id)
        return self._serialize(updated)

    def delete_product(self, store_id: int, product_id: int) -> None:
        product = self.products.get_by_id(store_id=store_id, product_id=product_id)
        if not product:
            raise NotFoundError("Product not found for this store.")

        self._delete_cloudinary_image(getattr(product, "image_public_id", None))
        self.products.delete(product)
        self.db.commit()

    def list_products(
        self,
        store_id: int,
        query: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        limit: int = 50,
    ) -> list[ProductResponse]:
        products = self.products.list_paginated(
            store_id=store_id,
            query=query,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
        )
        return [self._serialize(product) for product in products]

    def get_product(self, store_id: int, product_id: int) -> ProductResponse:
        product = self.products.get_by_id(store_id=store_id, product_id=product_id)
        if not product:
            raise NotFoundError("Product not found for this store.")
        return self._serialize(product)

    def list_all_products(self, store_id: int) -> list[ProductResponse]:
        products = self.products.list_by_store(store_id=store_id)
        return [self._serialize(product) for product in products]

    def search_products(
        self,
        store_id: int,
        query: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        limit: int = 20,
    ) -> list[ProductResponse]:
        products = self.products.search(
            store_id=store_id,
            query=query,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
            active_only=True,
        )
        return [self._serialize(product) for product in products]

    def count_products(self, store_id: int) -> int:
        return self.db.count_products(store_id)

    def count_low_stock_products(self, store_id: int, threshold: int = 10) -> int:
        return self.db.count_low_stock_products(store_id, threshold)
