import hashlib
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from pseudocodify.analyzer import (
    discover_files, hash_file, RECOGNIZED_EXTENSIONS,
    save_codebase_map, load_codebase_map,
    analyze_file, build_extraction_prompt,
    run_analysis,
)
from pseudocodify.models import CodebaseMap, FileAnalysis


# --- Task 4.1: File discovery and hashing ---

def test_discover_files_finds_python_files(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "README.md").write_text("# docs")
    (tmp_path / "image.png").write_bytes(b"\x89PNG")
    files = discover_files(tmp_path)
    paths = [str(f) for f in files]
    assert any("main.py" in p for p in paths)
    assert not any("README.md" in p for p in paths)
    assert not any("image.png" in p for p in paths)

def test_discover_files_respects_exclude(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x = 1")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("assert True")
    files = discover_files(tmp_path, exclude=["tests/**"])
    paths = [str(f) for f in files]
    assert any("app.py" in p for p in paths)
    assert not any("test_app.py" in p for p in paths)

def test_discover_files_respects_include(tmp_path):
    (tmp_path / "app.py").write_text("x = 1")
    (tmp_path / "app.js").write_text("const x = 1")
    files = discover_files(tmp_path, include=["*.py"])
    paths = [str(f) for f in files]
    assert any("app.py" in p for p in paths)
    assert not any("app.js" in p for p in paths)

def test_hash_file_returns_sha256(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("hello")
    h = hash_file(f)
    expected = hashlib.sha256(b"hello").hexdigest()
    assert h == expected

def test_hash_file_changes_with_content(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("hello")
    h1 = hash_file(f)
    f.write_text("world")
    h2 = hash_file(f)
    assert h1 != h2


# --- Task 4.2: Cache read/write ---

def test_save_and_load_codebase_map(tmp_path):
    cache_dir = tmp_path / ".pseudocodify"
    cm = CodebaseMap(
        source_root=str(tmp_path),
        files={},
        dominant_paradigm="OOP",
        recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00+00:00",
    )
    save_codebase_map(cm, cache_dir)
    loaded = load_codebase_map(cache_dir)
    assert loaded is not None
    assert loaded.dominant_paradigm == "OOP"

def test_load_returns_none_when_missing(tmp_path):
    cache_dir = tmp_path / ".pseudocodify"
    result = load_codebase_map(cache_dir)
    assert result is None

def test_cached_hashes_are_reused(tmp_path):
    cache_dir = tmp_path / ".pseudocodify"
    fa = FileAnalysis(
        path="src/main.py", language="Python", purpose="entry point",
        constructs=[], external_deps=[], internal_refs=[], source_hash="abc123"
    )
    cm = CodebaseMap(
        source_root=str(tmp_path), files={"src/main.py": fa},
        dominant_paradigm="OOP", recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00+00:00",
    )
    save_codebase_map(cm, cache_dir)
    loaded = load_codebase_map(cache_dir)
    assert loaded.files["src/main.py"].source_hash == "abc123"


# --- Task 4.3: LLM structure extraction ---

def test_analyze_file_returns_file_analysis(tmp_path):
    src = tmp_path / "app.py"
    src.write_text("def hello(): pass")

    valid_response = """{
        "path": "app.py", "language": "Python", "purpose": "entry point",
        "constructs": [{"name": "hello", "file": "app.py", "kind": "function"}],
        "external_deps": [], "internal_refs": []
    }"""
    mock_adapter = MagicMock()
    mock_adapter.run.return_value = valid_response

    result = analyze_file(src, source_root=tmp_path, adapter=mock_adapter)
    assert result is not None
    assert result.language == "Python"
    assert result.source_hash == hash_file(src)

def test_analyze_file_retries_on_invalid_json(tmp_path):
    src = tmp_path / "app.py"
    src.write_text("x = 1")

    valid_response = """{
        "path": "app.py", "language": "Python", "purpose": "x assignment",
        "constructs": [], "external_deps": [], "internal_refs": []
    }"""
    mock_adapter = MagicMock()
    mock_adapter.run.side_effect = ["not json", "still not json", valid_response]

    result = analyze_file(src, source_root=tmp_path, adapter=mock_adapter)
    assert result is not None
    assert mock_adapter.run.call_count == 3

def test_analyze_file_returns_none_after_3_failures(tmp_path):
    src = tmp_path / "app.py"
    src.write_text("x = 1")

    mock_adapter = MagicMock()
    mock_adapter.run.return_value = "not json at all"

    result = analyze_file(src, source_root=tmp_path, adapter=mock_adapter)
    assert result is None
    assert mock_adapter.run.call_count == 3

def test_build_extraction_prompt_contains_schema():
    prompt = build_extraction_prompt("def f(): pass", language="Python")
    assert "Python" in prompt
    assert "constructs" in prompt
    assert "external_deps" in prompt


# --- Task 4.4: CodebaseMap assembly ---

def test_run_analysis_builds_codebase_map(tmp_path):
    (tmp_path / "app.py").write_text("def main(): pass")
    (tmp_path / ".pseudocodify").mkdir()

    fa_data = {
        "path": "app.py", "language": "Python", "purpose": "entry point",
        "constructs": [], "external_deps": [], "internal_refs": [], "source_hash": "x"
    }
    mock_adapter = MagicMock()
    mock_adapter.run.return_value = json.dumps({
        k: v for k, v in fa_data.items() if k != "source_hash"
    })

    from pseudocodify.config import RunConfig
    cfg = RunConfig(source=str(tmp_path))
    cm = run_analysis(cfg, adapter=mock_adapter)
    assert "app.py" in cm.files
    assert cm.dominant_paradigm in ["OOP", "functional", "procedural", "mixed"]

def test_run_analysis_skips_unchanged_files(tmp_path):
    src = tmp_path / "app.py"
    src.write_text("x = 1")
    cache_dir = tmp_path / ".pseudocodify"

    fa = FileAnalysis(
        path="app.py", language="Python", purpose="cached",
        constructs=[], external_deps=[], internal_refs=[],
        source_hash=hash_file(src),
    )
    cm = CodebaseMap(
        source_root=str(tmp_path), files={"app.py": fa},
        dominant_paradigm="procedural", recommended_style="pascal",
        analysis_timestamp="2026-04-17T00:00:00+00:00",
    )
    save_codebase_map(cm, cache_dir)

    mock_adapter = MagicMock()
    from pseudocodify.config import RunConfig
    cfg = RunConfig(source=str(tmp_path))
    result = run_analysis(cfg, adapter=mock_adapter)
    mock_adapter.run.assert_not_called()
    assert result.files["app.py"].purpose == "cached"
