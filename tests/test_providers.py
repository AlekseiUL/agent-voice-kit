from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pytest

from agent_voice.provider import AzureProvider, OpenAIProvider, build_provider


class FakeResponse:
    def __init__(self, body: bytes = b"fake mp3"):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self.body


def test_provider_defaults():
    assert build_provider("edge").default_voice == "ru-RU-DmitryNeural"
    assert build_provider("azure").default_voice == "ru-RU-DmitryNeural"
    assert build_provider("openai").default_voice == "alloy"
    with pytest.raises(ValueError, match="unsupported provider"):
        build_provider("unknown")


def test_azure_provider_uses_official_api_without_leaking_key(monkeypatch, tmp_path):
    monkeypatch.setenv("AZURE_SPEECH_KEY", "private-key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "westeurope")
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    output = tmp_path / "azure.mp3"
    AzureProvider().save("A < B", output, voice="ru-RU-DmitryNeural", rate="+0%",
                         volume="+0%", pitch="+0Hz", timeout=12)

    request = captured["request"]
    assert request.full_url == "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1"
    assert b"A &lt; B" in request.data
    assert request.headers["Ocp-apim-subscription-key"] == "private-key"
    assert captured["timeout"] == 12
    assert output.read_bytes() == b"fake mp3"


def test_openai_provider_uses_official_speech_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "private-key")
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    output = tmp_path / "openai.mp3"
    OpenAIProvider().save("Hello", output, voice="alloy", rate="+0%", volume="+0%",
                          pitch="+0Hz", timeout=10, model="gpt-4o-mini-tts")

    request = captured["request"]
    payload = json.loads(request.data)
    assert request.full_url == "https://api.openai.com/v1/audio/speech"
    assert payload == {
        "model": "gpt-4o-mini-tts",
        "input": "Hello",
        "voice": "alloy",
        "response_format": "mp3",
    }
    assert request.headers["Authorization"] == "Bearer private-key"
    assert output.read_bytes() == b"fake mp3"


def test_openai_rejects_unimplemented_prosody(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "private-key")
    with pytest.raises(ValueError, match="edge/azure only"):
        OpenAIProvider().save("Hello", tmp_path / "x.mp3", voice="alloy", rate="+10%",
                              volume="+0%", pitch="+0Hz", timeout=10)
