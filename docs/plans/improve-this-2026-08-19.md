# Implementation Plan — improve-this findings (2026-08-19)

Source review: `docs/reviews/2026-08-19-improve-this.md`. Covers all 7 findings. Follow TDD for every task (failing test → minimal implementation → green → refactor), per project CLAUDE.md.

---

## Phase 1: Correctness Fixes (low-risk, unblock everything else)

**Goal:** Fix the two accuracy bugs and the duplication smell before touching prompt/concurrency architecture, so later phases build on a correct baseline.

### Task 1.1 — Fix unreachable "functional" paradigm (Finding #3)

- Write a failing test in `tests/test_analyzer.py` asserting `_infer_paradigm` returns `"functional"` for a `files` dict where constructs are functions with no enclosing class and analysis indicates no OOP constructs are used as containers (e.g., zero `class` constructs, all `function`/`variable` constructs, and — to distinguish "functional" from "procedural" — no `internal_refs` mutation-style call pattern is required by the model; simplest viable rule: reuse existing signal already available, e.g., add a rule that a codebase is "functional" only when it satisfies additional criteria beyond zero classes). Decide the exact discriminating rule during test-writing (see Investigation below) rather than guessing here.
- **Investigation first:** re-read `pseudocodify/models.py` and the three `styles/*.py` `PARADIGM_FIT` tuples to see which paradigms each style already claims to fit — this determines what distinguishing signal is worth computing (e.g., presence of higher-order function patterns isn't extractable from the current `ConstructRef` schema, so the realistic fix may be: reserve `"functional"` for zero classes AND zero variables at module level, vs `"procedural"` for zero classes with module-level variables present — pick whichever rule the style modules can actually make use of).
- Implement the fix in `_infer_paradigm`.
- Run `pytest tests/test_analyzer.py -v` — confirm green.

### Task 1.2 — Make JSON-decode retries adaptive (Finding #4)

- Write a failing test in `tests/test_analyzer.py`: mock `RLMAdapter.run` to return malformed JSON on attempt 1, then valid JSON on attempt 2, and assert the prompt passed on attempt 2 differs from attempt 1 (contains the parse error or an explicit "return valid JSON only" correction).
- Implement: on `JSONDecodeError`, append the error message to the prompt for the next attempt instead of resending the identical prompt.
- Run `pytest tests/test_analyzer.py -v` — confirm green.

### Task 1.3 — Deduplicate style-resolution expression (Finding #6)

- No new test needed (pure refactor); run existing `tests/test_generator.py` before and after to confirm no behavior change.
- In `run_generation`, compute `resolved_style_name = cfg.style if cfg.style != "auto" else cm.recommended_style` once, and use the local variable at all three call sites (`generator.py:119`, `:124`, `:163`).
- Run `pytest tests/test_generator.py -v` — confirm still green.

**Phase 1 exit criteria:** `pytest tests/ -v` fully green; `_infer_paradigm` can return all four documented paradigms; retries adapt to the failure; no duplicated style-resolution expression remains.

---

## Phase 2: Security Hardening

**Goal:** Reduce the prompt-injection surface (Finding #5) without restricting the tool's ability to translate arbitrary source code.

### Task 2.1 — Delimit and label source code in prompts

- Write a failing test in `tests/test_analyzer.py` and `tests/test_generator.py` asserting `build_extraction_prompt` / `build_generation_prompt` wrap the source code in an explicit, clearly-labeled boundary (e.g., fenced with a unique delimiter) and include an instruction that content inside the boundary is data to analyze/translate, not instructions to follow.
- Implement the prompt changes in `build_extraction_prompt` (`analyzer.py`) and `build_generation_prompt` (`generator.py`).
- Run `pytest tests/test_analyzer.py tests/test_generator.py -v` — confirm green.

**Note:** this is a mitigation, not a guarantee — document in the docstring/comment that it reduces but does not eliminate injection risk from adversarial source files, since instruction/data separation is best-effort with current LLMs.

**Phase 2 exit criteria:** both prompt builders demonstrably delimit source code from instructions; tests green.

---

## Phase 3: Token Efficiency — Scoped Context Per File

**Goal:** Stop resending the entire `CodebaseMap` on every generation call (Finding #1); send only what's relevant to the file being translated.

### Task 3.1 — Compute relevant-file context for a given file

- Write a failing test in `tests/test_generator.py` for a new helper (e.g., `relevant_context(fa: FileAnalysis, cm: CodebaseMap) -> CodebaseMap` or a lighter-weight dict) that, given a `FileAnalysis`, returns only: the file's own analysis, plus the analyses of files referenced via its `internal_refs` (both directions — files this file calls into, and files that call into it, since cross-file coherence needs both).
- Implement the helper in `generator.py`.
- Run `pytest tests/test_generator.py -v` — confirm green.

### Task 3.2 — Wire the scoped context into `build_generation_prompt`

- Write a failing test asserting `build_generation_prompt` embeds only the scoped context (not the full `cm.model_dump_json()`), and that a file with no internal refs produces a prompt containing only its own analysis.
- Implement: replace `cm.model_dump_json(indent=2)` in `build_generation_prompt` with the scoped context from Task 3.1.
- Run `pytest tests/test_generator.py -v` — confirm green.

**Phase 3 exit criteria:** per-file generation prompts scale with the file's reference neighborhood, not total codebase size; existing consolidate/incremental tests still pass unchanged.

---

## Phase 4: Scalability — Concurrent File Processing

**Goal:** Parallelize the independent per-file LLM calls in both analysis and generation phases (Finding #2). Do this after Phase 3 so concurrency doesn't amplify an already-oversized per-call payload.

### Task 4.1 — Concurrent analysis

- Write a failing test in `tests/test_analyzer.py`: given N files and a mocked adapter, assert `run_analysis` still produces correct per-file results and correctly preserves the cache-hit skip logic, using a test double that records call order/timing or simply asserts total call count equals number of uncached files (concurrency-safe assertions, not timing-based flakiness).
- Implement: replace the serial `for file_path in files:` loop in `run_analysis` with a bounded-concurrency executor (e.g., `concurrent.futures.ThreadPoolExecutor`, since `RLMAdapter.run` is I/O-bound), preserving current per-file error handling (`analyze_file` returning `None` → append to `failed`) and cache-hit behavior.
- Add a sensible default concurrency cap (e.g., a module constant) — do not add a new CLI flag unless the user asks; keep this internal per YAGNI.
- Run `pytest tests/test_analyzer.py -v` — confirm green.

### Task 4.2 — Concurrent generation

- Write a failing test in `tests/test_generator.py` mirroring Task 4.1's approach for `run_generation`'s per-file loop.
- Implement: replace the serial loop in `run_generation` with the same bounded-concurrency approach, preserving the incremental skip logic (`style_changed`, `source_unchanged`), the `failed` list, and consolidate-mode ordering (consolidated output must remain in `sorted(cm.files.items())` order regardless of completion order — collect results then assemble in order, don't append as-completed).
- Run `pytest tests/test_generator.py -v` — confirm green.

**Phase 4 exit criteria:** analysis and generation phases run with bounded concurrency; consolidated output order is deterministic; all existing incremental/caching tests still pass unmodified in behavior.

---

## Phase 5: Test Coverage — CLI Integration Test

**Goal:** Close the CLI-level integration gap (Finding #7) now that the underlying pipeline has changed shape (Phases 1-4), so the new test exercises the current wiring rather than a stale one.

### Task 5.1 — End-to-end happy-path CLI test

- Write a failing test in `tests/test_cli.py`: with `RLMAdapter.run` mocked to return valid extraction JSON and valid pseudocode text, invoke `app` against a small temp source tree with `--yes` (non-interactive) and assert: exit code 0, `Done.` in output, expected `.pseudo` files exist in the output directory, and `README.pseudo.md` was written.
- No implementation change expected — this task is pure test-writing against existing `cli.main()` wiring. If it reveals a real wiring bug, fix it as a follow-up task under this phase (write the fix, keep the test as the regression guard).
- Run `pytest tests/test_cli.py -v` — confirm green.

**Phase 5 exit criteria:** `pytest tests/ -v` fully green including a new CLI-level integration test; no regressions from Phases 1-4.

---

## Final Verification (all phases)

1. `pytest tests/ -v` — full suite green, pristine output (no unexpected warnings/errors).
2. Manual smoke test: run `pseudocodify` against a small real directory (e.g., a subset of this repo) with a real `ANTHROPIC_API_KEY`, confirm output is produced and `[TRANSLATION INCOMPLETE]` markers behave as before.
3. Commit each task separately per CLAUDE.md version-control rules, referencing phase/task number in the commit message (e.g., "Phase 3.2: scope generation prompt context to referenced files").
