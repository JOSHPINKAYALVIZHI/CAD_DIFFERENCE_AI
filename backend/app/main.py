from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title="AI Image Difference Detection API",
    version="1.0.0",
    description="Detect visual differences between two images."
)

# Configure CORS to allow the React development server to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development; narrow down for production deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files and generated visual outputs statically
app.mount("/api/v1/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/api/v1/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")

app.include_router(router)

@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "API is running 🚀"
    }