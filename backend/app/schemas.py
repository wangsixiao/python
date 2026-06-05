from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdateBody(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class ItemUpdate(ItemUpdateBody):
    id: int


class ItemDelete(BaseModel):
    id: int


class ItemResponse(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
