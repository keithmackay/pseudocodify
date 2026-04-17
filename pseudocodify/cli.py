# ABOUTME: CLI for converting code to pseudocode with interactive style selection.
# ABOUTME: Handles argument parsing, config loading, analysis, and generation phases.

import os
import sys
from pathlib import Path
import typer
from pseudocodify.config import load_config
from pseudocodify.styles import list_styles

app = typer.Typer(help="Convert any codebase to pseudocode.")

VALID_STYLES = ["auto"] + list_styles()

@app.command()
def main(
    source: str = typer.Argument(".", help="Source directory or file"),
    output: str = typer.Option("./pseudocode", "--output", "-o"),
    consolidate: bool = typer.Option(False, "--consolidate"),
    style: str = typer.Option("auto", "--style"),
    model: str = typer.Option("claude-opus-4-6", "--model"),
    include: list[str] = typer.Option([], "--include"),
    exclude: list[str] = typer.Option([], "--exclude"),
    yes: bool = typer.Option(False, "--yes"),
    verbose: bool = typer.Option(False, "--verbose"),
) -> None:
    # Validate style
    if style not in VALID_STYLES:
        typer.echo(f"Error: invalid style '{style}'. Valid options: {VALID_STYLES}", err=True)
        raise typer.Exit(1)

    # Validate API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        typer.echo("Error: ANTHROPIC_API_KEY environment variable is not set.", err=True)
        raise typer.Exit(1)

    # Load config, merge CLI overrides
    toml_path = Path(source) / ".pseudocodify.toml"
    cli_overrides = {
        "source": source, "output": output, "consolidate": consolidate,
        "style": style, "model": model, "include": include or [],
        "exclude": exclude or [], "yes": yes, "verbose": verbose,
    }
    cfg = load_config(toml_path=toml_path, cli_overrides=cli_overrides)

    from pseudocodify.rlm_adapter import RLMAdapter
    from pseudocodify.analyzer import run_analysis
    from pseudocodify.generator import run_generation

    adapter = RLMAdapter(model=cfg.model, verbose=cfg.verbose)

    if cfg.verbose:
        typer.echo("Phase 1: Analyzing codebase...")
    cm = run_analysis(cfg, adapter=adapter)

    # Interactive style selection if auto
    selected_style = cfg.style
    if cfg.style == "auto":
        selected_style = _prompt_style(cm.recommended_style, cm.dominant_paradigm, cfg.yes)
        cfg.style = selected_style

    if cfg.verbose:
        typer.echo("Phase 2: Generating pseudocode...")

    # Generate architecture summary
    summary_prompt = (
        f"In 100-200 words, describe the overall architecture of this codebase:\n"
        f"{cm.model_dump_json(indent=2)}"
    )
    architecture_summary = adapter.run(summary_prompt)

    run_generation(cm=cm, cfg=cfg, adapter=adapter, architecture_summary=architecture_summary)
    typer.echo("Done.")

def _prompt_style(recommended: str, paradigm: str, yes: bool) -> str:
    from pseudocodify.styles import get_style
    style_options = [
        ("cormen", "CLRS/Cormen", "textbook algorithmic style"),
        ("structured-english", "Structured English", "plain prose-code hybrid"),
        ("pascal", "Pascal-like", "BEGIN/END block style"),
    ]
    if yes or not sys.stdin.isatty():
        typer.echo(f"Using recommended style: {get_style(recommended).STYLE_NAME}")
        return recommended

    typer.echo(f"\nDetected codebase paradigm: {paradigm}")
    typer.echo(f"Recommended pseudocode style: {get_style(recommended).STYLE_NAME}\n")
    typer.echo("Available styles:")
    for i, (key, name, desc) in enumerate(style_options, 1):
        marker = "(recommended)" if key == recommended else ""
        typer.echo(f"  [{i}] {name:<30} {marker} — {desc}")
    typer.echo("")

    keys = [s[0] for s in style_options]
    default_idx = (keys.index(recommended) + 1) if recommended in keys else 1

    while True:
        raw = typer.prompt(f"Select style [{default_idx}]", default=str(default_idx))
        if raw.strip() == "" or raw.strip() == str(default_idx):
            return recommended
        try:
            choice = int(raw.strip())
            if 1 <= choice <= len(style_options):
                return style_options[choice - 1][0]
        except ValueError:
            pass
        typer.echo("Invalid selection. Please enter 1, 2, or 3.")
