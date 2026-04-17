# pseudocodify — Design Spec
**Date:** 2026-04-17  
**Status:** Approved

---

## Overview

`pseudocodify` is a CLI tool that converts any codebase into a perfect-fidelity, human-readable pseudocode representation. It is language-agnostic, LLM-powered, and designed to serve two equal purposes: **porting codebases to new languages** and **documenting/understanding unfamiliar code**.

The primary users are developers comfortable with the terminal. The tool is built in Python and uses the Anthropic SDK (Claude) as its LLM backend.

---

## CLI Interface

```
pseudocodify ./my-project --output ./my-project-pseudo
pseudocodify ./my-project --output single-file.pseudo.md --consolidate
pseudocodify ./my-project --style cormen
pseudocodify ./my-project --model claude-opus-4-6
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--output` | `./pseudocode/` | Target file (consolidate mode) or directory (per-file mode) |
| `--consolidate` | `false` | Merge all output into a single document |
| `--style` | `auto` | Pseudocode style: `auto`, `cormen`, `structured-english`, `pascal` |
| `--model` | `claude-opus-4-6` | LLM model to use |
| `--include` | recognized extensions | Glob patterns for files to include. Default: all files with recognized code extensions (`.py`, `.js`, `.ts`, `.go`, `.rb`, `.java`, `.cs`, `.cpp`, `.c`, `.rs`, `.php`, etc.). Binary files and non-text files are always skipped regardless of this flag. |
| `--exclude` | none | Glob patterns for files to skip |
| `--yes` | `false` | Skip interactive style confirmation (auto-accept recommendation) |
| `--verbose` | `false` | Show analysis and generation progress |

### `--style auto` Interactive Flow

When `--style auto` (the default), pseudocodify presents a style recommendation after Phase 1 analysis:

```
Detected codebase paradigm: Object-Oriented (Python)
Recommended pseudocode style: CLRS/Cormen

Available styles:
  [1] CLRS/Cormen          (recommended) — textbook algorithmic style
  [2] Structured English                 — plain prose-code hybrid
  [3] Pascal-like                        — BEGIN/END block style

Select style [1]: _
```

- Input: `1`, `2`, or `3` (or Enter to accept recommendation)
- Invalid input: re-prompts with the same menu
- Non-TTY / `--yes` flag: automatically selects the recommendation and logs `Using recommended style: CLRS/Cormen`

### Configuration File

Users may place a `.pseudocodify.toml` at the project root to set run defaults. CLI flags always take precedence. If the file is malformed (invalid TOML), the tool exits with a clear error message and no processing occurs.

```toml
[pseudocodify]
style = "cormen"
consolidate = false
exclude = ["tests/**", "vendor/**", "*.min.js"]
model = "claude-opus-4-6"
output = "./pseudocode"
```

---

## Data Models (`models.py`)

All inter-phase data is structured using these models (Pydantic v2).

```python
class ExternalDep:
    name: str               # import/package name
    description: str        # plain-English description of what it does
    known: bool             # True if the LLM recognized it as a well-known library

class ConstructRef:
    name: str               # function/class/variable name
    file: str               # relative path to source file
    kind: str               # "function" | "class" | "variable" | "method"

class FileAnalysis:
    path: str               # relative path from source root
    language: str           # detected language (e.g., "Python", "TypeScript")
    purpose: str            # one-line LLM-generated summary of the file's purpose
    constructs: list[ConstructRef]        # all top-level and nested constructs
    external_deps: list[ExternalDep]      # all external imports
    internal_refs: list[tuple[str, str]]  # (caller_construct_name, callee_file_path)
    source_hash: str        # SHA-256 of file contents at analysis time

class CodebaseMap:
    source_root: str                        # absolute path to source directory
    files: dict[str, FileAnalysis]          # keyed by relative file path
    dominant_paradigm: str                  # "OOP" | "functional" | "procedural" | "mixed"
    recommended_style: str                  # "cormen" | "structured-english" | "pascal"
    analysis_timestamp: str                 # ISO 8601
```

The `CodebaseMap` is serialized to `.pseudocodify/analysis.json` after Phase 1.

---

## Architecture: Two-Phase LLM Pipeline

### Phase 1 — Codebase Analysis

**Steps:**
1. **File discovery** — walks the source tree, collects all files matching `--include` and not matching `--exclude`. Language is detected via file extension (`.py` → Python, `.ts`/`.js` → TypeScript/JavaScript, etc.) with LLM fallback for ambiguous cases.
2. **Structure extraction** — for each file, the LLM is called with a structured extraction prompt (see below). Output must be valid JSON matching the `FileAnalysis` schema. If the LLM returns invalid JSON, up to 3 retries are attempted before the file is flagged `[ANALYSIS FAILED]`.
3. **Cross-file relationship mapping** — `internal_refs` across all `FileAnalysis` objects are aggregated into a call graph stored on the `CodebaseMap`.
4. **Style recommendation** — based on `dominant_paradigm`, the tool selects a default style and presents the interactive style menu (unless `--style` is explicitly set or `--yes` is passed).

