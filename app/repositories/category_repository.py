class CategoryRepository:
    def __init__(self, db) -> None:
        self.db = db

    def create(self, store_id: int, name: str):
        return self.db.create_category(store_id=store_id, name=name)

    def list_by_store(self, store_id: int):
        return self.db.list_categories_by_store(store_id)

    def get_by_id(self, store_id: int, category_id: int):
        return self.db.get_category_by_id(store_id=store_id, category_id=category_id)

    def get_by_name(self, store_id: int, name: str):
        return self.db.get_category_by_name(store_id=store_id, name=name)

    def has_products(self, store_id: int, category_id: int) -> bool:
        return self.db.category_has_products(store_id=store_id, category_id=category_id)

    def delete(self, store_id: int, category_id: int) -> None:
        self.db.delete_category(store_id=store_id, category_id=category_id)
