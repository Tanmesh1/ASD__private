class ProductRepository:
    def __init__(self, db) -> None:
        self.db = db

    def create(self, **kwargs):
        return self.db.create_product(**kwargs)

    def get_by_id(self, store_id: int, product_id: int):
        return self.db.get_product_by_id(store_id=store_id, product_id=product_id)

    def list_by_store(self, store_id: int):
        return self.db.list_products_by_store(store_id=store_id)

    def delete(self, product) -> None:
        self.db.delete_product(product.id)

    def update(self, product, updates: dict):
        return self.db.update_product(product_id=product.id, updates=updates)

    def search(
        self,
        store_id: int,
        query=None,
        category_id=None,
        min_price=None,
        max_price=None,
        limit: int = 20,
        active_only=None,
    ):
        return self.db.search_products(
            store_id=store_id,
            query=query,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
            active_only=active_only,
        )

    def list_paginated(
        self,
        store_id: int,
        query=None,
        category_id=None,
        min_price=None,
        max_price=None,
        limit: int = 50,
    ):
        return self.search(
            store_id=store_id,
            query=query,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
            active_only=None,
        )
