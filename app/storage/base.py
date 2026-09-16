from abc import ABC, abstractmethod


class StorageProvider(ABC):

    @abstractmethod
    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ):
        pass

    @abstractmethod
    async def delete(
        self,
        file_id: str,
        delete_reference: str | None = None,
    ):
        pass

    @abstractmethod
    async def get_info(
        self,
        file_id: str,
    ):
        pass

    @abstractmethod
    async def health_check(self):
        pass