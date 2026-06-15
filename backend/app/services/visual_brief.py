import logging
from typing import Optional

import httpx

from app.config import settings
from app.models_registry import ALLOWED_LLM_MODELS, get_llm_provider
from app.services.openai_client import openai_headers, openai_url

logger = logging.getLogger("app.visual_brief")

VISUAL_BRIEF_SYSTEM = """你是一个面向知识类内容的视觉创意分析师。用户输入通常是某个 topic 的知识描述，你需要先理解 topic 的核心含义，再输出一份供文生图模型 {image_model} 使用的 Visual Brief。

第一步：从 topic 中提取 3-6 个与主题强相关的关键词或核心概念（如对象、过程、关系、领域符号），后续画面必须围绕这些关键词展开，确保图片与 topic 高度相关。

视觉方向（必须遵守）：
- 风格：线条风格插图（line art illustration），清晰轮廓线，可搭配适度填色
- 色彩：必须有明确色彩，使用协调的配色（如 2-4 种主色），避免纯黑白或无色彩画面
- 表达：用图形、符号、结构、场景、隐喻来呈现知识，而不是把文字排版成图
- 禁止：大段文字、标题海报、纯文字图、字幕式排版、水印、标签堆叠、以文字为主体的设计

Visual Brief 需涵盖：
- 从 topic 提炼的关键词及对应视觉元素
- 主体与场景（与知识主题直接相关）
- 构图方式（如中心式、流程式、对比式、层级式）
- 线条风格与上色方式
- 色彩基调
- 关键图形细节

要求：
1. 画面内容必须能体现 topic 的核心知识，不能跑题
2. 输出为连贯的纯文本，不要 JSON、Markdown 标题或编号列表
3. 长度控制在 150-300 字
4. 使用与用户输入相同的语言
5. 只输出 Visual Brief 正文，不要有前言、解释或后语"""


class VisualBriefError(Exception):
    pass


def generate_visual_brief(
    user_prompt: str, image_model: str, llm_model: Optional[str] = None
) -> str:
    model = llm_model or settings.llm_model
    if model not in ALLOWED_LLM_MODELS:
        raise VisualBriefError(f"Unsupported LLM model: {model}")

    system_prompt = VISUAL_BRIEF_SYSTEM.format(image_model=image_model)
    provider = get_llm_provider(model)

    if provider == "openai":
        return _generate_visual_brief_openai(user_prompt, system_prompt, model)

    return _generate_visual_brief_dashscope(user_prompt, system_prompt, model)


def _generate_visual_brief_dashscope(
    user_prompt: str, system_prompt: str, llm_model: str
) -> str:
    if not settings.dashscope_api_key:
        raise VisualBriefError("DASHSCOPE_API_KEY is not configured")

    payload = {
        "model": llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }

    logger.info(
        "Calling DashScope LLM model=%s prompt_len=%d",
        llm_model,
        len(user_prompt),
    )

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                settings.dashscope_chat_url, json=payload, headers=headers
            )
    except httpx.RequestError as exc:
        logger.error("LLM request failed: %s", exc)
        raise VisualBriefError(f"Failed to call LLM API: {exc}") from exc

    if response.status_code != 200:
        logger.error(
            "LLM API error status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise VisualBriefError(
            f"LLM API error ({response.status_code}): {response.text}"
        )

    return _extract_message_content(response.json())


def _generate_visual_brief_openai(
    user_prompt: str, system_prompt: str, llm_model: str
) -> str:
    if not settings.openai_api_key:
        raise VisualBriefError("OPENAI_API_KEY is not configured")

    payload = {
        "model": llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
    }

    logger.info(
        "Calling OpenAI LLM model=%s prompt_len=%d",
        llm_model,
        len(user_prompt),
    )

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                openai_url("/chat/completions"),
                json=payload,
                headers=openai_headers(),
            )
    except httpx.RequestError as exc:
        logger.error("OpenAI LLM request failed: %s", exc)
        raise VisualBriefError(f"Failed to call OpenAI API: {exc}") from exc

    if response.status_code != 200:
        logger.error(
            "OpenAI LLM API error status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise VisualBriefError(
            f"OpenAI API error ({response.status_code}): {response.text}"
        )

    return _extract_message_content(response.json())


def _extract_message_content(data: dict) -> str:
    choices = data.get("choices") or []
    for choice in choices:
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

    output = data.get("output") or {}
    choices = output.get("choices") or []
    for choice in choices:
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

    logger.error("LLM response missing content: %s", data)
    raise VisualBriefError("No Visual Brief in LLM response")
