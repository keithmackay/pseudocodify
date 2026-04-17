from typing import Literal
from pydantic import BaseModel


class ExternalDep(BaseModel):
    name: str
    description: str
    known: bool


class ConstructRef(BaseModel):
    name: str
    file: str
    kind: Literal["function", "class", "variable", "method"]


class FileAnalysis(BaseModel):
    path: str
    language: str
    purpose: str
    constructs: list[ConstructRef]
    external_deps: list[ExternalDep]
    internal_refs: list[tuple[str, str]]
    source_hash: str


class CodebaseMap(BaseModel):
    source_root: str
    files: dict[str, FileAnalysis]
    dominant_paradigm: Literal["OOP", "functional", "procedural", "mixed"]
    recommended_style: Literal["cormen", "structured-english", "pascal"]
    analysis_timestamp: str
