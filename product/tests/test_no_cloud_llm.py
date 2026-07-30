"""Guardrail: product/ must only ever call the local Ollama backend, never a paid cloud LLM API."""

import re
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"

FORBIDDEN_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(anthropic|openai)\b", re.MULTILINE)
FORBIDDEN_ENV_VARS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")


def _source_files():
    return SRC_ROOT.rglob("*.py")


def test_no_cloud_llm_imports():
    offenders = [
        f"{path}: imports {match.group(1)!r}"
        for path in _source_files()
        for match in FORBIDDEN_IMPORT_RE.finditer(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, "product/ must only use the local Ollama backend:\n" + "\n".join(offenders)


def test_no_cloud_llm_api_keys():
    offenders = [
        f"{path}: references {name!r}"
        for path in _source_files()
        for name in FORBIDDEN_ENV_VARS
        if name in path.read_text(encoding="utf-8")
    ]
    assert not offenders, "product/ must never read a cloud LLM API key:\n" + "\n".join(offenders)
