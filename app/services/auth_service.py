from app.core.exceptions import ConflictError, UnauthorizedError
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.store_repository import StoreRepository
from app.schemas.auth import LoginResponse, RegisterRequest, RegisterResponse


class AuthService:
    def __init__(self, db) -> None:
        self.db = db
        self.stores = StoreRepository(db)
        self.merchants = MerchantRepository(db)

    def register(self, payload: RegisterRequest) -> RegisterResponse:
        merchant_name = payload.name.strip()
        store_name = payload.store_name.strip()
        email = payload.email.lower()

        store = self.stores.get_by_name(store_name)
        if not store:
            store = self.stores.create(name=store_name, whatsapp_phone=payload.whatsapp_phone)

        if self.merchants.get_by_email_and_store(email=email, store_id=store.id):
            raise ConflictError("Seller already exists for this store.")

        merchant = self.merchants.create(
            store_id=store.id,
            name=merchant_name,
            email=email,
            password=payload.password,
        )
        self.db.commit()

        return RegisterResponse(
            merchant_id=merchant.id,
            merchant_name=merchant.name,
            store_id=store.id,
            store_name=store.name,
            email=merchant.email,
        )

    def login(self, email: str, password: str, store_name: str) -> LoginResponse:
        store = self.stores.get_by_name(store_name.strip())
        if not store:
            raise UnauthorizedError("Invalid store or credentials.")

        merchant = self.merchants.get_by_email_and_store(email=email.lower(), store_id=store.id)
        if not merchant or merchant.password != password:
            raise UnauthorizedError("Invalid store or credentials.")

        self.merchants.record_login(merchant=merchant, store=store)
        self.db.commit()

        return LoginResponse(
            merchant_id=merchant.id,
            merchant_name=merchant.name,
            store_id=store.id,
            store_name=store.name,
        )
