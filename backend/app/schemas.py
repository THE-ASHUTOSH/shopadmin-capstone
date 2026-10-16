from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    sku: str = Field(min_length=1, max_length=40)
    category: str = "General"
    price: Decimal = Field(ge=0)
    stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    sku: str | None = Field(default=None, min_length=1, max_length=40)
    category: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)


class ProductOut(ProductIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class Stats(BaseModel):
    total: int
    low_stock: int
    categories: int
    inventory_value: float
