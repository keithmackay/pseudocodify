import tomllib
import pytest
from pathlib import Path
from pseudocodify.config import RunConfig, load_config


def test_defaults():
    cfg = RunConfig()
    assert cfg.style == "auto"
    assert cfg.consolidate is False
    assert cfg.output == "./pseudocode"
    assert cfg.model == "claude-opus-4-6"
    assert cfg.yes is False
    assert cfg.verbose is False


def test_toml_overrides_defaults(tmp_path):
    toml_file = tmp_path / ".pseudocodify.toml"
    toml_file.write_text('[pseudocodify]\nstyle = "pascal"\nconsolidate = true\n')
    cfg = load_config(toml_path=toml_file)
    assert cfg.style == "pascal"
    assert cfg.consolidate is True
    assert cfg.output == "./pseudocode"  # default unchanged


def test_cli_overrides_toml(tmp_path):
    toml_file = tmp_path / ".pseudocodify.toml"
    toml_file.write_text('[pseudocodify]\nstyle = "pascal"\n')
    cfg = load_config(toml_path=toml_file, cli_overrides={"style": "cormen"})
    assert cfg.style == "cormen"


def test_malformed_toml_raises(tmp_path):
    toml_file = tmp_path / ".pseudocodify.toml"
    toml_file.write_text("not valid toml ][")
    with pytest.raises(SystemExit):
        load_config(toml_path=toml_file)


def test_missing_toml_uses_defaults():
    cfg = load_config(toml_path=Path("/nonexistent/.pseudocodify.toml"))
    assert cfg.style == "auto"
