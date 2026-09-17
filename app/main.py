import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Header,
    Form,
)

from app.config import PUBLIC_API_URL
from app.database import (
    init_db,
    get_token,
    save_media,
    get_media_for_owner,
    delete_media_for_owner,
)

from app.storage.manager import StorageManager
from app.services.cleanup import cleanup_loop


# =========================================================
# GLOBAL
# =========================================================

storage = StorageManager()
cleanup_task = None


# =========================================================
# CONFIG
# =========================================================

MAX_FILE_SIZE = 100 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/heic",
    "image/heif",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
}


# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global cleanup_task

    # Khởi tạo database
    init_db()

    # Chạy cleanup worker nền
    cleanup_task = asyncio.create_task(
        cleanup_loop(300)
    )

    print(
        "[LISCAM] Storage API started"
    )

    print(
        "[LISCAM] Cleanup worker started "
        "(interval: 300 seconds)"
    )

    try:
        yield

    finally:
        if cleanup_task:

            cleanup_task.cancel()

            try:
                await cleanup_task

            except asyncio.CancelledError:
                pass

        print(
            "[LISCAM] Storage API stopped"
        )


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Liscam Storage API",
    version="1.3.0",
    description="Storage API for Liscam",
    lifespan=lifespan,
)


# =========================================================
# AUTH
# =========================================================

def get_bearer_token(
    authorization: str | None,
):
    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Thiếu Authorization header",
        )

    if not authorization.startswith(
        "Bearer "
    ):

        raise HTTPException(
            status_code=401,
            detail=(
                "Authorization phải có dạng "
                "Bearer <token>"
            ),
        )

    token = authorization[7:].strip()

    if not token:

        raise HTTPException(
            status_code=401,
            detail="Token không hợp lệ",
        )

    token_data = get_token(token)

    if token_data is None:

        raise HTTPException(
            status_code=401,
            detail=(
                "Token không hợp lệ "
                "hoặc đã bị vô hiệu hóa"
            ),
        )

    return token_data


# =========================================================
# ROOT
# =========================================================

@app.get("/")
async def root():

    return {
        "name": "Liscam Storage API",
        "version": "1.3.0",
        "status": "online",
        "cleanup": "enabled",
        "cleanup_interval_seconds": 300,
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def health():

    return {
        "status": "online",
        "cleanup_worker": (
            "running"
            if cleanup_task
            and not cleanup_task.done()
            else "stopped"
        ),
        "providers": (
            await storage.health_check()
        ),
    }


# =========================================================
# PROVIDERS
# =========================================================

@app.get("/api/v1/providers")
async def providers(
    authorization: str | None = Header(
        default=None
    ),
):

    get_bearer_token(
        authorization
    )

    return {
        "providers": (
            storage.list_providers()
        )
    }


# =========================================================
# UPLOAD
# =========================================================

@app.post("/api/v1/files/upload")
async def upload_file(
    file: UploadFile = File(...),

    provider: str | None = Form(
        default=None
    ),

    authorization: str | None = Header(
        default=None
    ),
):

    # -----------------------------------------
    # AUTH
    # -----------------------------------------

    token_data = get_bearer_token(
        authorization
    )


    # -----------------------------------------
    # FILE NAME
    # -----------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Thiếu tên file",
        )


    # -----------------------------------------
    # MIME TYPE
    # -----------------------------------------

    content_type = (
        file.content_type or ""
    )


    is_image = (
        content_type
        in ALLOWED_IMAGE_TYPES
    )

    is_video = (
        content_type
        in ALLOWED_VIDEO_TYPES
    )


    if not is_image and not is_video:

        raise HTTPException(
            status_code=400,
            detail=(
                "Loại file không được hỗ trợ: "
                f"{content_type}"
            ),
        )


    # -----------------------------------------
    # READ FILE
    # -----------------------------------------

    file_bytes = await file.read()


    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail="File rỗng",
        )


    # -----------------------------------------
    # SIZE
    # -----------------------------------------

    file_size = len(
        file_bytes
    )

    if file_size > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=413,
            detail="File vượt quá 100 MB",
        )


    # -----------------------------------------
    # PROVIDER COMPATIBILITY
    # -----------------------------------------

    if provider:

        provider_name = provider.lower()

        if provider_name not in (
            storage.list_providers()
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Storage provider "
                    f"'{provider}' không tồn tại"
                ),
            )


    # -----------------------------------------
    # UPLOAD STORAGE
    # -----------------------------------------

    try:

        result = await storage.upload(

            file_bytes=file_bytes,

            filename=file.filename,

            content_type=content_type,

            provider=provider,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=(
                "Storage provider error: "
                f"{str(e)}"
            ),
        )


    # -----------------------------------------
    # MEDIA ID
    # -----------------------------------------

    media_id = uuid.uuid4().hex


    # -----------------------------------------
    # TIME
    # -----------------------------------------

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(hours=24)
    )


    # -----------------------------------------
    # API URL
    # -----------------------------------------

    media_url = (
        f"{PUBLIC_API_URL}"
        f"/api/v1/files/{media_id}"
    )

    content_url = (
        f"{PUBLIC_API_URL}"
        f"/api/v1/files/"
        f"{media_id}/content"
    )


    # -----------------------------------------
    # SAVE DATABASE
    # -----------------------------------------

    try:

        save_media(

            media_id=media_id,

            owner_token_id=(
                token_data["id"]
            ),

            provider=result.get(
                "provider"
            ),

            provider_file_id=result.get(
                "provider_file_id"
            ),

            delete_reference=result.get(
                "delete_reference"
            ),

            url=result.get(
                "url"
            ),

            filename=result.get(
                "filename",
                file.filename,
            ),

            mime_type=result.get(
                "mime_type",
                content_type,
            ),

            size=result.get(
                "size",
                file_size,
            ),

            width=result.get(
                "width"
            ),

            height=result.get(
                "height"
            ),

            duration=result.get(
                "duration"
            ),

            created_at=(
                now.isoformat()
            ),

            expires_at=(
                expires_at.isoformat()
            ),
        )

    except Exception as e:

        # Nếu lưu DB thất bại,
        # cố gắng xóa file vừa upload
        try:

            await storage.delete(

                file_id=result.get(
                    "provider_file_id"
                ),

                provider=result.get(
                    "provider"
                ),

                delete_reference=result.get(
                    "delete_reference"
                ),
            )

        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=(
                "Không thể lưu metadata: "
                f"{str(e)}"
            ),
        )


    # -----------------------------------------
    # RESPONSE
    # -----------------------------------------

    return {

        "success": True,

        "id": media_id,

        "provider": result.get(
            "provider"
        ),

        "url": result.get(
            "url"
        ),

        "api_url": media_url,

        "content_url": content_url,

        "filename": result.get(
            "filename",
            file.filename,
        ),

        "mime_type": content_type,

        "size": file_size,

        "created_at": (
            now.isoformat()
        ),

        "expires_at": (
            expires_at.isoformat()
        ),

        "expires_in_seconds": 86400,
    }


