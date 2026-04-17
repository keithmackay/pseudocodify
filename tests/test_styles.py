import pytest
from pseudocodify.styles import get_style, list_styles, VALID_STYLES


def test_list_styles_returns_all_three():
    styles = list_styles()
    assert set(styles) == {"cormen", "structured-english", "pascal"}


def test_get_style_cormen():
    style = get_style("cormen")
    assert hasattr(style, "SYSTEM_PROMPT")
    assert hasattr(style, "STYLE_NAME")
    assert hasattr(style, "PARADIGM_FIT")
    assert isinstance(style.SYSTEM_PROMPT, str)
    assert len(style.SYSTEM_PROMPT) > 50
    assert isinstance(style.PARADIGM_FIT, list)


def test_get_style_all_valid():
    for name in ["cormen", "structured-english", "pascal"]:
        style = get_style(name)
        assert style.STYLE_NAME  # non-empty


def test_get_style_invalid_raises():
    with pytest.raises(ValueError, match="Unknown style"):
        get_style("nonexistent")


def test_paradigm_fit_values_are_valid():
    valid_paradigms = {"OOP", "functional", "procedural", "mixed"}
    for name in list_styles():
        style = get_style(name)
        for p in style.PARADIGM_FIT:
            assert p in valid_paradigms, f"{name}.PARADIGM_FIT contains invalid value: {p}"
