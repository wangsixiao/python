import logging
from typing import Optional

import httpx

from app.config import settings
from app.models_registry import ALLOWED_IMAGE_MODELS, get_image_provider

logger = logging.getLogger("app.image_gen")


class ImageGenerationError(Exception):
    pass


def generate_image(
    visual_brief: str,
    size: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    image_model = model or settings.image_model
    if image_model not in ALLOWED_IMAGE_MODELS:
        raise ImageGenerationError(f"Unsupported image model: {image_model}")

    image_size = size or settings.image_default_size
    provider = get_image_provider(image_model)

    if provider == "openai":
        from app.services.openai_image import generate_openai_image

        return generate_openai_image(visual_brief, image_size, image_model)

    return _generate_dashscope_image(visual_brief, image_size, image_model)


def _generate_dashscope_image(
    visual_brief: str, size: str, image_model: str
) -> str:
    if not settings.dashscope_api_key:
        raise ImageGenerationError("DASHSCOPE_API_KEY is not configured")

    payload = {
        "model": image_model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": visual_brief}],
                }
            ]
        },
        "parameters": {
            "size": size,
            "prompt_extend": False,
            "n": 1,
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }

    logger.info(
        "Calling DashScope model=%s size=%s brief_len=%d",
        image_model,
        size,
        len(visual_brief),
    )

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                settings.dashscope_base_url, json=payload, headers=headers
            )
    except httpx.RequestError as exc:
        logger.error("DashScope request failed: %s", exc)
        raise ImageGenerationError(f"Failed to call DashScope API: {exc}") from exc

    if response.status_code != 200:
        logger.error(
            "DashScope API error status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise ImageGenerationError(
            f"DashScope API error ({response.status_code}): {response.text}"
        )

    data = response.json()
    image_url = _extract_image_url(data)
    if not image_url:
        logger.error("DashScope response missing image URL: %s", data)
        raise ImageGenerationError("No image URL in DashScope response")

    logger.info("DashScope image generated successfully")
    return image_url


def _extract_image_url(data: dict) -> Optional[str]:
    output = data.get("output") or {}
    choices = output.get("choices") or []
    for choice in choices:
        message = choice.get("message") or {}
        for item in message.get("content") or []:
            if isinstance(item, dict) and item.get("image"):
                return item["image"]

    results = output.get("results") or []
    for result in results:
        if isinstance(result, dict) and result.get("url"):
            return result["url"]

    return None
