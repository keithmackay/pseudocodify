import os
import pytest
from typer.testing import CliRunner
from unittest.mock import patch
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
