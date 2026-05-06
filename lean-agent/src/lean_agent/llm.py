"""LLM client abstraction.

Protocol-based design so commands depend only on `LLMClient`, not on the
Anthropic SDK directly. `StubLLMClient` is the only test-time client; never
call Anthropic from tests.

Per `library-notes.md`:
- Use `Anthropic` (sync). `AsyncAnthropic` exists but is out of scope.
- Prompt caching is GA — pass `cache_control: {"type": "ephemeral"}` on each
  system block. Cached blocks must sit at the prefix; max 4 breakpoints; 5min TTL.
- `messages` must alternate user/assistant; first message must be user.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Iterator, Protocol, runtime_checkable

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlockParam


# v0 default model. Override per call by constructing AnthropicLLMClient(model=...).
DEFAULT_MODEL = "claude-sonnet-4-6"


@dataclass
class LLMRequest:
    system: str
    messages: list[dict[str, Any]]
    cache_keys: list[str] = field(default_factory=list)
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class LLMResponse:
    text: str
    raw: object | None = None
    # Per library-notes §anthropic: log these in v0 to observe whether prompt caching
    # actually fires. Currently GUARDRAILS alone is below Anthropic's 1024-token cache
    # minimum, so cache_creation_input_tokens / cache_read_input_tokens will both be 0
    # until v0.5 (when persona + template content joins the cached system prefix).
    usage: dict[str, Any] | None = None


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, req: LLMRequest) -> LLMResponse: ...
    def complete_streaming(self, req: LLMRequest) -> Iterator[str]: ...


@dataclass
class StubLLMClient:
    """In-memory client for tests. Returns canned responses in order; records every call.

    Never use in production code paths.
    """

    responses: list[str] = field(default_factory=list)
    streaming_responses: list[list[str]] = field(default_factory=list)
    calls: list[LLMRequest] = field(default_factory=list)
    streaming_calls: list[LLMRequest] = field(default_factory=list)

    def complete(self, req: LLMRequest) -> LLMResponse:
        self.calls.append(req)
        if not self.responses:
            raise RuntimeError("StubLLMClient out of canned responses")
        return LLMResponse(text=self.responses.pop(0))

    def complete_streaming(self, req: LLMRequest) -> Iterator[str]:
        self.streaming_calls.append(req)
        if not self.streaming_responses:
            raise RuntimeError("StubLLMClient out of canned streaming responses")
        chunks = self.streaming_responses.pop(0)
        return iter(chunks)


class AnthropicLLMClient:
    """Real Anthropic SDK client with prompt caching on the system block."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Run `export ANTHROPIC_API_KEY=sk-ant-...` "
                "and try again."
            )
        self._client = Anthropic(api_key=resolved_key)
        self._model = model

    def complete(self, req: LLMRequest) -> LLMResponse:
        system_blocks: list[TextBlockParam] = [
            {
                "type": "text",
                "text": req.system,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        user_messages: list[MessageParam] = [
            {"role": m["role"], "content": m["content"]} for m in req.messages
        ]
        # NOTE: The cache_control block is symbolic in v0 — GUARDRAILS is ~217 tokens,
        # below Anthropic's 1024-token cache minimum for Sonnet/Opus. Cache hits will
        # be 0 until v0.5 when richer system content (templates + personas) joins the
        # prefix. Telemetry is captured anyway so we can verify when caching activates.
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            system=system_blocks,
            messages=user_messages,
        )
        # Filter to text blocks; future tool_use / thinking blocks will be ignored here.
        text = "".join(b.text for b in resp.content if b.type == "text")
        usage = {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "cache_creation_input_tokens": getattr(resp.usage, "cache_creation_input_tokens", 0),
            "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", 0),
        }
        return LLMResponse(text=text, raw=resp, usage=usage)

    def complete_streaming(self, req: LLMRequest) -> Iterator[str]:
        """Stream text deltas from Anthropic.

        Wraps `client.messages.stream()` per Anthropic SDK 0.97.0 docs (verified
        2026-05-05). The context manager guarantees connection cleanup; iteration
        of `stream.text_stream` yields each text delta as a string. Final usage
        tokens (cache hits, etc.) are not captured here for v0.3 — the streaming
        path's per-chunk yields skip telemetry; non-streaming `complete()` keeps
        the existing telemetry capture.

        Exceptions from the SDK (`APIConnectionError`, `RateLimitError`,
        `APIStatusError`) propagate; the route handler in `api_routes/personas.py`
        catches them and emits an SSE `error` event.
        """
        system_blocks: list[TextBlockParam] = [
            {
                "type": "text",
                "text": req.system,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        user_messages: list[MessageParam] = [
            {"role": m["role"], "content": m["content"]} for m in req.messages
        ]
        with self._client.messages.stream(
            model=self._model,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            system=system_blocks,
            messages=user_messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
