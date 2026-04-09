from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate


class CategoryService:
    def __init__(self, db) -> None:
        self.db = db
        self.categories = CategoryRepository(db)

    def create_category(self, store_id: int, payload: CategoryCreate):
        if self.categories.get_by_name(store_id=store_id, name=payload.name.strip()):
            raise ConflictError("Category already exists for this store.")

        category = self.categories.create(store_id=store_id, name=payload.name.strip())
        self.db.commit()
        return category

    def list_categories(self, store_id: int):
        return self.categories.list_by_store(store_id)

    def count_categories(self, store_id: int) -> int:
        return self.db.count_categories(store_id)

    def delete_category(self, store_id: int, category_id: int) -> None:
        category = self.categories.get_by_id(store_id=store_id, category_id=category_id)
        if not category:
            raise NotFoundError("Category not found for this store.")

        if self.categories.has_products(store_id=store_id, category_id=category_id):
            raise ConflictError("Cannot delete a category that has products.")

        self.categories.delete(store_id=store_id, category_id=category_id)
        self.db.commit()
