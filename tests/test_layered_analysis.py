"""Tests for layered_analysis.py — INCREMENT 0015."""

import sys
from pathlib import Path
from unittest import TestCase

# Ensure the selfdev package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from layered_analysis import (
    Layer,
    classify_file,
    detect_cross_layer_deps,
    generate_layer_prompts,
    analyze_layers,
    _extract_imports,
    _issue_layer_tag,
)
from models import FileAnalysis, Priority, Perspective


class TestClassifyFile(TestCase):
    """AC-1: prompts can identify whether an issue is UI-only, service-only, or cross-layer."""

    def test_ui_path(self):
        layers = classify_file("components/Header.py")
        self.assertIn(Layer.UI, layers)

    def test_service_path(self):
        layers = classify_file("services/auth.py")
        self.assertIn(Layer.SERVICE, layers)

    def test_client_path(self):
        layers = classify_file("hooks/useAuth.py")
        self.assertIn(Layer.CLIENT, layers)

    def test_shared_when_no_signal(self):
        layers = classify_file("utils/helpers.py")
        self.assertEqual(layers, set())

    def test_ui_import(self):
        layers = classify_file("foo.py", imports={"react"})
        self.assertIn(Layer.UI, layers)

    def test_service_import(self):
        layers = classify_file("foo.py", imports={"fastapi"})
        self.assertIn(Layer.SERVICE, layers)

    def test_client_import(self):
        layers = classify_file("foo.py", imports={"requests"})
        self.assertIn(Layer.CLIENT, layers)

    def test_ui_content_pattern(self):
        code = "def view():\n    return render(<div>hello</div>)"
        layers = classify_file("foo.py", content=code)
        self.assertIn(Layer.UI, layers)

    def test_service_content_pattern(self):
        code = "@app.get('/users')\ndef list_users():\n    pass"
        layers = classify_file("foo.py", content=code)
        self.assertIn(Layer.SERVICE, layers)

    def test_client_content_pattern(self):
        code = "resp = fetch('/api/data')"
        layers = classify_file("foo.py", content=code)
        self.assertIn(Layer.CLIENT, layers)

    def test_cross_layer_multiple_signals(self):
        code = "@app.get('/x')\ndef handler():\n    return render(template)"
        layers = classify_file("foo.py", content=code)
        self.assertTrue(len(layers) > 1, "Expected cross-layer classification")

    def test_pages_path_is_ui(self):
        layers = classify_file("pages/index.py")
        self.assertIn(Layer.UI, layers)

    def test_controllers_path_is_service(self):
        layers = classify_file("controllers/user_controller.py")
        self.assertIn(Layer.SERVICE, layers)

    def test_store_path_is_client(self):
        layers = classify_file("stores/auth_store.py")
        self.assertIn(Layer.CLIENT, layers)


class TestExtractImports(TestCase):
    def test_simple_import(self):
        code = "import os\nimport json"
        self.assertEqual(_extract_imports(code), {"os", "json"})

    def test_from_import(self):
        code = "from pathlib import Path"
        self.assertIn("pathlib", _extract_imports(code))

    def test_syntax_error_returns_empty(self):
        self.assertEqual(_extract_imports("def (broken"), set())


class TestIssueLayerTag(TestCase):
    """AC-1: tags identify layer type."""

    def test_single_ui(self):
        self.assertEqual(_issue_layer_tag({Layer.UI}), "ui-only")

    def test_single_service(self):
        self.assertEqual(_issue_layer_tag({Layer.SERVICE}), "service-only")

    def test_cross_layer(self):
        tag = _issue_layer_tag({Layer.UI, Layer.SERVICE})
        self.assertIn("cross-layer", tag)

    def test_empty(self):
        self.assertEqual(_issue_layer_tag(set()), "unknown-layer")


