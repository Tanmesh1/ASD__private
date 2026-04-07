from pydantic import BaseModel


class ImageUploadResponse(BaseModel):
    image_url: str
    image_public_id: str
