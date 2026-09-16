import os
from dotenv import load_dotenv

load_dotenv()

IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "")
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"