**Structure extraction prompt contract:**

The LLM is instructed to return a JSON object matching `FileAnalysis` (minus `source_hash`, which is computed locally). The system prompt specifies:
- Language of the file (pre-detected)
- Required output schema (injected as JSON Schema)
- Instructions to identify all constructs, imports, and cross-file references
- For external deps: classify as known/unknown and provide a one-sentence description

If a file is too large to process in one call (estimated by token count), it is chunked by top-level construct boundaries. Each chunk is analyzed separately and results are merged into a single `FileAnalysis`.

**RLM integration:** For codebases with many files that together exceed practical sequential processing limits, Phase 1 uses the `rlms` PyPI package (`pip install rlms`, `from rlm import RLM`). The RLM is configured with the Anthropic backend. Each file analysis is issued as an RLM sub-call; the root call aggregates results into the `CodebaseMap`. This is transparent to the user — they see per-file progress output.

**Artifact:** Results are saved to `.pseudocodify/analysis.json`. On subsequent runs, each file's `source_hash` is compared to the current file hash. If unchanged, the existing `FileAnalysis` is reused. If any file has changed, only that file is re-analyzed; the `CodebaseMap` is then rebuilt from the mix of cached and fresh results.

---

### Phase 2 — Pseudocode Generation

**Steps:**
1. **File-by-file generation** — each source file is translated using its `FileAnalysis` plus the full `CodebaseMap` (serialized and injected as context) to ensure cross-file references are coherent.
2. **Construct-to-pseudocode mapping** — the style module for the selected style provides a system prompt template. The LLM returns pseudocode as a plain text string. No JSON parsing is required at this step.
3. **External dependency rendering** — the generator substitutes each external call site with the pseudocode form followed by `// [EXTERNAL: <name>] <description>`.
4. **Output writing** — each `.pseudo` file is written with a standard header (see Output Format).
5. **Consolidation** — if `--consolidate`, files are concatenated in directory-traversal order with section headers.

**Incremental runs:** A file's pseudocode output is only regenerated if its `source_hash` has changed since the last run, or if the selected style has changed. Style selection is stored in `.pseudocodify/state.json` with the schema:

```json
{ "last_style": "cormen" }
```

Where `last_style` is one of `"cormen"`, `"structured-english"`, or `"pascal"`. If `.pseudocodify/state.json` does not exist or `last_style` differs from the current run's style, all files are regenerated regardless of hash.

**RLM integration:** For individual files where the source exceeds ~3,000 tokens, the file is split at function/class boundaries before generation. Each chunk is generated as a separate RLM sub-call; results are reassembled in source order.

---

## RLM Adapter (`rlm_adapter.py`)

`rlm_adapter.py` is a thin wrapper around the `rlms` package that provides a consistent interface for both Phase 1 (analysis) and Phase 2 (generation). It abstracts RLM initialization and sub-call dispatch so that `analyzer.py` and `generator.py` do not import `rlms` directly.

**Public interface:**

```python
class RLMAdapter:
    def __init__(self, model: str):
        """Initialize the RLM client with the given model name using the Anthropic backend."""

    def run(self, prompt: str, context: str | None = None) -> str:
        """
        Execute a single RLM completion. The RLM may issue recursive sub-calls internally.
        Returns the final text response as a string.
        `context` is optional additional context injected before the prompt.
        Raises RLMError on unrecoverable failure.
        """
```

**Behavior:**
- Retry/timeout behavior is delegated to the `rlms` library internals — the adapter does not add its own retry layer
- Progress output (from `rlms` verbose mode) is forwarded to stdout when `--verbose` is set
- `RLMError` is a pseudocodify-defined exception wrapping any exception raised by the `rlms` library, so callers never import `rlms` exceptions directly

---

## Style Modules (`styles/`)

Each style module exports:
- `SYSTEM_PROMPT: str` — injected as the LLM system prompt for all generation calls when this style is active. Describes the notation rules (keyword set, block delimiters, assignment syntax, comment format).
- `STYLE_NAME: str` — display name (e.g., `"CLRS/Cormen"`)
- `PARADIGM_FIT: list[str]` — list of `dominant_paradigm` values this style is recommended for. Valid values must match those on `CodebaseMap.dominant_paradigm`: `"OOP"`, `"functional"`, `"procedural"`, `"mixed"`. Example: `["OOP", "functional"]`.

**Cormen style example rules (in `SYSTEM_PROMPT`):**
- Assignment: `x ← value`
- Blocks: indentation only (no delimiters)
- Keywords: `if`, `else`, `for`, `while`, `return`, `and`, `or`, `not`
- Constants: SMALL-CAPS
- Procedures: `FUNCTION name(params)`

