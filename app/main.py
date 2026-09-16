from fastapi import FastAPI, UploadFile, File, HTTPException, Form

from app.storage.manager import StorageManager


app = FastAPI(
    title="Liscam Storage API",
    version="1.1.0"
)

storage = StorageManager()


@app.get("/")
async def root():
    return {
        "name": "Liscam Storage API",
        "version": "1.1.0",
        "status": "online"
    }


@app.get("/health")
async def health():
    return await storage.health_check()


@app.get("/api/providers")
async def providers():
    return {
        "providers": storage.list_providers()
    }


@app.post("/api/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    provider: str = Form("imgbb")
):

    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="Không xác định được loại file"
        )

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif"
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Định dạng ảnh không được hỗ trợ"
        )

    file_bytes = await file.read()

    max_size = 32 * 1024 * 1024

    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=413,
            detail="File vượt quá 32 MB"
        )

    try:
        result = await storage.upload(
            file_bytes=file_bytes,
            filename=file.filename or "image",
            content_type=file.content_type,
            provider=provider
        )

        return {
            "success": True,
            "provider": provider,
            "media": result
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=str(e)
        )