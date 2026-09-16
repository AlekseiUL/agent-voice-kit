"""Small, deterministic Markdown-to-speech normalization and chunking."""

from __future__ import annotations

import html
import re


def markdown_to_text(value: str) -> str:
    """Remove common Markdown controls while preserving readable content."""
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\A---\s*\n.*?\n---\s*(?:\n|\Z)", "", text, flags=re.DOTALL)
    text = re.sub(r"```[^\n]*\n(.*?)```", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*(?:[-+*]|\d+[.)])\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~]{1,3}", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(html.unescape(text).split())


def split_text(value: str, max_chars: int) -> list[str]:
    """Split text without dropping characters, preferring sentence and word boundaries."""
    if max_chars < 100:
        raise ValueError("max_chars must be at least 100")
    normalized = " ".join(value.split())
    if not normalized:
        return []
    if len(normalized) <= max_chars:
        return [normalized]
    sentences = [part.strip() for part in re.split(r"(?<=[.!?;:,])\s+", normalized) if part.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        words = sentence.split()
        pieces: list[str] = []
        piece = ""
        for word in words:
            if len(word) > max_chars:
                if piece:
                    pieces.append(piece)
                    piece = ""
                pieces.extend(word[i:i + max_chars] for i in range(0, len(word), max_chars))
                continue
            candidate = f"{piece} {word}".strip()
            if piece and len(candidate) > max_chars:
                pieces.append(piece)
                piece = word
            else:
                piece = candidate
        if piece:
            pieces.append(piece)
        for item in pieces:
            candidate = f"{current} {item}".strip()
            if current and len(candidate) > max_chars:
                chunks.append(current)
                current = item
            else:
                current = candidate
    if current:
        chunks.append(current)
    return chunks
