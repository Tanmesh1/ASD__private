from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=2, max_length=4000)
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0)
    category_id: int
    image_url: HttpUrl | None = None
    image_public_id: str | None = None
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, min_length=2, max_length=4000)
    price: Decimal | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    category_id: int | None = None
    image_url: HttpUrl | None = None
    image_public_id: str | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store_id: int
    name: str
    description: str
    price: Decimal
    stock: int
    image_url: str | None
    is_active: bool
    category_id: int
    category: str
    image_public_id: str | None = None


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
