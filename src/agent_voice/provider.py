"""Speech providers: consumer Edge plus official Azure and OpenAI APIs."""

from __future__ import annotations

import asyncio
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse
from xml.sax.saxutils import escape, quoteattr


class SpeechProvider(Protocol):
    name: str
    default_voice: str

    def save(
        self,
        text: str,
        output: Path,
        *,
        voice: str,
        rate: str,
        volume: str,
        pitch: str,
        timeout: float,
        model: str | None = None,
    ) -> None: ...


class EdgeProvider:
    name = "edge"
    default_voice = "ru-RU-DmitryNeural"

    def save(self, text: str, output: Path, *, voice: str, rate: str, volume: str,
             pitch: str, timeout: float, model: str | None = None) -> None:
        import edge_tts

        async def run() -> None:
            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
            await asyncio.wait_for(communicate.save(str(output)), timeout=timeout)

        asyncio.run(run())


class AzureProvider:
    """Official Azure Speech REST API provider."""

    name = "azure"
    default_voice = "ru-RU-DmitryNeural"

    def save(self, text: str, output: Path, *, voice: str, rate: str, volume: str,
             pitch: str, timeout: float, model: str | None = None) -> None:
        key = os.environ.get("AZURE_SPEECH_KEY")
        region = os.environ.get("AZURE_SPEECH_REGION")
        endpoint = os.environ.get("AZURE_SPEECH_ENDPOINT")
        if not key:
            raise RuntimeError("AZURE_SPEECH_KEY is required for the azure provider")
        if not endpoint:
            if not region:
                raise RuntimeError("AZURE_SPEECH_REGION or AZURE_SPEECH_ENDPOINT is required")
            if not re.fullmatch(r"[a-z0-9-]+", region):
                raise ValueError("AZURE_SPEECH_REGION contains unsupported characters")
            endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        parsed = urlparse(endpoint)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (
            host.endswith(".speech.microsoft.com") or host.endswith(".cognitiveservices.azure.com")
        ):
            raise ValueError("AZURE_SPEECH_ENDPOINT must be an official HTTPS Azure Speech endpoint")
        if not endpoint.rstrip("/").endswith("cognitiveservices/v1"):
            endpoint = endpoint.rstrip("/") + "/cognitiveservices/v1"
        language = "-".join(voice.split("-")[:2]) if "-" in voice else "en-US"
        ssml = (
            f"<speak version='1.0' xml:lang={quoteattr(language)}>"
            f"<voice name={quoteattr(voice)}>"
            f"<prosody rate={quoteattr(rate)} volume={quoteattr(volume)} pitch={quoteattr(pitch)}>"
            f"{escape(text)}</prosody></voice></speak>"
        ).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=ssml,
            method="POST",
            headers={
                "Ocp-Apim-Subscription-Key": key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
                "User-Agent": "agent-voice-kit",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            output.write_bytes(response.read())


class OpenAIProvider:
    """Official OpenAI Audio Speech REST API provider."""

    name = "openai"
    default_voice = "alloy"
    default_model = "gpt-4o-mini-tts"

    def save(self, text: str, output: Path, *, voice: str, rate: str, volume: str,
             pitch: str, timeout: float, model: str | None = None) -> None:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is required for the openai provider")
        if (rate, volume, pitch) != ("+0%", "+0%", "+0Hz"):
            raise ValueError("rate, volume and pitch controls are currently supported by edge/azure only")
        payload = json.dumps({
            "model": model or self.default_model,
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/audio/speech",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "agent-voice-kit",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            output.write_bytes(response.read())


def build_provider(name: str) -> SpeechProvider:
    providers = {"edge": EdgeProvider, "azure": AzureProvider, "openai": OpenAIProvider}
    try:
        return providers[name]()
    except KeyError as exc:
        raise ValueError(f"unsupported provider: {name}") from exc


def retryable_provider_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, asyncio.TimeoutError)):
        return True
    name = type(exc).__name__
    if name in {"NoAudioReceived", "WebSocketError", "ClientConnectionError", "ServerTimeoutError"}:
        return True
    status = getattr(exc, "status", None)
    if status is None:
        status = getattr(exc, "code", None)
    return status == 429 or isinstance(status, int) and 500 <= status <= 599


# Backward-compatible name for callers of the v0.2 API.
retryable_edge_error = retryable_provider_error
