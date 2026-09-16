import httpx

from app.config import FREEIMAGE_API_KEY, FREEIMAGE_UPLOAD_URL
from app.storage.base import StorageProvider


class FreeImageStorage(StorageProvider):

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ):
        if not FREEIMAGE_API_KEY:
            raise RuntimeError(
                "FREEIMAGE_API_KEY chưa được cấu hình"
            )

        files = {
            "source": (
                filename,
                file_bytes,
                content_type,
            )
        }

        data = {
            "key": FREEIMAGE_API_KEY,
            "action": "upload",
            "format": "json",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                FREEIMAGE_UPLOAD_URL,
                data=data,
                files=files,
            )

        response.raise_for_status()

        result = response.json()

        if result.get("status_code") != 200:
            error = result.get("error", {})

            raise RuntimeError(
                error.get(
                    "message",
                    "FreeImage.host upload failed",
                )
            )

        image = result.get("image", {})

        return {
            "provider": "freeimage",
            "provider_file_id": image.get("id"),
            "url": image.get("url"),
            "display_url": image.get("display_url"),
            "thumbnail_url": (
                image.get("thumb", {}).get("url")
            ),
            "delete_reference": image.get("delete_url"),
            "mime_type": image.get("mime"),
            "width": image.get("width"),
            "height": image.get("height"),
            "size": image.get("size"),
            "filename": image.get(
                "filename",
                filename,
            ),
        }

    async def delete(
        self,
        file_id: str,
        delete_reference: str | None = None,
    ):
        if not delete_reference:
            return {
                "provider": "freeimage",
                "file_id": file_id,
                "deleted": False,
                "message": "Không có delete_reference",
            }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                delete_reference
            )

        if response.status_code >= 400:
            return {
                "provider": "freeimage",
                "file_id": file_id,
                "deleted": False,
                "status_code": response.status_code,
            }

        return {
            "provider": "freeimage",
            "file_id": file_id,
            "deleted": True,
        }

    async def get_info(self, file_id: str):
        return {
            "provider": "freeimage",
            "provider_file_id": file_id,
        }

    async def health_check(self):
        return {
            "provider": "freeimage",
            "status": (
                "configured"
                if FREEIMAGE_API_KEY
                else "not_configured"
            ),
        }