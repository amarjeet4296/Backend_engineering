from fastapi import APIRouter, HTTPException, status, Body, UploadFile, File, Form
from typing import Union, List, Dict, Any
from uuid import UUID
import uuid

from app.models.popup import PopupResponse, ProductPopupDetail, ImagePopupDetail
from app.services import db, blob_storage

router = APIRouter()

@router.get("/product/{product_id}", response_model=PopupResponse)
async def get_product_popup(product_id: Union[int, UUID]):
    """
    Get popup data for a product.
    This endpoint retrieves all the data needed to display a product detail popup.
    """
    # Check if product exists
    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Get product images
    images = await db.get_images_by_product(product_id)
    
    # Find primary image or use first image
    main_image = next((img for img in images if img.isPrimary), images[0] if images else None)
    
    # Get additional images (excluding the main one)
    additional_images = []
    if main_image and images:
        additional_images = [img.imageUrl for img in images if img.id != main_image.id]
    
    # Create popup detail object
    product_popup = ProductPopupDetail(
        title=f"Product: {product.name}",
        product_id=product.id,
        description=product.description,
        price=product.price,
        image_url=main_image.imageUrl if main_image else None,
        thumbnail_url=main_image.thumbnailUrl if main_image else None,
        additional_images=additional_images
    )
    
    # Generate a unique popup ID
    popup_id = f"popup-{uuid.uuid4().hex[:8]}"
    
    return PopupResponse(
        popup_id=popup_id,
        popup_type="product",
        data=product_popup
    )

@router.get("/image/{image_id}", response_model=PopupResponse)
async def get_image_popup(image_id: Union[int, UUID]):
    """
    Get popup data for a specific image.
    This endpoint retrieves all the data needed to display an image detail popup.
    """
    # Check if image exists
    image = await db.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    # Get product details
    product = await db.get_product(image.productId)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {image.productId} not found"
        )
    
    # Create image popup detail object
    image_popup = ImagePopupDetail(
        title=f"{product.name} - Image",
        product_id=product.id,
        image_url=image.imageUrl,
        alt_text=product.name,
        is_primary=image.isPrimary,
        image_type=image.imageType
    )
    
    # Generate a unique popup ID
    popup_id = f"popup-{uuid.uuid4().hex[:8]}"
    
    return PopupResponse(
        popup_id=popup_id,
        popup_type="image",
        data=image_popup
    )

@router.get("/product/{product_id}/full", response_model=List[PopupResponse])
async def get_all_product_image_popups(product_id: Union[int, UUID]):
    """
    Get popup data for all images of a product.
    This endpoint retrieves all the data needed to display a gallery of image popups.
    """
    # Check if product exists
    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Get product images
    images = await db.get_images_by_product(product_id)
    if not images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No images found for product with ID {product_id}"
        )
    
    # Create response with a popup for each image
    popups = []
    for idx, image in enumerate(images):
        image_popup = ImagePopupDetail(
            title=f"{product.name} - Image {idx+1}",
            product_id=product.id,
            image_url=image.imageUrl,
            alt_text=f"{product.name} - View {idx+1}",
            is_primary=image.isPrimary,
            image_type=image.imageType
        )
        
        # Generate a unique popup ID
        popup_id = f"popup-{uuid.uuid4().hex[:8]}"
        
        popups.append(
            PopupResponse(
                popup_id=popup_id,
                popup_type="image",
                data=image_popup
            )
        )
    
    return popups

@router.put("/product/{product_id}/save", status_code=status.HTTP_200_OK)
async def save_popup_changes(product_id: Union[int, UUID], changes: Dict[str, Any] = Body(...)):
    """
    Save changes made in a popup to the database.
    This endpoint receives the changes made in a popup and updates the database accordingly.
    
    The changes object can contain:
    - product_changes: Changes to the product properties
    - image_changes: Changes to image properties (including primary status, order, etc.)
    """
    # Check if product exists
    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Process product changes if any
    product_updated = False
    if "product_changes" in changes and changes["product_changes"]:
        product_data = changes["product_changes"]
        product_update = {}
        
        # Only include fields that are specified in the changes
        if "name" in product_data:
            product_update["name"] = product_data["name"]
        if "description" in product_data:
            product_update["description"] = product_data["description"]
        if "price" in product_data:
            product_update["price"] = float(product_data["price"])
        
        # Only update if there are changes
        if product_update:
            updated_product = await db.update_product(product_id, product_update)
            if not updated_product:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update product"
                )
            product_updated = True
    
    # Process image changes if any
    images_updated = False
    if "image_changes" in changes and changes["image_changes"]:
        image_updates = changes["image_changes"]
        
        for image_id, image_data in image_updates.items():
            # Get the image to verify it exists and belongs to this product
            image = await db.get_image(image_id)
            if not image or str(image.productId) != str(product_id):
                continue  # Skip if image doesn't exist or doesn't belong to this product
            
            image_update = {}
            
            # Process image changes
            if "is_primary" in image_data:
                image_update["isPrimary"] = image_data["is_primary"]
                
                # If setting this image as primary, make sure other images are not primary
                if image_data["is_primary"]:
                    # Get all other images for this product
                    product_images = await db.get_images_by_product(product_id)
                    for other_image in product_images:
                        if str(other_image.id) != str(image_id) and other_image.isPrimary:
                            # Update other image to not be primary
                            await db.update_image(other_image.id, {"isPrimary": False})
            
            if "image_type" in image_data:
                image_update["imageType"] = image_data["image_type"]
                
            if "alt_text" in image_data:
                image_update["altText"] = image_data["alt_text"]
            
            # Apply the updates
            if image_update:
                updated_image = await db.update_image(image_id, image_update)
                if updated_image:
                    images_updated = True
    
    # Return success message with details about what was updated
    return {
        "message": "Popup changes saved successfully",
        "product_updated": product_updated,
        "images_updated": images_updated,
        "product_id": str(product_id)
    }

