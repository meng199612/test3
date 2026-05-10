import os
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from backend.config import UPLOAD_DIR
from backend.services.sfm.pipeline import SfMPipeline

router = APIRouter()
active_tasks = {}


@router.post("/reconstruct/{session_id}")
async def start_reconstruction(session_id: str):
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    image_dir = os.path.join(session_dir, "images")
    if not os.path.exists(image_dir):
        raise HTTPException(status_code=404, detail="Session not found")

    active_tasks[session_id] = {"status": "pending", "progress": 0}
    return {"task_id": session_id}


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    image_dir = os.path.join(session_dir, "images")
    
    if not os.path.exists(image_dir):
        await websocket.send_json({"type": "error", "message": "Session not found"})
        await websocket.close()
        return

    active_tasks[session_id] = {"status": "running", "progress": 0}

    main_loop = asyncio.get_running_loop()

    def progress_callback(percent, message):
        active_tasks[session_id] = {"status": "running", "progress": percent}
        asyncio.run_coroutine_threadsafe(
            websocket.send_json({"type": "progress", "percent": percent, "message": message}),
            main_loop
        )

    try:
        pipeline = SfMPipeline(image_dir, session_dir, progress_callback)
        
        result = await main_loop.run_in_executor(None, pipeline.run)

        active_tasks[session_id] = {"status": "complete", "progress": 100}
        await websocket.send_json({
            "type": "complete",
            "session_id": session_id,
            "result": {
                "n_points": int(result["n_points"]),
                "n_registered": int(result["n_registered"])
            }
        })

    except Exception as e:
        active_tasks[session_id] = {"status": "error", "error": str(e)}
        await websocket.send_json({"type": "error", "message": str(e)})
    
    finally:
        await websocket.close()
