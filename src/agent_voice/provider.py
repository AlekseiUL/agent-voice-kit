"""Microsoft Edge Read Aloud provider through the independent edge-tts client."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol


class SpeechProvider(Protocol):
    def save(self, text: str, output: Path, *, voice: str, rate: str, volume: str, pitch: str, timeout: float) -> None: ...


class EdgeProvider:
    def save(self, text: str, output: Path, *, voice: str, rate: str, volume: str, pitch: str, timeout: float) -> None:
        import edge_tts

        async def run() -> None:
            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
            await asyncio.wait_for(communicate.save(str(output)), timeout=timeout)

        asyncio.run(run())


def retryable_edge_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, asyncio.TimeoutError)):
        return True
    name = type(exc).__name__
    if name in {"NoAudioReceived", "WebSocketError", "ClientConnectionError", "ServerTimeoutError"}:
        return True
    status = getattr(exc, "status", None)
    return status == 429 or isinstance(status, int) and 500 <= status <= 599
