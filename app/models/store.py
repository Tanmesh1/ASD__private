from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    whatsapp_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    merchants = relationship("Merchant", back_populates="store", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="store", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
