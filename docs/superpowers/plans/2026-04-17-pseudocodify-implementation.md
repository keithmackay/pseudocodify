# pseudocodify Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool that converts any codebase into standard pseudocode using a two-phase LLM pipeline (analysis then generation), with RLM support for large codebases.

**Architecture:** Phase 1 analyzes the codebase into a `CodebaseMap` JSON artifact; Phase 2 generates `.pseudo` files from that map using style-specific prompts. The `rlms` package handles recursive decomposition when files or codebases exceed context limits.

**Tech Stack:** Python 3.11+, Typer (CLI), Pydantic v2, Anthropic SDK, rlms (PyPI), tomllib (stdlib), pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Package metadata, dependencies, entry point |
| `pseudocodify/__init__.py` | Package init |
| `pseudocodify/models.py` | Pydantic data models: `ExternalDep`, `ConstructRef`, `FileAnalysis`, `CodebaseMap` |
| `pseudocodify/rlm_adapter.py` | Thin wrapper around `rlms`: `RLMAdapter` class, `RLMError` exception |
| `pseudocodify/styles/__init__.py` | Style registry: load style by name, list available styles |
| `pseudocodify/styles/cormen.py` | CLRS/Cormen style: `SYSTEM_PROMPT`, `STYLE_NAME`, `PARADIGM_FIT` |
| `pseudocodify/styles/structured_english.py` | Structured English style |
| `pseudocodify/styles/pascal.py` | Pascal-like style |
| `pseudocodify/config.py` | Config loading: `.pseudocodify.toml` + CLI flag merging → `RunConfig` dataclass |
| `pseudocodify/analyzer.py` | Phase 1: file discovery, LLM structure extraction, `CodebaseMap` assembly, cache read/write |
| `pseudocodify/generator.py` | Phase 2: per-file pseudocode generation, output writing, consolidation, README generation |
| `pseudocodify/cli.py` | Typer CLI entry point, startup validation, interactive style prompt, run orchestration |
| `tests/test_models.py` | Unit tests for Pydantic models |
| `tests/test_config.py` | Unit tests for config loading and merging |
| `tests/test_analyzer.py` | Unit tests for file discovery, hash computation, cache logic |
| `tests/test_generator.py` | Unit tests for output formatting, header generation, consolidation |
| `tests/test_styles.py` | Unit tests for style registry and style module contracts |
| `tests/test_rlm_adapter.py` | Unit tests for RLMAdapter and RLMError |
| `tests/test_cli.py` | Integration tests for CLI flag parsing and startup validation |

---

## Phase 1: Project Scaffold

### Task 1.1: Initialize Python package

**Files:**
- Create: `pyproject.toml`
- Create: `pseudocodify/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pseudocodify"
version = "0.1.0"
description = "Convert any codebase to pseudocode"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12",
    "anthropic>=0.25",
    "rlms>=0.1",
    "pydantic>=2.0",
]

[project.scripts]
pseudocodify = "pseudocodify.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create package files**

```python
# pseudocodify/__init__.py
# (empty)
```

```python
# tests/__init__.py
# (empty)
```

- [ ] **Step 3: Install the package in development mode**

```bash
pip install -e ".[dev]" 2>/dev/null || pip install -e .
pip install pytest pytest-mock
```

Expected: no errors, `pseudocodify` importable.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml pseudocodify/__init__.py tests/__init__.py
git commit -m "feat: initialize pseudocodify package scaffold"
```

---

### Task 1.2: Data models

**Files:**
- Create: `pseudocodify/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models.py
import pytest
from pseudocodify.models import ExternalDep, ConstructRef, FileAnalysis, CodebaseMap

def test_external_dep_fields():
    dep = ExternalDep(name="bcrypt", description="hashes passwords", known=True)
    assert dep.name == "bcrypt"
    assert dep.known is True

def test_construct_ref_kind_validation():
    ref = ConstructRef(name="User", file="models.py", kind="class")
    assert ref.kind == "class"

def test_file_analysis_serialization():
    fa = FileAnalysis(
        path="src/models.py",
        language="Python",
        purpose="User model",
        constructs=[],
        external_deps=[],
        internal_refs=[],
        source_hash="abc123",
    )
    data = fa.model_dump()
    assert data["path"] == "src/models.py"
    assert data["source_hash"] == "abc123"

def test_codebase_map_dominant_paradigm_values():
    valid = ["OOP", "functional", "procedural", "mixed"]
    for paradigm in valid:
        cm = CodebaseMap(
            source_root="/tmp/src",
            files={},
            dominant_paradigm=paradigm,
            recommended_style="cormen",
            analysis_timestamp="2026-04-17T00:00:00Z",
        )
        assert cm.dominant_paradigm == paradigm

def test_codebase_map_recommended_style_values():
    valid = ["cormen", "structured-english", "pascal"]
    for style in valid:
        cm = CodebaseMap(
            source_root="/tmp/src",
            files={},
            dominant_paradigm="OOP",
            recommended_style=style,
            analysis_timestamp="2026-04-17T00:00:00Z",
        )
        assert cm.recommended_style == style
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'pseudocodify.models'`

- [ ] **Step 3: Implement models**

