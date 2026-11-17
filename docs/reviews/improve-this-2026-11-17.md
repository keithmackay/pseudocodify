# pseudocodify: Improvement Review (2026-11-17)

**Scope:** The whole repository: code (`pseudocodify/`), tests (`tests/`), docs (`docs/`, `CHANGELOG.md`, `CONTRIBUTING.md`, `.github/` templates), `README.md`, the agent skill (`skill/pseudocodify/`) and the agent instruction file (`CLAUDE.md`).

**Project type:** A Python CLI tool and library that uses an LLM to convert a codebase to pseudocode. It is about 700 lines of code: 6 core modules plus 3 style modules, 66 pytest tests, and a Typer CLI with the `pseudocodify` entry point. It ships alongside a cross-platform **agent skill** that wraps the CLI (Claude Code, Codex, Antigravity, Gemini CLI).

**Artifacts found:**
- Skill/command files: `skill/pseudocodify/SKILL.md` and its byte-identical copy `skill/pseudocodify/skills/pseudocodify/SKILL.md`, two identical `help.md` files, `.codex-plugin/plugin.json`, `gemini-extension.json` and `GEMINI.md`
- READMEs: `README.md` (the CLI) and `skill/pseudocodify/README.md` (the skill)
- Agent instruction files: `CLAUDE.md`

**Categories evaluated:** Correctness & Calculation Accuracy, Test Coverage & Quality, Clarity & Simplification, Code Efficiency / Token Efficiency, Scalability, Security, Accuracy & Consistency (claims inventory across docs), README Quality, Skill Effectiveness, Token Efficiency & Progressive Disclosure (skill), Agent Instructions.

**How this run was carried out:**
- The run was non-interactive (assigned by Snugban), so the Step 3 category confirmation was skipped. The categories above are the full proposed set, and the task brief fixed the scope ahead of time.
- The skill's rubric files (`references/skill-rubric.md`, `references/readme-rubric.md`, `references/agent-instructions-rubric.md`) could not be read in this session because file access was denied. README Quality, Skill Effectiveness and Agent Instructions were therefore judged against the general criteria in the skill body, not the detailed rubrics. A rerun with rubric access may surface more findings in those three categories.
- The test suite could not be run because `pytest` is not installed in the available interpreter (Python 3.15). Code findings come from tracing the code by hand, not from running it. Each one cites the lines that support it.

---

## Part 1: Priority List

