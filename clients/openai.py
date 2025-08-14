import os
from typing import Generator, List, Dict, Any, Optional

from config import OPENAI_API_KEY, OPENAI_MODEL

try:
    # OpenAI Python SDK v1+
    from openai import OpenAI as _OpenAISDK
except Exception as e:
    _OpenAISDK = None
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


class OpenAIClient:
    """Thin wrapper around the OpenAI SDK for streaming chat completions.

    - Reads API key and default model from `config.py`.
    - Exposes `build_messages(...)` helper to construct messages payloads.
    - Exposes `stream_chat(...)` generator yielding incremental text chunks.
    """

    def __init__(
        self, api_key: Optional[str] = None, default_model: Optional[str] = None
    ):
        if _OpenAISDK is None:
            raise RuntimeError(
                f"OpenAI SDK not available: {_IMPORT_ERROR}. Install `openai` package."
            )

        key = (api_key or OPENAI_API_KEY or "").strip()
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Please configure it in your environment or .env file."
            )

        self.model = (default_model or OPENAI_MODEL or "gpt-4.1-mini").strip()
        self.client = _OpenAISDK(api_key=key)

    @staticmethod
    def build_messages(
        chat_history: List[Dict[str, Any]] | None,
        system_prompt: str,
        user_message: str,
        image_parts: List[Dict[str, Any]] | None,
    ) -> List[Dict[str, Any]]:
        """Construct OpenAI messages including prior turns and optional images."""
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": str(system_prompt)},
        ]

        # Add previous turns as plain text
        for m in chat_history or []:
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            content = m.get("content")
            if role in ("user", "assistant") and content is not None:
                messages.append({"role": role, "content": str(content)})

        # Current user message (with optional images)
        if image_parts:
            user_content: List[Dict[str, Any]] = [
                {"type": "text", "text": str(user_message)}
            ]
            user_content.extend(image_parts)
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": str(user_message)})

        return messages

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        *,
        temperature: float = 0.7,
        model: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Yield incremental content tokens from a chat completion stream."""
        target_model = (model or self.model).strip()
        stream = self.client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            # Cope with potential dict-like or attribute-like SDK objects
            try:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
            except Exception:
                # Fallback for dict-like
                choices = chunk.get("choices") if isinstance(chunk, dict) else None
                delta = (choices or [{}])[0].get("delta") if choices else None
                content = (delta or {}).get("content")

            if content:
                yield content
