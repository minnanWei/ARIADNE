from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict

from openai import OpenAI

_CLIENT: OpenAI | None = None


@dataclass
class UsageStats:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    api_calls: int = 0
    total_time_s: float = 0.0


_USAGE = UsageStats()


def _get_client() -> OpenAI:
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    api_key = os.getenv("MCTSCODER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing API key: set MCTSCODER_API_KEY or OPENAI_API_KEY.")
    base_url = os.getenv("MCTSCODER_BASE_URL", "https://yunwu.ai/v1")
    _CLIENT = OpenAI(base_url=base_url, api_key=api_key)
    return _CLIENT


def call_llm(prompt: str, *, temperature: float = 0.2, max_tokens: int = 2048) -> str:
    model = os.getenv("MCTSCODER_MODEL", "gpt-4o")
    timeout_s = float(os.getenv("MCTSCODER_TIMEOUT", "100"))
    debug = os.getenv("MCTSCODER_LLM_DEBUG", "0") == "1"

    client = _get_client()
    messages = [{"role": "user", "content": prompt}]
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        timeout=timeout_s,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    elapsed = time.perf_counter() - start

    if debug:
        snippet_prompt = prompt[:200].replace("\n", "\\n")
        print(f"[llm] prompt: {snippet_prompt}")

    content = None
    if response and response.choices:
        content = response.choices[0].message.content

    if not content:
        raise RuntimeError("LLM response was empty or malformed.")

    _record_usage(response, elapsed)

    if debug:
        snippet_resp = content[:200].replace("\n", "\\n")
        print(f"[llm] response: {snippet_resp}")

    return content


def _record_usage(response: Any, elapsed_s: float) -> None:
    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    _USAGE.prompt_tokens += prompt_tokens
    _USAGE.completion_tokens += completion_tokens
    _USAGE.api_calls += 1
    _USAGE.total_time_s += float(elapsed_s)


def reset_usage() -> None:
    global _USAGE
    _USAGE = UsageStats()


def get_usage() -> Dict[str, Any]:
    return {
        "prompt_tokens": _USAGE.prompt_tokens,
        "completion_tokens": _USAGE.completion_tokens,
        "api_calls": _USAGE.api_calls,
        "llm_time_s": _USAGE.total_time_s,
    }
