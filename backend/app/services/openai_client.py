import httpx

from app.config import settings


def openai_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }


def openai_url(path: str) -> str:
    base = settings.openai_base_url.rstrip("/")
    return f"{base}{path}"
