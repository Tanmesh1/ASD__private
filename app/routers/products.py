from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status

from app.database.session import get_db
from app.routers.dependencies import get_store_id
from app.schemas.common import MessageResponse
from app.schemas.product import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> ProductResponse:
    return ProductService(db).create_product(store_id=store_id, payload=payload)


@router.get("", response_model=ProductListResponse)
def list_products(
    query: str | None = None,
    category_id: int | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> ProductListResponse:
    products = ProductService(db).list_products(
        store_id=store_id,
        query=query,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
    )
    return ProductListResponse(products=products)


@router.get("/search", response_model=ProductListResponse)
def search_products(
    query: str | None = None,
    category_id: int | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> ProductListResponse:
    products = ProductService(db).search_products(
        store_id=store_id,
        query=query,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
    )
    return ProductListResponse(products=products)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> ProductResponse:
    return ProductService(db).update_product(store_id=store_id, product_id=product_id, payload=payload)


@router.delete("/{product_id}", response_model=MessageResponse)
def delete_product(
    product_id: int,
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> MessageResponse:
    ProductService(db).delete_product(store_id=store_id, product_id=product_id)
    return MessageResponse(message="Product deleted successfully.")
