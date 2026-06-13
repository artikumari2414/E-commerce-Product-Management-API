# E-commerce Product Management API

A backend E-commerce Product Management API built with **FastAPI**, **Pydantic v2**, and **JSON-based storage**.

## Features

- **Full CRUD Operations**: Create, Read, Update, and Delete products.
- **Robust Schema Validation**: Nested request and response validation utilizing Pydantic fields, field validators, and model validators.
- **Computed Fields**: Evaluates `final_price` (adjusting for base price, discount percentage, and tax rate) and `is_low_stock` (checking stock level against low stock threshold) dynamically.
- **Search, Filtering, Sorting & Pagination**:
  - Text search in name and description.
  - Filter by category, min/max price range, stock availability, and multiple tags.
  - Sort by `name`, `price`, `final_price`, `created_at`, or `quantity` in ascending/descending order.
  - Pagination using `skip` and `limit`.
- **Custom Middleware**: Computes API response latency and attaches it as `X-Process-Time` to response headers.
- **Thread-safe local database**: JSON file database wrapper with atomic writes and locks.
- **Environment Management**: Configuration handled using Pydantic Settings and loaded from `.env`.
- **Interactive Documentation**: Beautiful OpenAPI documentation with Swagger UI and ReDoc.

---

## Directory Structure

```text
├── app/
│   ├── database/
│   │   ├── __init__.py
│   │   └── json_db.py       # Thread-safe JSON database layer
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── process_time.py  # Custom response time middleware
│   ├── routers/
│   │   ├── __init__.py
│   │   └── products.py      # Product API routes
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── products.py      # Pydantic schemas (validations, computed fields)
│   ├── services/
│   │   ├── __init__.py
│   │   └── product_service.py # Business logic layer
│   ├── __init__.py
│   ├── config.py            # Environment configurations
│   ├── dependencies.py      # Dependency injection providers
│   ├── exceptions.py        # Custom HTTP exceptions
│   └── main.py              # Application entrypoint & initialization
├── data/
│   └── products.json        # Database JSON storage file (auto-generated)
├── tests/
│   ├── __init__.py
│   └── test_products.py     # Comprehensive automated test suite
├── .env                     # Local environment settings
├── requirements.txt         # Dependencies list
└── README.md                # Project documentation
```

---

## Setup & Running Guide

### 1. Installation
Install the required dependencies from the project root:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create or edit `.env` in the root folder:
```env
APP_NAME="E-commerce Product Management API"
APP_ENV="development"
PORT=8000
DATA_FILE_PATH="data/products.json"
```

### 3. Start the Server
Run the FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```
On startup, the application will automatically populate the JSON database with sample items if it is empty.

### 4. Interactive API Documentation
Open your browser and navigate to:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Testing

Run the test suite using `pytest`:
```bash
pytest
```
This tests CRUD endpoints, validation constraints, duplicates checking, filter/search/sort functions, computed fields, and custom middleware.
