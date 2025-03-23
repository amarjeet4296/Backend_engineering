import os
from datetime import datetime, timedelta
import uuid
from typing import Optional, Tuple
import shutil
from fastapi import UploadFile
from PIL import Image
import io
import asyncio

# Local file storage paths
STATIC_DIR = "app/static"
IMAGES_DIR = f"{STATIC_DIR}/images"
THUMBNAILS_DIR = f"{STATIC_DIR}/images/thumbnails"

# Ensure directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

async def save_image_locally(upload_file: UploadFile, product_id: str) -> Tuple[str, str]:
    """
    Save an uploaded image locally.
    
    Args:
        upload_file: The uploaded file
        product_id: The ID of the product
        
    Returns:
        Tuple[str, str]: (imageUrl, thumbnailUrl)
    """
    # Generate a unique filename
    file_extension = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ".jpg"
    filename = f"{product_id}_{uuid.uuid4()}{file_extension}"
    
    # Save the original image
    file_path = f"{IMAGES_DIR}/{filename}"
    with open(file_path, "wb") as f:
        # Read in chunks to handle large files
        content = await upload_file.read()
        f.write(content)
    
    # Create and save thumbnail
    await create_thumbnail(file_path, filename)
    
    # Return URLs (relative to static dir for web serving)
    return f"/static/images/{filename}", f"/static/images/thumbnails/{filename}"

async def create_thumbnail(original_path: str, filename: str, size: Tuple[int, int] = (200, 200)) -> str:
    """
    Create a thumbnail from the original image
    
    Args:
        original_path: Path to the original image
        filename: Filename for the thumbnail
        size: Size of the thumbnail (width, height)
        
    Returns:
        Path to the created thumbnail
    """
    thumbnail_path = f"{THUMBNAILS_DIR}/{filename}"
    
    # Process image with Pillow
    with Image.open(original_path) as img:
        # Create a thumbnail
        img.thumbnail(size)
        img.save(thumbnail_path)
    
    return thumbnail_path

async def get_or_create_thumbnail(image_path: str) -> str:
    """
    Get a thumbnail for an image, creating it if it doesn't exist.
    
    Args:
        image_path: Path to the original image
        
    Returns:
        Path to the thumbnail (URL for web serving)
    """
    # Convert from URL to file path if needed
    if image_path.startswith("/static/"):
        file_path = f"app{image_path}"
    else:
        file_path = image_path
        image_path = f"/static/images/{os.path.basename(image_path)}"
    
    # Check if this is a valid image path
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return "/static/images/thumbnails/placeholder.jpg"
    
    # Get filename and check if thumbnail exists
    filename = os.path.basename(file_path)
    thumbnail_path = f"{THUMBNAILS_DIR}/{filename}"
    thumbnail_url = f"/static/images/thumbnails/{filename}"
    
    # If thumbnail doesn't exist, create it
    if not os.path.exists(thumbnail_path):
        await create_thumbnail(file_path, filename)
    
    return thumbnail_url

async def delete_image(image_url: str, thumbnail_url: str) -> bool:
    """
    Delete image files from the local filesystem
    
    Args:
        image_url: URL of the image to delete
        thumbnail_url: URL of the thumbnail to delete
        
    Returns:
        True if successful, False otherwise
    """
    # Remove "/static" prefix to get local path
    image_path = f"app/{image_url[1:]}" if image_url.startswith("/static") else f"app/static/{image_url}"
    thumbnail_path = f"app/{thumbnail_url[1:]}" if thumbnail_url.startswith("/static") else f"app/static/{thumbnail_url}"
    
    # Delete files if they exist
    success = True
    
    if os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception:
            success = False
    
    if os.path.exists(thumbnail_path):
        try:
            os.remove(thumbnail_path)
        except Exception:
            success = False
    
    return success 