```
#1  [Impact: High   | Confidence: High]   Correctness: incremental mode never regenerates modified files (stale .pseudo kept forever)
#2  [Impact: High   | Confidence: High]   Correctness: .pseudocodify.toml values are always overwritten by CLI defaults (config file has no effect)
#3  [Impact: High   | Confidence: High]   Correctness: an LLM/network error during generation crashes the whole run
#4  [Impact: High   | Confidence: High]   Test Quality: the "regenerates changed file" test exercises an unreachable state and hides #1
#5  [Impact: High   | Confidence: High]   Accuracy & Consistency: docs/TESTING_GUIDELINES.md belongs to another project (HabitPeeps/Flutter/Playwright)
#6  [Impact: High   | Confidence: High]   Accuracy & Consistency: "failures never silently dropped" is false for analysis failures
#7  [Impact: High   | Confidence: Medium] Scalability / Cost: no default excludes, so venv/node_modules/.git sources get sent to Opus
#8  [Impact: High   | Confidence: Medium] Accuracy & Consistency: "large codebase / context-window fallback" claims are not implemented
#9  [Impact: Medium | Confidence: High]   Correctness: failed translations (marker files) are never retried and count as successes
#10 [Impact: Medium | Confidence: High]   Correctness: --consolidate writes intermediate .pseudo files next to the output file (e.g. into CWD)
#11 [Impact: Medium | Confidence: High]   Correctness: output path collisions (foo.py and foo.js both map to foo.pseudo)
#12 [Impact: Medium | Confidence: High]   Accuracy & Consistency: three different version numbers (0.1.0 / 1.0.0 / 1.1.0), and the skill's --version reads files that don't exist
#13 [Impact: Medium | Confidence: High]   Skill Effectiveness: the --dry-run example shows the wrong output file naming (models.py.pseudo vs models.pseudo)
#14 [Impact: Medium | Confidence: High]   Accuracy & Consistency: CHANGELOG 1.1.0 lists skill-only flags as if they were CLI features
#15 [Impact: Medium | Confidence: High]   Correctness: analysis retries cover only JSON errors, so schema/validation errors fail on the first attempt
#16 [Impact: Medium | Confidence: High]   Agent Instructions: CLAUDE.md bans mocks in E2E tests, but the CLI "end-to-end" test mocks the adapter
#17 [Impact: Medium | Confidence: High]   Accuracy & Consistency: "source may be a file" is advertised but not supported
#18 [Impact: Medium | Confidence: High]   Clarity: ABOUTME header rule violated by 16 of 18 Python files
#19 [Impact: Medium | Confidence: Medium] README Quality: root README omits the agent skill, the cache directory, cost/privacy notes and sample output
#20 [Impact: Medium | Confidence: Medium] Token Efficiency & Progressive Disclosure: --version and --dry-run procedures sit in the always-loaded SKILL.md
#21 [Impact: Medium | Confidence: Medium] Skill Effectiveness: duplicated SKILL.md/help.md copies with no sync check
#22 [Impact: Medium | Confidence: Medium] Agent Instructions: CLAUDE.md is entirely generic: no build/test commands, architecture or project facts
#23 [Impact: Medium | Confidence: Medium] Agent Instructions: CLAUDE.md references a "journal tool" that this project does not provide
#24 [Impact: Medium | Confidence: Medium] Skill README: install paths are ambiguous and the Gemini URL is a placeholder
#25 [Impact: Medium | Confidence: Medium] Accuracy & Consistency: the architecture summary sends the full CodebaseMap in one prompt, unbounded
#26 [Impact: Low    | Confidence: High]   Calculation Accuracy: the "pascal" style can never be auto-recommended
#27 [Impact: Low    | Confidence: High]   Accuracy & Consistency: CONTRIBUTING says "all 49 tests" (there are 66); README installs the unused pytest-mock
#28 [Impact: Low    | Confidence: High]   Clarity: duplicated constants (MAX_WORKERS, extension lists, style menu, model default, VALID_STYLES name)
#29 [Impact: Low    | Confidence: High]   Clarity: duplicate "[ANALYSIS FAILED]" warnings printed per failed file
#30 [Impact: Low    | Confidence: Medium] Correctness: a corrupt or out-of-date cache (analysis.json / state.json) crashes the run
#31 [Impact: Low    | Confidence: Medium] Security: source text can close the "untrusted data" delimiter early
#32 [Impact: Low    | Confidence: Medium] Accuracy & Consistency: --verbose promises per-file progress that is never printed
#33 [Impact: Low    | Confidence: Medium] Test Quality: tautological / weak assertions in a few tests
#34 [Impact: Low    | Confidence: Medium] Agent Instructions: internal tensions and small errors in CLAUDE.md
#35 [Impact: Low    | Confidence: Medium] Test Coverage: no CI workflow; dev dependencies not declared in pyproject
```

---

## Part 2: Categorized Breakdown

### Correctness & Calculation Accuracy

**#1 Incremental mode never regenerates modified files** (Impact: High | Confidence: High)
- Evidence: `pseudocodify/analyzer.py:183-187` re-analyzes a changed file and stores the *current* hash (`data["source_hash"] = source_hash`, `analyzer.py:125`). `pseudocodify/generator.py:159-163` then decides whether to skip by comparing `hash_file(source_path) == fa.source_hash`. Those two values are now always equal, so if the old `.pseudo` exists the check `if not style_changed and pseudo_path.exists() and source_unchanged:` skips the file.
- Why: the generator's hash check compares the source with the analysis that was just recomputed. It never compares the source with the version the existing `.pseudo` was generated from. After the first run, editing a source file updates `analysis.json`, but the stale pseudocode is kept and reported as success. "Incremental by default" is the headline feature (`README.md:12`, `SKILL.md:106`), and in a normal workflow it silently produces wrong output. Only a style change or deleting the output forces regeneration.