**Structured English example rules:**
- Plain prose with light code structure
- Assignment: `set x to value`
- Blocks: indented under `if ... then:` / `for each ... do:`
- No formal keyword set — readability over formality

**Pascal-like example rules:**
- `PROCEDURE` / `FUNCTION` declarations
- `BEGIN` / `END` block delimiters
- Assignment: `:=`

---

## Output Format

### Per-file mode (default)
```
pseudocode/
  src/
    models/
      user.pseudo
    services/
      auth.pseudo
  README.pseudo.md
```

### `.pseudo` file structure

Every `.pseudo` file follows this structure:

```
// SOURCE: src/models/user.py
// LANGUAGE: Python
// PURPOSE: Defines the User data model and related factory methods
// ─────────────────────────────────────────────────────────────────

CLASS User
  ATTRIBUTES: id, email, password_hash, created_at

  FUNCTION create(email, password)
    hash ← hash_password(password)   // [EXTERNAL: bcrypt] hashes a plaintext password using bcrypt
    RETURN new User with email=email, password_hash=hash, created_at=now()

  FUNCTION to_dict()
    RETURN { "id": id, "email": email, "created_at": created_at }

// ─────────────────────────────────────────────────────────────────
// [TRANSLATION INCOMPLETE: auth.pseudo — LLM returned malformed output after 3 retries]
```

**Format rules:**
- Header block: 3-line comment (SOURCE, LANGUAGE, PURPOSE) followed by a `─` divider line
- Each top-level construct (class, function, file-level code) is separated by a blank line
- File-level (non-class) code is rendered under a `// --- File-level code ---` comment
- Nested classes are indented one additional level with their own `CLASS` header
- Multi-return is expressed as `RETURN (value1, value2)`
- Source comments are preserved as `// <original comment text>` inline
- The `[TRANSLATION INCOMPLETE]` marker is appended at the bottom of the file for any failed chunk

### `README.pseudo.md`

Always generated at the output root. Contains:

```markdown
# Pseudocode Index — <source directory name>
Generated: <ISO 8601 timestamp>
Style: <style name>

## Architecture Summary
<LLM-generated 100-200 word plain-English description of the codebase's overall structure,
dominant paradigm, and main components — generated during Phase 1>

## File Index
- [src/models/user.pseudo](src/models/user.pseudo) — User data model and factory methods
- [src/services/auth.pseudo](src/services/auth.pseudo) — Authentication and session management
...
```

The index is a flat list sorted by directory traversal order. Each entry links to the `.pseudo` file and includes the file's `purpose` field from its `FileAnalysis`.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Malformed `.pseudocodify.toml` | Exit with error message before any processing |
| Invalid `--style` value | Exit with error listing valid options |
| Missing/invalid Anthropic API key | Exit with error before any LLM calls |
| Output directory not writable | Exit with error before any processing |
| File analysis fails after 3 retries | File flagged `[ANALYSIS FAILED]` in summary; processing continues |
| LLM returns malformed pseudocode after 3 retries | File flagged `[TRANSLATION INCOMPLETE]`; marker appended to output file |
| RLM sub-call failure | Warning logged with file path; remaining files continue |
| Source file unreadable (permissions) | Warning logged; file skipped |
| Invalid `--style auto` interactive input | Re-prompt until valid input received |

All warnings and errors are collected and printed as a summary table at the end of each run. Exit code is `0` if at least one file was successfully translated; `1` if all files failed or a startup validation failed.

---

## Project Structure

```
pseudocodify/
  pseudocodify/
    cli.py              ← CLI entry point (Typer)
    analyzer.py         ← Phase 1: codebase analysis
    generator.py        ← Phase 2: pseudocode generation
    rlm_adapter.py      ← RLM integration wrapper (wraps rlms package)
    styles/
      cormen.py         ← CLRS/Cormen style prompts and rules
      structured_english.py
      pascal.py
    models.py           ← Pydantic models (CodebaseMap, FileAnalysis, etc.)
  tests/
  docs/
  pyproject.toml
```

**External dependencies:**
- `typer` — CLI framework
- `anthropic` — Anthropic Python SDK
- `rlms` — Recursive Language Models package (PyPI: `rlms`)
- `pydantic` v2 — data models and JSON serialization
- `toml` / `tomllib` — config file parsing (stdlib in Python 3.11+)

---

## Key Principles

- **YAGNI** — no features beyond what's described here until the core is working
- **Correctness over speed** — when processing large codebases via RLM, accuracy takes priority over throughput
- **Language-agnostic** — no language-specific parsers; the LLM handles all structure extraction
- **Incremental by default** — avoid re-processing unchanged files
- **Transparent failures** — never silently drop content; always flag incomplete translations
