from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.upload import router as upload_router
from backend.routers.reconstruct import router as reconstruct_router
from backend.routers.download import router as download_router

app = FastAPI(title="Pic2PointCloud")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(reconstruct_router, prefix="/api")
app.include_router(download_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Pic2PointCloud API", "status": "running"}
