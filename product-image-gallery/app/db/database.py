from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import models

async def reset_primary_images(product_id: int, exclude_image_id: int = None):
    """
    Reset is_primary flag to False for all images of a product except the excluded one.
    
    Args:
        product_id (int): The ID of the product
        exclude_image_id (int, optional): The ID of the image to exclude from reset
        
    Returns:
        bool: True if successful
    """
    try:
        async with get_session() as session:
            # Find all images for this product except the excluded one
            query = select(models.Image).where(
                and_(
                    models.Image.product_id == product_id,
                    models.Image.is_primary == True
                )
            )
            
            if exclude_image_id:
                query = query.where(models.Image.id != exclude_image_id)
                
            result = await session.execute(query)
            images = result.scalars().all()
            
            # Set is_primary to False for all found images
            for image in images:
                image.is_primary = False
                session.add(image)
            
            await session.commit()
            return True
    except Exception as e:
        print(f"Error resetting primary images: {str(e)}")
        return False 