import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app import crud, models, schemas

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_categories",
            "description": "List all categories with item counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max categories to return (default 100).",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_category",
            "description": "Create a new category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Category name."},
                    "description": {
                        "type": "string",
                        "description": "Optional category description.",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_category",
            "description": "Update an existing category by id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Category id."},
                    "name": {"type": "string", "description": "New name."},
                    "description": {
                        "type": "string",
                        "description": "New description.",
                    },
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_category",
            "description": (
                "Delete a category by id. Fails if the category still has items."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Category id."}
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_items",
            "description": "List items, optionally filtered by category_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_id": {
                        "type": "integer",
                        "description": "Filter by category id.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max items to return (default 100).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_item",
            "description": "Create a new item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Item title."},
                    "description": {
                        "type": "string",
                        "description": "Optional item description.",
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "Optional category id.",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_item",
            "description": "Update an existing item by id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Item id."},
                    "title": {"type": "string", "description": "New title."},
                    "description": {
                        "type": "string",
                        "description": "New description.",
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "New category id (use null to unset).",
                    },
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_item",
            "description": "Delete an item by id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Item id."}
                },
                "required": ["id"],
            },
        },
    },
]


def execute_tool(db: Session, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        if name == "list_categories":
            limit = arguments.get("limit", 100)
            categories = crud.get_categories(db, limit=limit)
            return {
                "ok": True,
                "data": [
                    crud.serialize_category(
                        c, crud.get_category_item_count(db, c.id)
                    ).model_dump(mode="json")
                    for c in categories
                ],
            }

        if name == "create_category":
            existing = (
                db.query(models.Category)
                .filter(models.Category.name == arguments["name"])
                .first()
            )
            if existing:
                return {"ok": False, "error": "Category name already exists"}
            created = crud.create_category(
                db, schemas.CategoryCreate(**arguments)
            )
            return {
                "ok": True,
                "data": crud.serialize_category(created, 0).model_dump(mode="json"),
            }

        if name == "update_category":
            category_id = arguments.pop("id")
            updated = crud.update_category(
                db, category_id, schemas.CategoryUpdateBody(**arguments)
            )
            if not updated:
                return {"ok": False, "error": "Category not found"}
            return {
                "ok": True,
                "data": crud.serialize_category(
                    updated, crud.get_category_item_count(db, category_id)
                ).model_dump(mode="json"),
            }

        if name == "delete_category":
            deleted, reason = crud.delete_category(db, arguments["id"])
            if not deleted:
                if reason == "has_items":
                    return {
                        "ok": False,
                        "error": "Cannot delete category with existing items",
                    }
                return {"ok": False, "error": "Category not found"}
            return {"ok": True, "data": {"deleted_id": arguments["id"]}}

        if name == "list_items":
            limit = arguments.get("limit", 100)
            category_id: Optional[int] = arguments.get("category_id")
            items = crud.get_items(db, limit=limit, category_id=category_id)
            return {
                "ok": True,
                "data": [crud.serialize_item(i).model_dump(mode="json") for i in items],
            }

        if name == "create_item":
            created, error = crud.create_item(db, schemas.ItemCreate(**arguments))
            if error:
                return {"ok": False, "error": error}
            return {
                "ok": True,
                "data": crud.serialize_item(created).model_dump(mode="json"),
            }

        if name == "update_item":
            item_id = arguments.pop("id")
            updated, error = crud.update_item(
                db, item_id, schemas.ItemUpdateBody(**arguments)
            )
            if error == "not_found":
                return {"ok": False, "error": "Item not found"}
            if error == "invalid_category":
                return {"ok": False, "error": "Invalid category"}
            return {
                "ok": True,
                "data": crud.serialize_item(updated).model_dump(mode="json"),
            }

        if name == "delete_item":
            deleted = crud.delete_item(db, arguments["id"])
            if not deleted:
                return {"ok": False, "error": "Item not found"}
            return {"ok": True, "data": {"deleted_id": arguments["id"]}}

        return {"ok": False, "error": f"Unknown tool: {name}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def parse_tool_arguments(raw: Optional[str]) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}
