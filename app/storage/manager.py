from app.storage.imgbb import ImgBBStorage
from app.storage.freeimage import FreeImageStorage
from app.storage.imagekit import ImageKitStorage


class StorageManager:

    def __init__(self):
        self.providers = {
            "imgbb": ImgBBStorage(),
            "freeimage": FreeImageStorage(),
            "imagekit": ImageKitStorage(),
        }

        # Thứ tự ưu tiên cho ảnh
        self.image_providers = [
            "freeimage",
            "imgbb",
            "imagekit",
        ]

        # Video dùng ImageKit
        self.video_providers = [
            "imagekit",
        ]

    def get_provider(self, name: str):
        provider = self.providers.get(name)

        if provider is None:
            raise ValueError(
                f"Storage provider '{name}' is not available"
            )

        return provider

    def get_candidates(self, content_type: str):
        if content_type.startswith("image/"):
            return self.image_providers.copy()

        if content_type.startswith("video/"):
            return self.video_providers.copy()

        raise ValueError(
            f"Không hỗ trợ loại media: {content_type}"
        )

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        provider: str | None = None,
    ):
        # Nếu người dùng chỉ định provider
        if provider:
            storage = self.get_provider(provider)

            return await storage.upload(
                file_bytes=file_bytes,
                filename=filename,
                content_type=content_type,
            )

        # Tự động chọn provider + fallback
        candidates = self.get_candidates(content_type)

        errors = []

        for name in candidates:
            storage = self.get_provider(name)

            try:
                result = await storage.upload(
                    file_bytes=file_bytes,
                    filename=filename,
                    content_type=content_type,
                )

                return result

            except Exception as e:
                errors.append(
                    f"{name}: {str(e)}"
                )

        raise RuntimeError(
            "Tất cả storage provider đều thất bại: "
            + " | ".join(errors)
        )

    async def delete(
        self,
        file_id: str,
        provider: str,
        delete_reference: str | None = None,
    ):
        storage = self.get_provider(provider)

        return await storage.delete(
            file_id=file_id,
            delete_reference=delete_reference,
        )

    async def get_info(
        self,
        file_id: str,
        provider: str,
    ):
        storage = self.get_provider(provider)

        return await storage.get_info(file_id)

    async def health_check(self):
        results = {}

        for name, provider in self.providers.items():
            try:
                results[name] = await provider.health_check()

            except Exception as e:
                results[name] = {
                    "provider": name,
                    "status": "error",
                    "error": str(e),
                }

        return results

    def list_providers(self):
        return list(self.providers.keys())