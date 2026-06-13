from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, Query, status
from app.schemas.products import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService
from app.dependencies import get_product_service

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    service: ProductService = Depends(get_product_service)
):
    return service.create_product(product)

@router.get("/", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = Query(None, description="Search in product name and description"),
    category: Optional[str] = Query(None, description="Filter by category name or sub-category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum final price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum final price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    tags: Optional[List[str]] = Query(None, description="Filter by matching tags"),
    sort_by: Optional[Literal["name", "price", "final_price", "created_at", "quantity"]] = Query(None, description="Sort by field"),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(10, ge=1, le=100, description="Limit for pagination"),
    service: ProductService = Depends(get_product_service)
):
    return service.list_products(
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    )

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    service: ProductService = Depends(get_product_service)
):
    return service.get_product_by_id(product_id)

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    product: ProductUpdate,
    service: ProductService = Depends(get_product_service)
):
    return service.update_product(product_id, product)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    service: ProductService = Depends(get_product_service)
):
    service.delete_product(product_id)
