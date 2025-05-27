from typing import Optional
from pydantic import BaseModel

class ImageResponse(BaseModel):
    filename: str
    thumbnail: str
    referenceid: Optional[str] = None
    gtinnumber: str
    itemdesc: str

    class Config:
        from_attributes = True

class UpdateImageRequest(BaseModel):
    filename: str
    thumbnail: Optional[str] = None
    referenceid: Optional[str] = None
    gtinnumber: Optional[str] = None 