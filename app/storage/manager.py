from app.storage.imgbb import ImgBBStorage


class StorageManager:

    def __init__(self):
        self.providers = {
            "imgbb": ImgBBStorage()
        }

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str
    ):
        # V1: sử dụng ImgBB.
        # V2 có thể thêm thuật toán lựa chọn provider.

        provider = self.providers["imgbb"]

        return await provider.upload(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type
        )