import pytest

from lean_agent.llm import (
    AnthropicLLMClient,
    DEFAULT_MODEL,
    LLMClient,
    LLMRequest,
    StubLLMClient,
)


def test_stub_returns_canned():
    stub = StubLLMClient(responses=["hello", "world"])
    r1 = stub.complete(LLMRequest(system="s", messages=[{"role": "user", "content": "x"}]))
    r2 = stub.complete(LLMRequest(system="s", messages=[{"role": "user", "content": "y"}]))
    assert r1.text == "hello"
    assert r2.text == "world"


def test_stub_records_calls():
    stub = StubLLMClient(responses=["ok"])
    stub.complete(LLMRequest(system="sys-prompt", messages=[{"role": "user", "content": "hi"}]))
    assert len(stub.calls) == 1
    assert stub.calls[0].system == "sys-prompt"


def test_stub_runs_out_of_responses_raises():
    stub = StubLLMClient(responses=[])
    with pytest.raises(RuntimeError, match="StubLLMClient out of canned responses"):
        stub.complete(LLMRequest(system="s", messages=[{"role": "user", "content": "x"}]))


def test_protocol_isinstance():
    assert isinstance(StubLLMClient(responses=[]), LLMClient)


def test_default_model_constant_set():
    assert DEFAULT_MODEL.startswith("claude-")


def test_anthropic_client_complete(mocker):
    """AnthropicLLMClient sends a single ephemeral-cached system block and reads back text."""
    mock_anthropic_class = mocker.patch("lean_agent.llm.Anthropic")
    mock_msg = mocker.MagicMock()
    text_block = mocker.MagicMock()
    text_block.type = "text"
    text_block.text = "hi"
    mock_msg.content = [text_block]
    mock_anthropic_class.return_value.messages.create.return_value = mock_msg

    client = AnthropicLLMClient(api_key="sk-test")
    resp = client.complete(LLMRequest(system="SYS", messages=[{"role": "user", "content": "x"}]))

    assert resp.text == "hi"
    assert resp.raw is mock_msg

    # Verify the SDK call shape: model is the constant, max_tokens passed, system is a list of blocks with cache_control.
    call_kwargs = mock_anthropic_class.return_value.messages.create.call_args.kwargs
    assert call_kwargs["model"] == DEFAULT_MODEL
    assert call_kwargs["max_tokens"] == 4096
    assert isinstance(call_kwargs["system"], list)
    assert call_kwargs["system"][0] == {
        "type": "text",
        "text": "SYS",
        "cache_control": {"type": "ephemeral"},
    }
    assert call_kwargs["messages"] == [{"role": "user", "content": "x"}]


def test_anthropic_client_populates_usage_telemetry(mocker):
    """Per library-notes: usage telemetry must be observable so we can verify caching."""
    mock_anthropic_class = mocker.patch("lean_agent.llm.Anthropic")
    mock_msg = mocker.MagicMock()
    text_block = mocker.MagicMock()
    text_block.type = "text"
    text_block.text = "ok"
    mock_msg.content = [text_block]
    mock_msg.usage.input_tokens = 100
    mock_msg.usage.output_tokens = 50
    mock_msg.usage.cache_creation_input_tokens = 0
    mock_msg.usage.cache_read_input_tokens = 0
    mock_anthropic_class.return_value.messages.create.return_value = mock_msg

    client = AnthropicLLMClient(api_key="sk-test")
    resp = client.complete(LLMRequest(system="SYS", messages=[{"role": "user", "content": "x"}]))

    assert resp.usage == {
        "input_tokens": 100,
        "output_tokens": 50,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }


def test_anthropic_client_raises_runtime_error_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY is not set"):
        AnthropicLLMClient()


def test_stub_llm_client_streaming_yields_canned_chunks():
    stub = StubLLMClient(responses=[], streaming_responses=[["Hello, ", "world", "!"]])
    req = LLMRequest(system="sys", messages=[{"role": "user", "content": "hi"}])

    chunks = list(stub.complete_streaming(req))

    assert chunks == ["Hello, ", "world", "!"]
    assert len(stub.streaming_calls) == 1
    assert stub.streaming_calls[0].system == "sys"


def test_stub_llm_client_streaming_raises_when_no_canned_responses():
    stub = StubLLMClient(responses=[], streaming_responses=[])
    req = LLMRequest(system="sys", messages=[{"role": "user", "content": "hi"}])

    with pytest.raises(RuntimeError, match="out of canned streaming responses"):
        stub.complete_streaming(req)