```python
# pseudocodify/models.py
from typing import Literal
from pydantic import BaseModel

class ExternalDep(BaseModel):
    name: str
    description: str
    known: bool

class ConstructRef(BaseModel):
    name: str
    file: str
    kind: Literal["function", "class", "variable", "method"]

class FileAnalysis(BaseModel):
    path: str
    language: str
    purpose: str
    constructs: list[ConstructRef]
    external_deps: list[ExternalDep]
    internal_refs: list[tuple[str, str]]
    source_hash: str

class CodebaseMap(BaseModel):
    source_root: str
    files: dict[str, FileAnalysis]
    dominant_paradigm: Literal["OOP", "functional", "procedural", "mixed"]
    recommended_style: Literal["cormen", "structured-english", "pascal"]
    analysis_timestamp: str
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/models.py tests/test_models.py
git commit -m "feat: add Pydantic data models"
```

---

### Task 1.3: Config loading

**Files:**
- Create: `pseudocodify/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_config.py
import tomllib
import pytest
from pathlib import Path
from pseudocodify.config import RunConfig, load_config

def test_defaults():
    cfg = RunConfig()
    assert cfg.style == "auto"
    assert cfg.consolidate is False
    assert cfg.output == "./pseudocode"
    assert cfg.model == "claude-opus-4-6"
    assert cfg.yes is False
    assert cfg.verbose is False

def test_toml_overrides_defaults(tmp_path):
    toml_file = tmp_path / ".pseudocodify.toml"
    toml_file.write_text('[pseudocodify]\nstyle = "pascal"\nconsolidate = true\n')
    cfg = load_config(toml_path=toml_file)
    assert cfg.style == "pascal"
    assert cfg.consolidate is True
    assert cfg.output == "./pseudocode"  # default unchanged

def test_cli_overrides_toml(tmp_path):
    toml_file = tmp_path / ".pseudocodify.toml"
    toml_file.write_text('[pseudocodify]\nstyle = "pascal"\n')
    cfg = load_config(toml_path=toml_file, cli_overrides={"style": "cormen"})
    assert cfg.style == "cormen"

def test_malformed_toml_raises(tmp_path):
    toml_file = tmp_path / ".pseudocodify.toml"
    toml_file.write_text("not valid toml ][")
    with pytest.raises(SystemExit):
        load_config(toml_path=toml_file)

def test_missing_toml_uses_defaults():
    cfg = load_config(toml_path=Path("/nonexistent/.pseudocodify.toml"))
    assert cfg.style == "auto"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'pseudocodify.config'`

- [ ] **Step 3: Implement config**

```python
# pseudocodify/config.py
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class RunConfig:
    source: str = "."
    output: str = "./pseudocode"
    consolidate: bool = False
    style: str = "auto"
    model: str = "claude-opus-4-6"
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    yes: bool = False
    verbose: bool = False

def load_config(
    toml_path: Path | None = None,
    cli_overrides: dict | None = None,
) -> RunConfig:
    cfg = RunConfig()
    if toml_path and toml_path.exists():
        try:
            with open(toml_path, "rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            print(f"Error: malformed .pseudocodify.toml — {e}", file=sys.stderr)
            raise SystemExit(1)
        section = data.get("pseudocodify", {})
        for key, value in section.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
    if cli_overrides:
        for key, value in cli_overrides.items():
            if value is not None and hasattr(cfg, key):
                setattr(cfg, key, value)
    return cfg
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/config.py tests/test_config.py
git commit -m "feat: add config loading with TOML and CLI override support"
```

---

## Phase 2: Style Modules

### Task 2.1: Style registry and contracts

**Files:**
- Create: `pseudocodify/styles/__init__.py`
- Create: `pseudocodify/styles/cormen.py`
- Create: `pseudocodify/styles/structured_english.py`
- Create: `pseudocodify/styles/pascal.py`
- Create: `tests/test_styles.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_styles.py
import pytest
from pseudocodify.styles import get_style, list_styles, VALID_STYLES

def test_list_styles_returns_all_three():
    styles = list_styles()
    assert set(styles) == {"cormen", "structured-english", "pascal"}

def test_get_style_cormen():
    style = get_style("cormen")
    assert hasattr(style, "SYSTEM_PROMPT")
    assert hasattr(style, "STYLE_NAME")
    assert hasattr(style, "PARADIGM_FIT")
    assert isinstance(style.SYSTEM_PROMPT, str)
    assert len(style.SYSTEM_PROMPT) > 50
    assert isinstance(style.PARADIGM_FIT, list)

def test_get_style_all_valid():
    for name in ["cormen", "structured-english", "pascal"]:
        style = get_style(name)
        assert style.STYLE_NAME  # non-empty

def test_get_style_invalid_raises():
    with pytest.raises(ValueError, match="Unknown style"):
        get_style("nonexistent")

def test_paradigm_fit_values_are_valid():
    valid_paradigms = {"OOP", "functional", "procedural", "mixed"}
    for name in list_styles():
        style = get_style(name)
        for p in style.PARADIGM_FIT:
            assert p in valid_paradigms, f"{name}.PARADIGM_FIT contains invalid value: {p}"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_styles.py -v
```

Expected: `ModuleNotFoundError: No module named 'pseudocodify.styles'`

- [ ] **Step 3: Implement style modules**

```python
# pseudocodify/styles/cormen.py
STYLE_NAME = "CLRS/Cormen"
PARADIGM_FIT = ["OOP", "functional"]
SYSTEM_PROMPT = """
You are a pseudocode translator using CLRS/Cormen textbook notation.

Rules:
- Assignment: use ← (e.g., x ← 5)
- Blocks: indentation only, no BEGIN/END delimiters
- Keywords: if, else, for, while, return, and, or, not (all lowercase)
- Constants and global names: SMALL-CAPS
- Function declarations: FUNCTION name(param1, param2)
- Procedure declarations: PROCEDURE name(param1, param2)
- Comments: // comment text
- External calls: call_site()  // [EXTERNAL: library] one-sentence description
- Multi-return: return (value1, value2)
- Attributes: referenced as object.attribute

Translate the provided source code to pseudocode following these rules exactly.
Preserve all logic. Do not omit any construct. Output plain text only.
""".strip()
```

