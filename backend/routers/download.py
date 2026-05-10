import os
import shutil
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from backend.config import UPLOAD_DIR

router = APIRouter()


def _get_session_dir(session_id: str) -> str:
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    if not os.path.exists(session_dir):
        raise HTTPException(404, "Session not found")
    return session_dir


@router.get("/pointcloud/{session_id}")
async def get_pointcloud(session_id: str):
    session_dir = _get_session_dir(session_id)
    json_path = os.path.join(session_dir, "result_simple.json")
    if not os.path.exists(json_path):
        raise HTTPException(404, "Point cloud not generated yet")
    with open(json_path, 'r') as f:
        data = json.load(f)
    return JSONResponse(content=data)


@router.get("/download/{session_id}")
async def download_ply(session_id: str):
    session_dir = _get_session_dir(session_id)
    ply_path = os.path.join(session_dir, "result.ply")
    if not os.path.exists(ply_path):
        raise HTTPException(404, "PLY file not found")
    return FileResponse(
        ply_path,
        media_type="application/octet-stream",
        filename=f"pointcloud_{session_id}.ply"
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    session_dir = _get_session_dir(session_id)
    shutil.rmtree(session_dir)
    return {"deleted": True}
