from typing import Literal, TypedDict

Provider = Literal["dashscope", "openai"]


class ModelInfo(TypedDict):
    label: str
    provider: Provider


ALLOWED_IMAGE_MODELS: dict[str, ModelInfo] = {
    "qwen-image-2.0-pro": {
        "label": "千问 Qwen Image 2.0 Pro",
        "provider": "dashscope",
    },
    "qwen-image-2.0": {
        "label": "千问 Qwen Image 2.0",
        "provider": "dashscope",
    },
    "wan2.6-t2i": {
        "label": "万相 Wan 2.6 文生图",
        "provider": "dashscope",
    },
    "z-image-turbo": {
        "label": "Z-Image Turbo",
        "provider": "dashscope",
    },
    "gpt-image-1.5": {
        "label": "GPT Image 1.5",
        "provider": "openai",
    },
}

ALLOWED_LLM_MODELS: dict[str, ModelInfo] = {
    "qwen-plus": {
        "label": "通义千问 Plus",
        "provider": "dashscope",
    },
    "qwen-turbo": {
        "label": "通义千问 Turbo",
        "provider": "dashscope",
    },
    "gpt-5.4-mini": {
        "label": "gpt-5.4-mini",
        "provider": "openai",
    },
}

GPT_IMAGE_SIZE_MAP = {
    "1024*1024": "1024x1024",
    "1024*1536": "1024x1536",
    "1536*1024": "1536x1024",
}

OPENAI_SIZE_MAP = {
    "dall-e-3": {
        "1024*1024": "1024x1024",
        "1024*1536": "1024x1792",
        "1536*1024": "1792x1024",
    },
    "dall-e-2": {
        "512*512": "512x512",
        "1024*1024": "1024x1024",
    },
    "gpt-image-1.5": GPT_IMAGE_SIZE_MAP,
}


def is_gpt_image_model(model: str) -> bool:
    return model.startswith("gpt-image-")


def get_openai_size_mapping(model: str) -> dict[str, str]:
    if is_gpt_image_model(model):
        return GPT_IMAGE_SIZE_MAP
    return OPENAI_SIZE_MAP.get(model, {})


def get_image_provider(model: str) -> Provider:
    return ALLOWED_IMAGE_MODELS[model]["provider"]


def get_llm_provider(model: str) -> Provider:
    return ALLOWED_LLM_MODELS[model]["provider"]


def map_size_for_openai(model: str, size: str) -> str:
    mapping = get_openai_size_mapping(model)
    if size not in mapping:
        supported = ", ".join(sorted(mapping))
        raise ValueError(
            f"model {model} does not support size {size!r}; "
            f"supported: {supported}"
        )
    return mapping[size]
