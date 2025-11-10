import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Product, ContactMessage

app = FastAPI(title="Elsea Grosir API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Elsea Grosir Backend is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from Elsea Grosir API"}


def _seed_products_if_empty():
    if db is None:
        return
    count = db["product"].count_documents({})
    if count > 0:
        return
    sample_products = [
        {
            "title": "Beras Premium 5kg",
            "description": "Beras pulen kualitas premium, cocok untuk kebutuhan rumah tangga.",
            "price": 78000,
            "category": "beras",
            "in_stock": True,
            "unit": "pack",
            "image_url": "https://images.unsplash.com/photo-1604908554007-27b99b2b8d11?q=80&w=800&auto=format&fit=crop",
            "discount": 10,
        },
        {
            "title": "Minyak Goreng 1 Liter",
            "description": "Minyak goreng sawit kemasan 1L, jernih dan berkualitas.",
            "price": 17000,
            "category": "minyak",
            "in_stock": True,
            "unit": "liter",
            "image_url": "https://images.unsplash.com/photo-1625944528148-8b1877fa9afd?q=80&w=800&auto=format&fit=crop",
            "discount": 5,
        },
        {
            "title": "Gula Pasir 1kg",
            "description": "Gula pasir putih kristal berkualitas.",
            "price": 15000,
            "category": "gula",
            "in_stock": True,
            "unit": "kg",
            "image_url": "https://images.unsplash.com/photo-1603833665858-e61d17a86224?q=80&w=800&auto=format&fit=crop",
            "discount": 0,
        },
        {
            "title": "Telur Ayam 1 Tray (30 butir)",
            "description": "Telur ayam segar langsung dari peternak.",
            "price": 57000,
            "category": "telur",
            "in_stock": True,
            "unit": "tray",
            "image_url": "https://images.unsplash.com/photo-1517959105821-eaf2591984bd?q=80&w=800&auto=format&fit=crop",
            "discount": 8,
        },
        {
            "title": "Tepung Terigu 1kg",
            "description": "Tepung terigu serbaguna untuk berbagai olahan.",
            "price": 12000,
            "category": "tepung",
            "in_stock": True,
            "unit": "kg",
            "image_url": "https://images.unsplash.com/photo-1519682337058-a94d519337bc?q=80&w=800&auto=format&fit=crop",
            "discount": 0,
        },
    ]
    for p in sample_products:
        create_document("product", p)


@app.on_event("startup")
async def startup_event():
    try:
        _seed_products_if_empty()
    except Exception as e:
        print("Seed error:", str(e))


class ProductsResponse(BaseModel):
    items: List[Product]
    total: int
    categories: List[str]


@app.get("/api/products", response_model=ProductsResponse)
def list_products(q: Optional[str] = None, category: Optional[str] = None, limit: int = 100):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    filt = {}
    if category:
        filt["category"] = category
    if q:
        filt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    docs = get_documents("product", filt, limit)
    # Normalize _id to string and map to Product shape
    items: List[Product] = []
    for d in docs:
        d.pop("_id", None)
        items.append(Product(**d))
    categories = sorted(list({d["category"] for d in docs if "category" in d}))
    return {"items": items, "total": len(items), "categories": categories}


@app.get("/api/categories", response_model=List[str])
def list_categories():
    if db is None:
        return []
    cats = db["product"].distinct("category")
    return sorted([c for c in cats if c])


@app.get("/api/featured", response_model=List[Product])
def featured_products(limit: int = 6):
    if db is None:
        return []
    cursor = db["product"].find({"discount": {"$gte": 5}}).sort("discount", -1).limit(limit)
    items: List[Product] = []
    for d in cursor:
        d.pop("_id", None)
        items.append(Product(**d))
    return items


@app.post("/api/contact")
def submit_contact(msg: ContactMessage):
    try:
        doc_id = create_document("contactmessage", msg)
        return {"status": "ok", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
