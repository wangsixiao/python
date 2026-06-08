from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app import models, schemas


def serialize_item(item: models.Item) -> schemas.ItemResponse:
    return schemas.ItemResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        category_id=item.category_id,
        category_name=item.category.name if item.category else None,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def serialize_category(category: models.Category, item_count: int = 0) -> schemas.CategoryResponse:
    return schemas.CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        item_count=item_count,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()


def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_category_item_count(db: Session, category_id: int) -> int:
    return (
        db.query(func.count(models.Item.id))
        .filter(models.Item.category_id == category_id)
        .scalar()
        or 0
    )


def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category: schemas.CategoryUpdateBody):
    db_category = get_category(db, category_id)
    if not db_category:
        return None

    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id)
    if not db_category:
        return False, "not_found"

    item_count = get_category_item_count(db, category_id)
    if item_count > 0:
        return False, "has_items"

    db.delete(db_category)
    db.commit()
    return True, None


def get_items(
    db: Session, skip: int = 0, limit: int = 100, category_id: Optional[int] = None
):
    query = db.query(models.Item).options(joinedload(models.Item.category))
    if category_id is not None:
        query = query.filter(models.Item.category_id == category_id)
    return query.offset(skip).limit(limit).all()


def get_item(db: Session, item_id: int):
    return (
        db.query(models.Item)
        .options(joinedload(models.Item.category))
        .filter(models.Item.id == item_id)
        .first()
    )


def create_item(db: Session, item: schemas.ItemCreate):
    if item.category_id is not None and not get_category(db, item.category_id):
        return None, "invalid_category"

    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    db_item = get_item(db, db_item.id)
    return db_item, None


def update_item(db: Session, item_id: int, item: schemas.ItemUpdateBody):
    db_item = get_item(db, item_id)
    if not db_item:
        return None, "not_found"

    update_data = item.model_dump(exclude_unset=True)
    if "category_id" in update_data and update_data["category_id"] is not None:
        if not get_category(db, update_data["category_id"]):
            return None, "invalid_category"

    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    db_item = get_item(db, item_id)
    return db_item, None


def delete_item(db: Session, item_id: int):
    db_item = get_item(db, item_id)
    if not db_item:
        return False

    db.delete(db_item)
    db.commit()
    return True
