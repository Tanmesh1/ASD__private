from app.database.session import MongoSession
from app.repositories.category_repository import CategoryRepository
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository


def seed(db: MongoSession) -> None:
    stores = StoreRepository(db)
    merchants = MerchantRepository(db)
    categories = CategoryRepository(db)
    products = ProductRepository(db)

    store = stores.get_by_name("GlowMart")
    if store:
        return

    store = stores.create(name="GlowMart", whatsapp_phone="+911234567890")
    merchants.create(
        store_id=store.id,
        name="Admin User",
        email="admin@glowmart.com",
        password="admin123",
    )

    skincare = categories.create(store_id=store.id, name="Skincare")
    haircare = categories.create(store_id=store.id, name="Haircare")

    products.create(
        store_id=store.id,
        category_id=skincare.id,
        name="Face Wash",
        description="Gentle foam cleanser for daily skincare routines.",
        price=299,
        stock=25,
        image_url="https://example.com/face-wash.jpg",
        is_active=True,
    )
    products.create(
        store_id=store.id,
        category_id=haircare.id,
        name="Hair Serum",
        description="Lightweight serum that adds shine and reduces frizz.",
        price=499,
        stock=10,
        image_url="https://example.com/hair-serum.jpg",
        is_active=True,
    )


if __name__ == "__main__":
    session = MongoSession()
    try:
        session.ping()
        session.ensure_indexes()
        seed(session)
    finally:
        session.close()
