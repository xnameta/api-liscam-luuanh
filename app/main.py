import uuid
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
    get_media,
    get_media_for_owner,
    delete_media_for_owner,
)
from app.storage.manager import StorageManager


app = FastAPI(
    title="Liscam Storage API",
    version="1.2.0",
    description="Storage API for Liscam",
)

storage = StorageManager()


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


@app.on_event("startup")
async def startup():
    init_db()


def get_bearer_token(
    authorization: str | None,
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Thiếu Authorization header",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization phải có dạng Bearer <token>",
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
            detail="Token không hợp lệ hoặc đã bị vô hiệu hóa",
        )

    return token_data


@app.get("/")
async def root():
    return {
        "name": "Liscam Storage API",
        "version": "1.2.0",
        "status": "online",
    }


@app.get("/health")
async def health():
    return {
        "status": "online",
        "providers": await storage.health_check(),
    }


@app.get("/api/v1/providers")
async def providers(
    authorization: str | None = Header(default=None),
):
    get_bearer_token(authorization)

    return {
        "providers": storage.list_providers(),
    }


@app.post("/api/v1/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    provider: str | None = Form(default=None),
    authorization: str | None = Header(default=None),
):
    token_data = get_bearer_token(authorization)

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Thiếu tên file",
        )

    content_type = file.content_type or ""

    if (
        content_type not in ALLOWED_IMAGE_TYPES
        and content_type not in ALLOWED_VIDEO_TYPES
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Loại file không được hỗ trợ: {content_type}",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="File rỗng",
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File vượt quá 100 MB",
        )

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
            detail=f"Storage provider error: {str(e)}",
        )

    media_id = uuid.uuid4().hex

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=24)

    media_url = (
        f"{PUBLIC_API_URL}/api/v1/files/{media_id}"
    )

    content_url = (
        f"{PUBLIC_API_URL}/api/v1/files/"
        f"{media_id}/content"
    )

    save_media(
        media_id=media_id,
        owner_token_id=token_data["id"],
        provider=result.get("provider"),
        provider_file_id=result.get("provider_file_id"),
        delete_reference=result.get("delete_reference"),
        url=result.get("url"),
        filename=result.get("filename", file.filename),
        mime_type=result.get(
            "mime_type",
            content_type,
        ),
        size=result.get("size", len(file_bytes)),
        width=result.get("width"),
        height=result.get("height"),
        duration=result.get("duration"),
        created_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
    )

    return {
        "success": True,
        "id": media_id,
        "provider": result.get("provider"),
        "url": result.get("url"),
        "api_url": media_url,
        "content_url": content_url,
        "filename": result.get(
            "filename",
            file.filename,
        ),
        "mime_type": content_type,
        "size": len(file_bytes),
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }


@app.get("/api/v1/files/{media_id}")
async def get_file(
    media_id: str,
    authorization: str | None = Header(default=None),
):
    token_data = get_bearer_token(authorization)

    media = get_media_for_owner(
        media_id,
        token_data["id"],
    )

    if media is None:
        raise HTTPException(
            status_code=404,
            detail="File không tồn tại hoặc bạn không có quyền truy cập",
        )

    expires_at = datetime.fromisoformat(
        media["expires_at"]
    )

    if expires_at <= datetime.now(timezone.utc):
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


@app.get("/api/v1/files/{media_id}/content")
async def get_file_content(
    media_id: str,
    authorization: str | None = Header(default=None),
):
    token_data = get_bearer_token(authorization)

    media = get_media_for_owner(
        media_id,
        token_data["id"],
    )

    if media is None:
        raise HTTPException(
            status_code=404,
            detail="File không tồn tại hoặc bạn không có quyền truy cập",
        )

    expires_at = datetime.fromisoformat(
        media["expires_at"]
    )

    if expires_at <= datetime.now(timezone.utc):
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
    }


@app.delete("/api/v1/files/{media_id}")
async def delete_file(
    media_id: str,
    authorization: str | None = Header(default=None),
):
    token_data = get_bearer_token(authorization)

    media = get_media_for_owner(
        media_id,
        token_data["id"],
    )

    if media is None:
        raise HTTPException(
            status_code=404,
            detail="File không tồn tại hoặc bạn không có quyền truy cập",
        )

    try:
        result = await storage.delete(
            file_id=media["provider_file_id"],
            provider=media["provider"],
            delete_reference=media["delete_reference"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Không thể xóa file khỏi storage: {str(e)}",
        )

    if not result.get("deleted"):
        raise HTTPException(
            status_code=502,
            detail="Storage provider không xác nhận đã xóa file",
        )

    delete_media_for_owner(
        media_id,
        token_data["id"],
    )

    return {
        "success": True,
        "id": media_id,
        "deleted": True,
    }