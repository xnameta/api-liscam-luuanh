import httpx

from app.config import IMGBB_API_KEY, IMGBB_UPLOAD_URL
from app.storage.base import StorageProvider


class ImgBBStorage(StorageProvider):

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ):
        if not IMGBB_API_KEY:
            raise RuntimeError(
                "IMGBB_API_KEY chưa được cấu hình"
            )

        files = {
            "image": (
                filename,
                file_bytes,
                content_type,
            )
        }

        data = {
            "key": IMGBB_API_KEY,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                IMGBB_UPLOAD_URL,
                data=data,
                files=files,
            )

        response.raise_for_status()

        result = response.json()

        if not result.get("success"):
            raise RuntimeError(
                "ImgBB upload failed"
            )

        image = result.get("data", {})

        return {
            "provider": "imgbb",
            "provider_file_id": image.get("id"),
            "url": image.get("url"),
            "display_url": image.get("display_url"),
            "thumbnail_url": (
                image.get("thumb", {}).get("url")
            ),
            "delete_reference": image.get("delete_url"),
            "width": image.get("width"),
            "height": image.get("height"),
            "size": image.get("size"),
            "mime_type": content_type,
            "filename": filename,
        }

    async def delete(
        self,
        file_id: str,
        delete_reference: str | None = None,
    ):
        if not delete_reference:
            return {
                "provider": "imgbb",
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
                "provider": "imgbb",
                "file_id": file_id,
                "deleted": False,
                "status_code": response.status_code,
            }

        return {
            "provider": "imgbb",
            "file_id": file_id,
            "deleted": True,
        }

    async def get_info(self, file_id: str):
        return {
            "provider": "imgbb",
            "provider_file_id": file_id,
        }

    async def health_check(self):
        return {
            "provider": "imgbb",
            "status": (
                "configured"
                if IMGBB_API_KEY
                else "not_configured"
            ),
        }