class TestDetectCrossLayerDeps(TestCase):
    """AC-4: cross-layer issues detect caller/callee."""

    def test_no_deps_same_layer(self):
        file_layers = {"a.py": {Layer.UI}, "b.py": {Layer.UI}}
        import_graph = {"a.py": {"b.py"}}
        deps = detect_cross_layer_deps(file_layers, import_graph)
        self.assertEqual(deps, [])

    def test_cross_layer_dep_detected(self):
        file_layers = {"a.py": {Layer.UI}, "b.py": {Layer.SERVICE}}
        import_graph = {"a.py": {"b.py"}}
        deps = detect_cross_layer_deps(file_layers, import_graph)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0], ("a.py", "b.py", Layer.UI, Layer.SERVICE))

    def test_shared_layer_ignored(self):
        file_layers = {"a.py": {Layer.SHARED}, "b.py": {Layer.SERVICE}}
        import_graph = {"a.py": {"b.py"}}
        deps = detect_cross_layer_deps(file_layers, import_graph)
        self.assertEqual(deps, [])


class TestGenerateLayerPrompts(TestCase):
    """AC-2, AC-3, AC-4: prompt content matches layer type."""

    def _make_analysis(self, path, issues=None):
        return FileAnalysis(
            path=path, lines=100, functions=5, classes=1,
            imports=3, complexity=5.0, has_tests=False,
            issues=issues or [],
        )

    def test_ui_prompt_mentions_component_and_state(self):
        """AC-2: UI prompts mention view/component and state transition."""
        analyses = {"components/Card.py": self._make_analysis(
            "components/Card.py", ["High complexity: 15.0"]
        )}
        file_layers = {"components/Card.py": {Layer.UI}}
        prompts = generate_layer_prompts(file_layers, analyses, [])
        self.assertTrue(len(prompts) >= 1)
        p = prompts[0]
        self.assertIn("Card", p.title)
        self.assertIn("ui-only", p.title)
        self.assertIn("state transition", p.description.lower())

    def test_service_prompt_mentions_contract(self):
        """AC-3: service prompts mention route/contract."""
        analyses = {"services/auth.py": self._make_analysis(
            "services/auth.py", ["File too long"]
        )}
        file_layers = {"services/auth.py": {Layer.SERVICE}}
        prompts = generate_layer_prompts(file_layers, analyses, [])
        self.assertTrue(len(prompts) >= 1)
        p = prompts[0]
        self.assertIn("service-only", p.title)
        self.assertIn("contract", p.description.lower())

    def test_client_prompt_mentions_route(self):
        """AC-3: client prompts mention route/error path."""
        analyses = {"hooks/useFetch.py": self._make_analysis(
            "hooks/useFetch.py", ["High complexity: 12.0"]
        )}
        file_layers = {"hooks/useFetch.py": {Layer.CLIENT}}
        prompts = generate_layer_prompts(file_layers, analyses, [])
        self.assertTrue(len(prompts) >= 1)
        p = prompts[0]
        self.assertIn("client-only", p.title)
        self.assertIn("route", p.description.lower())

    def test_cross_layer_requires_both_verified(self):
        """AC-4: cross-layer prompts require caller and callee verification."""
        analyses = {"mixed.py": self._make_analysis(
            "mixed.py", ["High complexity: 20.0"]
        )}
        file_layers = {"mixed.py": {Layer.UI, Layer.SERVICE}}
        prompts = generate_layer_prompts(file_layers, analyses, [])
        self.assertTrue(len(prompts) >= 1)
        p = prompts[0]
        self.assertIn("cross-layer", p.title)
        self.assertIn("caller", p.description.lower())
        self.assertIn("callee", p.description.lower())
        self.assertTrue(
            any("caller" in ac.lower() for ac in p.acceptance_criteria),
            "Acceptance criteria should mention caller",
        )
        self.assertTrue(
            any("callee" in ac.lower() for ac in p.acceptance_criteria),
            "Acceptance criteria should mention callee",
        )

    def test_cross_layer_dep_prompt(self):
        """AC-3 + AC-4: cross-layer dependency prompt names contract."""
        analyses = {"a.py": self._make_analysis("a.py")}
        file_layers = {"a.py": {Layer.UI}, "b.py": {Layer.SERVICE}}
        cross_deps = [("a.py", "b.py", Layer.UI, Layer.SERVICE)]
        prompts = generate_layer_prompts(file_layers, analyses, cross_deps)
        self.assertTrue(len(prompts) >= 1)
        p = prompts[0]
        self.assertIn("cross-layer", p.title)
        self.assertIn("contract", p.description.lower())

    def test_no_issues_no_prompts(self):
        analyses = {"foo.py": self._make_analysis("foo.py")}
        file_layers = {"foo.py": {Layer.UI}}
        prompts = generate_layer_prompts(file_layers, analyses, [])
        self.assertEqual(prompts, [])

    def test_cross_layer_prompt_is_high_priority(self):
        """AC-4: cross-layer issues get higher priority."""
        analyses = {"mixed.py": self._make_analysis(
            "mixed.py", ["High complexity"]
        )}
        file_layers = {"mixed.py": {Layer.UI, Layer.SERVICE}}
        prompts = generate_layer_prompts(file_layers, analyses, [])
        self.assertEqual(prompts[0].priority, Priority.HIGH)

    def test_single_layer_prompt_is_medium_priority(self):
        analyses = {"components/X.py": self._make_analysis(
            "components/X.py", ["Issue"]
        )}
        file_layers = {"components/X.py": {Layer.UI}}
        prompts = generate_layer_prompts(file_layers, analyses, [])
        self.assertEqual(prompts[0].priority, Priority.MEDIUM)


