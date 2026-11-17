# Contributing to pseudocodify

## Reporting Bugs

Open an issue using the bug report template. Include the source language, command you ran, and the error or unexpected output you received.

## Suggesting Features

Open an issue using the feature request template. Describe the problem you're trying to solve, not just the solution you have in mind.

## Development Setup

Requires Python 3.11+ and an Anthropic API key (`ANTHROPIC_API_KEY`) for any tests that make real LLM calls.

```bash
git clone https://github.com/keithmackay/pseudocodify
cd pseudocodify
pip install -e .
pip install pytest pytest-mock
pytest tests/ -v
```

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Write a failing test before implementing anything new
3. Make the smallest change that makes the test pass
4. Ensure the full test suite passes with no failures: `pytest tests/ -v`
5. Open a PR against `main` with a clear description of what changed and why, filling in every section of the PR template (`.github/pull_request_template.md`)

## Code Style

- Match the formatting of the file you're editing
- All new source files must begin with two `# ABOUTME:` comment lines describing what the file does, so every file's purpose can be found with `grep ABOUTME`
- Add only what the current task needs — no speculative features
- Comments explain *what* or *why*, not *how it's better than before*
