import asyncio
import logging

from app.database import (
    get_expired_media,
    delete_media,
)
from app.storage.manager import StorageManager


logger = logging.getLogger("liscam.cleanup")


class CleanupService:

    def __init__(self):
        self.storage = StorageManager()

    async def cleanup_once(self):
        expired_items = get_expired_media()

        if not expired_items:
            return {
                "checked": 0,
                "deleted": 0,
                "failed": 0,
            }

        deleted = 0
        failed = 0

        for media in expired_items:
            media_id = media["id"]
            provider = media["provider"]
            provider_file_id = media.get(
                "provider_file_id"
            )
            delete_reference = media.get(
                "delete_reference"
            )

            try:
                result = await self.storage.delete(
                    file_id=provider_file_id,
                    provider=provider,
                    delete_reference=delete_reference,
                )

                if result.get("deleted"):
                    delete_media(media_id)
                    deleted += 1

                    logger.info(
                        "Deleted expired media: %s",
                        media_id,
                    )
                else:
                    failed += 1

                    logger.warning(
                        "Provider delete failed: %s",
                        media_id,
                    )

            except Exception as e:
                failed += 1

                logger.exception(
                    "Cleanup error for %s: %s",
                    media_id,
                    e,
                )

        return {
            "checked": len(expired_items),
            "deleted": deleted,
            "failed": failed,
        }


async def cleanup_loop(interval_seconds=300):
    service = CleanupService()

    logger.info(
        "Liscam cleanup worker started"
    )

    while True:
        try:
            result = await service.cleanup_once()

            if result["checked"] > 0:
                logger.info(
                    "Cleanup result: %s",
                    result,
                )

        except Exception as e:
            logger.exception(
                "Cleanup worker error: %s",
                e,
            )

        await asyncio.sleep(interval_seconds)