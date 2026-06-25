import json
import logging
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.agents.prompts import AGENT_SYSTEM_PROMPT
from app.agents.tools import TOOL_DEFINITIONS, execute_tool, parse_tool_arguments
from app.config import settings
from app.models_registry import ALLOWED_LLM_MODELS, get_llm_provider
from app.services.openai_client import openai_headers, openai_url

logger = logging.getLogger("app.agent")

MAX_AGENT_ITERATIONS = 10


class AgentError(Exception):
    pass


def run_agent(
    db: Session,
    messages: list[dict[str, Any]],
    llm_model: Optional[str] = None,
) -> dict[str, Any]:
    model = llm_model or settings.llm_model
    if model not in ALLOWED_LLM_MODELS:
        raise AgentError(f"Unsupported LLM model: {model}")

    provider = get_llm_provider(model)
    if provider == "openai" and not settings.openai_api_key:
        raise AgentError("OPENAI_API_KEY is not configured")
    if provider == "dashscope" and not settings.dashscope_api_key:
        raise AgentError("DASHSCOPE_API_KEY is not configured")

    working_messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        *messages,
    ]
    tool_calls_log: list[dict[str, Any]] = []

    for iteration in range(MAX_AGENT_ITERATIONS):
        logger.info("Agent iteration=%d model=%s", iteration + 1, model)

        if provider == "openai":
            response_data = _call_openai(working_messages, model)
        else:
            response_data = _call_dashscope(working_messages, model)

        choice = _first_choice(response_data)
        message = choice.get("message") or {}
        finish_reason = choice.get("finish_reason")

        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": message.get("content"),
        }
        raw_tool_calls = message.get("tool_calls") or []
        if raw_tool_calls:
            assistant_message["tool_calls"] = raw_tool_calls
        working_messages.append(assistant_message)

        if not raw_tool_calls:
            return {
                "message": _string_content(message.get("content")),
                "tool_calls": tool_calls_log,
                "finish_reason": finish_reason or "stop",
            }

        for tool_call in raw_tool_calls:
            fn = tool_call.get("function") or {}
            tool_name = fn.get("name", "")
            tool_call_id = tool_call.get("id", "")
            arguments = parse_tool_arguments(fn.get("arguments"))

            logger.info("Agent tool=%s args=%s", tool_name, arguments)
            result = execute_tool(db, tool_name, arguments)
            result_text = json.dumps(result, ensure_ascii=False)

            tool_calls_log.append(
                {
                    "id": tool_call_id,
                    "name": tool_name,
                    "arguments": arguments,
                    "result": result,
                }
            )

            working_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result_text,
                }
            )

    raise AgentError("Agent exceeded maximum iterations without finishing")


def _call_dashscope(messages: list[dict[str, Any]], model: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                settings.dashscope_chat_url, json=payload, headers=headers
            )
    except httpx.RequestError as exc:
        logger.error("Agent LLM request failed: %s", exc)
        raise AgentError(f"Failed to call LLM API: {exc}") from exc

    if response.status_code != 200:
        logger.error(
            "Agent LLM API error status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise AgentError(
            f"LLM API error ({response.status_code}): {response.text}"
        )

    return response.json()


def _call_openai(messages: list[dict[str, Any]], model: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "temperature": 0.3,
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                openai_url("/chat/completions"),
                json=payload,
                headers=openai_headers(),
            )
    except httpx.RequestError as exc:
        logger.error("Agent OpenAI request failed: %s", exc)
        raise AgentError(f"Failed to call OpenAI API: {exc}") from exc

    if response.status_code != 200:
        logger.error(
            "Agent OpenAI API error status=%s body=%s",
            response.status_code,
            response.text,
        )
        raise AgentError(
            f"OpenAI API error ({response.status_code}): {response.text}"
        )

    return response.json()


def _first_choice(data: dict[str, Any]) -> dict[str, Any]:
    choices = data.get("choices") or []
    if choices:
        return choices[0]

    output = data.get("output") or {}
    output_choices = output.get("choices") or []
    if output_choices:
        return output_choices[0]

    logger.error("Agent LLM response missing choices: %s", data)
    raise AgentError("No response from LLM")


def _string_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()
    return ""
