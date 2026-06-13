from fastapi import Depends
from app.database.json_db import JSONDatabase
from app.services.product_service import ProductService

# Singleton database instance
db_instance = JSONDatabase()

def get_db() -> JSONDatabase:
    return db_instance

def get_product_service(db: JSONDatabase = Depends(get_db)) -> ProductService:
    return ProductService(db)
