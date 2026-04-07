from pathlib import Path

from app.core.config import get_settings


class CloudinaryService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _configure(self):
        try:
            import cloudinary
        except ImportError as exc:
            raise RuntimeError("Cloudinary package is not installed.") from exc

        if not (
            self.settings.cloudinary_cloud_name
            and self.settings.cloudinary_api_key
            and self.settings.cloudinary_api_secret
        ):
            raise RuntimeError("Cloudinary credentials are not configured.")

        cloudinary.config(
            cloud_name=self.settings.cloudinary_cloud_name,
            api_key=self.settings.cloudinary_api_key,
            api_secret=self.settings.cloudinary_api_secret,
            secure=True,
        )

    def upload_product_image(self, image_path: Path) -> tuple[str, str]:
        self._configure()

        from cloudinary import uploader

        result = uploader.upload(
            str(image_path),
            folder=self.settings.cloudinary_product_folder,
            resource_type="image",
        )
        return result["secure_url"], result["public_id"]

    def delete_image(self, public_id: str | None) -> None:
        if not public_id:
            return

        self._configure()

        from cloudinary import uploader

        uploader.destroy(public_id, resource_type="image", invalidate=True)
