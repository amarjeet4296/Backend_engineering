from datetime import datetime
from typing import Dict, List, Optional, Union
from uuid import UUID
import uuid

from app.models.product import Product, ProductCreate, ProductUpdate
from app.models.image import Image, ImageCreate, ImageUpdate
from app.services import blob_storage

# Mock database - in-memory data
# In a real application, this would be replaced with a real database

# Products database
products_db: List[Product] = [
    Product(
        id=1,
        name="Product 1",
        description="This is product 1",
        price=19.99,
        imageUrl="/static/images/product1.jpg",
        thumbnailUrl="/static/images/thumbnails/product1.jpg",
        created_at=datetime.now(),
        updated_at=datetime.now()
    ),
    Product(
        id=2,
        name="Product 2",
        description="This is product 2",
        price=29.99,
        imageUrl="/static/images/product2.jpg",
        thumbnailUrl="/static/images/thumbnails/product2.jpg",
        created_at=datetime.now(),
        updated_at=datetime.now()
    ),
    Product(
        id=3,
        name="Product 3",
        description="This is product 3",
        price=39.99,
        imageUrl="/static/images/product3.jpg",
        thumbnailUrl="/static/images/thumbnails/product3.jpg",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
]

# Images database
images_db: List[Image] = [
    Image(
        id=1,
        productId=1,
        imageUrl="/static/images/product1.jpg",
        thumbnailUrl="/static/images/thumbnails/product1.jpg",
        isPrimary=True,
        imageType="main",
        created_at=datetime.now(),
        updated_at=datetime.now()
    ),
    Image(
        id=2,
        productId=2,
        imageUrl="/static/images/product2.jpg",
        thumbnailUrl="/static/images/thumbnails/product2.jpg",
        isPrimary=True,
        imageType="main",
        created_at=datetime.now(),
        updated_at=datetime.now()
    ),
    Image(
        id=3,
        productId=3,
        imageUrl="/static/images/product3.jpg",
        thumbnailUrl="/static/images/thumbnails/product3.jpg",
        isPrimary=True,
        imageType="main",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
]

# Product service functions
async def get_all_products() -> List[Product]:
    # Ensure thumbnails exist for all products
    for product in products_db:
        if not product.thumbnailUrl or product.thumbnailUrl == "/static/images/thumbnails/placeholder.jpg":
            # Generate thumbnail if it doesn't exist
            product.thumbnailUrl = await blob_storage.get_or_create_thumbnail(product.imageUrl)
    return products_db

async def get_product(product_id: Union[int, UUID]) -> Optional[Product]:
    for product in products_db:
        if product.id == product_id:
            # Generate thumbnail if it doesn't exist
            if not product.thumbnailUrl or product.thumbnailUrl == "/static/images/thumbnails/placeholder.jpg":
                product.thumbnailUrl = await blob_storage.get_or_create_thumbnail(product.imageUrl)
            return product
    return None

async def create_product(product: ProductCreate) -> Product:
    # Set default image if none provided
    image_url = product.imageUrl or "/static/images/placeholder.jpg"
    
    # Generate thumbnail if needed
    thumbnail_url = product.thumbnailUrl
    if not thumbnail_url or thumbnail_url == "/static/images/thumbnails/placeholder.jpg":
        thumbnail_url = await blob_storage.get_or_create_thumbnail(image_url)
    
    # Create new product
    new_product = Product(
        id=len(products_db) + 1 if isinstance(products_db[0].id, int) else uuid.uuid4(),
        name=product.name,
        description=product.description,
        price=product.price,
        imageUrl=image_url,
        thumbnailUrl=thumbnail_url,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    products_db.append(new_product)
    return new_product

async def update_product(product_id: Union[int, UUID], product_update: ProductUpdate) -> Optional[Product]:
    for i, product in enumerate(products_db):
        if product.id == product_id:
            # Update fields if they are provided
            update_data = product_update.dict(exclude_unset=True)
            
            # If image URL is updated, generate new thumbnail
            if "imageUrl" in update_data and update_data["imageUrl"]:
                update_data["thumbnailUrl"] = await blob_storage.get_or_create_thumbnail(update_data["imageUrl"])
            
            updated_product = product.copy(update=update_data)
            updated_product.updated_at = datetime.now()
            products_db[i] = updated_product
            return updated_product
    return None

def delete_product(product_id: Union[int, UUID]) -> bool:
    global products_db
    product = get_product(product_id)
    if product:
        products_db = [p for p in products_db if p.id != product_id]
        return True
    return False

# Image service functions
async def get_images_by_product(product_id: Union[int, UUID]) -> List[Image]:
    images = [image for image in images_db if image.productId == product_id]
    
    # Ensure thumbnails exist for all images
    for image in images:
        if not image.thumbnailUrl or image.thumbnailUrl == "/static/images/thumbnails/placeholder.jpg":
            image.thumbnailUrl = await blob_storage.get_or_create_thumbnail(image.imageUrl)
    
    return images

async def get_image(image_id: Union[int, UUID]) -> Optional[Image]:
    for image in images_db:
        if image.id == image_id:
            # Generate thumbnail if it doesn't exist
            if not image.thumbnailUrl or image.thumbnailUrl == "/static/images/thumbnails/placeholder.jpg":
                image.thumbnailUrl = await blob_storage.get_or_create_thumbnail(image.imageUrl)
            return image
    return None

async def create_image(image: ImageCreate, image_url: str, thumbnail_url: str = None) -> Image:
    # Generate thumbnail if not provided
    if not thumbnail_url:
        thumbnail_url = await blob_storage.get_or_create_thumbnail(image_url)
    
    # Create new image
    new_image = Image(
        id=len(images_db) + 1 if isinstance(images_db[0].id, int) else uuid.uuid4(),
        productId=image.productId,
        imageUrl=image_url,
        thumbnailUrl=thumbnail_url,
        isPrimary=image.isPrimary,
        imageType=image.imageType,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    images_db.append(new_image)
    
    # If this is a primary image, update the product
    if image.isPrimary:
        product = await get_product(image.productId)
        if product:
            await update_product(image.productId, ProductUpdate(
                imageUrl=image_url,
                thumbnailUrl=thumbnail_url
            ))
    
    return new_image

async def update_image(image_id: Union[int, UUID], image_update: ImageUpdate) -> Optional[Image]:
    for i, image in enumerate(images_db):
        if image.id == image_id:
            # Update fields if they are provided
            update_data = image_update.dict(exclude_unset=True)
            
            # If image URL is updated, generate new thumbnail
            if "imageUrl" in update_data and update_data["imageUrl"]:
                update_data["thumbnailUrl"] = await blob_storage.get_or_create_thumbnail(update_data["imageUrl"])
            
            updated_image = image.copy(update=update_data)
            updated_image.updated_at = datetime.now()
            images_db[i] = updated_image
            
            # If this is now a primary image, update the product
            if updated_image.isPrimary:
                product = await get_product(updated_image.productId)
                if product:
                    await update_product(updated_image.productId, ProductUpdate(
                        imageUrl=updated_image.imageUrl,
                        thumbnailUrl=updated_image.thumbnailUrl
                    ))
            
            return updated_image
    return None

def delete_image(image_id: Union[int, UUID]) -> bool:
    global images_db
    image = get_image(image_id)
    if image:
        images_db = [img for img in images_db if img.id != image_id]
        return True
    return False 