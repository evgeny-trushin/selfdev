"""
Layered UI and Client-Service analysis for the Self-Development Organism.

Classifies source files into layers (UI, client, service) based on file
paths, imports, and content patterns.  Detects cross-layer dependencies
and generates prompts that name the exact layer, component, route, or
contract involved.

INCREMENT 0015
"""

import ast
import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from models import FileAnalysis, Priority, Perspective, Prompt


# ── Layer enum ────────────────────────────────────────────────────────

class Layer(Enum):
    UI = "ui"
    CLIENT = "client"
    SERVICE = "service"
    SHARED = "shared"


# ── Classification patterns ──────────────────────────────────────────

# Path fragments that indicate a layer
_PATH_PATTERNS: Dict[Layer, List[str]] = {
    Layer.UI: [
        "components", "pages", "views", "templates", "layouts",
        "widgets", "screens", "ui", "frontend",
    ],
    Layer.CLIENT: [
        "hooks", "store", "stores", "state", "api", "client",
        "fetch", "queries", "mutations", "context",
    ],
    Layer.SERVICE: [
        "services", "routes", "controllers", "handlers", "endpoints",
        "server", "backend", "api", "middleware", "resolvers",
    ],
}

# Import names that strongly suggest a layer
_IMPORT_PATTERNS: Dict[Layer, List[str]] = {
    Layer.UI: [
        "react", "vue", "angular", "svelte", "jinja", "django.template",
        "flask.render", "tkinter", "streamlit", "gradio",
    ],
    Layer.CLIENT: [
        "requests", "httpx", "aiohttp", "fetch", "axios", "urllib",
        "websocket", "grpc", "swr", "react-query", "tanstack",
    ],
    Layer.SERVICE: [
        "fastapi", "flask", "django.views", "django.rest_framework",
        "express", "koa", "hono", "sqlalchemy", "peewee", "prisma",
        "celery", "dramatiq", "rq",
    ],
}

# Content patterns (regex) that indicate a layer
_CONTENT_PATTERNS: Dict[Layer, List[re.Pattern]] = {
    Layer.UI: [
        re.compile(r'render\s*\('),
        re.compile(r'<template>|<div |<span |<button ', re.IGNORECASE),
        re.compile(r'className=|class=|style=', re.IGNORECASE),
        re.compile(r'useState|useEffect|useRef|useContext'),
        re.compile(r'@component|@Component'),
    ],
    Layer.CLIENT: [
        re.compile(r'\bfetch\s*\('),
        re.compile(r'\.get\s*\(|\.post\s*\(|\.put\s*\(|\.delete\s*\(|\.patch\s*\('),
        re.compile(r'async\s+def\s+\w+.*->.*Response'),
        re.compile(r'localStorage|sessionStorage|indexedDB'),
        re.compile(r'retry|backoff|timeout', re.IGNORECASE),
    ],
    Layer.SERVICE: [
        re.compile(r'@app\.(get|post|put|delete|patch|route)\s*\('),
        re.compile(r'@router\.(get|post|put|delete|patch)\s*\('),
        re.compile(r'def\s+(get|post|put|delete|patch)\s*\(.*request'),
        re.compile(r'(session|cursor|query|execute)\s*\('),
        re.compile(r'@celery|@dramatiq|\.delay\s*\('),
    ],
}


# ── File classifier ──────────────────────────────────────────────────

def classify_file(path: str, content: str = "",
                  imports: Optional[Set[str]] = None) -> Set[Layer]:
    """Return the set of layers a file belongs to.

    Uses three signals: path fragments, import names, and content
    patterns.  A file may belong to multiple layers (cross-layer).
    """
    layers: Set[Layer] = set()
    path_lower = path.lower().replace("\\", "/")
    imports = imports or set()
    imports_lower = {i.lower() for i in imports}

    for layer, fragments in _PATH_PATTERNS.items():
        for frag in fragments:
            if f"/{frag}/" in f"/{path_lower}/" or path_lower.startswith(f"{frag}/"):
                layers.add(layer)

    for layer, patterns in _IMPORT_PATTERNS.items():
        for pat in patterns:
            if any(pat.lower() in imp for imp in imports_lower):
                layers.add(layer)

    for layer, patterns in _CONTENT_PATTERNS.items():
        for pat in patterns:
            if pat.search(content):
                layers.add(layer)
                break

    return layers


def _extract_imports(content: str) -> Set[str]:
    """Extract top-level import names from Python source."""
    names: Set[str] = set()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
    return names


# ── Cross-layer dependency detection ─────────────────────────────────

