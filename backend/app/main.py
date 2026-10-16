from fastapi import Depends, FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .models import Product
from .schemas import ProductIn, ProductOut, ProductUpdate, Stats

LOW_STOCK = 10

app = FastAPI(title="ShopAdmin API")
Instrumentator().instrument(app).expose(app)


@app.get("/")
def root():
    return {"app": "shopadmin", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(text("select 1"))
    return {"status": "ready"}


@app.get("/api/products", response_model=list[ProductOut])
def list_products(q: str = "", category: str = "", db: Session = Depends(get_db)):
    query = select(Product).order_by(Product.id.desc())
    if q:
        query = query.where(Product.name.ilike(f"%{q}%") | Product.sku.ilike(f"%{q}%"))
    if category:
        query = query.where(Product.category == category)
    return db.scalars(query).all()


@app.get("/api/products/stats", response_model=Stats)
def stats(db: Session = Depends(get_db)):
    total, categories, value = db.execute(
        select(func.count(Product.id), func.count(func.distinct(Product.category)), func.sum(Product.price * Product.stock))
    ).one()
    low = db.scalar(select(func.count(Product.id)).where(Product.stock < LOW_STOCK))
    return Stats(total=total, low_stock=low, categories=categories, inventory_value=float(value or 0))


def find(db, product_id):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "product not found")
    return product


def save(db, product):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "sku already exists")
    db.refresh(product)
    return product


@app.get("/api/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return find(db, product_id)


@app.post("/api/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, db: Session = Depends(get_db)):
    product = Product(**data.model_dump())
    db.add(product)
    return save(db, product)


@app.put("/api/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    product = find(db, product_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    return save(db, product)


@app.delete("/api/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db.delete(find(db, product_id))
    db.commit()