```python
# pseudocodify/styles/structured_english.py
STYLE_NAME = "Structured English"
PARADIGM_FIT = ["procedural", "mixed"]
SYSTEM_PROMPT = """
You are a pseudocode translator using Structured English notation.

Rules:
- Assignment: set x to value
- Conditionals: if <condition> then: / else:
- Loops: for each <item> in <collection> do: / while <condition> do:
- Function declarations: define <name>(<params>):
- Return: return <value>
- Comments: // comment text
- External calls: call <name>(<args>)  // [EXTERNAL: library] one-sentence description
- Multi-return: return (<value1>, <value2>)
- No formal keyword set beyond the above — prioritize readability over formality

Translate the provided source code to pseudocode following these rules exactly.
Preserve all logic. Do not omit any construct. Output plain text only.
""".strip()
```

```python
# pseudocodify/styles/pascal.py
STYLE_NAME = "Pascal-like"
PARADIGM_FIT = ["procedural", "OOP"]
SYSTEM_PROMPT = """
You are a pseudocode translator using Pascal-like notation.

Rules:
- Assignment: :=  (e.g., x := 5)
- Blocks: BEGIN ... END
- Conditionals: IF <condition> THEN BEGIN ... END ELSE BEGIN ... END
- Loops: FOR <var> := <start> TO <end> DO BEGIN ... END
         WHILE <condition> DO BEGIN ... END
- Function declarations: FUNCTION name(param1: type): return_type
- Procedure declarations: PROCEDURE name(param1: type)
- Return: RETURN <value>
- Comments: // comment text
- External calls: <name>(<args>)  // [EXTERNAL: library] one-sentence description

Translate the provided source code to pseudocode following these rules exactly.
Preserve all logic. Do not omit any construct. Output plain text only.
""".strip()
```

```python
# pseudocodify/styles/__init__.py
import types
from pseudocodify.styles import cormen, structured_english, pascal

VALID_STYLES: dict[str, types.ModuleType] = {
    "cormen": cormen,
    "structured-english": structured_english,
    "pascal": pascal,
}

def get_style(name: str) -> types.ModuleType:
    if name not in VALID_STYLES:
        raise ValueError(f"Unknown style '{name}'. Valid options: {list(VALID_STYLES)}")
    return VALID_STYLES[name]

def list_styles() -> list[str]:
    return list(VALID_STYLES.keys())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_styles.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/styles/ tests/test_styles.py
git commit -m "feat: add style modules (cormen, structured-english, pascal) and registry"
```

---

## Phase 3: RLM Adapter

### Task 3.1: RLMAdapter and RLMError

**Files:**
- Create: `pseudocodify/rlm_adapter.py`
- Create: `tests/test_rlm_adapter.py`

> **Context:** The `rlms` package (`pip install rlms`) is the Recursive Language Models library. Import with `from rlm import RLM`. Initialize with `RLM(backend="anthropic", backend_kwargs={"model_name": model})`. Call with `rlm.completion(prompt).response`. Do NOT import `rlms` exceptions directly in other modules — wrap them in `RLMError`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_rlm_adapter.py
import pytest
from unittest.mock import MagicMock, patch
from pseudocodify.rlm_adapter import RLMAdapter, RLMError

def test_run_returns_response_string():
    mock_completion = MagicMock()
    mock_completion.response = "translated output"
    mock_rlm = MagicMock()
    mock_rlm.completion.return_value = mock_completion

    with patch("pseudocodify.rlm_adapter.RLM", return_value=mock_rlm):
        adapter = RLMAdapter(model="claude-opus-4-6")
        result = adapter.run("translate this")
    assert result == "translated output"

def test_run_with_context_prepends_context():
    mock_completion = MagicMock()
    mock_completion.response = "output"
    mock_rlm = MagicMock()
    mock_rlm.completion.return_value = mock_completion

    with patch("pseudocodify.rlm_adapter.RLM", return_value=mock_rlm):
        adapter = RLMAdapter(model="claude-opus-4-6")
        adapter.run("prompt", context="extra context")

    call_args = mock_rlm.completion.call_args[0][0]
    assert "extra context" in call_args
    assert "prompt" in call_args

def test_rlm_exception_wrapped_as_rlm_error():
    mock_rlm = MagicMock()
    mock_rlm.completion.side_effect = Exception("rlms internal error")

    with patch("pseudocodify.rlm_adapter.RLM", return_value=mock_rlm):
        adapter = RLMAdapter(model="claude-opus-4-6")
        with pytest.raises(RLMError, match="rlms internal error"):
            adapter.run("prompt")

def test_rlm_error_is_not_base_exception():
    assert issubclass(RLMError, Exception)
    assert not issubclass(RLMError, BaseException) or issubclass(RLMError, Exception)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_rlm_adapter.py -v
```

Expected: `ModuleNotFoundError: No module named 'pseudocodify.rlm_adapter'`

- [ ] **Step 3: Implement RLMAdapter**

```python
# pseudocodify/rlm_adapter.py
from rlm import RLM