**#2 `.pseudocodify.toml` is effectively ignored** (Impact: High | Confidence: High)
- Evidence: `pseudocodify/cli.py:39-43` builds `cli_overrides` from every Typer parameter, including untouched defaults (`"output": output`, `"style": style`, `"model": model`, `"include": include or []`, …). `pseudocodify/config.py:38` applies each override `if value is not None`. No default is `None`, so every TOML key is overwritten.
- Why: `README.md:73` ("Place a `.pseudocodify.toml` … to set run defaults") and `SKILL.md:102` describe a feature that does nothing when the tool runs from the CLI. `tests/test_config.py:26-30` only tests `load_config` with a hand-built overrides dict, so the bug in how the CLI wires it up isn't covered.

**#3 A generation-phase LLM error crashes the whole run** (Impact: High | Confidence: High)
- Evidence: `pseudocodify/generator.py:102`: `result = adapter.run(prompt, context=style.SYSTEM_PROMPT)` has no try/except, and `RLMAdapter.run` raises `RLMError` (`rlm_adapter.py:27`). `generator.py:180` `success = future.result()` re-raises in the main thread. `cli.py:70` `architecture_summary = adapter.run(summary_prompt)` is also unguarded.
- Why: one transient API error (rate limit, timeout) aborts the run. No README index is written, no state is saved, and you get a traceback instead of the `[TRANSLATION INCOMPLETE]` marker. The design spec says failures should be handled per file (`docs/superpowers/specs/2026-04-17-pseudocodify-design.md:288`: "Warning logged with file path; remaining files continue"). The analyzer phase does catch these errors (`analyzer.py:134`), so the two phases behave inconsistently.

**#9 Failed translations are never retried and are counted as successes** (Impact: Medium | Confidence: High)
- Evidence: on failure, `generator.py:116-117` still writes a `.pseudo` file containing the `[TRANSLATION INCOMPLETE …]` marker. On the next run `generator.py:163` sees `pseudo_path.exists()` and an unchanged hash, adds the file to `succeeded` and skips it. In consolidate mode, `generator.py:192-194` then includes the marker file as successful content.
- Why: a transient failure becomes permanent until the source or style changes. The end-of-run summary (`generator.py:211`) then overstates success.

**#10 `--consolidate` scatters intermediate `.pseudo` files next to the output file** (Impact: Medium | Confidence: High)
- Evidence: `generator.py:151`: `pseudo_dir = output.parent if cfg.consolidate else output`. With the documented `--output all.pseudo.md` (`README.md:49`), `output.parent` is the current directory, so a per-file `.pseudo` tree mirroring the source is written into CWD.
- Why: you get unexpected files mixed into your working directory (possibly the source tree itself), and none of this is documented.

