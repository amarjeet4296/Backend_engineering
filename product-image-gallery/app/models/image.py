from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID, uuid4

class ImageBase(BaseModel):
    """Base model for image data"""
    imageUrl: str
    thumbnailUrl: str
    isPrimary: bool = False
    imageType: str = "main"  # Possible values: main, thumbnail, gallery
    
class ImageCreate(BaseModel):
    """Model for creating a new image"""
    productId: Union[int, UUID]
    isPrimary: Optional[bool] = False
    imageType: Optional[str] = "main"
    
class ImageUpdate(BaseModel):
    """Model for updating an existing image"""
    imageUrl: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    isPrimary: Optional[bool] = None
    imageType: Optional[str] = None
    
class ImageInDB(ImageBase):
    """Model for an image as stored in the database"""
    id: Union[int, UUID] = Field(default_factory=uuid4)
    productId: Union[int, UUID]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        orm_mode = True
        
class Image(ImageInDB):
    """Model for an image as returned by the API"""
    pass

class ImageUpload(BaseModel):
    """Model for image upload response"""
    imageUrl: str
    thumbnailUrl: str 