from csv import writer
from io import StringIO

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from app.database.session import get_db
from app.routers.dependencies import get_store_id
from app.schemas.category import CategoryCreate, CategoryResponse
from app.schemas.common import MessageResponse
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> CategoryResponse:
    return CategoryService(db).create_category(store_id=store_id, payload=payload)


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> list[CategoryResponse]:
    return CategoryService(db).list_categories(store_id=store_id)


@router.get("/export")
def export_categories(
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> Response:
    categories = CategoryService(db).list_categories(store_id=store_id)
    output = StringIO()
    csv_writer = writer(output)
    csv_writer.writerow(["id", "store_id", "name"])
    for category in categories:
        csv_writer.writerow([category.id, category.store_id, category.name])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=categories.csv"},
    )


@router.delete("/{category_id}", response_model=MessageResponse)
def delete_category(
    category_id: int,
    store_id: int = Depends(get_store_id),
    db=Depends(get_db),
) -> MessageResponse:
    CategoryService(db).delete_category(store_id=store_id, category_id=category_id)
    return MessageResponse(message="Category deleted successfully.")
