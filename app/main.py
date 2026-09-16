from fastapi import FastAPI, UploadFile, File, HTTPException

from app.storage.manager import StorageManager


app = FastAPI(
    title="Liscam Storage API",
    version="1.0.0"
)

storage = StorageManager()


@app.get("/")
async def root():
    return {
        "name": "Liscam Storage API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }


@app.post("/api/media/upload")
async def upload_media(file: UploadFile = File(...)):

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

    # 32 MB
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
            content_type=file.content_type
        )

        return {
            "success": True,
            "media": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=str(e)
        )