# pseudocodify — Phases Summary

Quick reference for the implementation roadmap. Full detail in `docs/superpowers/plans/2026-04-17-pseudocodify-implementation.md`.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| CLI | Typer |
| LLM | Anthropic SDK (Claude) |
| Large codebase support | rlms (PyPI) |
| Data models | Pydantic v2 |
| Config | tomllib (stdlib) |
| Testing | pytest, pytest-mock |

---

## Key Principles

- **TDD** — write the failing test first, then the minimal implementation
- **DRY** — no repeated logic across modules
- **YAGNI** — no speculative features
- **Frequent commits** — every task ends with a commit
- **Transparent failures** — never silently drop content; always flag incomplete translations

---

## Phase 1: Project Scaffold

**Goal:** Establish the Python package, data models, and config loading — the foundation everything else builds on.

| Task | Description | Deliverable |
|------|-------------|-------------|
| 1.1 | Initialize Python package | `pyproject.toml`, package installed |
| 1.2 | Data models | `models.py` with Pydantic v2 models |
| 1.3 | Config loading | `config.py` with TOML + CLI merge |

**Key deliverables:** Installable package, tested data models, config loading with TOML override support.

---

## Phase 2: Style Modules

**Goal:** Implement all three pseudocode style modules and the registry that selects them by name.

| Task | Description | Deliverable |
|------|-------------|-------------|
| 2.1 | Style registry + 3 style modules | `styles/` directory, `get_style()`, `list_styles()` |

**Key deliverables:** Cormen, Structured English, and Pascal style prompts; registry with validation.

---

## Phase 3: RLM Adapter

**Goal:** Wrap the `rlms` package in a clean interface so neither `analyzer.py` nor `generator.py` imports `rlms` directly.

| Task | Description | Deliverable |
|------|-------------|-------------|
| 3.1 | RLMAdapter + RLMError | `rlm_adapter.py` with mocked tests |

**Key deliverables:** `RLMAdapter.run()` method, `RLMError` exception, fully unit-tested via mocks.

---

## Phase 4: Analyzer (Phase 1 Pipeline)

**Goal:** Implement the codebase analysis pipeline — file discovery, LLM structure extraction, cache, and `CodebaseMap` assembly.

| Task | Description | Deliverable |
|------|-------------|-------------|
| 4.1 | File discovery + hashing | `discover_files()`, `hash_file()` |
| 4.2 | Cache read/write | `save_codebase_map()`, `load_codebase_map()` |
| 4.3 | LLM structure extraction | `analyze_file()`, `build_extraction_prompt()` |
| 4.4 | CodebaseMap assembly | `run_analysis()` — full Phase 1 orchestration |

**Key deliverables:** Full Phase 1 pipeline from directory → `CodebaseMap` JSON artifact; incremental re-analysis on changed files only.

---

## Phase 5: Generator (Phase 2 Pipeline)

**Goal:** Implement pseudocode generation — per-file LLM translation, output formatting, consolidation, README, and state tracking.

| Task | Description | Deliverable |
|------|-------------|-------------|
| 5.1 | Output formatting | `build_pseudo_header()`, `build_readme_index()` |
| 5.2 | Per-file pseudocode generation | `generate_file_pseudocode()` with retry + failure marker |
| 5.3 | Full generation run | `run_generation()`, `save_state()`, `load_state()`, end-of-run summary |

**Key deliverables:** Full Phase 2 pipeline; per-file `.pseudo` output or consolidated single file; `README.pseudo.md`; incremental regeneration on style/hash change.

---

## Phase 6: CLI

**Goal:** Wire everything together behind a Typer CLI with startup validation, interactive style selection, and user-facing output.

| Task | Description | Deliverable |
|------|-------------|-------------|
| 6.1 | CLI skeleton + startup validation | `cli.py` with all flags, API key check, style validation, interactive prompt |

**Key deliverables:** Working `pseudocodify` command; all flags functional; interactive style menu; non-TTY/`--yes` support.

---

## Phase 7: Integration & Polish

**Goal:** Verify the full system works end-to-end, update documentation, and push to GitHub.

| Task | Description | Deliverable |
|------|-------------|-------------|
| 7.1 | Full test suite + smoke test | All tests green; CLI smoke-tested on real codebase |
| 7.2 | README + pyproject metadata | Installation and usage docs complete |
| 7.3 | Push to GitHub | All commits pushed to `keithmackay/pseudocodify` |

**Key deliverables:** Shippable v0.1.0; full test coverage; documented; pushed.

---

## Success Criteria

- `pseudocodify ./any-project` produces `.pseudo` files mirroring source structure
- All three pseudocode styles produce valid, readable output
- Large codebases (>context limit) complete without crashing via RLM
- Unchanged files are not re-processed on re-runs
- Failed translations are flagged, not silently dropped
- All tests pass: `pytest tests/ -v`

---

## Post-Launch Maintenance

- Monitor for `[TRANSLATION INCOMPLETE]` rates — if high, improve extraction prompts
- As new languages gain users, extend `RECOGNIZED_EXTENSIONS` and `_detect_language` in `analyzer.py`
- Style quality feedback → update `SYSTEM_PROMPT` in the relevant `styles/` module
- RLM API changes → update `rlm_adapter.py` only (all callers remain unchanged)
