import json


def test_sse_formats_event_and_data():
    from lean_agent.api_routes._sse import sse

    record = sse("token", {"text": "hello"})

    assert record == 'event: token\ndata: {"text": "hello"}\n\n'


def test_sse_handles_unicode_in_data():
    from lean_agent.api_routes._sse import sse

    record = sse("token", {"text": "héllo — world"})

    # ensure_ascii=False so the wire format is utf-8 directly, not \u escapes
    assert "héllo" in record
    assert "—" in record


def test_sse_done_event_with_full_content():
    from lean_agent.api_routes._sse import sse

    record = sse("done", {"ok": True, "content": "abc"})

    assert "event: done" in record
    parsed = json.loads(record.split("data: ")[1].rstrip("\n"))
    assert parsed == {"ok": True, "content": "abc"}
