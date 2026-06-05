from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

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


@app.get("/api/list", response_model=list[schemas.ItemResponse])
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_items(db, skip=skip, limit=limit)


@app.get("/api/detail", response_model=schemas.ItemResponse)
def detail_item(id: int = Query(...), db: Session = Depends(get_db)):
    item = crud.get_item(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post("/api/add", response_model=schemas.ItemResponse, status_code=201)
def add_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


@app.post("/api/update", response_model=schemas.ItemResponse)
def update_item(item: schemas.ItemUpdate, db: Session = Depends(get_db)):
    updated = crud.update_item(db, item.id, item)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@app.post("/api/delete")
def delete_item(item: schemas.ItemDelete, db: Session = Depends(get_db)):
    deleted = crud.delete_item(db, item.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"success": True}
