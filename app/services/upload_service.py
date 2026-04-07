from pathlib import Path
from time import time
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.services.cloudinary_service import CloudinaryService


class UploadService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.cloudinary = CloudinaryService()

    def _cleanup_stale_temp_files(self, temp_root: Path) -> None:
        cutoff = time() - self.settings.temp_upload_max_age_seconds
        for path in temp_root.iterdir():
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink(missing_ok=True)

    def save_product_image(self, file: UploadFile) -> tuple[str, str]:
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files can be uploaded.",
            )

        temp_root = Path(self.settings.temp_upload_dir)
        temp_root.mkdir(parents=True, exist_ok=True)
        self._cleanup_stale_temp_files(temp_root)

        extension = Path(file.filename or "").suffix or ".jpg"
        filename = f"{uuid4().hex}{extension}"
        destination = temp_root / filename

        with destination.open("wb") as buffer:
            buffer.write(file.file.read())

        try:
            return self.cloudinary.upload_product_image(destination)
        except RuntimeError as exc:
            destination.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            destination.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Cloudinary image upload failed.",
            ) from exc
