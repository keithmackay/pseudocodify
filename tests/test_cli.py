import json
import os
import pytest
from typer.testing import CliRunner
from unittest.mock import MagicMock, patch
from pseudocodify.cli import app

runner = CliRunner()

def test_invalid_style_exits_with_error():
    result = runner.invoke(app, [".", "--style", "badstyle"])
    assert result.exit_code != 0
    assert "badstyle" in result.output or "badstyle" in str(result.exception or "")

def test_missing_api_key_exits_with_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = runner.invoke(app, ["."])
    assert result.exit_code != 0
    assert "ANTHROPIC_API_KEY" in result.output

def test_help_shows_flags():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "--style" in result.output
    assert "--model" in result.output


def test_full_run_analyzes_and_generates_pseudocode(tmp_path, monkeypatch):
    """End-to-end happy path: analysis -> auto style selection -> generation."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("def main(): pass")

    output = tmp_path / "out"

    extraction_response = json.dumps({
        "path": "app.py", "language": "Python", "purpose": "entry point",
        "constructs": [{"name": "main", "file": "app.py", "kind": "function"}],
        "external_deps": [], "internal_refs": [],
    })
    generation_response = "FUNCTION main()\n    return"
    architecture_summary_response = "A small single-file Python script."

    mock_adapter = MagicMock()
    mock_adapter.run.side_effect = [
        extraction_response,
        architecture_summary_response,
        generation_response,
    ]

    with patch("pseudocodify.rlm_adapter.RLMAdapter", return_value=mock_adapter):
        result = runner.invoke(app, [
            str(source), "--output", str(output), "--yes",
        ])

    assert result.exit_code == 0, result.output
    assert "Done." in result.output
    assert (output / "app.pseudo").exists()
    assert "FUNCTION main()" in (output / "app.pseudo").read_text()
    assert (output / "README.pseudo.md").exists()
