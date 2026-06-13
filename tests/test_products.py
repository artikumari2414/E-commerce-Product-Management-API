import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.dependencies import db_instance

# Override database file path for tests
TEST_DB_FILE = "data/test_products.json"

@pytest.fixture(autouse=True)
def setup_test_db():
    # Store original file path
    original_path = settings.data_file_path
    
    # Override
    settings.data_file_path = TEST_DB_FILE
    db_instance.file_path = settings.absolute_data_file_path
    db_instance._ensure_db_exists()
    
    # Reset/clear DB data for test runs
    db_instance.write_all([])
    
    yield
    
    # Tear down test db file
    if os.path.exists(db_instance.file_path):
        try:
            os.remove(db_instance.file_path)
        except Exception:
            pass
            
    # Restore original path settings
    settings.data_file_path = original_path
    db_instance.file_path = settings.absolute_data_file_path

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs_url" in data

def test_create_product_success():
    payload = {
        "name": "Test iPhone 15",
        "description": "Standard flagship device description with 30 characters.",
        "category": {
            "name": "Electronics",
            "sub_category": "Smartphones"
        },
        "price_details": {
            "price": 1000.0,
            "discount_percentage": 10.0,
            "tax_rate": 8.0
        },
        "inventory": {
            "quantity": 10,
            "low_stock_threshold": 3
        },
        "tags": ["Phone", "Apple", "15"]
    }
    
    response = client.post("/api/v1/products/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test iPhone 15"
    assert data["tags"] == ["phone", "apple", "15"]  # Should be normalized/lowercased
    
    # Verify computed fields
    # final_price: 1000 * (1 - 0.10) * (1 + 0.08) = 900 * 1.08 = 972.0
    assert data["final_price"] == 972.0
    assert data["is_low_stock"] is False
    assert "X-Process-Time" in response.headers

def test_schema_validators():
    # Try invalid name (short) and invalid price (<= 0)
    payload = {
        "name": "ab",  # Too short (min 3)
        "description": "short",  # Too short (min 10)
        "category": {
            "name": "e",  # Too short (min 2)
            "sub_category": None
        },
        "price_details": {
            "price": -50.0,  # Invalid
            "discount_percentage": 120.0,  # Invalid (max 100)
            "tax_rate": 5.0
        },
        "inventory": {
            "quantity": -2,  # Invalid
            "low_stock_threshold": 5
        },
        "tags": []
    }
    response = client.post("/api/v1/products/", json=payload)
    assert response.status_code == 422

def test_category_sub_category_identical_validator():
    # Category and sub-category cannot be identical
    payload = {
        "name": "Unique Gadget",
        "description": "This is a description that is long enough.",
        "category": {
            "name": "Electronics",
            "sub_category": "electronics"
        },
        "price_details": {
            "price": 100.0,
            "discount_percentage": 0.0,
            "tax_rate": 0.0
        },
        "inventory": {
            "quantity": 10,
            "low_stock_threshold": 5
        },
        "tags": ["gadget"]
    }
    response = client.post("/api/v1/products/", json=payload)
    assert response.status_code == 422
    assert "Category and sub-category names cannot be identical" in response.text

def test_duplicate_product_name():
    payload = {
        "name": "Duplicate Watch",
        "description": "Some description text that is long enough to pass.",
        "category": {"name": "Watches", "sub_category": None},
        "price_details": {"price": 250.0, "discount_percentage": 0.0, "tax_rate": 0.0},
        "inventory": {"quantity": 10, "low_stock_threshold": 5},
        "tags": ["watch"]
    }
    
    response = client.post("/api/v1/products/", json=payload)
    assert response.status_code == 201
    
    # Try posting again with same name (case-insensitive)
    payload_dup = payload.copy()
    payload_dup["name"] = "  duplicate WATCH  "
    response_dup = client.post("/api/v1/products/", json=payload_dup)
    assert response_dup.status_code == 409
    assert "already exists" in response_dup.json()["detail"]

def test_get_and_delete_product():
    payload = {
        "name": "Product for Deletion",
        "description": "This is another description text that is long enough.",
        "category": {"name": "Home", "sub_category": None},
        "price_details": {"price": 12.50, "discount_percentage": 0.0, "tax_rate": 0.0},
        "inventory": {"quantity": 100, "low_stock_threshold": 5},
        "tags": ["home"]
    }
    res_create = client.post("/api/v1/products/", json=payload)
    prod_id = res_create.json()["id"]
    
    # Get by ID
    res_get = client.get(f"/api/v1/products/{prod_id}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Product for Deletion"
    
    # Delete product
    res_del = client.delete(f"/api/v1/products/{prod_id}")
    assert res_del.status_code == 204
    
    # Get by ID again (404)
    res_get_deleted = client.get(f"/api/v1/products/{prod_id}")
    assert res_get_deleted.status_code == 404

def test_update_product():
    payload = {
        "name": "Initial Product Name",
        "description": "A very suitable and detailed description of the product.",
        "category": {"name": "Sports", "sub_category": "Fitness"},
        "price_details": {"price": 100.0, "discount_percentage": 10.0, "tax_rate": 10.0},
        "inventory": {"quantity": 20, "low_stock_threshold": 5},
        "tags": ["sports", "fitness"]
    }
    res_create = client.post("/api/v1/products/", json=payload)
    prod_id = res_create.json()["id"]
    
    # Update price only
    update_payload = {
        "price_details": {
            "price": 120.0
        }
    }
    res_update = client.put(f"/api/v1/products/{prod_id}", json=update_payload)
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["price_details"]["price"] == 120.0
    # verify nested values are kept/merged (e.g. discount and tax should be kept)
    assert updated_data["price_details"]["discount_percentage"] == 10.0
    assert updated_data["price_details"]["tax_rate"] == 10.0
    # Verify final price is recalculated: 120 * 0.9 * 1.1 = 118.8
    assert updated_data["final_price"] == 118.8
    
    # Verify updated_at is updated
    assert updated_data["updated_at"] > updated_data["created_at"]

def test_list_filtering_and_sorting():
    items = [
        {
            "name": "Leather Shoes",
            "description": "Handcrafted formal leather shoes for men.",
            "category": {"name": "Apparel", "sub_category": "Footwear"},
            "price_details": {"price": 150.0, "discount_percentage": 20.0, "tax_rate": 5.0}, # final = 150 * 0.8 * 1.05 = 126.0
            "inventory": {"quantity": 8, "low_stock_threshold": 10}, # is_low_stock = True
            "tags": ["shoes", "leather", "formal"]
        },
        {
            "name": "Wireless Mouse",
            "description": "Ergonomic bluetooth wireless mouse.",
            "category": {"name": "Electronics", "sub_category": "Accessories"},
            "price_details": {"price": 40.0, "discount_percentage": 0.0, "tax_rate": 0.0}, # final = 40.0
            "inventory": {"quantity": 100, "low_stock_threshold": 5}, # is_low_stock = False
            "tags": ["mouse", "wireless", "electronics"]
        },
        {
            "name": "Leather Wallet",
            "description": "Genuine leather bi-fold wallet for men.",
            "category": {"name": "Apparel", "sub_category": "Accessories"},
            "price_details": {"price": 50.0, "discount_percentage": 10.0, "tax_rate": 10.0}, # final = 50 * 0.9 * 1.1 = 49.5
            "inventory": {"quantity": 0, "low_stock_threshold": 5}, # is_low_stock = True, quantity = 0
            "tags": ["wallet", "leather", "apparel"]
        }
    ]
    for item in items:
        client.post("/api/v1/products/", json=item)
        
    # Filter by search string
    res = client.get("/api/v1/products/?search=leather")
    assert len(res.json()) == 2
    
    # Filter by category
    res = client.get("/api/v1/products/?category=Apparel")
    assert len(res.json()) == 2
    
    # Filter by min/max price
    res = client.get("/api/v1/products/?min_price=45&max_price=130")
    assert len(res.json()) == 2 # Leather Wallet (49.5) and Leather Shoes (126.0)
    
    # Filter by stock availability
    res = client.get("/api/v1/products/?in_stock=true")
    assert len(res.json()) == 2 # Shoes (8) and Mouse (100)
    
    # Filter by tags
    res = client.get("/api/v1/products/?tags=leather&tags=apparel")
    assert len(res.json()) == 1
    assert res.json()[0]["name"] == "Leather Wallet"

    # Sort final price ascending
    res = client.get("/api/v1/products/?sort_by=final_price&sort_order=asc")
    sorted_items = res.json()
    assert sorted_items[0]["name"] == "Wireless Mouse"   # 40.0
    assert sorted_items[1]["name"] == "Leather Wallet"  # 49.5
    assert sorted_items[2]["name"] == "Leather Shoes"   # 126.0

    # Pagination
    res = client.get("/api/v1/products/?skip=1&limit=1")
    assert len(res.json()) == 1
