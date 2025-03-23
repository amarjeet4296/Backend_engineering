from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Import routers
from app.api.product_router import router as product_router
from app.api.image_router import router as image_router
from app.api.popup_router import router as popup_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Product Image Gallery API",
    description="API for managing product images with Azure Blob Storage",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(product_router, prefix="/api/products", tags=["products"])
app.include_router(image_router, prefix="/api/images", tags=["images"])
app.include_router(popup_router, prefix="/api/popups", tags=["popups"])

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint to check if the API is running
    """
    return {"message": "Product Image Gallery API is running"} 