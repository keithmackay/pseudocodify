import datetime
import fnmatch
import hashlib
import json
import sys
from pathlib import Path

from pseudocodify.config import RunConfig
from pseudocodify.models import CodebaseMap, FileAnalysis
from pseudocodify.rlm_adapter import RLMAdapter

RECOGNIZED_EXTENSIONS = {
    ".py", ".js", ".ts", ".go", ".rb", ".java", ".cs",
    ".cpp", ".c", ".rs", ".php", ".swift", ".kt", ".scala",
    ".r", ".m", ".sh", ".bash", ".pl", ".lua",
}

EXTRACTION_SCHEMA = """
{
  "path": "string (relative path)",
  "language": "string",
  "purpose": "string (one sentence)",
  "constructs": [{"name": "string", "file": "string", "kind": "function|class|variable|method"}],
  "external_deps": [{"name": "string", "description": "string", "known": true|false}],
  "internal_refs": [["caller_name", "callee_file_path"]]
}
"""


def discover_files(
    source: Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[Path]:
    results = []
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in RECOGNIZED_EXTENSIONS:
            continue
        rel = path.relative_to(source)
        rel_str = str(rel)
        if exclude:
            if any(fnmatch.fnmatch(rel_str, pat) for pat in exclude):
                continue
        if include:
            if not any(fnmatch.fnmatch(rel_str, pat) for pat in include):
                continue
        results.append(path)
    return sorted(results)


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_codebase_map(cm: CodebaseMap, cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "analysis.json").write_text(cm.model_dump_json(indent=2))


def load_codebase_map(cache_dir: Path) -> CodebaseMap | None:
    path = cache_dir / "analysis.json"
    if not path.exists():
        return None
    return CodebaseMap.model_validate_json(path.read_text())


def build_extraction_prompt(source_code: str, language: str) -> str:
    return f"""Analyze the following {language} source code and return a JSON object matching this schema exactly:

{EXTRACTION_SCHEMA}

Rules:
- `constructs`: list every function, class, method, and module-level variable
- `external_deps`: list every import/require that is NOT from the same project; set `known: true` if it is a well-known library, false if unknown; provide a one-sentence description
- `internal_refs`: list pairs of [calling_construct_name, relative_path_of_called_file] for cross-file calls within the project
- `purpose`: one sentence describing what this file does overall

Return ONLY the JSON object. No explanation, no markdown, no code fences.

Source code:
{source_code}"""


def _detect_language(path: Path) -> str:
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".go": "Go", ".rb": "Ruby", ".java": "Java", ".cs": "C#",
        ".cpp": "C++", ".c": "C", ".rs": "Rust", ".php": "PHP",
        ".swift": "Swift", ".kt": "Kotlin", ".scala": "Scala",
        ".r": "R", ".m": "Objective-C", ".sh": "Shell",
        ".bash": "Bash", ".pl": "Perl", ".lua": "Lua",
    }
    return ext_map.get(path.suffix.lower(), "Unknown")


def analyze_file(
    path: Path,
    source_root: Path,
    adapter: RLMAdapter,
) -> FileAnalysis | None:
    rel_path = str(path.relative_to(source_root))
    source_code = path.read_text(errors="replace")
    language = _detect_language(path)
    source_hash = hash_file(path)
    prompt = build_extraction_prompt(source_code, language)

    for attempt in range(3):
        try:
            raw = adapter.run(prompt)
            data = json.loads(raw)
            data["path"] = rel_path
            data["source_hash"] = source_hash
            return FileAnalysis.model_validate(data)
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"WARNING: [ANALYSIS FAILED] {rel_path} — {e}", file=sys.stderr)
            return None
    return None


def _infer_paradigm(files: dict) -> str:
    class_count = sum(
        1 for fa in files.values()
        for c in fa.constructs if c.kind == "class"
    )
    func_count = sum(
        1 for fa in files.values()
        for c in fa.constructs if c.kind == "function"
    )
    variable_count = sum(
        1 for fa in files.values()
        for c in fa.constructs if c.kind == "variable"
    )
    if class_count > func_count:
        return "OOP"
    if class_count == 0 and func_count > 0:
        return "functional" if variable_count == 0 else "procedural"
    if class_count > 0 and func_count > 0:
        return "mixed"
    return "procedural"


def _recommend_style(paradigm: str) -> str:
    from pseudocodify.styles import get_style, list_styles
    for name in list_styles():
        style = get_style(name)
        if paradigm in style.PARADIGM_FIT:
            return name
    return "cormen"


def run_analysis(cfg: RunConfig, adapter: RLMAdapter) -> CodebaseMap:
    source = Path(cfg.source)
    cache_dir = source / ".pseudocodify"
    cached = load_codebase_map(cache_dir)
    files = discover_files(source, include=cfg.include or None, exclude=cfg.exclude or None)

    result_files: dict[str, FileAnalysis] = {}
    failed: list[str] = []

    for file_path in files:
        rel = str(file_path.relative_to(source))
        current_hash = hash_file(file_path)
        if cached and rel in cached.files and cached.files[rel].source_hash == current_hash:
            result_files[rel] = cached.files[rel]
            continue
        fa = analyze_file(file_path, source_root=source, adapter=adapter)
        if fa is None:
            failed.append(rel)
        else:
            result_files[rel] = fa

    if failed:
        for f in failed:
            print(f"WARNING: [ANALYSIS FAILED] {f}", file=sys.stderr)

    paradigm = _infer_paradigm(result_files)
    style = _recommend_style(paradigm)
    cm = CodebaseMap(
        source_root=str(source.resolve()),
        files=result_files,
        dominant_paradigm=paradigm,
        recommended_style=style,
        analysis_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    save_codebase_map(cm, cache_dir)
    return cm
