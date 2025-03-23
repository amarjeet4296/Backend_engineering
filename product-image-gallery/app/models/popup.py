from pydantic import BaseModel, Field
from typing import Optional, Union, List
from uuid import UUID

class PopupBase(BaseModel):
    """Base class for popup data"""
    title: str = Field(..., description="Title to display in the popup")
    product_id: Union[int, UUID] = Field(..., description="ID of the product this popup relates to")
    
class ProductPopupDetail(PopupBase):
    """Model for detailed product popup data"""
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[float] = Field(None, description="Product price")
    image_url: Optional[str] = Field(None, description="URL of the main product image")
    thumbnail_url: Optional[str] = Field(None, description="URL of the product thumbnail")
    additional_images: Optional[List[str]] = Field(None, description="List of additional image URLs")
    
class ImagePopupDetail(PopupBase):
    """Model for detailed image popup data"""
    image_url: str = Field(..., description="URL of the full-size image")
    alt_text: Optional[str] = Field(None, description="Alternative text for the image")
    is_primary: Optional[bool] = Field(False, description="Whether this is the primary product image")
    image_type: Optional[str] = Field("main", description="Type of image (main, detail, etc.)")

class PopupResponse(BaseModel):
    """Response model for popup data"""
    popup_id: str = Field(..., description="Unique identifier for this popup view")
    popup_type: str = Field(..., description="Type of popup (product, image)")
    data: Union[ProductPopupDetail, ImagePopupDetail] = Field(..., description="Popup data")
    
    class Config:
        schema_extra = {
            "example": {
                "popup_id": "popup-123456",
                "popup_type": "product",
                "data": {
                    "title": "Product Detail",
                    "product_id": 1,
                    "description": "This is a product description",
                    "price": 19.99,
                    "image_url": "/static/images/products/1/main.jpg",
                    "thumbnail_url": "/static/images/products/1/thumbnail.jpg",
                    "additional_images": [
                        "/static/images/products/1/detail1.jpg",
                        "/static/images/products/1/detail2.jpg"
                    ]
                }
            }
        } 