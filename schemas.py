"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in IDR")
    category: str = Field(..., description="Product category, e.g., beras, minyak, gula, telur")
    in_stock: bool = Field(True, description="Whether product is in stock")
    unit: str = Field("kg", description="Unit of measurement, e.g., kg, liter, pack, tray")
    image_url: Optional[str] = Field(None, description="Image URL for the product")
    discount: Optional[float] = Field(0, ge=0, le=100, description="Discount percentage (0-100)")

class ContactMessage(BaseModel):
    """Contact messages from the website form"""
    name: str
    email: str
    phone: Optional[str] = None
    message: str
