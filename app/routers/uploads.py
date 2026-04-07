from fastapi import APIRouter, File, UploadFile, status

from app.schemas.upload import ImageUploadResponse
from app.services.upload_service import UploadService

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("/product-image", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_product_image(file: UploadFile = File(...)) -> ImageUploadResponse:
    image_url, image_public_id = UploadService().save_product_image(file)
    return ImageUploadResponse(image_url=image_url, image_public_id=image_public_id)