class RLMError(Exception):
    """Wraps any exception raised by the rlms library."""


class RLMAdapter:
    def __init__(self, model: str, verbose: bool = False):
        self._rlm = RLM(
            backend="anthropic",
            backend_kwargs={"model_name": model},
            verbose=verbose,
        )

    def run(self, prompt: str, context: str | None = None) -> str:
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        try:
            result = self._rlm.completion(full_prompt)
            return result.response
        except Exception as e:
            raise RLMError(str(e)) from e
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_rlm_adapter.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/rlm_adapter.py tests/test_rlm_adapter.py
git commit -m "feat: add RLMAdapter wrapping rlms package"
```

---

## Phase 4: Analyzer (Phase 1)

### Task 4.1: File discovery and hashing

**Files:**
- Create: `pseudocodify/analyzer.py`
- Create: `tests/test_analyzer.py`

- [ ] **Step 1: Write failing tests for file discovery**

```python
# tests/test_analyzer.py
import hashlib
import pytest
from pathlib import Path
from pseudocodify.analyzer import discover_files, hash_file, RECOGNIZED_EXTENSIONS

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_analyzer.py -v
```

Expected: `ModuleNotFoundError: No module named 'pseudocodify.analyzer'`

- [ ] **Step 3: Implement file discovery and hashing**

```python
# pseudocodify/analyzer.py
import hashlib
import fnmatch
from pathlib import Path

RECOGNIZED_EXTENSIONS = {
    ".py", ".js", ".ts", ".go", ".rb", ".java", ".cs",
    ".cpp", ".c", ".rs", ".php", ".swift", ".kt", ".scala",
    ".r", ".m", ".sh", ".bash", ".pl", ".lua",
}

