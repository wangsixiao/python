import logging

import httpx

from app.config import settings
from app.models_registry import is_gpt_image_model, map_size_for_openai
from app.services.image_gen import ImageGenerationError
from app.services.openai_client import openai_headers, openai_url

logger = logging.getLogger("app.openai_image")


def generate_openai_image(
    prompt: str, size: str, model: str = "dall-e-3"
) -> str:
    if not settings.openai_api_key:
        raise ImageGenerationError("OPENAI_API_KEY is not configured")

    try:
        openai_size = map_size_for_openai(model, size)
    except ValueError as exc:
        raise ImageGenerationError(str(exc)) from exc

    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": openai_size,
    }
    if not is_gpt_image_model(model):
        payload["response_format"] = "url"

    logger.info(
        "Calling OpenAI image model=%s size=%s prompt_len=%d",
        model,
        openai_size,
        len(prompt),
    )

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                openai_url("/images/generations"),
                json=payload,
                headers=openai_headers(),
            )
    except httpx.RequestError as exc:
        logger.error("OpenAI image request failed: %s", exc)
        raise ImageGenerationError(f"Failed to call OpenAI API: {exc}") from exc

    if response.status_code != 200:
        logger.error(
            "OpenAI image API error status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise ImageGenerationError(
            f"OpenAI API error ({response.status_code}): {response.text}"
        )

    data = response.json()
    items = data.get("data") or []
    if not items:
        logger.error("OpenAI response missing image data: %s", data)
        raise ImageGenerationError("No image data in OpenAI response")

    item = items[0]
    if item.get("url"):
        logger.info("OpenAI image generated successfully")
        return item["url"]

    b64_json = item.get("b64_json")
    if b64_json:
        logger.info("OpenAI image generated successfully (base64)")
        return f"data:image/png;base64,{b64_json}"

    logger.error("OpenAI response missing image URL or base64: %s", data)
    raise ImageGenerationError("No image URL in OpenAI response")
