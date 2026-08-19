---
name: pseudocodify
description: >-
  Use when the user wants to convert a codebase into language-agnostic
  pseudocode — for porting logic to another language, documenting an
  unfamiliar codebase, or producing a language-independent reference of
  program behavior. Triggers on "pseudocodify", "convert to pseudocode",
  "pseudocode this codebase", "port this to <language>" (as a first step),
  or "document this codebase's logic without the language specifics".
---

# Pseudocodify

Convert any codebase into human-readable, language-agnostic pseudocode using the `pseudocodify` CLI. It analyzes a codebase in two phases — building a structured map of the codebase, then generating pseudocode per file using that map for cross-file coherence — and writes `.pseudo` output faithfully capturing logic, structure, and intent regardless of source language.

## When to Use

- The user wants to port a codebase to a new language and needs a language-neutral intermediate representation first
- The user wants to document unfamiliar code without reading every file
- The user explicitly asks to "pseudocodify" a directory or project

## Prerequisites

1. `pseudocodify` must be installed and on `PATH`. Check with `pseudocodify --help`. If missing, install it:
   ```bash
   pip install pseudocodify
   ```
   or from source (if working inside the pseudocodify repo itself):
   ```bash
   pip install -e .
   ```
2. `ANTHROPIC_API_KEY` must be set in the environment. If it isn't, stop and ask the user for it — do not guess or fabricate a key.

## Usage

Run the CLI against the target source directory:

```bash
pseudocodify <source> --output <output> [flags]
```

Ask the user (or infer from context) for:

- **source** — the directory or file to convert (defaults to `.`)
- **output** — where results go (default `./pseudocode/`); use `--consolidate` with a single file path (e.g. `--output all.pseudo.md`) if they want one document instead of per-file output
- **style** — `auto` (default, recommends based on the codebase's dominant paradigm), `cormen` (CLRS/algorithmic), `structured-english` (prose-code hybrid), or `pascal` (BEGIN/END blocks). Prefer `--yes` in non-interactive/agent contexts to skip the interactive style confirmation prompt, unless the user wants to review the recommendation first.
- **include/exclude** — glob patterns to scope the run, useful for large codebases or to skip generated/vendor code (`--exclude "vendor/**" --exclude "*.min.js"`)

Example:

```bash
pseudocodify ./my-project --output ./my-project-pseudo --style auto --yes
```

If a `.pseudocodify.toml` exists at the source root, it supplies defaults; CLI flags always override it.

## Behavior Notes

- **Incremental by default** — re-running against the same output only re-processes changed files, so it's safe to re-invoke after edits.
- **Large codebases** — the tool automatically falls back to a recursive strategy when a codebase exceeds the model's context window; no special flags needed.
- **Failed translations are never silently dropped** — a file that couldn't be translated is marked `[TRANSLATION INCOMPLETE]` in its output. After a run, grep the output for this marker and report any incomplete files to the user rather than treating the run as fully successful.

## After Running

1. Confirm the command exited successfully (`Done.` on stdout).
2. Check output for `[TRANSLATION INCOMPLETE]` markers and surface any to the user.
3. Point the user at the output location; do not open every generated file unless asked.
