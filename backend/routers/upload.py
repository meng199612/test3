import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.config import UPLOAD_DIR, MAX_IMAGES, ALLOWED_EXTENSIONS

router = APIRouter()

@router.post("/upload")
async def upload_images(files: list[UploadFile] = File(...)):
    if len(files) > MAX_IMAGES:
        raise HTTPException(400, f"最多上传 {MAX_IMAGES} 张图片")
    if len(files) < 2:
        raise HTTPException(400, "至少需要 2 张图片")

    session_id = str(uuid.uuid4())[:8]
    session_dir = os.path.join(UPLOAD_DIR, session_id, "images")
    os.makedirs(session_dir, exist_ok=True)

    saved_files = []
    for i, file in enumerate(files, 1):
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, f"不支持的文件格式: {ext}")
        
        save_name = f"{i:03d}{ext}"
        save_path = os.path.join(session_dir, save_name)
        
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
        saved_files.append(save_name)

    return {
        "session_id": session_id,
        "file_count": len(saved_files),
        "files": saved_files
    }
