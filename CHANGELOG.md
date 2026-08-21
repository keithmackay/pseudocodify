# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

- Add --version flag support, reporting installed version and a best-effort GitHub update check
- Add Changelog section to README linking CHANGELOG.md

## [0.1.0] - 2026-04-17

### Added

- Two-phase LLM pipeline: Phase 1 builds a `CodebaseMap` via structure extraction; Phase 2 generates `.pseudo` files from that map
- Three pseudocode styles: CLRS/Cormen, Structured English, Pascal-like
- Style auto-recommendation based on detected codebase paradigm (OOP, functional, procedural, mixed)
- Interactive style selection menu with `--yes` flag for non-TTY environments
- Incremental processing: unchanged files are skipped on re-runs using SHA-256 source hashing
- Consolidation mode (`--consolidate`) to merge all output into a single document
- `README.pseudo.md` index generated at the output root on every run
- `[TRANSLATION INCOMPLETE]` marker appended to files where LLM translation fails after 3 retries
- `[ANALYSIS FAILED]` marker for files where structure extraction fails after 3 retries
- RLM adapter wrapping the `rlms` package for large-codebase support
- `.pseudocodify.toml` config file support with CLI flag override
- `--include` / `--exclude` glob pattern filtering
- `--model` flag to select the Claude model
- `--verbose` flag for per-file progress output
