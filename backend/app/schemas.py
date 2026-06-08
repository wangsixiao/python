from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdateBody(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryUpdate(CategoryUpdateBody):
    id: int


class CategoryDelete(BaseModel):
    id: int


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_count: int = 0
    created_at: datetime
    updated_at: datetime


class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdateBody(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None


class ItemUpdate(ItemUpdateBody):
    id: int


class ItemDelete(BaseModel):
    id: int


class ItemResponse(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