class TestAnalyzeLayers(TestCase):
    """Integration test for the high-level entry point."""

    def test_returns_layers_and_prompts(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            comp_dir = root / "components"
            comp_dir.mkdir()
            py = comp_dir / "Widget.py"
            py.write_text("class Widget:\n    pass\n")

            analyses = {
                "components/Widget.py": FileAnalysis(
                    path="components/Widget.py", lines=2, functions=0,
                    classes=1, imports=0, complexity=1.0, has_tests=False,
                )
            }

            file_layers, prompts = analyze_layers(root, analyses)
            self.assertIn("components/Widget.py", file_layers)
            self.assertIn(Layer.UI, file_layers["components/Widget.py"])
            # No issues → no prompts
            self.assertEqual(prompts, [])

    def test_with_issues_generates_prompts(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            svc_dir = root / "services"
            svc_dir.mkdir()
            py = svc_dir / "api.py"
            py.write_text("from fastapi import FastAPI\n")

            analyses = {
                "services/api.py": FileAnalysis(
                    path="services/api.py", lines=500, functions=10,
                    classes=0, imports=1, complexity=15.0, has_tests=False,
                    issues=["File too long: 500 lines (max 300)"],
                )
            }

            _layers, prompts = analyze_layers(root, analyses)
            self.assertTrue(len(prompts) >= 1)
            self.assertIn("service-only", prompts[0].title)


class TestSystemPerspectiveIntegration(TestCase):
    """Verify that SystemPerspective now includes layer-aware prompts."""

    def test_system_perspective_calls_layer_analysis(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            svc_dir = root / "services"
            svc_dir.mkdir()
            py = svc_dir / "handler.py"
            # A long file that triggers the system perspective AND has service signals
            lines = ["from fastapi import FastAPI\n"]
            lines += [f"def func_{i}(): pass\n" for i in range(400)]
            py.write_text("".join(lines))

            from models import OrganismState
            from perspectives import SystemPerspective

            state = OrganismState()
            sp = SystemPerspective(root, state)
            metrics, prompts = sp.analyze()

            # Should contain at least one layer-tagged prompt
            layer_prompts = [p for p in prompts if "layer-analysis" in p.tags]
            # The file is >300 lines so system perspective flags it,
            # and it's in services/ so layered analysis tags it service-only
            self.assertTrue(
                len(layer_prompts) >= 1,
                f"Expected layer-analysis prompts, got tags: {[p.tags for p in prompts]}",
            )
