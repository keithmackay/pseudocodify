# pseudocodify — improve-this Phases Summary (2026-08-19)

Quick reference for the improvement roadmap from the 2026-08-19 `/improve-this` review. Full detail in `docs/plans/improve-this-2026-08-19.md`. Source findings in `docs/reviews/2026-08-19-improve-this.md`.

---

## Key Principles

- **TDD** — write the failing test first, then the minimal implementation
- **DRY** — no repeated logic across modules
- **YAGNI** — no speculative flags/config; keep new knobs (e.g., concurrency caps) internal unless requested
- **Frequent commits** — every task ends with a commit, referencing phase/task number
- **Transparent failures** — never silently drop content; preserve existing `[TRANSLATION INCOMPLETE]` behavior through every phase

---

## Phase 1: Correctness Fixes

**Goal:** Fix accuracy bugs and remove duplication before touching prompt/concurrency architecture.

| Task | Description | Finding |
|------|-------------|---------|
| 1.1 | Fix unreachable `"functional"` paradigm in `_infer_paradigm` | #3 |
| 1.2 | Make JSON-decode retries adaptive (include parse error in retry prompt) | #4 |
| 1.3 | Deduplicate the repeated style-resolution expression in `run_generation` | #6 |

**Key deliverables:** All four documented paradigms reachable; retries carry error feedback; single source of truth for resolved style.

---

## Phase 2: Security Hardening

**Goal:** Reduce prompt-injection surface without restricting translation capability.

| Task | Description | Finding |
|------|-------------|---------|
| 2.1 | Delimit and label source code in extraction/generation prompts | #5 |

**Key deliverables:** Both prompt builders clearly separate "data to analyze" from "instructions to follow."

---

## Phase 3: Token Efficiency — Scoped Context Per File

**Goal:** Stop resending the full `CodebaseMap` on every generation call.

| Task | Description | Finding |
|------|-------------|---------|
| 3.1 | Compute relevant-file context (self + `internal_refs` neighbors) for a given file | #1 |
| 3.2 | Wire scoped context into `build_generation_prompt`, replacing full-map serialization | #1 |

**Key deliverables:** Per-file prompt size scales with reference neighborhood, not total codebase size.

---

## Phase 4: Scalability — Concurrent File Processing

**Goal:** Parallelize independent per-file LLM calls in analysis and generation. Sequenced after Phase 3 so concurrency doesn't amplify oversized payloads.

| Task | Description | Finding |
|------|-------------|---------|
| 4.1 | Bounded-concurrency analysis (replace serial loop in `run_analysis`) | #2 |
| 4.2 | Bounded-concurrency generation (replace serial loop in `run_generation`), preserving deterministic consolidate-mode ordering | #2 |

**Key deliverables:** Both phases run with bounded concurrency; incremental/caching behavior unchanged; consolidated output order remains deterministic.

---

## Phase 5: Test Coverage — CLI Integration Test

**Goal:** Close the CLI-level integration gap once the pipeline's shape has settled from Phases 1-4.

| Task | Description | Finding |
|------|-------------|---------|
| 5.1 | End-to-end happy-path CLI test (mocked adapter, temp source tree, `--yes`) | #7 |

**Key deliverables:** Full pipeline wiring (`analysis → style selection → generation`) covered by a single integration test.

---

## Final Verification

1. `pytest tests/ -v` fully green, pristine output.
2. Manual smoke test against a small real directory with a real `ANTHROPIC_API_KEY`.
3. Each task committed separately, referencing phase/task number in the commit message.