@router.post("/product/{product_id}/image", status_code=status.HTTP_201_CREATED)
async def add_image_from_popup(
    product_id: Union[int, UUID],
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    image_type: str = Form("main"),
    alt_text: str = Form(None)
):
    """
    Add a new image to a product from the popup interface.
    This endpoint handles file uploads within the popup context.
    """
    # Check if product exists
    product = await db.get_product(product_id)
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
        
        # If this is set as primary, update all other images to not be primary
        if is_primary:
            product_images = await db.get_images_by_product(product_id)
            for other_image in product_images:
                if other_image.isPrimary:
                    await db.update_image(other_image.id, {"isPrimary": False})
        
        # Create image record in database with alt text if provided
        from app.models.image import ImageCreate
        image_create = ImageCreate(
            productId=product_id,
            isPrimary=is_primary,
            imageType=image_type
        )
        
        new_image = await db.create_image(image_create, image_url, thumbnail_url)
        
        # If alt text was provided, update the image with it
        if alt_text and new_image:
            await db.update_image(new_image.id, {"altText": alt_text})
            new_image = await db.get_image(new_image.id)  # Refresh image data
        
        # Generate popup response for the new image
        # Generate a unique popup ID
        popup_id = f"popup-{uuid.uuid4().hex[:8]}"
        
        # Create image popup detail object
        image_popup = ImagePopupDetail(
            title=f"{product.name} - New Image",
            product_id=product.id,
            image_url=new_image.imageUrl,
            alt_text=alt_text or product.name,
            is_primary=is_primary,
            image_type=image_type
        )
        
        return PopupResponse(
            popup_id=popup_id,
            popup_type="image",
            data=image_popup
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding image: {str(e)}"
        )

@router.put("/product/{product_id}/image/{image_id}", status_code=status.HTTP_200_OK)
async def update_image_properties(
    product_id: int,
    image_id: int,
    alt_text: str = Form(...),
    image_type: str = Form(...),
    is_primary: bool = Form(False)
):
    # Check if product exists
    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Check if image exists
    image = await db.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    # Check if image belongs to product
    if image.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image does not belong to this product"
        )
    
    # Update image in database
    image_update = {
        "alt_text": alt_text,
        "image_type": image_type,
        "is_primary": is_primary
    }
    
    # If this image is being set as primary, update other images of this product
    if is_primary:
        await db.reset_primary_images(product_id, image_id)
    
    updated_image = await db.update_image(image_id, image_update)
    
    # Generate a unique popup ID
    popup_id = f"popup-{uuid.uuid4()}"
    
    # Prepare the popup data
    popup_data = ImagePopupDetail(
        id=image_id,
        product_id=product_id,
        url=updated_image.url,
        thumbnail_url=updated_image.thumbnail_url,
        alt_text=updated_image.alt_text,
        image_type=updated_image.image_type,
        is_primary=updated_image.is_primary,
        product_name=product.name
    )
    
    return {"message": "Image updated successfully.", "popup_id": popup_id, "popup_data": popup_data.dict()}

@router.delete("/product/{product_id}/image/{image_id}", status_code=status.HTTP_200_OK)
async def delete_image_from_popup(product_id: int, image_id: int):
    # Check if product exists
    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Check if image exists
    image = await db.get_image(image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID {image_id} not found"
        )
    
    # Check if image belongs to product
    if image.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image does not belong to this product"
        )
    
    # Get image URL to delete from storage
    image_url = image.url
    thumbnail_url = image.thumbnail_url
    
    # Delete image from database
    success = await db.delete_image(image_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image from database"
        )
    
    # Delete image file from storage
    try:
        await blob_storage.delete_image(image_url)
        if thumbnail_url:
            await blob_storage.delete_image(thumbnail_url)
    except Exception as e:
        # If image deletion from storage fails, log the error but continue
        # The database record is already deleted
        print(f"Failed to delete image file: {str(e)}")
    
    # If the deleted image was primary, set another image as primary if available
    if image.is_primary:
        # Get remaining images for this product
        images = await db.get_images_by_product(product_id)
        if images:
            # Set the first remaining image as primary
            await db.update_image(images[0].id, {"is_primary": True})
    
    return {"message": "Image deleted successfully"}

@router.get("/image/{image_id}", status_code=status.HTTP_200_OK)
async def get_image_popup(image_id: int, product_id: int = None):
    """
    Get details for an image to display in a popup.
    """
    try:
        # Get image details
        image = await db.get_image(image_id)
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found"
            )
        
        # Verify image belongs to product if product_id is provided
        if product_id and image.product_id != product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image does not belong to this product"
            )
        
        # Get product details
        product = await db.get_product(image.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {image.product_id} not found"
            )
        
        # Generate a unique popup ID
        popup_id = f"popup-{uuid.uuid4()}"
        
        # Prepare the popup data
        popup_data = ImagePopupDetail(
            id=image.id,
            product_id=image.product_id,
            url=image.url,
            thumbnail_url=image.thumbnail_url,
            alt_text=image.alt_text,
            image_type=image.image_type,
            is_primary=image.is_primary,
            product_name=product.name
        )
        
        return {"popup_id": popup_id, "popup_data": popup_data.dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving image: {str(e)}"
        ) 