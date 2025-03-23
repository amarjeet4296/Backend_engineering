from fastapi import APIRouter, HTTPException, status, Body
from typing import List, Union
from uuid import UUID

from app.models.product import Product, ProductCreate, ProductUpdate
from app.services import db

router = APIRouter()

@router.get("/", response_model=List[Product])
async def get_all_products():
    """
    Get all products
    """
    return await db.get_all_products()

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: Union[int, UUID]):
    """
    Get a single product by ID
    """
    product = await db.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return product

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate):
    """
    Create a new product
    """
    return await db.create_product(product)

@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: Union[int, UUID], product_update: ProductUpdate):
    """
    Update a product - this is what will happen when user edits in the popup
    """
    updated_product = await db.update_product(product_id, product_update)
    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return updated_product

@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product_id: Union[int, UUID]):
    """
    Delete a product
    """
    success = db.delete_product(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    return {"message": "Product deleted successfully"} 