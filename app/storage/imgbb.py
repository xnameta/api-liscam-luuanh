import httpx

from app.config import IMGBB_API_KEY, IMGBB_UPLOAD_URL
from app.storage.base import StorageProvider


class ImgBBStorage(StorageProvider):

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str
    ):
        if not IMGBB_API_KEY:
            raise RuntimeError("IMGBB_API_KEY chưa được cấu hình")

        files = {
            "image": (
                filename,
                file_bytes,
                content_type
            )
        }

        data = {
            "key": IMGBB_API_KEY
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                IMGBB_UPLOAD_URL,
                data=data,
                files=files
            )

        response.raise_for_status()

        result = response.json()

        if not result.get("success"):
            raise RuntimeError("ImgBB upload thất bại")

        image = result["data"]

        return {
            "provider": "imgbb",
            "provider_file_id": image.get("id"),
            "url": image.get("url"),
            "display_url": image.get("display_url"),
            "thumbnail_url": image.get("thumb", {}).get("url"),
            "delete_url": image.get("delete_url"),
            "width": image.get("width"),
            "height": image.get("height"),
            "size": image.get("size")
        }

    async def delete(self, file_id: str):
        # ImgBB trả delete_url theo từng file.
        # Có thể bổ sung cơ chế quản lý delete_url sau.
        return {
            "success": False,
            "message": "Chưa triển khai delete cho ImgBB"
        }