# =========================================================
# GET MEDIA INFO
# =========================================================

@app.get(
    "/api/v1/files/{media_id}"
)
async def get_file(

    media_id: str,

    authorization: str | None = Header(
        default=None
    ),
):

    token_data = get_bearer_token(
        authorization
    )


    media = get_media_for_owner(

        media_id,

        token_data["id"],
    )


    if media is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "File không tồn tại "
                "hoặc bạn không có quyền "
                "truy cập"
            ),
        )


    expires_at = datetime.fromisoformat(
        media["expires_at"]
    )


    if expires_at <= datetime.now(
        timezone.utc
    ):

        raise HTTPException(
            status_code=404,
            detail="File đã hết hạn",
        )


    return {

        "success": True,

        "id": media["id"],

        "provider": media["provider"],

        "url": media["url"],

        "filename": media["filename"],

        "mime_type": media["mime_type"],

        "size": media["size"],

        "width": media["width"],

        "height": media["height"],

        "duration": media["duration"],

        "created_at": media["created_at"],

        "expires_at": media["expires_at"],

    }


# =========================================================
# GET MEDIA CONTENT / URL
# =========================================================

@app.get(
    "/api/v1/files/{media_id}/content"
)
async def get_file_content(

    media_id: str,

    authorization: str | None = Header(
        default=None
    ),
):

    token_data = get_bearer_token(
        authorization
    )


    media = get_media_for_owner(

        media_id,

        token_data["id"],
    )


    if media is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "File không tồn tại "
                "hoặc bạn không có quyền "
                "truy cập"
            ),
        )


    expires_at = datetime.fromisoformat(
        media["expires_at"]
    )


    if expires_at <= datetime.now(
        timezone.utc
    ):

        raise HTTPException(
            status_code=404,
            detail="File đã hết hạn",
        )


    return {

        "success": True,

        "id": media["id"],

        "url": media["url"],

        "mime_type": media["mime_type"],

        "filename": media["filename"],

        "expires_at": media["expires_at"],

    }


# =========================================================
# DELETE MEDIA
# =========================================================

@app.delete(
    "/api/v1/files/{media_id}"
)
async def delete_file(

    media_id: str,

    authorization: str | None = Header(
        default=None
    ),
):

    token_data = get_bearer_token(
        authorization
    )


    media = get_media_for_owner(

        media_id,

        token_data["id"],
    )


    if media is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "File không tồn tại "
                "hoặc bạn không có quyền "
                "truy cập"
            ),
        )


    # -----------------------------------------
    # DELETE STORAGE
    # -----------------------------------------

    try:

        result = await storage.delete(

            file_id=media[
                "provider_file_id"
            ],

            provider=media[
                "provider"
            ],

            delete_reference=media.get(
                "delete_reference"
            ),
        )

    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=(
                "Không thể xóa file khỏi "
                "storage: "
                f"{str(e)}"
            ),
        )


    if not result.get(
        "deleted"
    ):

        raise HTTPException(
            status_code=502,
            detail=(
                "Storage provider không "
                "xác nhận đã xóa file"
            ),
        )


    # -----------------------------------------
    # DELETE DATABASE
    # -----------------------------------------

    deleted = delete_media_for_owner(

        media_id,

        token_data["id"],
    )


    if not deleted:

        raise HTTPException(
            status_code=500,
            detail=(
                "File đã xóa khỏi storage "
                "nhưng không xóa được "
                "metadata"
            ),
        )


    return {

        "success": True,

        "id": media_id,

        "deleted": True,

    }