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

## Flags

### `--help`

If the user invokes this skill with a `--help` flag (e.g. `/pseudocodify --help`), do not run the conversion. Instead, read and display the contents of `help.md` (in this skill's folder) verbatim, then stop. (This is distinct from the underlying `pseudocodify` CLI's own `--help`, which is documented in the Usage section below.)

### `--version`

If the user invokes this skill with a `--version` flag (e.g. `/pseudocodify --version`), do not run the conversion. Instead:

1. Read the installed version from this skill's own manifest: `.claude-plugin/plugin.json` if present, else `.codex-plugin/plugin.json`, else `gemini-extension.json` — whichever exists for this platform install. If none exist (a bare Claude Code skill with only SKILL.md), read the topmost version heading in `CHANGELOG.md` instead.
2. Print: `pseudocodify v<installed-version>`
3. Best-effort update check — determine this skill's GitHub source repo:
   a. If `.git` exists here and `git remote get-url origin` resolves to a `github.com` URL, use that `owner/repo`.
   b. Otherwise, search this skill's own `README.md` for the first `https://github.com/<owner>/<repo>` URL and use that.
   c. If neither yields a repo, or the `gh` CLI isn't installed/authenticated: stop here. Print nothing further — no status line, no error.
4. If a repo was found: run `gh api repos/<owner>/<repo>/releases/latest -q .tag_name` (strip a leading `v`). Compare to the installed version:
   - Equal → append: `Status: up to date`
   - Installed is older → append: `Status: newer version available (v<latest>). To update: if you installed this via a Claude Code marketplace, run /plugin marketplace update <marketplace-name> then reinstall; otherwise, git pull in your install directory if it's a git checkout, or re-copy from https://github.com/<owner>/<repo> per this README's Installation section.`
   - Installed is newer → append: `Status: ahead of latest release (development checkout)`
   - If the API call fails for any reason (network, auth, rate limit, malformed tag): print nothing further — no status line, no error shown to the user.
5. Stop — do not proceed to run the skill's actual workflow.

Note: this version is the **skill's** own version (from its manifest), not the underlying `pseudocodify` CLI's version — check that separately with `pseudocodify --version`.

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
