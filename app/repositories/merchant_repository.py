class MerchantRepository:
    def __init__(self, db) -> None:
        self.db = db

    def get_by_email_and_store(self, email: str, store_id: int):
        return self.db.get_merchant_by_email_and_store(email=email, store_id=store_id)

    def create(self, store_id: int, name: str, email: str, password: str):
        return self.db.create_merchant(store_id=store_id, name=name, email=email, password=password)

    def record_login(self, merchant, store):
        return self.db.create_logged_in_user(merchant=merchant, store=store)
