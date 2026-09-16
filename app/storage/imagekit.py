import base64

import httpx

from app.config import IMAGEKIT_PRIVATE_KEY, IMAGEKIT_UPLOAD_URL
from app.storage.base import StorageProvider


class ImageKitStorage(StorageProvider):

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ):
        if not IMAGEKIT_PRIVATE_KEY:
            raise RuntimeError(
                "IMAGEKIT_PRIVATE_KEY chưa được cấu hình"
            )

        auth = base64.b64encode(
            f"{IMAGEKIT_PRIVATE_KEY}:".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth}",
        }

        files = {
            "file": (
                filename,
                file_bytes,
                content_type,
            )
        }

        data = {
            "fileName": filename,
        }

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                IMAGEKIT_UPLOAD_URL,
                headers=headers,
                data=data,
                files=files,
            )

        response.raise_for_status()

        result = response.json()

        return {
            "provider": "imagekit",
            "provider_file_id": result.get("fileId"),
            "url": result.get("url"),
            "thumbnail_url": result.get("thumbnailUrl"),
            "delete_reference": result.get("fileId"),
            "mime_type": content_type,
            "width": result.get("width"),
            "height": result.get("height"),
            "size": result.get("size"),
            "filename": result.get(
                "name",
                filename,
            ),
            "file_type": result.get("fileType"),
            "duration": result.get("duration"),
        }

    async def delete(
        self,
        file_id: str,
        delete_reference: str | None = None,
    ):
        target_id = delete_reference or file_id

        if not target_id:
            return {
                "provider": "imagekit",
                "file_id": file_id,
                "deleted": False,
                "message": "Không có file ID",
            }

        if not IMAGEKIT_PRIVATE_KEY:
            raise RuntimeError(
                "IMAGEKIT_PRIVATE_KEY chưa được cấu hình"
            )

        url = (
            "https://api.imagekit.io/v1/files/"
            f"{target_id}"
        )

        auth = base64.b64encode(
            f"{IMAGEKIT_PRIVATE_KEY}:".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth}",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.delete(
                url,
                headers=headers,
            )

        if response.status_code == 404:
            return {
                "provider": "imagekit",
                "file_id": file_id,
                "deleted": False,
                "message": "File không tồn tại",
            }

        response.raise_for_status()

        return {
            "provider": "imagekit",
            "file_id": file_id,
            "deleted": True,
        }

    async def get_info(self, file_id: str):
        return {
            "provider": "imagekit",
            "provider_file_id": file_id,
        }

    async def health_check(self):
        return {
            "provider": "imagekit",
            "status": (
                "configured"
                if IMAGEKIT_PRIVATE_KEY
                else "not_configured"
            ),
        }