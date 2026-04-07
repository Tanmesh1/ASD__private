from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Merchant(Base):
    __tablename__ = "merchants"
    __table_args__ = (UniqueConstraint("email", "store_id", name="uq_merchant_email_store"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(120), nullable=False)

    store = relationship("Store", back_populates="merchants")