def discover_files(
    source: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[Path]:
    results = []
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in RECOGNIZED_EXTENSIONS:
            continue
        rel = path.relative_to(source)
        rel_str = str(rel)
        if exclude:
            if any(fnmatch.fnmatch(rel_str, pat) for pat in exclude):
                continue
        if include:
            if not any(fnmatch.fnmatch(rel_str, pat) for pat in include):
                continue
        results.append(path)
    return sorted(results)

def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_analyzer.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/analyzer.py tests/test_analyzer.py
git commit -m "feat: add file discovery and SHA-256 hashing"
```

---

### Task 4.2: Cache read/write

**Files:**
- Modify: `pseudocodify/analyzer.py`
- Modify: `tests/test_analyzer.py`

- [ ] **Step 1: Write failing tests for cache**

Add to `tests/test_analyzer.py`:

```python
from pseudocodify.analyzer import save_codebase_map, load_codebase_map
from pseudocodify.models import CodebaseMap

def test_save_and_load_codebase_map(tmp_path):
    cache_dir = tmp_path / ".pseudocodify"
    cm = CodebaseMap(
        source_root=str(tmp_path),
        files={},
        dominant_paradigm="OOP",
        recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00Z",
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
    from pseudocodify.models import FileAnalysis
    fa = FileAnalysis(
        path="src/main.py", language="Python", purpose="entry point",
        constructs=[], external_deps=[], internal_refs=[], source_hash="abc123"
    )
    cm = CodebaseMap(
        source_root=str(tmp_path), files={"src/main.py": fa},
        dominant_paradigm="OOP", recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00Z",
    )
    save_codebase_map(cm, cache_dir)
    loaded = load_codebase_map(cache_dir)
    assert loaded.files["src/main.py"].source_hash == "abc123"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_analyzer.py::test_save_and_load_codebase_map -v
```

Expected: `ImportError` or `AttributeError`

- [ ] **Step 3: Implement cache functions**

Add to `pseudocodify/analyzer.py`:

```python
import json
from pseudocodify.models import CodebaseMap

def save_codebase_map(cm: CodebaseMap, cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "analysis.json").write_text(cm.model_dump_json(indent=2))

def load_codebase_map(cache_dir: Path) -> CodebaseMap | None:
    path = cache_dir / "analysis.json"
    if not path.exists():
        return None
    return CodebaseMap.model_validate_json(path.read_text())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_analyzer.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/analyzer.py tests/test_analyzer.py
git commit -m "feat: add CodebaseMap cache save/load"
```

---

### Task 4.3: LLM structure extraction

**Files:**
- Modify: `pseudocodify/analyzer.py`
- Modify: `tests/test_analyzer.py`

> **Context:** `analyze_file` calls `RLMAdapter.run()` with a prompt asking the LLM to return a JSON object matching the `FileAnalysis` schema (minus `source_hash`). On invalid JSON, retry up to 3 times. On all failures, return `None` (caller flags the file).

- [ ] **Step 1: Write failing tests for structure extraction**

Add to `tests/test_analyzer.py`:

```python
from unittest.mock import MagicMock
from pseudocodify.analyzer import analyze_file, build_extraction_prompt

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_analyzer.py -k "analyze_file or extraction_prompt" -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement structure extraction**

Add to `pseudocodify/analyzer.py`:

```python
import json
from pseudocodify.models import FileAnalysis
from pseudocodify.rlm_adapter import RLMAdapter

EXTRACTION_SCHEMA = """
{
  "path": "string (relative path)",
  "language": "string",
  "purpose": "string (one sentence)",
  "constructs": [{"name": "string", "file": "string", "kind": "function|class|variable|method"}],
  "external_deps": [{"name": "string", "description": "string", "known": true|false}],
  "internal_refs": [["caller_name", "callee_file_path"]]
}
"""

def build_extraction_prompt(source_code: str, language: str) -> str:
    return f"""Analyze the following {language} source code and return a JSON object matching this schema exactly:

{EXTRACTION_SCHEMA}

Rules:
- `constructs`: list every function, class, method, and module-level variable
- `external_deps`: list every import/require that is NOT from the same project; set `known: true` if it is a well-known library, false if unknown; provide a one-sentence description
- `internal_refs`: list pairs of [calling_construct_name, relative_path_of_called_file] for cross-file calls within the project
- `purpose`: one sentence describing what this file does overall

Return ONLY the JSON object. No explanation, no markdown, no code fences.

Source code:
{source_code}"""

def analyze_file(
    path: Path,
    source_root: Path,
    adapter: RLMAdapter,
) -> FileAnalysis | None:
    rel_path = str(path.relative_to(source_root))
    source_code = path.read_text(errors="replace")
    language = _detect_language(path)
    source_hash = hash_file(path)
    prompt = build_extraction_prompt(source_code, language)

    for attempt in range(3):
        try:
            raw = adapter.run(prompt)
            data = json.loads(raw)
            data["path"] = rel_path
            data["source_hash"] = source_hash
            return FileAnalysis.model_validate(data)
        except (json.JSONDecodeError, Exception):
            continue
    return None

def _detect_language(path: Path) -> str:
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".go": "Go", ".rb": "Ruby", ".java": "Java", ".cs": "C#",
        ".cpp": "C++", ".c": "C", ".rs": "Rust", ".php": "PHP",
        ".swift": "Swift", ".kt": "Kotlin", ".scala": "Scala",
        ".r": "R", ".m": "Objective-C", ".sh": "Shell",
        ".bash": "Bash", ".pl": "Perl", ".lua": "Lua",
    }
    return ext_map.get(path.suffix.lower(), "Unknown")
```

- [ ] **Step 4: Run all analyzer tests**

```bash
pytest tests/test_analyzer.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/analyzer.py tests/test_analyzer.py
git commit -m "feat: add LLM structure extraction with retry logic"
```

---

### Task 4.4: CodebaseMap assembly

**Files:**
- Modify: `pseudocodify/analyzer.py`
- Modify: `tests/test_analyzer.py`

- [ ] **Step 1: Write failing tests for full analysis**

Add to `tests/test_analyzer.py`:

```python
from pseudocodify.analyzer import run_analysis

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

    from pseudocodify.models import FileAnalysis, CodebaseMap
    fa = FileAnalysis(
        path="app.py", language="Python", purpose="cached",
        constructs=[], external_deps=[], internal_refs=[],
        source_hash=hash_file(src),
    )
    cm = CodebaseMap(
        source_root=str(tmp_path), files={"app.py": fa},
        dominant_paradigm="procedural", recommended_style="pascal",
        analysis_timestamp="2026-04-17T00:00:00Z",
    )
    save_codebase_map(cm, cache_dir)

    mock_adapter = MagicMock()
    from pseudocodify.config import RunConfig
    cfg = RunConfig(source=str(tmp_path))
    result = run_analysis(cfg, adapter=mock_adapter)
    mock_adapter.run.assert_not_called()
    assert result.files["app.py"].purpose == "cached"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_analyzer.py -k "run_analysis" -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement `run_analysis`**

Add to `pseudocodify/analyzer.py`:

```python
import datetime
from pseudocodify.config import RunConfig
from pseudocodify.models import CodebaseMap

def _infer_paradigm(files: dict) -> str:
    """
    Heuristic: OOP if classes dominate; procedural if functions dominate
    with no classes; functional if there are many small functions with no
    side-effectful constructs (approximated by near-zero class count and
    many functions); mixed otherwise.
    """
    class_count = sum(
        1 for fa in files.values()
        for c in fa.constructs if c.kind == "class"
    )
    func_count = sum(
        1 for fa in files.values()
        for c in fa.constructs if c.kind == "function"
    )
    if class_count > func_count:
        return "OOP"
    if class_count == 0 and func_count > 0:
        # No classes: could be procedural or functional.
        # Treat as procedural (safe default — functional is rare in practice).
        return "procedural"
    if class_count > 0 and func_count > 0:
        return "mixed"
    return "procedural"

def _recommend_style(paradigm: str) -> str:
    from pseudocodify.styles import get_style, list_styles
    for name in list_styles():
        style = get_style(name)
        if paradigm in style.PARADIGM_FIT:
            return name
    return "cormen"

def run_analysis(cfg: RunConfig, adapter: RLMAdapter) -> CodebaseMap:
    source = Path(cfg.source)
    cache_dir = source / ".pseudocodify"
    cached = load_codebase_map(cache_dir)
    files = discover_files(source, include=cfg.include or None, exclude=cfg.exclude or None)

    result_files: dict[str, "FileAnalysis"] = {}
    failed: list[str] = []

    for file_path in files:
        rel = str(file_path.relative_to(source))
        current_hash = hash_file(file_path)
        if cached and rel in cached.files and cached.files[rel].source_hash == current_hash:
            result_files[rel] = cached.files[rel]
            continue
        fa = analyze_file(file_path, source_root=source, adapter=adapter)
        if fa is None:
            failed.append(rel)
        else:
            result_files[rel] = fa

    if failed:
        import sys
        for f in failed:
            print(f"WARNING: [ANALYSIS FAILED] {f}", file=sys.stderr)

    paradigm = _infer_paradigm(result_files)
    style = _recommend_style(paradigm)
    cm = CodebaseMap(
        source_root=str(source.resolve()),
        files=result_files,
        dominant_paradigm=paradigm,
        recommended_style=style,
        analysis_timestamp=datetime.datetime.utcnow().isoformat() + "Z",
    )
    save_codebase_map(cm, cache_dir)
    return cm
```

- [ ] **Step 4: Run all analyzer tests**

```bash
pytest tests/test_analyzer.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/analyzer.py tests/test_analyzer.py
git commit -m "feat: implement full Phase 1 analysis pipeline"
```

---

## Phase 5: Generator (Phase 2)

### Task 5.1: Output formatting

**Files:**
- Create: `pseudocodify/generator.py`
- Create: `tests/test_generator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_generator.py
import pytest
from pseudocodify.generator import build_pseudo_header, build_readme_index
from pseudocodify.models import CodebaseMap, FileAnalysis

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
        analysis_timestamp="2026-04-17T00:00:00Z",
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
        analysis_timestamp="2026-04-17T00:00:00Z",
    )
    readme = build_readme_index(cm, style_name="CLRS/Cormen", architecture_summary="x")
    assert "2026-04-17" in readme
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_generator.py -v
```

Expected: `ModuleNotFoundError: No module named 'pseudocodify.generator'`

- [ ] **Step 3: Implement output formatting**

```python
# pseudocodify/generator.py
from pseudocodify.models import CodebaseMap

DIVIDER = "// " + "─" * 65

def build_pseudo_header(source_path: str, language: str, purpose: str) -> str:
    return "\n".join([
        f"// SOURCE: {source_path}",
        f"// LANGUAGE: {language}",
        f"// PURPOSE: {purpose}",
        DIVIDER,
    ])

def build_readme_index(
    cm: CodebaseMap,
    style_name: str,
    architecture_summary: str,
) -> str:
    import os
    source_name = os.path.basename(cm.source_root)
    lines = [
        f"# Pseudocode Index — {source_name}",
        f"Generated: {cm.analysis_timestamp}",
        f"Style: {style_name}",
        "",
        "## Architecture Summary",
        architecture_summary,
        "",
        "## File Index",
    ]
    for rel_path, fa in sorted(cm.files.items()):
        pseudo_path = rel_path.rsplit(".", 1)[0] + ".pseudo"
        lines.append(f"- [{pseudo_path}]({pseudo_path}) — {fa.purpose}")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_generator.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/generator.py tests/test_generator.py
git commit -m "feat: add pseudo file header and README index generation"
```

---

### Task 5.2: Per-file pseudocode generation

**Files:**
- Modify: `pseudocodify/generator.py`
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_generator.py`:

```python
import json
from unittest.mock import MagicMock
from pathlib import Path
from pseudocodify.generator import generate_file_pseudocode, build_generation_prompt

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
        analysis_timestamp="2026-04-17T00:00:00Z",
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
        analysis_timestamp="2026-04-17T00:00:00Z",
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
        analysis_timestamp="2026-04-17T00:00:00Z",
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_generator.py -k "generate_file" -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement per-file generation**

Add to `pseudocodify/generator.py`:

```python
import types
from pathlib import Path
from pseudocodify.models import FileAnalysis, CodebaseMap
from pseudocodify.rlm_adapter import RLMAdapter

def build_generation_prompt(
    source_code: str,
    fa: FileAnalysis,
    cm: CodebaseMap,
) -> str:
    context = f"Codebase context (for cross-file references):\n{cm.model_dump_json(indent=2)}\n\n"
    return (
        f"{context}"
        f"Translate the following {fa.language} source file to pseudocode.\n"
        f"File: {fa.path}\n"
        f"Purpose: {fa.purpose}\n\n"
        f"Source code:\n{source_code}"
    )

def generate_file_pseudocode(
    fa: FileAnalysis,
    cm: CodebaseMap,
    source_root: Path,
    output_dir: Path,
    style: types.ModuleType,
    adapter: RLMAdapter,
) -> bool:
    source_path = source_root / fa.path
    if not source_path.exists():
        return False
    source_code = source_path.read_text(errors="replace")
    prompt = build_generation_prompt(source_code, fa, cm)

    pseudocode = None
    for _ in range(3):
        result = adapter.run(prompt, context=style.SYSTEM_PROMPT)
        if result and result.strip():
            pseudocode = result.strip()
            break

    pseudo_path = output_dir / (fa.path.rsplit(".", 1)[0] + ".pseudo")
    pseudo_path.parent.mkdir(parents=True, exist_ok=True)

    header = build_pseudo_header(fa.path, fa.language, fa.purpose)

    if pseudocode:
        pseudo_path.write_text(header + "\n\n" + pseudocode + "\n")
        return True
    else:
        marker = f"\n{DIVIDER}\n// [TRANSLATION INCOMPLETE: {fa.path} — LLM returned malformed output after 3 retries]\n"
        pseudo_path.write_text(header + marker)
        return False
```

- [ ] **Step 4: Run all generator tests**

```bash
pytest tests/test_generator.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/generator.py tests/test_generator.py
git commit -m "feat: implement per-file pseudocode generation with retry and failure marker"
```

---

### Task 5.3: Full generation run (consolidation, state, README)

**Files:**
- Modify: `pseudocodify/generator.py`
- Modify: `tests/test_generator.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_generator.py`:

```python
from pseudocodify.generator import run_generation, load_state, save_state

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
        analysis_timestamp="2026-04-17T00:00:00Z",
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
    fa = FileAnalysis(
        path="app.py", language="Python", purpose="entry",
        constructs=[], external_deps=[], internal_refs=[], source_hash="x"
    )
    cm = CodebaseMap(
        source_root=str(tmp_path), files={"app.py": fa},
        dominant_paradigm="OOP", recommended_style="cormen",
        analysis_timestamp="2026-04-17T00:00:00Z",
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_generator.py -k "run_generation or save_state or load_state" -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement run_generation, state functions**

Add to `pseudocodify/generator.py`:

```python
import json
import sys
from pseudocodify.config import RunConfig

def save_state(cache_dir: Path, style: str) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "state.json").write_text(json.dumps({"last_style": style}))

def load_state(cache_dir: Path) -> dict:
    path = cache_dir / "state.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())

def run_generation(
    cm: CodebaseMap,
    cfg: RunConfig,
    adapter: RLMAdapter,
    architecture_summary: str,
) -> None:
    from pseudocodify.styles import get_style

    style = get_style(cfg.style if cfg.style != "auto" else cm.recommended_style)
    source = Path(cfg.source)
    cache_dir = source / ".pseudocodify"

    state = load_state(cache_dir)
    style_changed = state.get("last_style") != (cfg.style if cfg.style != "auto" else cm.recommended_style)

    output = Path(cfg.output)
    failed: list[str] = []
    pseudo_contents: list[str] = []

    for rel_path, fa in sorted(cm.files.items()):
        pseudo_path = output / (rel_path.rsplit(".", 1)[0] + ".pseudo")
        if not style_changed and pseudo_path.exists():
            # File unchanged — skip regeneration, collect for consolidation if needed
            if cfg.consolidate:
                pseudo_contents.append(pseudo_path.read_text())
            continue

        success = generate_file_pseudocode(
            fa=fa, cm=cm, source_root=source,
            output_dir=output, style=style, adapter=adapter,
        )
        if not success:
            failed.append(rel_path)
            print(f"WARNING: [TRANSLATION INCOMPLETE] {rel_path}", file=sys.stderr)
        elif cfg.consolidate:
            pseudo_contents.append(pseudo_path.read_text())

    readme_content = build_readme_index(cm, style.STYLE_NAME, architecture_summary)

    if cfg.consolidate:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(readme_content + "\n---\n\n" + "\n\n---\n\n".join(pseudo_contents))
    else:
        output.mkdir(parents=True, exist_ok=True)
        (output / "README.pseudo.md").write_text(readme_content)

    save_state(cache_dir, style=cfg.style if cfg.style != "auto" else cm.recommended_style)

    # End-of-run summary (printed to stdout so user always sees it)
    total = len(cm.files)
    n_failed = len(failed)
    n_ok = total - n_failed
    print(f"\n{'─' * 50}")
    print(f"Run complete: {n_ok}/{total} files translated successfully.")
    if failed:
        print("Files with issues:")
        for f in failed:
            print(f"  [TRANSLATION INCOMPLETE] {f}")
```

- [ ] **Step 4: Run all generator tests**

```bash
pytest tests/test_generator.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pseudocodify/generator.py tests/test_generator.py
git commit -m "feat: implement full generation run with consolidation, state tracking, and README"
```

---

## Phase 6: CLI

### Task 6.1: Startup validation and CLI skeleton

**Files:**
- Create: `pseudocodify/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_cli.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cli.py -v
```

Expected: `ModuleNotFoundError: No module named 'pseudocodify.cli'`

- [ ] **Step 3: Implement CLI**

```python
# pseudocodify/cli.py
import os
import sys
from pathlib import Path
import typer
from pseudocodify.config import RunConfig, load_config
from pseudocodify.styles import list_styles, get_style

app = typer.Typer(help="Convert any codebase to pseudocode.")

VALID_STYLES = ["auto"] + list_styles()

@app.command()
def main(
    source: str = typer.Argument(".", help="Source directory or file"),
    output: str = typer.Option("./pseudocode", "--output", "-o"),
    consolidate: bool = typer.Option(False, "--consolidate"),
    style: str = typer.Option("auto", "--style"),
    model: str = typer.Option("claude-opus-4-6", "--model"),
    include: list[str] = typer.Option([], "--include"),
    exclude: list[str] = typer.Option([], "--exclude"),
    yes: bool = typer.Option(False, "--yes"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    # Validate style
    if style not in VALID_STYLES:
        typer.echo(f"Error: invalid style '{style}'. Valid options: {VALID_STYLES}", err=True)
        raise typer.Exit(1)

    # Validate API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        typer.echo("Error: ANTHROPIC_API_KEY environment variable is not set.", err=True)
        raise typer.Exit(1)

    # Load config, merge CLI overrides
    toml_path = Path(source) / ".pseudocodify.toml"
    cli_overrides = {
        "source": source, "output": output, "consolidate": consolidate,
        "style": style, "model": model, "include": include or [],
        "exclude": exclude or [], "yes": yes, "verbose": verbose,
    }
    cfg = load_config(toml_path=toml_path, cli_overrides=cli_overrides)

    from pseudocodify.rlm_adapter import RLMAdapter
    from pseudocodify.analyzer import run_analysis
    from pseudocodify.generator import run_generation

    adapter = RLMAdapter(model=cfg.model, verbose=cfg.verbose)

    if cfg.verbose:
        typer.echo("Phase 1: Analyzing codebase...")
    cm = run_analysis(cfg, adapter=adapter)

    # Interactive style selection if auto
    selected_style = cfg.style
    if cfg.style == "auto":
        selected_style = _prompt_style(cm.recommended_style, cm.dominant_paradigm, cfg.yes)
        cfg.style = selected_style

    if cfg.verbose:
        typer.echo("Phase 2: Generating pseudocode...")

    # Generate architecture summary
    summary_prompt = (
        f"In 100-200 words, describe the overall architecture of this codebase:\n"
        f"{cm.model_dump_json(indent=2)}"
    )
    architecture_summary = adapter.run(summary_prompt)

    run_generation(cm=cm, cfg=cfg, adapter=adapter, architecture_summary=architecture_summary)
    typer.echo("Done.")

def _prompt_style(recommended: str, paradigm: str, yes: bool) -> str:
    from pseudocodify.styles import get_style
    style_options = [
        ("cormen", "CLRS/Cormen", "textbook algorithmic style"),
        ("structured-english", "Structured English", "plain prose-code hybrid"),
        ("pascal", "Pascal-like", "BEGIN/END block style"),
    ]
    if yes or not sys.stdin.isatty():
        typer.echo(f"Using recommended style: {get_style(recommended).STYLE_NAME}")
        return recommended

    typer.echo(f"\nDetected codebase paradigm: {paradigm}")
    typer.echo(f"Recommended pseudocode style: {get_style(recommended).STYLE_NAME}\n")
    typer.echo("Available styles:")
    for i, (key, name, desc) in enumerate(style_options, 1):
        marker = "(recommended)" if key == recommended else ""
        typer.echo(f"  [{i}] {name:<30} {marker} — {desc}")
    typer.echo("")

    keys = [s[0] for s in style_options]
    default_idx = keys.index(recommended) + 1

    while True:
        raw = typer.prompt(f"Select style [{default_idx}]", default=str(default_idx))
        if raw.strip() == "" or raw.strip() == str(default_idx):
            return recommended
        try:
            choice = int(raw.strip())
            if 1 <= choice <= len(style_options):
                return style_options[choice - 1][0]
        except ValueError:
            pass
        typer.echo("Invalid selection. Please enter 1, 2, or 3.")
```

- [ ] **Step 4: Run CLI tests**

```bash
pytest tests/test_cli.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Verify entry point works**

```bash
pseudocodify --help
```

Expected: help text showing all flags.

- [ ] **Step 6: Commit**

```bash
git add pseudocodify/cli.py tests/test_cli.py
git commit -m "feat: implement Typer CLI with startup validation and interactive style selection"
```

---

## Phase 7: Integration & Polish

### Task 7.1: Run full test suite

- [ ] **Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: all tests PASS. If any fail, fix them before proceeding.

- [ ] **Step 2: Verify the CLI runs end-to-end on a real (small) codebase**

```bash
# Run pseudocodify on its own source directory as a smoke test
ANTHROPIC_API_KEY=your_key pseudocodify ./pseudocodify --output /tmp/pseudocodify-out --yes --verbose
```

Expected:
- No unhandled exceptions
- `/tmp/pseudocodify-out/` directory created with `.pseudo` files
- `/tmp/pseudocodify-out/README.pseudo.md` exists
- Terminal output ends with `Run complete: N/N files translated successfully.`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: verify all tests pass and smoke test CLI"
```

---

### Task 7.2: Update README and pyproject metadata

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml`

- [ ] **Step 1: Update README.md Installation section**

```markdown
## Installation

```bash
pip install pseudocodify
```

Or from source:

```bash
git clone https://github.com/keithmackay/pseudocodify
cd pseudocodify
pip install -e .
```

Requires Python 3.11+. Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your_key_here
```
```

- [ ] **Step 2: Update README.md Usage section**

```markdown
## Usage

```bash
# Translate a codebase to pseudocode (per-file output)
pseudocodify ./my-project --output ./my-project-pseudo

# Single consolidated output file
pseudocodify ./my-project --output all.pseudo.md --consolidate

# Specific pseudocode style
pseudocodify ./my-project --style cormen

# Skip interactive style confirmation
pseudocodify ./my-project --yes
```
```

- [ ] **Step 3: Commit**

```bash
git add README.md pyproject.toml
git commit -m "docs: update README with installation and usage instructions"
```

---

### Task 7.3: Push to GitHub

- [ ] **Step 1: Push all commits**

```bash
git push origin main
```

Expected: all commits pushed to `keithmackay/pseudocodify` (private).

---

## Next Steps

Ideas for future enhancements after the core tool is launched and stable.

- **[Keith's idea] Web UI** — a simple browser interface where you can paste or upload code and get pseudocode back without using the terminal
- **[Keith's idea] VS Code extension** — translate the currently open file or selection to pseudocode inline
- **[Claude's idea] `--target-language` flag** — extend Phase 2 to generate idiomatic code in a target language (Python → Go, etc.) using the pseudocode as the intermediate representation
- **[Claude's idea] GitHub Actions integration** — a workflow that auto-generates pseudocode on PR and commits it as a documentation artifact
- **[Claude's idea] Diff mode** — when re-running on an updated codebase, produce a diff of what changed in the pseudocode (not just re-generate), making it useful for code review
- **[Claude's idea] Semantic search over pseudocode** — embed pseudocode chunks and expose a `pseudocodify search "find all places that validate user input"` command
- **[Claude's idea] Interactive review mode** — after generation, step through each file's pseudocode interactively and let the user flag sections as incorrect before finalizing
