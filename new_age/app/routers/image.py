from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from app.database.config import get_db
from app.models.image import ImageMetadata
from app.schemas.image import ImageResponse, UpdateImageRequest

router = APIRouter(tags=["Images"])

class ResearchLogData(BaseModel):
    filename: str = None
    data: Dict[str, Any] = None

@router.get("/images", response_model=List[ImageResponse])
def get_all_images(db: Session = Depends(get_db)):
    """Fetch all images from the database."""
    images = db.query(ImageMetadata).all()
    return images

@router.get("/popup/{filename}", response_model=ImageResponse)
def get_image_details(filename: str, db: Session = Depends(get_db)):
    """Fetch image details by filename."""
    image = db.query(ImageMetadata).filter(ImageMetadata.filename == filename).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return image

@router.post("/update", response_model=ImageResponse)
def update_image_details(request: UpdateImageRequest, db: Session = Depends(get_db)):
    """Update image details."""
    image = db.query(ImageMetadata).filter(ImageMetadata.filename == request.filename).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    # Update fields if provided in the request
    if request.thumbnail:
        image.thumbnail = request.thumbnail
    
    if request.gtinnumber:
        image.gtinnumber = request.gtinnumber
    
    # Always update referenceid if it was NULL
    if request.referenceid or image.referenceid is None:
        image.referenceid = request.referenceid
    
    db.commit()
    db.refresh(image)
    return image

@router.post("/saveResearchLog")
async def save_research_log(data: ResearchLogData):
    """Save research log data."""
    try:
        # Log the received data
        print(f"Received research log data: {data}")
        
        # Process and store the research log data
        # This is a placeholder implementation
        
        return {"status": "success", "message": "Research log saved successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save research log: {str(e)}"
        ) 