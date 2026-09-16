import os

from dotenv import load_dotenv


load_dotenv()


PUBLIC_API_URL = os.getenv(
    "PUBLIC_API_URL",
    "http://127.0.0.1:8000",
).strip().rstrip("/")


IMGBB_API_KEY = os.getenv(
    "IMGBB_API_KEY",
    "",
).strip()

IMGBB_UPLOAD_URL = os.getenv(
    "IMGBB_UPLOAD_URL",
    "https://api.imgbb.com/1/upload",
).strip()


IMAGEKIT_PRIVATE_KEY = os.getenv(
    "IMAGEKIT_PRIVATE_KEY",
    "",
).strip()

IMAGEKIT_UPLOAD_URL = os.getenv(
    "IMAGEKIT_UPLOAD_URL",
    "https://upload.imagekit.io/api/v1/files/upload",
).strip()


FREEIMAGE_API_KEY = os.getenv(
    "FREEIMAGE_API_KEY",
    "",
).strip()

FREEIMAGE_UPLOAD_URL = os.getenv(
    "FREEIMAGE_UPLOAD_URL",
    "https://freeimage.host/api/1/upload",
).strip()


def provider_config():
    return {
        "imgbb": bool(IMGBB_API_KEY),
        "imagekit": bool(IMAGEKIT_PRIVATE_KEY),
        "freeimage": bool(FREEIMAGE_API_KEY),
    }