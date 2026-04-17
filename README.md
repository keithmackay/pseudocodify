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

Available flags:

| Flag | Default | Description |
|------|---------|-------------|
| `--output` | `./pseudocode/` | Output file (consolidate mode) or directory (per-file mode) |
| `--consolidate` | `false` | Merge all output into a single document |
| `--style` | `auto` | `auto`, `cormen`, `structured-english`, or `pascal` |
| `--model` | `claude-opus-4-6` | Claude model to use |
| `--include` | recognized extensions | Glob patterns for files to include |
| `--exclude` | none | Glob patterns for files to skip |
| `--yes` | `false` | Skip interactive style confirmation |
| `--verbose` | `false` | Show per-file progress |

## Configuration

Place a `.pseudocodify.toml` at your project root to set run defaults. CLI flags always take precedence.

```toml
[pseudocodify]
style = "cormen"
consolidate = false
exclude = ["tests/**", "vendor/**", "*.min.js"]
model = "claude-opus-4-6"
output = "./pseudocode"
```

## Development

```bash
git clone https://github.com/keithmackay/pseudocodify
cd pseudocodify
pip install -e .
pip install pytest pytest-mock
pytest tests/ -v
```

## Contributing

Contributions are welcome. Fork the repo, create a branch, and open a pull request. Please ensure all tests pass before submitting.

## License

[MIT](LICENSE)
