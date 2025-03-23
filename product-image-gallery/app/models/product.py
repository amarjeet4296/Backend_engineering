from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID, uuid4

class ProductBase(BaseModel):
    """Base model for product data"""
    name: str
    description: str
    price: float = Field(gt=0)
    
class ProductCreate(ProductBase):
    """Model for creating a new product"""
    imageUrl: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    
class ProductUpdate(BaseModel):
    """Model for updating an existing product"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    imageUrl: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    
class ProductInDB(ProductBase):
    """Model for a product as stored in the database"""
    id: Union[int, UUID] = Field(default_factory=uuid4)
    imageUrl: str = "/static/images/placeholder.jpg"
    thumbnailUrl: str = "/static/images/thumbnails/placeholder.jpg"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        orm_mode = True
        
class Product(ProductInDB):
    """Model for a product as returned by the API"""
    pass 