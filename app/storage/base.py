from abc import ABC, abstractmethod


class StorageProvider(ABC):

    @abstractmethod
    async def upload(self, file_bytes: bytes, filename: str, content_type: str):
        pass

    @abstractmethod
    async def delete(self, file_id: str):
        pass