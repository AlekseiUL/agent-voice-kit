from __future__ import annotations

import json
from pathlib import Path

from agent_voice import cli
from agent_voice.diagnostics import doctor


ROOT = Path(__file__).resolve().parents[1]


def test_doctor_reports_local_prerequisites(tmp_path):
    report = doctor(tmp_path / "cache")
    assert report["network_checked"] is False
    assert report["checks"]["edge_tts_installed"] is True
    assert report["checks"]["cache_writable"] is True
    assert set(report["checks"]) == {
        "edge_tts_installed",
        "ffmpeg_available",
        "ffprobe_available",
        "libopus_available",
        "libmp3lame_available",
        "cache_writable",
    }


def test_cli_doctor_needs_no_synthesis_input(monkeypatch, capsys):
    expected = {
        "ready": True,
        "network_checked": False,
        "checks": {"example": True},
        "next_step": "Run a live test.",
    }
    monkeypatch.setattr(cli, "doctor", lambda cache_dir, provider: expected)
    assert cli.main(["--doctor", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == expected


def test_agent_install_contract_and_hermes_skill_match_release():
    contract = (ROOT / "INSTALL_FOR_AGENTS.md").read_text(encoding="utf-8")
    setup = (ROOT / "docs" / "AGENT_SETUP.md").read_text(encoding="utf-8")
    skill = (ROOT / "integrations" / "hermes" / "SKILL.md").read_text(encoding="utf-8")

    assert "v0.3.1" in contract
    assert "v0.3.1" in setup
    assert "version: 0.3.1" in skill
    assert "--name agent-voice --yes" in contract
    assert "agent-voice --doctor --json" in contract
    assert "[[audio_as_voice]]" in skill
    assert "MEDIA:/absolute/path/to/result.ogg" in skill
    assert "Microsoft" in skill


def test_cli_accepts_non_markdown_utf8_text_file(monkeypatch, tmp_path, capsys):
    source = tmp_path / "notes.log"
    source.write_text("literal **markers**", encoding="utf-8")
    captured = {}

    class Result:
        def receipt(self):
            return {"provider": "edge", "output": "voice.ogg"}

    def fake_synthesize(text, output, **kwargs):
        captured.update(text=text, output=output, **kwargs)
        return Result()

    monkeypatch.setattr(cli, "synthesize", fake_synthesize)
    assert cli.main([str(source), "--output", str(tmp_path / "voice.ogg"), "--json"]) == 0
    assert captured["text"] == "literal **markers**"
    assert captured["markdown"] is False
    assert json.loads(capsys.readouterr().out)["success"] is True
