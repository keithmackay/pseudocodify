# ABOUTME: Tests for pseudocode generation — headers, README index, per-file translation, and full runs.
# ABOUTME: Covers formatting, retry logic, failure markers, state persistence, and consolidation.

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from pseudocodify.generator import (
    build_pseudo_header,
    build_readme_index,
    build_generation_prompt,
    generate_file_pseudocode,
    run_generation,
    load_state,
    save_state,
)
from pseudocodify.models import CodebaseMap, FileAnalysis


# ── Task 5.1: Output formatting ──────────────────────────────────────────────

def test_build_pseudo_header():
    header = build_pseudo_header(
        source_path="src/models/user.py",
        language="Python",
        purpose="User data model",
    )
    assert "// SOURCE: src/models/user.py" in header
    assert "// LANGUAGE: Python" in header
    assert "// PURPOSE: User data model" in header
    assert "─" in header  # divider line


def test_build_readme_index():
    fa = FileAnalysis(
        path="src/models/user.py", language="Python", purpose="User model",
        constructs=[], external_deps=[], internal_refs=[], source_hash="x"
    )
    cm = CodebaseMap(
        source_root="/tmp/src", files={"src/models/user.py": fa},
        dominant_paradigm="OOP", recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00+00:00",
    )
    readme = build_readme_index(cm, style_name="CLRS/Cormen", architecture_summary="A simple app.")
    assert "# Pseudocode Index" in readme
    assert "## Architecture Summary" in readme
    assert "A simple app." in readme
    assert "## File Index" in readme
    assert "src/models/user.pseudo" in readme
    assert "User model" in readme


def test_build_readme_includes_timestamp():
    cm = CodebaseMap(
        source_root="/tmp/src", files={},
        dominant_paradigm="OOP", recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00+00:00",
    )
    readme = build_readme_index(cm, style_name="CLRS/Cormen", architecture_summary="x")
    assert "2026-04-17" in readme


# ── Task 5.2: Per-file pseudocode generation ─────────────────────────────────

def test_generate_file_pseudocode_writes_output(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    source_file = source_dir / "app.py"
    source_file.write_text("def hello(): pass")

    output_dir = tmp_path / "pseudocode"
    fa = FileAnalysis(
        path="src/app.py", language="Python", purpose="entry point",
        constructs=[], external_deps=[], internal_refs=[], source_hash="x"
    )
    cm = CodebaseMap(
        source_root=str(tmp_path), files={"src/app.py": fa},
        dominant_paradigm="OOP", recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00+00:00",
    )

    mock_adapter = MagicMock()
    mock_adapter.run.return_value = "FUNCTION hello()\n  // does nothing"

    from pseudocodify.styles import get_style
    style = get_style("cormen")
    generate_file_pseudocode(
        fa=fa, cm=cm, source_root=Path(str(tmp_path)),
        output_dir=output_dir, style=style, adapter=mock_adapter,
    )

    out_file = output_dir / "src" / "app.pseudo"
    assert out_file.exists()
    content = out_file.read_text()
    assert "// SOURCE: src/app.py" in content
    assert "FUNCTION hello()" in content


def test_generate_file_pseudocode_retries_on_empty(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "app.py").write_text("x = 1")
    output_dir = tmp_path / "pseudocode"

    fa = FileAnalysis(
        path="src/app.py", language="Python", purpose="x assignment",
        constructs=[], external_deps=[], internal_refs=[], source_hash="x"
    )
    cm = CodebaseMap(
        source_root=str(tmp_path), files={},
        dominant_paradigm="procedural", recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00+00:00",
    )
    mock_adapter = MagicMock()
    mock_adapter.run.side_effect = ["", "", "// file-level code\nx ← 1"]

    from pseudocodify.styles import get_style
    generate_file_pseudocode(
        fa=fa, cm=cm, source_root=Path(str(tmp_path)),
        output_dir=output_dir, style=get_style("cormen"), adapter=mock_adapter,
    )
    assert mock_adapter.run.call_count == 3


def test_translation_incomplete_marker_on_failure(tmp_path):
    (tmp_path / "app.py").write_text("x = 1")
    output_dir = tmp_path / "pseudocode"

    fa = FileAnalysis(
        path="app.py", language="Python", purpose="x",
        constructs=[], external_deps=[], internal_refs=[], source_hash="x"
    )
    cm = CodebaseMap(
        source_root=str(tmp_path), files={},
        dominant_paradigm="procedural", recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00+00:00",
    )
    mock_adapter = MagicMock()
    mock_adapter.run.return_value = ""

    from pseudocodify.styles import get_style
    result = generate_file_pseudocode(
        fa=fa, cm=cm, source_root=Path(str(tmp_path)),
        output_dir=output_dir, style=get_style("cormen"), adapter=mock_adapter,
    )
    out_file = output_dir / "app.pseudo"
    assert "[TRANSLATION INCOMPLETE" in out_file.read_text()
    assert result is False


# ── Task 5.3: Full generation run ────────────────────────────────────────────

def test_save_and_load_state(tmp_path):
    cache_dir = tmp_path / ".pseudocodify"
    save_state(cache_dir, style="cormen")
    state = load_state(cache_dir)
    assert state["last_style"] == "cormen"


def test_load_state_missing_returns_empty(tmp_path):
    cache_dir = tmp_path / ".pseudocodify"
    assert load_state(cache_dir) == {}


def test_run_generation_creates_readme(tmp_path, capsys):
    (tmp_path / "app.py").write_text("def main(): pass")
    output_dir = tmp_path / "out"

    fa = FileAnalysis(
        path="app.py", language="Python", purpose="entry",
        constructs=[], external_deps=[], internal_refs=[], source_hash="x"
    )
    cm = CodebaseMap(
        source_root=str(tmp_path), files={"app.py": fa},
        dominant_paradigm="OOP", recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00+00:00",
    )
    mock_adapter = MagicMock()
    mock_adapter.run.return_value = "FUNCTION main()\n  // entry point"

    from pseudocodify.config import RunConfig
    cfg = RunConfig(source=str(tmp_path), output=str(output_dir))
    run_generation(cm=cm, cfg=cfg, adapter=mock_adapter, architecture_summary="A simple app.")

    assert (output_dir / "README.pseudo.md").exists()
    assert (output_dir / "app.pseudo").exists()
    captured = capsys.readouterr()
    assert "Run complete" in captured.out


def test_run_generation_consolidate(tmp_path):
    (tmp_path / "app.py").write_text("def main(): pass")
    fa = FileAnalysis(
        path="app.py", language="Python", purpose="entry",
        constructs=[], external_deps=[], internal_refs=[], source_hash="x"
    )
    cm = CodebaseMap(
        source_root=str(tmp_path), files={"app.py": fa},
        dominant_paradigm="OOP", recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00+00:00",
    )
    mock_adapter = MagicMock()
    mock_adapter.run.return_value = "FUNCTION main()"

    from pseudocodify.config import RunConfig
    output_file = tmp_path / "all.pseudo.md"
    cfg = RunConfig(source=str(tmp_path), output=str(output_file), consolidate=True)
    run_generation(cm=cm, cfg=cfg, adapter=mock_adapter, architecture_summary="x")

    assert output_file.exists()
    content = output_file.read_text()
    assert "app.py" in content
