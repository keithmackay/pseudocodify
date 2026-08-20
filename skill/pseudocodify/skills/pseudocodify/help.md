pseudocodify — convert a codebase into language-agnostic pseudocode

WHAT IT DOES
  Wraps the pseudocodify CLI to convert any codebase into human
  -readable, language-agnostic pseudocode. Analyzes the codebase in two
  phases — building a structured map, then generating per-file
  pseudocode using that map for cross-file coherence — and writes
  .pseudo output faithfully capturing logic, structure, and intent
  regardless of source language. Useful as a first step before porting
  logic to a new language, or for documenting unfamiliar code without
  reading every file.

WHAT IT NEEDS
  - The `pseudocodify` CLI installed and on PATH (`pip install
    pseudocodify`, or `pip install -e .` from inside the pseudocodify
    repo itself)
  - `ANTHROPIC_API_KEY` set in the environment

USAGE
  /pseudocodify                    Convert the current directory
  /pseudocodify <source>           Convert a specific directory/file
  /pseudocodify --help             Show this message and exit

  The skill runs the underlying CLI:
    pseudocodify <source> --output <output> [flags]

FLAGS (skill-level)
  --help          Show this help message without making any changes

FLAGS (underlying pseudocodify CLI, passed through)
  --output        Where results go (default ./pseudocode/)
  --consolidate   Combine output into a single file instead of per-file
  --style         auto | cormen | structured-english | pascal
  --yes           Skip the interactive style confirmation prompt
  --include/--exclude   Glob patterns to scope the run

  Run `pseudocodify --help` directly for the CLI's own full flag list.
