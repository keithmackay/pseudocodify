# pseudocodify

## Description

A tool that generates a perfect-fidelity pseudocode version of a codebase that can be used to regenerate functionality in a new language. Point pseudocodify at a codebase and it will create a human-readable pseudocode version of the code. Regardless of source language, all coding structures will be analyzed, mapped to base coding concepts, and the logic will be written in standard pseudocode syntax.

The goal is for pseudocodify to serve as the hub for a universal language translator — converting any codebase into language-agnostic pseudocode that faithfully captures all logic, structure, and intent. For large codebases that exceed context limits, pseudocodify uses the Recursive Language Model (RLM) strategy to process files recursively and at scale.

## Installation

```bash
pip install pseudocodify
```

Or from source:

```bash
git clone https://github.com/keithmackay/pseudocodify
cd pseudocodify
pip install -e .
```

Requires Python 3.11+. Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Usage

```bash
# Translate a codebase to pseudocode (per-file output)
pseudocodify ./my-project --output ./my-project-pseudo

# Single consolidated output file
pseudocodify ./my-project --output all.pseudo.md --consolidate

# Specific pseudocode style
pseudocodify ./my-project --style cormen

# Skip interactive style confirmation
pseudocodify ./my-project --yes
```

## License

_Placeholder_
