from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, computed_field

class Category(BaseModel):
    name: str = Field(..., min_length=2, description="The category name")
    sub_category: Optional[str] = Field(None, min_length=2, description="The sub-category name")

class PriceDetails(BaseModel):
    price: float = Field(..., gt=0, description="The base price of the product, must be greater than 0")
    discount_percentage: float = Field(0.0, ge=0.0, le=100.0, description="Discount percentage, between 0 and 100")
    tax_rate: float = Field(0.0, ge=0.0, le=100.0, description="Tax rate, between 0 and 100")

class Inventory(BaseModel):
    quantity: int = Field(..., ge=0, description="The stock quantity, must be greater than or equal to 0")
    low_stock_threshold: int = Field(5, gt=0, description="Threshold below which inventory is considered low")

class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="The name of the product")
    description: str = Field(..., min_length=10, max_length=1000, description="Description of the product")
    category: Category
    price_details: PriceDetails
    inventory: Inventory
    tags: List[str] = Field(default=[], description="List of tags associated with the product")

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        cleaned_tags = []
        for tag in v:
            tag_stripped = tag.strip().lower()
            if not tag_stripped:
                raise ValueError("Tags cannot contain empty strings")
            if tag_stripped not in cleaned_tags:
                cleaned_tags.append(tag_stripped)
        return cleaned_tags

class ProductCreate(ProductBase):
    @model_validator(mode='after')
    def validate_product_create(self) -> 'ProductCreate':
        if self.category.sub_category and self.category.name.lower() == self.category.sub_category.lower():
            raise ValueError("Category and sub-category names cannot be identical")
        return self

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    category: Optional[Category] = None
    price_details: Optional[PriceDetails] = None
    inventory: Optional[Inventory] = None
    tags: Optional[List[str]] = None

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        cleaned_tags = []
        for tag in v:
            tag_stripped = tag.strip().lower()
            if not tag_stripped:
                raise ValueError("Tags cannot contain empty strings")
            if tag_stripped not in cleaned_tags:
                cleaned_tags.append(tag_stripped)
        return cleaned_tags

    @model_validator(mode='after')
    def validate_product_update(self) -> 'ProductUpdate':
        # If both category and sub_category are updated, check them
        if self.category and self.category.sub_category:
            if self.category.name.lower() == self.category.sub_category.lower():
                raise ValueError("Category and sub-category names cannot be identical")
        return self

class ProductResponse(ProductBase):
    id: str = Field(..., description="Unique product identifier (UUID)")
    created_at: datetime = Field(..., description="Timestamp of when the product was created")
    updated_at: datetime = Field(..., description="Timestamp of when the product was last updated")

    @computed_field
    @property
    def final_price(self) -> float:
        price = self.price_details.price
        discount = self.price_details.discount_percentage
        tax = self.price_details.tax_rate
        discounted_price = price * (1 - (discount / 100))
        final = discounted_price * (1 + (tax / 100))
        return round(final, 2)

    @computed_field
    @property
    def is_low_stock(self) -> bool:
        return self.inventory.quantity <= self.inventory.low_stock_threshold
