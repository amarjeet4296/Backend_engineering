from sqlalchemy import Column, String, Text
from app.database.config import Base

class ImageMetadata(Base):
    __tablename__ = "image_metadata"

    filename = Column(String, primary_key=True, index=True)
    thumbnail = Column(String, nullable=False)
    referenceid = Column(String, nullable=True)
    gtinnumber = Column(String, nullable=False)
    itemdesc = Column(Text, nullable=False) 