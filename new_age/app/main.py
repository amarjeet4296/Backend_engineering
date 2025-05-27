from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database.config import engine, Base
from app.database.seed import seed_db
from app.routers import image

# Create database tables
Base.metadata.create_all(bind=engine)

# Seed the database with sample data
seed_db()

app = FastAPI(
    title="Image Metadata API",
    description="API for managing image metadata",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(image.router)

@app.get("/")
def read_root():
    return FileResponse("app/static/redirect.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 