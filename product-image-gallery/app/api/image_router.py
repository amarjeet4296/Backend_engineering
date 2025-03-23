from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Depends
from typing import List, Union, Optional
from uuid import UUID

from app.models.image import Image, ImageCreate, ImageUpdate, ImageUpload
from app.services import db, blob_storage

router = APIRouter()

@router.get("/product/{product_id}", response_model=List[Image])
async def get_product_images(product_id: Union[int, UUID]):
    """
    Get all images for a product
    """
    # Check if product exists
    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    return await db.get_images_by_product(product_id)

@router.get("/{image_id}", response_model=Image)
async def get_image(image_id: Union[int, UUID]):
    """
    Get a single image by ID
    """
    image = await db.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    return image

@router.post("/upload", response_model=ImageUpload, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    product_id: str = Form(...),
    is_primary: bool = Form(False),
    image_type: str = Form("main")
):
    """
    Upload an image for a product.
    The image will be stored in the local filesystem.
    """
    # Check if product exists
    product = await db.get_product(int(product_id) if product_id.isdigit() else product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Check if file is an image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not an image"
        )
    
    try:
        # Save image locally
        image_url, thumbnail_url = await blob_storage.save_image_locally(file, product_id)
        
        # Create image record in database
        image_create = ImageCreate(
            productId=int(product_id) if product_id.isdigit() else product_id,
            isPrimary=is_primary,
            imageType=image_type
        )
        
        await db.create_image(image_create, image_url, thumbnail_url)
        
        return ImageUpload(imageUrl=image_url, thumbnailUrl=thumbnail_url)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image: {str(e)}"
        )

@router.put("/{image_id}", response_model=Image)
async def update_image(image_id: Union[int, UUID], image_update: ImageUpdate):
    """
    Update image details
    """
    updated_image = await db.update_image(image_id, image_update)
    if not updated_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    return updated_image

@router.delete("/{image_id}", status_code=status.HTTP_200_OK)
async def delete_image(image_id: Union[int, UUID]):
    """
    Delete an image
    """
    # Get image before deletion
    image = await db.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    # Delete from storage
    await blob_storage.delete_image(image.imageUrl, image.thumbnailUrl)
    
    # Delete from database
    success = db.delete_image(image_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting image"
        )
    
    return {"message": "Image deleted successfully"} 