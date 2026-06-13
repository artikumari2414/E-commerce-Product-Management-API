import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.json_db import JSONDatabase
from app.middleware.process_time import ProcessTimeMiddleware
from app.routers.products import router as products_router

def init_sample_data(db: JSONDatabase):
    """Pre-populates the database with sample products if it is empty."""
    if len(db.read_all()) > 0:
        return

    now = datetime.now(timezone.utc).isoformat()
    sample_products = [
        {
            "id": str(uuid.uuid4()),
            "name": "iPhone 15 Pro",
            "description": "Apple's latest flagship smartphone with titanium design and A17 Pro chip.",
            "category": {
                "name": "Electronics",
                "sub_category": "Smartphones"
            },
            "price_details": {
                "price": 999.99,
                "discount_percentage": 10.0,
                "tax_rate": 8.0
            },
            "inventory": {
                "quantity": 15,
                "low_stock_threshold": 5
            },
            "tags": ["phone", "apple", "ios", "electronics"],
            "created_at": now,
            "updated_at": now
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Sony WH-1000XM5",
            "description": "Industry-leading noise-canceling wireless over-ear headphones with superior audio.",
            "category": {
                "name": "Electronics",
                "sub_category": "Audio"
            },
            "price_details": {
                "price": 399.99,
                "discount_percentage": 15.0,
                "tax_rate": 5.0
            },
            "inventory": {
                "quantity": 3,
                "low_stock_threshold": 5
            },
            "tags": ["audio", "headphones", "sony", "electronics"],
            "created_at": now,
            "updated_at": now
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Ergonomic Office Chair",
            "description": "High-back mesh office chair with lumbar support and 3D adjustable armrests.",
            "category": {
                "name": "Furniture",
                "sub_category": "Office"
            },
            "price_details": {
                "price": 249.99,
                "discount_percentage": 0.0,
                "tax_rate": 10.0
            },
            "inventory": {
                "quantity": 25,
                "low_stock_threshold": 8
            },
            "tags": ["furniture", "office", "chair", "ergonomic"],
            "created_at": now,
            "updated_at": now
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Hydro Flask Water Bottle",
            "description": "Double-wall vacuum insulated stainless steel water bottle with wide mouth leakproof cap.",
            "category": {
                "name": "Home & Kitchen",
                "sub_category": "Drinkware"
            },
            "price_details": {
                "price": 45.0,
                "discount_percentage": 5.0,
                "tax_rate": 0.0
            },
            "inventory": {
                "quantity": 0,
                "low_stock_threshold": 5
            },
            "tags": ["bottle", "kitchen", "water", "hydroflask"],
            "created_at": now,
            "updated_at": now
        }
    ]
    db.write_all(sample_products)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup behavior: initialize database settings and sample products
    from app.dependencies import db_instance
    init_sample_data(db_instance)
    yield
    # Shutdown behavior: optional cleanups can go here

app = FastAPI(
    title=settings.app_name,
    description="Backend E-commerce Product Management API with FastAPI and Pydantic validation.",
    version="1.0.0",
    lifespan=lifespan
)

# Standard CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom request timing middleware
app.add_middleware(ProcessTimeMiddleware)

# Include routes under versioned prefix
app.include_router(products_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
def root_route():
    return {
        "message": f"Welcome to the {settings.app_name}!",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
