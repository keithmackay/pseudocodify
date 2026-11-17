# pseudocodify

![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![PyPI](https://img.shields.io/pypi/v/pseudocodify) ![Last Commit](https://img.shields.io/github/last-commit/keithmackay/pseudocodify)

Convert any codebase into language-agnostic pseudocode. Point `pseudocodify` at a project directory and it produces human-readable `.pseudo` files that faithfully capture all logic, structure, and intent — regardless of source language. Useful for porting codebases to new languages or documenting unfamiliar code without needing to read every file.

## Highlights

- **Language-agnostic** — LLM-powered analysis handles Python, TypeScript, Go, Rust, Java, and more without language-specific parsers
- **Two-phase pipeline** — Phase 1 builds a structured `CodebaseMap`; Phase 2 generates pseudocode using that map for cross-file coherence
- **Three pseudocode styles** — CLRS/Cormen (algorithmic), Structured English (prose-code), or Pascal-like (BEGIN/END blocks), with auto-recommendation based on codebase paradigm
- **Incremental by default** — unchanged files are skipped on re-runs; only modified files are re-processed
- **Large codebase support** — uses the Recursive Language Model (RLM) strategy to process codebases that exceed context limits
- **Transparent failures** — failed translations are flagged with `[TRANSLATION INCOMPLETE]`, never silently dropped

## Getting Started

**Prerequisites:**
- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

**Installation:**

```bash
pip install pseudocodify
```

Or from source:

```bash
git clone https://github.com/keithmackay/pseudocodify
cd pseudocodify
pip install -e .
```

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
# Translate a codebase to pseudocode (per-file output)
pseudocodify ./my-project --output ./my-project-pseudo

# Single consolidated output file
pseudocodify ./my-project --output all.pseudo.md --consolidate

# Specify a pseudocode style
pseudocodify ./my-project --style cormen

# Skip interactive style confirmation
pseudocodify ./my-project --yes
```

The positional `SOURCE` argument is the directory to translate and defaults to `.`.

Available flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--output`, `-o` | `./pseudocode/` | Output file (consolidate mode) or directory (per-file mode) |
| `--consolidate` | `false` | Merge all output into a single document |
| `--style` | `auto` | `auto`, `cormen`, `structured-english`, or `pascal` |
| `--model` | `claude-opus-4-6` | Claude model to use |
| `--include` | recognized extensions | Glob patterns for files to include (repeatable) |
| `--exclude` | none | Glob patterns for files to skip (repeatable) |
| `--yes` | `false` | Skip interactive style confirmation |
| `--verbose` | `false` | Show per-file progress |

With `--style auto`, `pseudocodify` detects the codebase's dominant paradigm (OOP, functional, procedural, or mixed), recommends a style, and lets you accept it or pick another from a menu. It skips the prompt and uses the recommendation when you pass `--yes` or when stdin is not a terminal.

### Output

In per-file mode, each source file gets a `.pseudo` file at the same relative path under the output directory, with its extension replaced (`src/cli.py` → `pseudocode/src/cli.pseudo`). A `README.pseudo.md` index with an architecture summary and file list is written at the output root.

In consolidate mode, the index and every translated file are merged into the single `--output` file. The per-file `.pseudo` files are still written, alongside that file.

Run state (the cached `CodebaseMap` and the last-used style) is stored in a `.pseudocodify/` directory inside the source directory. You'll likely want to add it to that project's `.gitignore`. Changing the style forces every file to be regenerated.

Files that fail structure extraction after 3 retries are reported as `[ANALYSIS FAILED]` on stderr. Files that fail translation after 3 retries get a `.pseudo` file containing only the header and a `[TRANSLATION INCOMPLETE]` marker, are left out of consolidated output, and are listed in the end-of-run summary.

Only files with a recognized source extension are processed: `.py`, `.js`, `.ts`, `.go`, `.rb`, `.java`, `.cs`, `.cpp`, `.c`, `.rs`, `.php`, `.swift`, `.kt`, `.scala`, `.r`, `.m`, `.sh`, `.bash`, `.pl`, `.lua`. `--include` narrows that set; it can't add other extensions.

## Configuration

Place a `.pseudocodify.toml` in the source directory to set run defaults. Any field from the flags table is accepted, and CLI flags take precedence.

```toml
[pseudocodify]
style = "cormen"
consolidate = false
exclude = ["tests/**", "vendor/**", "*.min.js"]
model = "claude-opus-4-6"
output = "./pseudocode"
```

> [!NOTE]
> See [Limitations](#limitations): when run from the CLI, values in this file are overridden by the CLI's own defaults.

## Coding-Agent Skill

The [`skill/pseudocodify/`](skill/pseudocodify/) directory contains a skill that wraps this CLI for Claude Code, Codex, Antigravity, and Gemini CLI. It checks prerequisites, runs `pseudocodify` with sensible flags, and reports any `[TRANSLATION INCOMPLETE]` files. It also supports `--help`, `--version`, and a `--dry-run` preview of which `.pseudo` files a run would create or overwrite.

Install it from the mackayi marketplace in Claude Code:

```text
/plugin marketplace add keithmackay/mackayi
/plugin install pseudocodify@mackayi
```

See [skill/pseudocodify/README.md](skill/pseudocodify/README.md) for per-platform installation instructions.

## Limitations

- **Config file values are overridden by CLI defaults** — the CLI passes every option (including unset ones at their default values) as an override, so settings in `.pseudocodify.toml` never take effect when you run `pseudocodify` from the command line. Pass the options as flags instead.
- **Same-name files collide** — output paths drop the source extension, so `utils.py` and `utils.ts` in the same directory both map to `utils.pseudo`, and one overwrites the other.
- **Fixed language list** — files outside the recognized extensions listed under [Output](#output) are skipped silently.

## Development

```bash
git clone https://github.com/keithmackay/pseudocodify
cd pseudocodify
pip install -e .
pip install pytest
pytest tests/ -v
```

## Contributing

Contributions are welcome. Fork the repo, create a branch, and open a pull request. Please ensure all tests pass before submitting. See [CONTRIBUTING.md](CONTRIBUTING.md) for bug-report, feature-request, and code-style guidance.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

[MIT](LICENSE) © 2026 Keith MacKay
