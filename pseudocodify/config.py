import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RunConfig:
    source: str = "."
    output: str = "./pseudocode"
    consolidate: bool = False
    style: str = "auto"
    model: str = "claude-opus-4-6"
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    yes: bool = False
    verbose: bool = False


def load_config(
    toml_path: Path | None = None,
    cli_overrides: dict | None = None,
) -> RunConfig:
    cfg = RunConfig()
    if toml_path and toml_path.exists():
        try:
            with open(toml_path, "rb") as f:
                data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            print(f"Error: malformed .pseudocodify.toml — {e}", file=sys.stderr)
            raise SystemExit(1)
        section = data.get("pseudocodify", {})
        for key, value in section.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
    if cli_overrides:
        for key, value in cli_overrides.items():
            if value is not None and hasattr(cfg, key):
                setattr(cfg, key, value)
    return cfg
