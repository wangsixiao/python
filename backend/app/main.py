import logging
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.models_registry import ALLOWED_IMAGE_MODELS, ALLOWED_LLM_MODELS
from app.database import get_db, init_db
from app.logging_config import setup_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.services.image_gen import ImageGenerationError, generate_image
from app.services.visual_brief import VisualBriefError, generate_visual_brief

setup_logging(settings.log_level)
logger = logging.getLogger("app.api")

init_db()

app = FastAPI(title="CRUD API", version="1.0.0")

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def log_http_exception(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP %s %s%s | detail=%s",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
    )
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def log_unhandled_exception(request: Request, exc: Exception):
    logger.exception(
        "Unhandled error on %s %s%s",
        request.method,
        request.url.path,
        f"?{request.url.query}" if request.url.query else "",
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


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


@app.get("/api/image/models", response_model=list[schemas.ImageModelOption])
def list_image_models():
    return [
        schemas.ImageModelOption(
            value=value, label=info["label"], provider=info["provider"]
        )
        for value, info in ALLOWED_IMAGE_MODELS.items()
    ]


@app.get("/api/image/llm-models", response_model=list[schemas.LlmModelOption])
def list_llm_models():
    return [
        schemas.LlmModelOption(
            value=value, label=info["label"], provider=info["provider"]
        )
        for value, info in ALLOWED_LLM_MODELS.items()
    ]


@app.post(
    "/api/image/generate",
    response_model=schemas.GeneratedImageResponse,
    status_code=201,
)
def generate_image_from_prompt(
    body: schemas.ImageGenerate, db: Session = Depends(get_db)
):
    image_model = body.model or settings.image_model
    llm_model = body.llm_model or settings.llm_model

    logger.info(
        "Image generate request image_model=%s llm_model=%s size=%s "
        "prompt_len=%d use_visual_brief=%s",
        image_model,
        llm_model,
        body.size,
        len(body.prompt),
        body.use_visual_brief,
    )

    visual_brief = None
    image_prompt = body.prompt

    if body.use_visual_brief:
        try:
            visual_brief = generate_visual_brief(
                body.prompt, image_model, llm_model
            )
        except VisualBriefError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        image_prompt = visual_brief

    try:
        image_url = generate_image(image_prompt, body.size, image_model)
    except ImageGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    created = crud.create_generated_image(
        db,
        prompt=body.prompt,
        visual_brief=visual_brief,
        image_url=image_url,
        model=image_model,
        size=body.size,
    )
    logger.info("Image saved to database id=%s", created.id)
    return crud.serialize_generated_image(created)


@app.get("/api/image/list", response_model=list[schemas.GeneratedImageResponse])
def list_generated_images(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = Query(None, min_length=1, max_length=200),
    db: Session = Depends(get_db),
):
    images = crud.get_generated_images(db, skip=skip, limit=limit, keyword=q)
    return [crud.serialize_generated_image(image) for image in images]


@app.get("/api/image/detail", response_model=schemas.GeneratedImageResponse)
def detail_generated_image(id: int = Query(...), db: Session = Depends(get_db)):
    image = crud.get_generated_image(db, id)
    if not image:
        raise HTTPException(status_code=404, detail="Generated image not found")
    return crud.serialize_generated_image(image)


@app.post("/api/image/delete")
def delete_generated_image(
    body: schemas.ImageDelete, db: Session = Depends(get_db)
):
    deleted = crud.delete_generated_image(db, body.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Generated image not found")
    return {"success": True}
