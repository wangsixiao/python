from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


from app.models_registry import (
    ALLOWED_IMAGE_MODELS,
    ALLOWED_LLM_MODELS,
    get_image_provider,
    get_openai_size_mapping,
)

ALLOWED_IMAGE_SIZES = {
    "512*512",
    "768*768",
    "1024*1024",
    "1024*1536",
    "1536*1024",
    "1536*1536",
    "2048*2048",
}


class ImageModelOption(BaseModel):
    value: str
    label: str
    provider: str


class LlmModelOption(BaseModel):
    value: str
    label: str
    provider: str


class ImageGenerate(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    size: Optional[str] = Field(None, max_length=32)
    model: Optional[str] = Field(None, max_length=64)
    llm_model: Optional[str] = Field(None, max_length=64)
    use_visual_brief: bool = False

    @model_validator(mode="after")
    def validate_fields(self):
        image_model = self.model
        if image_model is not None and image_model not in ALLOWED_IMAGE_MODELS:
            raise ValueError(
                f"model must be one of {sorted(ALLOWED_IMAGE_MODELS)}, "
                f"got {image_model!r}"
            )

        if self.llm_model is not None and self.llm_model not in ALLOWED_LLM_MODELS:
            raise ValueError(
                f"llm_model must be one of {sorted(ALLOWED_LLM_MODELS)}, "
                f"got {self.llm_model!r}"
            )

        if self.size is None:
            return self

        if image_model and get_image_provider(image_model) == "openai":
            openai_sizes = get_openai_size_mapping(image_model)
            if self.size not in openai_sizes:
                raise ValueError(
                    f"size must be one of {sorted(openai_sizes)}, got {self.size!r}"
                )
        elif self.size not in ALLOWED_IMAGE_SIZES:
            raise ValueError(
                f"size must be one of {sorted(ALLOWED_IMAGE_SIZES)}, got {self.size!r}"
            )
        return self


class ImageDelete(BaseModel):
    id: int


class GeneratedImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    visual_brief: Optional[str] = None
    image_url: str
    model: Optional[str] = None
    size: Optional[str] = None
    created_at: datetime
    updated_at: datetime