**#11 Output path collisions** (Impact: Medium | Confidence: High)
- Evidence: `generator.py:107`, `:157` and `:46` all derive the output name with `rel_path.rsplit(".", 1)[0] + ".pseudo"`.
- Why: `util.py` and `util.js`, or `foo.c` and `foo.h` (`.h` isn't recognized today, but `foo.ts` and `foo.js` are), map to the same `foo.pseudo`. The concurrent writers race and one translation silently overwrites the other. The README index then lists two entries pointing to the same file. This is common in mixed TS/JS or C/C++ repos.

**#15 Analysis retries only cover JSON decode errors** (Impact: Medium | Confidence: High)
- Evidence: `analyzer.py:127-136`. `json.JSONDecodeError` gets a corrective retry. Every other exception, including pydantic `ValidationError` (e.g. the model emits `"kind": "interface"` or omits `purpose`), hits `except Exception`, which prints a warning and returns `None` on the first attempt.
- Why: schema-violating but valid JSON is the most likely LLM failure once the prompt says "JSON only", and it is the case where a corrective retry would help most. The CHANGELOG claim "after 3 retries" (`CHANGELOG.md:28`) doesn't hold for it. `tests/test_analyzer.py:165-176` asserts that non-JSON errors do not retry, which is reasonable for `RLMError`, but it also locks in this behaviour for validation errors.

**#26 The "pascal" style can never be auto-recommended** (Impact: Low | Confidence: High)
- Evidence: `analyzer.py:164-167` returns the first style in dict order whose `PARADIGM_FIT` contains the paradigm. `cormen.py:2` claims `["OOP", "functional"]` and `structured_english.py:2` claims `["procedural", "mixed"]`, so `pascal.py:2` `["procedural", "OOP"]` never wins.
- Why: `PARADIGM_FIT` on pascal is dead data, and the "auto-recommendation" (`README.md:11`) really only chooses between two styles. A related issue: `_infer_paradigm` calls any class-free codebase with zero module-level variables "functional" (`analyzer.py:156`), which is a weak signal (methods aren't counted at all).

**#30 A corrupt or out-of-date cache crashes the run** (Impact: Low | Confidence: Medium)
- Evidence: `analyzer.py:72` `CodebaseMap.model_validate_json(path.read_text())` and `generator.py:130` `json.loads(path.read_text())` have no error handling.
- Why: an interrupted write or a future schema change to `CodebaseMap` turns every later run into a traceback until you find and delete `.pseudocodify/` by hand. That directory isn't documented anywhere (see #19).

### Test Coverage & Quality

**#4 The "regenerates changed file" test exercises an unreachable state** (Impact: High | Confidence: High)
- Evidence: `tests/test_generator.py:384`: `source_hash="stale_hash"`. In the real pipeline, `run_analysis` always refreshes `source_hash` before `run_generation` runs (see #1), so a `FileAnalysis` with a stale hash never reaches the generator.
- Why: the test passes while the behaviour it claims to protect ("Files whose source hash differs from the cached hash must be re-generated", `test_generator.py:366`) is broken end to end. No test runs analysis then generation twice with a source edit in between.

**#33 Tautological or weak assertions** (Impact: Low | Confidence: Medium)
- Evidence: `tests/test_rlm_adapter.py:45`, `assert not issubclass(RLMError, BaseException) or issubclass(RLMError, Exception)`, is always true. `tests/test_cli.py:13` accepts the style name appearing anywhere in output *or* the exception string. `tests/test_styles.py:16` checks `len(style.SYSTEM_PROMPT) > 50`.
- Why: these tests add to the count without guarding behaviour. Several tests (e.g. `test_rlm_adapter.py:6-15`) mainly check that a mocked return value comes back out. The project's CLAUDE.md (`CLAUDE.md:119`) asks for these to be flagged.

**#35 No CI; dev dependencies undeclared** (Impact: Low | Confidence: Medium)
- Evidence: `.github/` has only issue/PR templates, and no `workflows/` directory exists. `pyproject.toml` has no `[project.optional-dependencies]` or dependency group for `pytest`.
- Why: the PR template asks contributors to confirm `pytest tests/ -v` passes (`.github/pull_request_template.md:7`), but nothing enforces it. Contributors install test tools from prose instructions.

### Clarity & Simplification

**#18 The ABOUTME header rule is mostly unmet** (Impact: Medium | Confidence: High)
- Evidence: `CLAUDE.md:92` says "All code files MUST start with a brief 2-line comment … 'ABOUTME: '". `CONTRIBUTING.md:34` and the PR template (`.github/pull_request_template.md:14`) repeat it. Only `pseudocodify/cli.py`, `pseudocodify/generator.py` and `tests/test_generator.py` comply. The other 16 Python files are missing it, including `analyzer.py`, `config.py`, `models.py`, `rlm_adapter.py`, all `styles/*.py` and all other test files.
- Why: either the rule should apply (and the files are out of compliance) or it shouldn't. As things stand, the documented standard and the code disagree.

**#28 Duplicated constants and parallel sources of truth** (Impact: Low | Confidence: High)
- Evidence:
  - `MAX_WORKERS = 8` is defined in both `analyzer.py:13` and `generator.py:17`.
  - `RECOGNIZED_EXTENSIONS` (`analyzer.py:15-19`) duplicates the keys of `ext_map` in `_detect_language` (`analyzer.py:97-104`).
  - The style menu in `cli.py:77-81` hard-codes names and descriptions that already live in each style module's `STYLE_NAME`.
  - The prompt text `"Please enter 1, 2, or 3."` (`cli.py:107`) hard-codes the count.
  - The model default `"claude-opus-4-6"` appears in `config.py:13`, `cli.py:21`, `README.md:65` and `README.md:80`.
  - `VALID_STYLES` names a list in `cli.py:13` and a dict in `styles/__init__.py:4`.
- Why: each pair can drift. A fourth style or a new extension needs edits in several places, and `docs/plans/PHASES_SUMMARY.md:137` already tells maintainers to update two lists by hand.

**#29 Duplicate failure warnings** (Impact: Low | Confidence: High)
- Evidence: `analyzer.py:135` prints `WARNING: [ANALYSIS FAILED] {rel_path} — {e}` inside `analyze_file`, and `analyzer.py:204-205` prints `WARNING: [ANALYSIS FAILED] {f}` again for the same file.
- Why: noisy stderr that makes failure counts look doubled.

### Code Efficiency / Token Efficiency & Scalability

**#7 No default excludes, so vendored and virtualenv code is sent to the LLM** (Impact: High | Confidence: Medium)
- Evidence: `analyzer.py:42` `for path in source.rglob("*")` filters only by extension and by user-supplied globs. Nothing skips `.git/`, `venv/`, `.venv/`, `node_modules/`, `.worktrees/`, `dist/` or `build/`.
- Why: `pseudocodify .` on a typical Python or JS project picks up thousands of third-party files. Each costs two Opus calls (analysis plus generation), and they all go into the summary prompt (#25). This is a large, unannounced cost and latency multiplier. Confidence is Medium only because some users will always pass `--exclude`. The README example config (`README.md:79`) shows excludes but doesn't warn that they are effectively required.

**#25 The architecture summary prompt is unbounded** (Impact: Medium | Confidence: Medium)
- Evidence: `cli.py:66-70` interpolates `cm.model_dump_json(indent=2)` for the *entire* codebase into one prompt.
- Why: the previous review's scoped-context fix (`generator.py:51-65`) bounded per-file prompts, but this call still grows linearly with codebase size. On large repos it will exceed the model's context and, because of #3, crash after all the analysis spend. This is the scenario "Large codebase support" is meant to cover (see #8).

### Security

**#31 Source text can close the delimiter early** (Impact: Low | Confidence: Medium)
- Evidence: `analyzer.py:21-22` and `generator.py:82` wrap source in fixed markers (`<<<END SOURCE CODE>>>`) without escaping or checking for that string in the source.
- Why: a hostile file can contain the end marker followed by instructions, which bypasses the framing added after the previous review. The impact is still limited to misleading pseudocode, but a per-run random nonce in the markers would close the gap cheaply. Separately, the README never tells users that **full source code is sent to Anthropic's API** (see #19), which matters for proprietary code.

### Accuracy & Consistency (claims inventory)

**#5 `docs/TESTING_GUIDELINES.md` describes a different project** (Impact: High | Confidence: High)
- Evidence: `docs/TESTING_GUIDELINES.md:1`: "# HabitPeeps Testing Guidelines". It prescribes Flutter `test`, widget tests and Playwright (`:23`, `:72`).
- Why: any human or agent that reads it for this Python project gets wrong instructions. It appears to have been copied in from a template and never adapted.

**#6 "Failures are never silently dropped" is false for analysis failures** (Impact: High | Confidence: High)
- Evidence: `README.md:14` says "failed translations are flagged with `[TRANSLATION INCOMPLETE]`, never silently dropped". `SKILL.md:108` says "Failed translations are never silently dropped". But a file that fails *analysis* is left out of `result_files` (`analyzer.py:198-199`). It gets no `.pseudo`, no marker, no README index entry, and it isn't counted in the `n_ok/total` summary, because `total = len(cm.files)` (`generator.py:207`).
- Why: the only trace is a stderr line. The skill tells agents to judge success by grepping output for `[TRANSLATION INCOMPLETE]` (`SKILL.md:113`), so agents will report a run as complete when files are missing.

**#8 Large-codebase / context-window fallback claims are not implemented** (Impact: High | Confidence: Medium)
- Evidence:
  - `README.md:13` claims "uses the Recursive Language Model (RLM) strategy to process codebases that exceed context limits".
  - `SKILL.md:107` claims "the tool automatically falls back to a recursive strategy when a codebase exceeds the model's context window".
  - The design spec (`docs/superpowers/specs/…-design.md:151`) promises splitting files over ~3,000 tokens at function/class boundaries.
  - The code (`rlm_adapter.py:21-25`) makes one `completion()` call per prompt with no chunking, size check or fallback path. The success criterion "Large codebases (>context limit) complete without crashing via RLM" (`docs/plans/PHASES_SUMMARY.md:129`) can't be met while #3 and #25 stand.
- Why: users and agents will rely on a capability that doesn't exist in this repo. Confidence is Medium because the `rlms` library may recurse internally on one oversized prompt. Even so, nothing here verifies or tests that behaviour.

**#12 Three different version numbers; the skill's `--version` reads files that aren't there** (Impact: Medium | Confidence: High)
- Evidence:
  - `pyproject.toml:7` says `version = "0.1.0"`, `skill/pseudocodify/.codex-plugin/plugin.json:3` and `gemini-extension.json:4` say `"1.0.0"`, and `CHANGELOG.md:9` says `## [1.1.0]`. The latest commit is "Bump version to v1.1.0".
  - `SKILL.md:32` reads `.claude-plugin/plugin.json` (absent) and then falls back to "the topmost version heading in `CHANGELOG.md`". No `CHANGELOG.md` exists in the skill folder. The root changelog's topmost heading is `## [Unreleased]`, not a version.
- Why: `/pseudocodify --version` prints `1.0.0` or an invalid value, and its update check compares against GitHub releases of a repo that also versions the CLI. `pip show pseudocodify` reports 0.1.0. You can't tell which version you're running.

**#14 CHANGELOG 1.1.0 lists skill-only flags as CLI features** (Impact: Medium | Confidence: High)
- Evidence: `CHANGELOG.md:11` "Add `--dry-run` flag" and `:13` "Add --version flag support". The CLI (`cli.py:16-26`) has neither flag. Both exist only in `SKILL.md`. The changelog doesn't separate CLI changes from skill changes.
- Why: CLI users will try `pseudocodify --dry-run` or `pseudocodify --version` and get a Typer error. `SKILL.md:45` also tells users to "check that separately with `pseudocodify --version`", which doesn't exist. The bug-report template asks for the "pseudocodify version" (`.github/ISSUE_TEMPLATE/bug_report.yml:47`), and there is no CLI way to get it.

**#17 "Source may be a file" is advertised but unsupported** (Impact: Medium | Confidence: High)
- Evidence: `cli.py:17` `help="Source directory or file"`, `SKILL.md:91` "the directory or file to convert", `help.md:21` "Convert a specific directory/file". But `discover_files` calls `source.rglob("*")` (`analyzer.py:42`), which yields nothing for a file. The TOML lookup becomes `<file>/.pseudocodify.toml` (`cli.py:38`).
- Why: a single-file run quietly processes zero files, prints "Done." and still makes one LLM call for the architecture summary.

**#27 Stale counts and unnecessary dependencies in contributor docs** (Impact: Low | Confidence: High)
- Evidence: `CONTRIBUTING.md:28` says "Ensure all 49 tests pass", but there are 66 test functions across `tests/`. `README.md:90` and `CONTRIBUTING.md:17` install `pytest-mock`, but no test uses the `mocker` fixture (all tests use `unittest.mock`). `CONTRIBUTING.md:21` mentions "tests that make real LLM calls", and none exist.
- Why: small inaccuracies that make the docs look unmaintained.

**#32 `--verbose` promises per-file progress** (Impact: Low | Confidence: Medium)
- Evidence: `README.md:69` "`--verbose` … Show per-file progress" and `CHANGELOG.md:33`. The code only prints the two phase banners (`cli.py:52-53`, `:62-63`) and passes `verbose` through to `rlms`.
- Why: the docs describe output that the code doesn't produce. Confidence is Medium because `rlms` verbose output may include something per call.

### README Quality

**#19 The root README leaves out several things users need** (Impact: Medium | Confidence: Medium)
- Evidence (from reading all of `README.md`):
  - No mention of the agent skill in `skill/pseudocodify/` or the mackayi marketplace install. `CHANGELOG.md:12` says this was documented "in README", but it's only in the skill's README.
  - No mention that a `.pseudocodify/` cache directory is written *into the source tree* (`analyzer.py:173`), or that it should be gitignored.
  - No cost or privacy note: every file's full source is sent to Anthropic, twice, with Opus as the default model.
  - No sample of what a `.pseudo` file looks like in each style, though choosing a style is the main interactive decision.
  - The `-o` short alias (`cli.py:18`) isn't documented.
  - `--model` default `claude-opus-4-6` isn't the current model generation. That's fine as a pin, but worth revisiting.
  - The PyPI badge and `pip install pseudocodify` (`README.md:3`, `:25`) couldn't be checked offline. If the package isn't published, the primary install path fails.
- Why: the README is the deliverable most users read. These gaps cover what to install, where files are written, and what running it costs.

### Skill Effectiveness

**#13 The `--dry-run` example shows the wrong output naming** (Impact: Medium | Confidence: High)
- Evidence: `SKILL.md:60-63` shows `./pseudocode/src/models.py.pseudo`. The generator strips the source extension and writes `src/models.pseudo` (`generator.py:107`).
- Why: an agent following the example reports wrong paths and, worse, checks the wrong paths for "would overwrite". Every existing file then looks like "would create".

**Related: the dry-run "would skip (unchanged)" step has no method** (part of #13)
- Evidence: `SKILL.md:66` asks the agent to identify unchanged files "via SHA-256 hashing" but never says that the hashes live in `<source>/.pseudocodify/analysis.json` or how to compare them. Because of #1 and #9, "unchanged" in the real tool doesn't mean what the dry-run would infer anyway.
- Why: the agent has to improvise this step, so different runs will report different results.

**#21 Duplicated skill files with no sync check** (Impact: Medium | Confidence: Medium)
- Evidence: `skill/pseudocodify/SKILL.md` and `skill/pseudocodify/skills/pseudocodify/SKILL.md` are byte-identical (114 lines), and so are the two `help.md` files. `GEMINI.md:1` points at the nested copy, and `.codex-plugin/plugin.json:5` points at `./skills/`. Nothing records which copy is canonical, and there is no script to keep them in sync.
- Why: the next edit to one copy will make them drift, and each platform will then behave differently. Findings #13, #12 and #8 already have to be fixed in both places.

**#24 The skill README's install instructions are ambiguous** (Impact: Medium | Confidence: Medium)
- Evidence: `skill/pseudocodify/README.md:17` `cp -r /path/to/pseudocodify/ ~/.claude/skills/pseudocodify/`. It's unclear whether `/path/to/pseudocodify/` means the repo root (which would copy the whole Python project) or `skill/pseudocodify/`. `:68` `gemini extensions install https://github.com/<owner>/pseudocodify-skill` uses a placeholder owner and a repo name that doesn't match `keithmackay/pseudocodify`. `:76` says the skill "must live in a GitHub repository" without saying which one.
- Why: users copying these commands literally get a broken install. The `--version` update check (`SKILL.md:36`) also uses "the first github URL in README.md", which here is the CLI repo. That only works if the CLI and the skill share release tags.

### Token Efficiency & Progressive Disclosure (skill)

**#20 Situational procedures sit in the always-loaded SKILL.md** (Impact: Medium | Confidence: Medium)
- Evidence: the `--version` procedure (`SKILL.md:28-45`, about 18 lines including the GitHub API and update-message wording) and the `--dry-run` procedure (`SKILL.md:47-67`, about 21 lines) take up about a third of the file. The install commands in Prerequisites (`SKILL.md:71-78`) are needed only when the CLI is missing.
- Content to move out:
  - The `--version` procedure → `version.md`, loaded only when `--version` is passed (the same pattern the skill already uses for `--help` → `help.md`).
  - The `--dry-run` procedure → `dry-run.md`, loaded only when `--dry-run` is passed.
  - The install/setup commands → the skill's `README.md` or `help.md`, referenced only when `pseudocodify --help` fails.
- A Clarity & Simplification pass on the remaining always-loaded content is also worthwhile. In particular, the "Behavior Notes" claims need correcting to match the tool's real behaviour (#1, #6, #8).

### Agent Instructions (`CLAUDE.md`)

**#16 The no-mocks-in-E2E rule conflicts with the existing test** (Impact: Medium | Confidence: High)
- Evidence: `CLAUDE.md:120` says "YOU MUST NEVER implement mocks in end to end tests. We always use real data and real APIs." But `tests/test_cli.py:30` says `"""End-to-end happy path …"""` and patches `RLMAdapter` with a `MagicMock` (`test_cli.py:47-54`). There are no real-API tests.
- Why: an agent following CLAUDE.md must either "fix" this test into a paid live-API test or treat the rule as dead. Either the rule needs a project-specific note (how real-API E2E tests run, which key, what cost limit) or the test needs a different label.

**#22 CLAUDE.md is entirely generic** (Impact: Medium | Confidence: Medium)
- Evidence: all 169 lines are cross-project behaviour rules. There is no project command (`pip install -e .`, `pytest tests/ -v`), no module map (analyzer → generator → styles → rlm_adapter), no note about the `.pseudocodify/` cache, the duplicated skill files (#21), or the requirement to keep `ANTHROPIC_API_KEY` out of tests.
- Why: an agent starting in this repo gets nothing from the always-loaded file about *this* project. Facts such as "keep both SKILL.md copies in sync" or "CLI and skill are versioned separately" are exactly what an instruction file should hold.

**#23 References to tools this project doesn't provide** (Impact: Medium | Confidence: Medium)
- Evidence: `CLAUDE.md:23-24` "Use your journal …" and `CLAUDE.md:163-167` "YOU MUST use the journal tool frequently". No journal tool or MCP server is configured in the repo. `CLAUDE.md:127` names "TodoWrite", which isn't available under that name on every agent platform the skill targets.
- Why: MUST-level instructions that can't be followed teach agents to ignore the file's MUSTs, which weakens the rules that matter.

**#34 Internal tensions and small errors** (Impact: Low | Confidence: Medium)
- Evidence:
  - `CLAUDE.md:19` "YOU MUST ALWAYS STOP and ask for clarification rather than making assumptions" against `CLAUDE.md:32` "When asked to do something, just do it". These need a tie-breaker; the "Only pause … when" list at `:33-38` partly provides one, but the absolute wording at `:19` contradicts it.
  - `CLAUDE.md:110` requires phase/task numbers in every commit message, but recent history (`dde1bf8 Bump version to v1.1.0`, `7b261d4 Add --dry-run flag …`) doesn't follow it.
  - Typo at `CLAUDE.md:25`: "architectutral". `CLAUDE.md:30` uses a `#` H1 among `##` sections.
- Why: contradictory absolutes make agent behaviour unpredictable, and a rule that history doesn't follow reads as optional.

---

## Next Steps

1. **Save report:** saved to `docs/reviews/improve-this-2026-11-17.md`. The Snugban task set this path, so it was used instead of the skill's default `docs/reviews/YYYY-MM-DD-improve-this.md`.
2. **Implementation plan:** not created. The task is evaluate-and-report only, and no findings were selected. To create one, rerun improve-this's Step 6 and pick finding numbers (e.g. `1,2,3,4,6`). For the skill-related findings (#20, #19, #24, #13), the plan should use the `make-readme` skill for README work and the `plsfix` skill for the SKILL.md clarity and token-efficiency pass.
