from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db, init_db

init_db()

app = FastAPI(title="CRUD API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/category/list", response_model=list[schemas.CategoryResponse])
def list_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = crud.get_categories(db, skip=skip, limit=limit)
    return [
        crud.serialize_category(category, crud.get_category_item_count(db, category.id))
        for category in categories
    ]


@app.get("/api/category/detail", response_model=schemas.CategoryResponse)
def detail_category(id: int = Query(...), db: Session = Depends(get_db)):
    category = crud.get_category(db, id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return crud.serialize_category(category, crud.get_category_item_count(db, id))


@app.post("/api/category/add", response_model=schemas.CategoryResponse, status_code=201)
def add_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(models.Category)
        .filter(models.Category.name == category.name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Category name already exists")

    created = crud.create_category(db, category)
    return crud.serialize_category(created, 0)


@app.post("/api/category/update", response_model=schemas.CategoryResponse)
def update_category(category: schemas.CategoryUpdate, db: Session = Depends(get_db)):
    updated = crud.update_category(db, category.id, category)
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    return crud.serialize_category(
        updated, crud.get_category_item_count(db, category.id)
    )


@app.post("/api/category/delete")
def delete_category(category: schemas.CategoryDelete, db: Session = Depends(get_db)):
    deleted, reason = crud.delete_category(db, category.id)
    if not deleted:
        if reason == "has_items":
            raise HTTPException(
                status_code=400, detail="Cannot delete category with existing items"
            )
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True}


@app.get("/api/list", response_model=list[schemas.ItemResponse])
def list_items(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    items = crud.get_items(db, skip=skip, limit=limit, category_id=category_id)
    return [crud.serialize_item(item) for item in items]


@app.get("/api/detail", response_model=schemas.ItemResponse)
def detail_item(id: int = Query(...), db: Session = Depends(get_db)):
    item = crud.get_item(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.serialize_item(item)


@app.post("/api/add", response_model=schemas.ItemResponse, status_code=201)
def add_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    created, error = crud.create_item(db, item)
    if error == "invalid_category":
        raise HTTPException(status_code=400, detail="Invalid category")
    return crud.serialize_item(created)


@app.post("/api/update", response_model=schemas.ItemResponse)
def update_item(item: schemas.ItemUpdate, db: Session = Depends(get_db)):
    updated, error = crud.update_item(db, item.id, item)
    if error == "not_found":
        raise HTTPException(status_code=404, detail="Item not found")
    if error == "invalid_category":
        raise HTTPException(status_code=400, detail="Invalid category")
    return crud.serialize_item(updated)


@app.post("/api/delete")
def delete_item(item: schemas.ItemDelete, db: Session = Depends(get_db)):
    deleted = crud.delete_item(db, item.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"success": True}