def detect_cross_layer_deps(
    file_layers: Dict[str, Set[Layer]],
    import_graph: Dict[str, Set[str]],
) -> List[Tuple[str, str, Layer, Layer]]:
    """Find pairs of files where one layer imports from another.

    Returns a list of (importer, imported, importer_layer, imported_layer)
    tuples where the two layers differ.
    """
    deps: List[Tuple[str, str, Layer, Layer]] = []
    for src, targets in import_graph.items():
        src_layers = file_layers.get(src, set())
        for tgt in targets:
            tgt_layers = file_layers.get(tgt, set())
            for sl in src_layers:
                for tl in tgt_layers:
                    if sl != tl and sl != Layer.SHARED and tl != Layer.SHARED:
                        deps.append((src, tgt, sl, tl))
    return deps


# ── Prompt generation ────────────────────────────────────────────────

def _issue_layer_tag(layers: Set[Layer]) -> str:
    """Return a human-readable tag like 'UI-only' or 'cross-layer (UI↔service)'."""
    if not layers:
        return "unknown-layer"
    if len(layers) == 1:
        return f"{next(iter(layers)).value}-only"
    names = sorted(l.value for l in layers)
    return "cross-layer (" + "\u2194".join(names) + ")"


def generate_layer_prompts(
    file_layers: Dict[str, Set[Layer]],
    analyses: Dict[str, FileAnalysis],
    cross_deps: List[Tuple[str, str, Layer, Layer]],
) -> List[Prompt]:
    """Generate prompts that classify issues by layer.

    Acceptance criteria mapping:
      AC-1: every prompt's title includes the layer tag
      AC-2: UI prompts name the view/component and state transition
      AC-3: client-service prompts name route/contract/error path
      AC-4: cross-layer prompts require both caller and callee verification
    """
    prompts: List[Prompt] = []

    # Per-file layer-aware prompts for files with issues
    for path, analysis in analyses.items():
        if not analysis.issues:
            continue
        layers = file_layers.get(path, set())
        tag = _issue_layer_tag(layers)

        for issue_text in analysis.issues:
            if Layer.UI in layers and len(layers) == 1:
                # AC-2: UI prompts mention view/component and state transition
                component = Path(path).stem
                prompts.append(Prompt(
                    perspective=Perspective.SYSTEM,
                    priority=Priority.MEDIUM,
                    title=f"[{tag}] {issue_text} in {component}",
                    description=(
                        f"UI component '{component}' has an issue: {issue_text}. "
                        f"Verify empty, loading, error, and success state transitions."
                    ),
                    file_path=path,
                    evaluative_evidence=f"CodeAnalyzer flagged '{issue_text}' in UI file {path}",
                    directive_evidence=(
                        f"Fix the issue in component '{component}' and verify "
                        f"all UI state transitions (empty/loading/error/success)"
                    ),
                    expected_next_state=(
                        f"'{component}' passes analysis with 0 issues and all "
                        f"state transitions render correctly"
                    ),
                    acceptance_criteria=[
                        f"Resolve '{issue_text}' in {path}",
                        f"Verify state transitions for component '{component}'",
                    ],
                    tags=["ui", "layer-analysis"],
                    reason=f"{tag}: {issue_text}",
                ))
            elif Layer.SERVICE in layers and len(layers) == 1:
                # AC-3: service-only prompts mention route/contract
                prompts.append(Prompt(
                    perspective=Perspective.SYSTEM,
                    priority=Priority.MEDIUM,
                    title=f"[{tag}] {issue_text} in {Path(path).name}",
                    description=(
                        f"Service file '{path}' has an issue: {issue_text}. "
                        f"Inspect API contract, validation rules, and error responses."
                    ),
                    file_path=path,
                    evaluative_evidence=f"CodeAnalyzer flagged '{issue_text}' in service file {path}",
                    directive_evidence=(
                        f"Fix the issue in '{path}' and verify API contract, "
                        f"status codes, and error handling"
                    ),
                    expected_next_state=f"Service file {path} has 0 analysis issues",
                    acceptance_criteria=[
                        f"Resolve '{issue_text}' in {path}",
                        "Verify API contract and error responses",
                    ],
                    tags=["service", "layer-analysis"],
                    reason=f"{tag}: {issue_text}",
                ))
            elif Layer.CLIENT in layers and len(layers) == 1:
                # AC-3: client-only prompts mention route/error path
                prompts.append(Prompt(
                    perspective=Perspective.SYSTEM,
                    priority=Priority.MEDIUM,
                    title=f"[{tag}] {issue_text} in {Path(path).name}",
                    description=(
                        f"Client file '{path}' has an issue: {issue_text}. "
                        f"Inspect the fetch route, error path, and retry logic."
                    ),
                    file_path=path,
                    evaluative_evidence=f"CodeAnalyzer flagged '{issue_text}' in client file {path}",
                    directive_evidence=(
                        f"Fix the issue in '{path}' and verify request/response "
                        f"handling, error rendering, and retry behavior"
                    ),
                    expected_next_state=f"Client file {path} has 0 analysis issues",
                    acceptance_criteria=[
                        f"Resolve '{issue_text}' in {path}",
                        "Verify error path and retry logic",
                    ],
                    tags=["client", "layer-analysis"],
                    reason=f"{tag}: {issue_text}",
                ))
            elif len(layers) > 1:
                # AC-4: cross-layer requires both caller and callee verified
                prompts.append(Prompt(
                    perspective=Perspective.SYSTEM,
                    priority=Priority.HIGH,
                    title=f"[{tag}] {issue_text} in {Path(path).name}",
                    description=(
                        f"Cross-layer file '{path}' has an issue: {issue_text}. "
                        f"Both caller and callee behavior must be verified."
                    ),
                    file_path=path,
                    evaluative_evidence=f"CodeAnalyzer flagged '{issue_text}' in cross-layer file {path}",
                    directive_evidence=(
                        f"Fix the issue in '{path}' and verify both the calling "
                        f"layer and the receiving layer behave correctly"
                    ),
                    expected_next_state=(
                        f"File {path} has 0 issues and both caller and callee "
                        f"behavior is verified"
                    ),
                    acceptance_criteria=[
                        f"Resolve '{issue_text}' in {path}",
                        "Verify caller behavior",
                        "Verify callee behavior",
                    ],
                    tags=["cross-layer", "layer-analysis"],
                    reason=f"{tag}: {issue_text}",
                ))

    # Cross-layer dependency prompts  (AC-3 + AC-4)
    for importer, imported, src_layer, tgt_layer in cross_deps:
        tag = f"cross-layer ({src_layer.value}\u2194{tgt_layer.value})"
        prompts.append(Prompt(
            perspective=Perspective.SYSTEM,
            priority=Priority.MEDIUM,
            title=f"[{tag}] {Path(importer).name} depends on {Path(imported).name}",
            description=(
                f"'{importer}' ({src_layer.value} layer) imports from "
                f"'{imported}' ({tgt_layer.value} layer). Verify the contract "
                f"between them: request/response shape, error handling, and "
                f"status codes."
            ),
            file_path=importer,
            evaluative_evidence=(
                f"{importer} ({src_layer.value}) imports {imported} ({tgt_layer.value})"
            ),
            directive_evidence=(
                f"Review the interface between {importer} and {imported}; "
                f"ensure both sides agree on contract, error paths, and data shapes"
            ),
            expected_next_state=(
                f"Both {importer} and {imported} handle shared contract correctly"
            ),
            acceptance_criteria=[
                f"Verify caller ({importer}) handles all response/error cases",
                f"Verify callee ({imported}) returns documented contract",
                "Confirm both sides agree on data shapes and status codes",
            ],
            tags=["cross-layer", "contract", "layer-analysis"],
            reason=f"Cross-layer dependency: {src_layer.value} -> {tgt_layer.value}",
        ))

    return prompts


# ── High-level entry point ───────────────────────────────────────────

def analyze_layers(
    root_dir: Path,
    analyses: Dict[str, FileAnalysis],
) -> Tuple[Dict[str, Set[Layer]], List[Prompt]]:
    """Classify all analysed files by layer and generate layer-aware prompts.

    Returns (file_layers, prompts).
    """
    file_layers: Dict[str, Set[Layer]] = {}
    import_graph: Dict[str, Set[str]] = {}

    for rel_path in analyses:
        full_path = root_dir / rel_path
        if not full_path.exists():
            continue
        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        imports = _extract_imports(content)
        layers = classify_file(rel_path, content, imports)
        if not layers:
            layers = {Layer.SHARED}
        file_layers[rel_path] = layers

        # Build a simple import graph (module name -> relative path match)
        import_graph[rel_path] = set()
        for imp_name in imports:
            stem = imp_name.split(".")[-1]
            for other_path in analyses:
                if Path(other_path).stem == stem and other_path != rel_path:
                    import_graph[rel_path].add(other_path)

    cross_deps = detect_cross_layer_deps(file_layers, import_graph)
    prompts = generate_layer_prompts(file_layers, analyses, cross_deps)

    return file_layers, prompts
