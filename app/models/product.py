from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_store_id", "store_id"),
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_name", "name"),
        Index("ix_products_store_name", "store_id", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_public_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")
