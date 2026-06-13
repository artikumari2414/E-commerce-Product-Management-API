import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from app.database.json_db import JSONDatabase
from app.schemas.products import ProductCreate, ProductUpdate, ProductResponse, Category, PriceDetails, Inventory
from app.exceptions import ProductNotFoundException, ProductAlreadyExistsException

class ProductService:
    def __init__(self, db: JSONDatabase):
        self.db = db

    def create_product(self, product_in: ProductCreate) -> ProductResponse:
        products_data = self.db.read_all()
        
        # Check if name already exists (case-insensitive duplicate check)
        name_lower = product_in.name.lower().strip()
        for p in products_data:
            if p.get("name", "").lower().strip() == name_lower:
                raise ProductAlreadyExistsException(product_in.name)

        now = datetime.now(timezone.utc)
        product_id = str(uuid.uuid4())
        
        # Dump to dictionary, then add id and timestamps
        product_dict = product_in.model_dump()
        product_dict.update({
            "id": product_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        })

        products_data.append(product_dict)
        self.db.write_all(products_data)

        # Validate to return ProductResponse (which computes final_price, is_low_stock, etc.)
        return ProductResponse.model_validate(product_dict)

    def get_product_by_id(self, product_id: str) -> ProductResponse:
        products_data = self.db.read_all()
        for p in products_data:
            if p.get("id") == product_id:
                return ProductResponse.model_validate(p)
        raise ProductNotFoundException(product_id)

    def update_product(self, product_id: str, product_in: ProductUpdate) -> ProductResponse:
        products_data = self.db.read_all()
        
        product_idx = -1
        for idx, p in enumerate(products_data):
            if p.get("id") == product_id:
                product_idx = idx
                break
        
        if product_idx == -1:
            raise ProductNotFoundException(product_id)

        existing_data = products_data[product_idx]
        existing_model = ProductResponse.model_validate(existing_data)

        # Check name conflict
        if product_in.name is not None:
            name_lower = product_in.name.lower().strip()
            if name_lower != existing_model.name.lower().strip():
                for p in products_data:
                    if p.get("id") != product_id and p.get("name", "").lower().strip() == name_lower:
                        raise ProductAlreadyExistsException(product_in.name)

        # Extract only updated fields
        update_data = product_in.model_dump(exclude_unset=True)
        
        # Explicitly handle nested objects to perform a deep merge
        if product_in.category is not None:
            existing_cat = existing_model.category
            new_cat_data = product_in.category.model_dump(exclude_unset=True)
            updated_cat = existing_cat.model_copy(update=new_cat_data)
            update_data["category"] = updated_cat.model_dump()
            
        if product_in.price_details is not None:
            existing_price = existing_model.price_details
            new_price_data = product_in.price_details.model_dump(exclude_unset=True)
            updated_price = existing_price.model_copy(update=new_price_data)
            update_data["price_details"] = updated_price.model_dump()

        if product_in.inventory is not None:
            existing_inv = existing_model.inventory
            new_inv_data = product_in.inventory.model_dump(exclude_unset=True)
            updated_inv = existing_inv.model_copy(update=new_inv_data)
            update_data["inventory"] = updated_inv.model_dump()

        # Update timestamps
        now = datetime.now(timezone.utc)
        update_data["updated_at"] = now.isoformat()

        # Merge update_data into existing_data dict
        merged_dict = {**existing_data, **update_data}
        products_data[product_idx] = merged_dict
        self.db.write_all(products_data)

        return ProductResponse.model_validate(merged_dict)

    def delete_product(self, product_id: str) -> None:
        products_data = self.db.read_all()
        for idx, p in enumerate(products_data):
            if p.get("id") == product_id:
                products_data.pop(idx)
                self.db.write_all(products_data)
                return
        raise ProductNotFoundException(product_id)

    def list_products(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        skip: int = 0,
        limit: int = 10
    ) -> List[ProductResponse]:
        products_data = self.db.read_all()
        products = [ProductResponse.model_validate(p) for p in products_data]

        # Apply Filters
        if search:
            search_lower = search.lower().strip()
            products = [
                p for p in products 
                if search_lower in p.name.lower() or search_lower in p.description.lower()
            ]

        if category:
            category_lower = category.lower().strip()
            products = [
                p for p in products 
                if p.category.name.lower() == category_lower or 
                (p.category.sub_category and p.category.sub_category.lower() == category_lower)
            ]

        if min_price is not None:
            products = [p for p in products if p.final_price >= min_price]

        if max_price is not None:
            products = [p for p in products if p.final_price <= max_price]

        if in_stock is not None:
            if in_stock:
                products = [p for p in products if p.inventory.quantity > 0]
            else:
                products = [p for p in products if p.inventory.quantity == 0]

        if tags:
            query_tags = [t.strip().lower() for t in tags if t.strip()]
            if query_tags:
                products = [
                    p for p in products 
                    if all(t in p.tags for t in query_tags)
                ]

        # Apply Sorting
        if sort_by:
            reverse = (sort_order.lower() == "desc")
            if sort_by == "name":
                products.sort(key=lambda p: p.name.lower(), reverse=reverse)
            elif sort_by == "price":
                products.sort(key=lambda p: p.price_details.price, reverse=reverse)
            elif sort_by == "final_price":
                products.sort(key=lambda p: p.final_price, reverse=reverse)
            elif sort_by == "created_at":
                products.sort(key=lambda p: p.created_at, reverse=reverse)
            elif sort_by == "quantity":
                products.sort(key=lambda p: p.inventory.quantity, reverse=reverse)

        # Pagination
        return products[skip:skip+limit]
