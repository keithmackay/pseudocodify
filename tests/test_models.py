import pytest
from pseudocodify.models import ExternalDep, ConstructRef, FileAnalysis, CodebaseMap


def test_external_dep_fields():
    dep = ExternalDep(name="bcrypt", description="hashes passwords", known=True)
    assert dep.name == "bcrypt"
    assert dep.known is True


def test_construct_ref_kind_validation():
    ref = ConstructRef(name="User", file="models.py", kind="class")
    assert ref.kind == "class"


def test_file_analysis_serialization():
    fa = FileAnalysis(
        path="src/models.py",
        language="Python",
        purpose="User model",
        constructs=[],
        external_deps=[],
        internal_refs=[],
        source_hash="abc123",
    )
    data = fa.model_dump()
    assert data["path"] == "src/models.py"
    assert data["source_hash"] == "abc123"


def test_codebase_map_dominant_paradigm_values():
    valid = ["OOP", "functional", "procedural", "mixed"]
    for paradigm in valid:
        cm = CodebaseMap(
            source_root="/tmp/src",
            files={},
            dominant_paradigm=paradigm,
            recommended_style="cormen",
            analysis_timestamp="2026-04-17T00:00:00+00:00",
        )
        assert cm.dominant_paradigm == paradigm


def test_codebase_map_recommended_style_values():
    valid = ["cormen", "structured-english", "pascal"]
    for style in valid:
        cm = CodebaseMap(
            source_root="/tmp/src",
            files={},
            dominant_paradigm="OOP",
            recommended_style=style,
            analysis_timestamp="2026-04-17T00:00:00+00:00",
        )
        assert cm.recommended_style == style
