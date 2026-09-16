from agent_voice.text import markdown_to_text, split_text


def test_markdown_normalization_preserves_meaning():
    source = "# Title\n\n- **Bold** [label](https://example.com)\n\n`code`"
    assert markdown_to_text(source) == "Title Bold label code"


def test_chunking_preserves_normalized_text():
    text = " ".join(f"word{i}" for i in range(80))
    chunks = split_text(text, 100)
    assert len(chunks) > 1
    assert " ".join(chunks) == text
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_chunk_limit_guard():
    try:
        split_text("hello", 99)
    except ValueError as exc:
        assert "at least 100" in str(exc)
    else:
        raise AssertionError("expected ValueError")
