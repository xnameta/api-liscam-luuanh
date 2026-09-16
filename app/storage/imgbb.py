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
            raise Exception("ImgBB upload failed")

        image = result["data"]

        return {
            "provider": "imgbb",
            "provider_file_id": image.get("id"),
            "url": image.get("url"),
            "display_url": image.get("display_url"),
            "thumbnail_url": image.get("thumb", {}).get("url"),
            "delete_reference": image.get("delete_url"),
            "width": image.get("width"),
            "height": image.get("height"),
            "size": image.get("size"),
            "mime_type": content_type,
            "filename": filename,
        }

    async def delete(self, file_id: str):
        # ImgBB dùng delete URL được trả về lúc upload.
        # Sẽ hoàn thiện cơ chế xóa ở bước Storage Manager.
        return {
            "provider": "imgbb",
            "file_id": file_id,
            "deleted": False,
            "message": "Delete handler will be completed in the next step"
        }

    async def get_info(self, file_id: str):
        return {
            "provider": "imgbb",
            "provider_file_id": file_id
        }

    async def health_check(self):
        return {
            "provider": "imgbb",
            "status": "configured" if IMGBB_API_KEY else "not_configured"
        }