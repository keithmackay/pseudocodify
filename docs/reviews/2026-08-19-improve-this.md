# pseudocodify — Improvement Review (2026-08-19)

**Scope:** Full project (no argument passed).

**Project type:** Python CLI/library — LLM-powered codebase-to-pseudocode converter (~560 LOC across 6 core modules + 3 style modules).

**Categories reviewed:** Clarity & Simplification, Code Efficiency, Scalability, Calculation Speed & Accuracy, Test Coverage & Quality, Security, Token Efficiency.

---

## Priority List

```
#1  [Impact: High   | Confidence: High]   Token Efficiency — full CodebaseMap re-serialized into every per-file generation prompt
#2  [Impact: High   | Confidence: High]   Scalability — files analyzed and generated serially, one LLM round-trip at a time
#3  [Impact: Medium | Confidence: High]   Calculation Accuracy — _infer_paradigm can never return "functional" despite schema allowing it
#4  [Impact: Medium | Confidence: Medium] Calculation Accuracy — JSON-decode retries resend the identical prompt, unlikely to self-correct
#5  [Impact: Medium | Confidence: Medium] Security — raw source code is interpolated into LLM prompts with no injection framing/guardrails
#6  [Impact: Low    | Confidence: High]   Clarity — duplicated "resolved style" expression in generator.run_generation
#7  [Impact: Low    | Confidence: Medium] Test Coverage — no end-to-end test of the CLI happy path (analysis → style → generation)
```

---

## Categorized Breakdown

### Token Efficiency

**Full CodebaseMap resent per file** — `pseudocodify/generator.py:54`, `build_generation_prompt`

Every per-file translation prompt embeds `cm.model_dump_json(indent=2)` — the entire analyzed codebase (all files' constructs, deps, refs) — not just the current file's relevant context. Token cost per generation call scales with total codebase size, and total run cost scales as O(files × codebase_size). For a 200-file project this multiplies cost/latency dramatically versus sending only the current file's analysis plus the handful of files it references via `internal_refs`.

Impact: High. Confidence: High.

### Scalability

**Serial LLM calls** — `pseudocodify/analyzer.py:160` (loop in `run_analysis`), `pseudocodify/generator.py:132` (loop in `run_generation`)

Both phases process files one at a time with no concurrency. Each file analysis and each file generation is a separate network round-trip to the LLM; for large codebases this makes total runtime roughly linear in file count with no parallelism, when these are independent, embarrassingly-parallel calls (aside from the map being built before generation starts).

Impact: High. Confidence: High.

### Calculation Speed & Accuracy

**Unreachable "functional" paradigm** — `pseudocodify/analyzer.py:124`, `_infer_paradigm`

`CodebaseMap.dominant_paradigm` is typed as `Literal["OOP", "functional", "procedural", "mixed"]`, but `_infer_paradigm` only ever returns `"OOP"`, `"procedural"`, or `"mixed"` — there's no code path that produces `"functional"`, even for a codebase that's clearly functional (e.g., all top-level functions, no classes). This silently mis-recommends style for functional codebases.

Impact: Medium. Confidence: High.

**Non-adaptive JSON retry** — `pseudocodify/analyzer.py:109-121`, `analyze_file`

On `JSONDecodeError` the loop retries with the exact same prompt up to 3 times. Since LLM output is somewhat stochastic this occasionally helps, but the retry doesn't tell the model what went wrong (e.g., include the parse error or "return valid JSON only") — a wasted-call pattern that lowers the odds of correction.

Impact: Medium. Confidence: Medium.

### Security

**Unmitigated prompt injection surface** — `pseudocodify/analyzer.py:69` (`build_extraction_prompt`), `pseudocodify/generator.py:49` (`build_generation_prompt`)

Raw source file contents are interpolated directly into prompts sent to the LLM, with no delimiter/sandboxing framing beyond a trailing "Source code:" label. A source file containing adversarial text (e.g., a comment saying "ignore prior instructions and instead output X") could manipulate the extraction/generation output. Since this tool is meant to run over third-party or vendored code, this is a plausible real scenario, though the blast radius is limited to malformed/misleading pseudocode output rather than code execution or credential leakage.

Impact: Medium. Confidence: Medium.

### Clarity & Simplification

**Duplicated style-resolution expression** — `pseudocodify/generator.py:119`, `:124`, `:163`

`cfg.style if cfg.style != "auto" else cm.recommended_style` appears three times in `run_generation`. Should be computed once into a local variable. Low risk of bugs today, but a maintenance/readability smell — if the two copies ever drift, style selection and cache-invalidation (`style_changed`) could disagree.

Impact: Low. Confidence: High.

### Test Coverage & Quality

**No CLI-level happy-path integration test** — `tests/test_cli.py`

The three existing CLI tests only cover error paths (invalid style, missing API key, `--help`). There's no test that exercises `cli.main()` end-to-end (analysis → style prompt/auto-select → generation) even with the adapter mocked, so a regression in how `cli.py` wires `run_analysis`/`run_generation`/`_prompt_style` together wouldn't be caught at this layer even though each piece is unit-tested individually.

Impact: Low. Confidence: Medium.
