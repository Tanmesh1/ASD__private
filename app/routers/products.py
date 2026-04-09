from csv import writer
from decimal import Decimal
from io import StringIO

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response

from app.database.session import get_db
from app.routers.dependencies import get_store_id
from app.schemas.common import MessageResponse
from app.schemas.product import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/with-image", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_with_image(
    name: str = Form(...),
    description: str = Form(...),
    price: Decimal = Form(...),
    stock: int = Form(...),
    category_id: int = Form(...),
    is_active: bool = Form(True),
    file: UploadFile = File(...),
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> ProductResponse:
    payload = ProductCreate(
        name=name,
        description=description,
        price=price,
        stock=stock,
        category_id=category_id,
        is_active=is_active,
    )
    return ProductService(db).create_product_with_image(store_id=store_id, payload=payload, image=file)


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


@router.get("/count", response_model=int)
def count_products(
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> int:
    return ProductService(db).count_products(store_id)


@router.get("/low-stock", response_model=int)
def count_low_stock_products(
    threshold: int = Query(default=10, ge=1),
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> int:
    return ProductService(db).count_low_stock_products(store_id, threshold)


@router.get("/export")
def export_products(
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> Response:
    products = ProductService(db).list_all_products(store_id=store_id)
    output = StringIO()
    csv_writer = writer(output)
    csv_writer.writerow(
        [
            "id",
            "store_id",
            "name",
            "description",
            "price",
            "stock",
            "category_id",
            "category",
            "image_url",
            "image_public_id",
            "is_active",
        ]
    )
    for product in products:
        csv_writer.writerow(
            [
                product.id,
                product.store_id,
                product.name,
                product.description,
                product.price,
                product.stock,
                product.category_id,
                product.category,
                product.image_url,
                product.image_public_id,
                product.is_active,
            ]
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"},
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> ProductResponse:
    return ProductService(db).get_product(store_id=store_id, product_id=product_id)
