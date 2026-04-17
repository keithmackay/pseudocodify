# Contributing to pseudocodify

## Reporting Bugs

Open an issue using the bug report template. Include the source language, command you ran, and the error or unexpected output you received.

## Suggesting Features

Open an issue using the feature request template. Describe the problem you're trying to solve, not just the solution you have in mind.

## Development Setup

```bash
git clone https://github.com/keithmackay/pseudocodify
cd pseudocodify
pip install -e .
pip install pytest pytest-mock
pytest tests/ -v
```

Requires Python 3.11+ and an Anthropic API key (`ANTHROPIC_API_KEY`) for any tests that make real LLM calls.

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Write a failing test before implementing anything new
3. Make the smallest change that makes the test pass
4. Ensure all 49 tests pass: `pytest tests/ -v`
5. Open a PR against `main` with a clear description of what changed and why

## Code Style

- Match the formatting of the file you're editing
- All new source files must begin with two `# ABOUTME:` comment lines describing what the file does
- No speculative features — if it's not needed for the current task, don't add it
- Comments explain *what* or *why*, not *how it's better than before*
