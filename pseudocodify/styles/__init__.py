import types
from pseudocodify.styles import cormen, structured_english, pascal

VALID_STYLES: dict[str, types.ModuleType] = {
    "cormen": cormen,
    "structured-english": structured_english,
    "pascal": pascal,
}


def get_style(name: str) -> types.ModuleType:
    if name not in VALID_STYLES:
        raise ValueError(f"Unknown style '{name}'. Valid options: {list(VALID_STYLES)}")
    return VALID_STYLES[name]


def list_styles() -> list[str]:
    return list(VALID_STYLES.keys())
