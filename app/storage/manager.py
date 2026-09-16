from app.storage.imgbb import ImgBBStorage
from app.storage.imagekit import ImageKitStorage


class StorageManager:

    def __init__(self):
        self.providers = {
            "imgbb": ImgBBStorage(),
        }

    def get_provider(self, name: str):
        provider = self.providers.get(name)

        if provider is None:
            raise ValueError(
                f"Storage provider '{name}' is not available"
            )

        return provider

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        provider: str = "imgbb",
    ):
        storage = self.get_provider(provider)

        result = await storage.upload(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
        )

        return result

    async def delete(
        self,
        file_id: str,
        provider: str,
    ):
        storage = self.get_provider(provider)

        return await storage.delete(file_id)

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