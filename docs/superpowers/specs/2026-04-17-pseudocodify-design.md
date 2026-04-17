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
pseudocodify ./my-project --depth 2
pseudocodify ./my-project --model claude-opus-4-6
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--output` | `./pseudocode/` | Target file (consolidate mode) or directory (per-file mode) |
| `--consolidate` | `false` | Merge all output into a single document |
| `--style` | `auto` | Pseudocode style: `auto`, `cormen`, `structured-english`, `pascal` |
| `--model` | `claude-opus-4-6` | LLM model to use |
| `--depth` | unlimited | Max directory recursion depth |
| `--include` | `*` | Glob patterns for files to include |
| `--exclude` | none | Glob patterns for files to skip |
| `--verbose` | `false` | Show analysis and generation progress |

When `--style auto` (the default), pseudocodify analyzes the codebase structure and presents 2–3 style options with a recommendation before generating. The user confirms or overrides interactively.

### Configuration File

Users may place a `.pseudocodify.toml` at the project root to set run defaults. CLI flags always take precedence.

```toml
[pseudocodify]
style = "cormen"
consolidate = false
exclude = ["tests/**", "vendor/**", "*.min.js"]
model = "claude-opus-4-6"
output = "./pseudocode"
```

---

## Architecture: Two-Phase LLM Pipeline

### Phase 1 — Codebase Analysis

Before generating pseudocode, pseudocodify builds a **codebase map**: a structured JSON artifact capturing all constructs, relationships, and dependencies across the codebase.

**Steps:**
1. **File discovery** — walks the source tree, identifies all code files, groups by detected language (extension + content heuristics)
2. **Structure extraction** — for each file, the LLM identifies: classes, functions/methods, control flow patterns, data structures, external dependencies (imports/requires), and cross-file references
3. **Cross-file relationship mapping** — builds a call graph and dependency graph across the whole codebase
4. **External dependency classification** — for each external import, the LLM determines if it's a well-known library and generates a plain-English description; unknown dependencies are flagged
5. **Style recommendation** — based on the codebase's dominant paradigm (OOP, functional, procedural, mixed), pseudocodify recommends a pseudocode style and presents options to the user

**RLM integration:** For large codebases that exceed LLM context limits, Phase 1 uses the `rlms` package (Recursive Language Models) to recursively decompose analysis work. The LLM spawns sub-calls to analyze individual files or modules, then aggregates results bottom-up into the full codebase map. This is transparent to the user.

**Artifact:** The codebase map is persisted as `.pseudocodify/analysis.json`. If it already exists and source files are unchanged (verified via hash), Phase 1 is skipped on subsequent runs.

---

### Phase 2 — Pseudocode Generation

With the codebase map available as context, Phase 2 generates pseudocode output file-by-file.

**Steps:**
1. **File-by-file generation** — each source file is translated independently, with the full codebase map injected as context to ensure cross-file references are coherent
2. **Structure-to-pseudocode mapping** — each identified construct is mapped to the chosen style using a style-specific system prompt
3. **External dependency handling** — calls to external/3rd-party functions are rendered with a `[EXTERNAL: library-name]` flag and inline plain-English description
4. **Output formatting** — each pseudocode file includes a header (source path, detected language, one-line purpose summary); functions and classes are separated by clear dividers
5. **Consolidation** — if `--consolidate` is set, all generated files are merged into one document organized by directory structure

**RLM integration:** For very large individual files, RLM is used within generation too — the file is chunked by function/class boundaries, each chunk translated, then reassembled in order.

**Incremental runs:** Only files whose source hashes have changed since the last run are regenerated.

---

## Pseudocode Styles

| Style | Best For |
|-------|----------|
| **CLRS/Cormen** | Algorithmic, CS-heavy codebases |
| **Structured English** | Business logic, CRUD, workflow-heavy codebases |
| **Pascal-like** | Procedural codebases; teams from older language backgrounds |

When `--style auto`, the tool recommends a style based on the dominant paradigm detected in Phase 1, presents the options, and waits for user confirmation.

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
  README.pseudo.md     ← index + high-level architecture summary
```

### Sample `.pseudo` file
```
// SOURCE: src/models/user.py | LANGUAGE: Python | PURPOSE: User data model

CLASS User
  ATTRIBUTES: id, email, password_hash, created_at

  FUNCTION create(email, password)
    hash ← hash_password(password)   // [EXTERNAL: bcrypt] hashes password using bcrypt
    RETURN new User(email, hash)
```

A `README.pseudo.md` is always generated at the output root. It provides a plain-English summary of the overall codebase architecture and an index of all pseudocode files.

---

## Error Handling

- Files that fail to parse or translate are skipped with a warning; processing continues
- Malformed or incomplete LLM output triggers up to 3 retries; if all fail, the file is flagged `[TRANSLATION INCOMPLETE]`
- RLM sub-call failures are surfaced as warnings with the affected file path; remaining files continue
- All warnings and errors are collected and printed as a summary at the end of each run

---

## Project Structure

```
pseudocodify/
  pseudocodify/
    cli.py              ← CLI entry point (Typer)
    analyzer.py         ← Phase 1: codebase analysis
    generator.py        ← Phase 2: pseudocode generation
    rlm_adapter.py      ← RLM integration wrapper
    styles/
      cormen.py         ← style-specific prompt templates
      structured_english.py
      pascal.py
    models.py           ← shared data models (CodebaseMap, FileAnalysis, etc.)
  tests/
  docs/
  pyproject.toml
```

---

## Key Principles

- **YAGNI** — no features beyond what's described here until the core is working
- **Correctness over speed** — when processing large codebases via RLM, accuracy takes priority over throughput
- **Language-agnostic** — no language-specific parsers; the LLM handles all structure extraction
- **Incremental by default** — avoid re-processing unchanged files
- **Transparent failures** — never silently drop content; always flag incomplete translations
