class StoreRepository:
    def __init__(self, db) -> None:
        self.db = db

    def get_by_name(self, name: str):
        return self.db.get_store_by_name(name)

    def create(self, name: str, whatsapp_phone: str | None = None):
        return self.db.create_store(name=name, whatsapp_phone=whatsapp_phone)
