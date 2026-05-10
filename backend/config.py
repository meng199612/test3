import os

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
MAX_IMAGES = 50
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
HOST = "0.0.0.0"
PORT = 8000

CAMERA_FX = 1000
CAMERA_FY = 1000
