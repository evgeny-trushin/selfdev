"""
Tests for INCREMENT 0010: Performance.

Acceptance criteria:
  1. Full analysis completes within 30 seconds
  2. Memory usage stays within reasonable bounds
  3. No external API calls are required for core analysis
"""

import sys
import os
import time
import tempfile
import unittest
from pathlib import Path

# Ensure parent directory is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from performance import (
    timed_operation,
    check_analysis_time,
    get_memory_usage_mb,
    check_memory_usage,
    verify_no_external_apis,
    ANALYSIS_TIMEOUT_SECONDS,
    MEMORY_LIMIT_MB,
)
from models import OrganismState


class TestTimedOperation(unittest.TestCase):
    """Tests for the timed_operation context manager."""

    def test_measures_elapsed_time(self):
        with timed_operation("test") as t:
            time.sleep(0.05)
        self.assertGreaterEqual(t["elapsed"], 0.04)
        self.assertLess(t["elapsed"], 1.0)

    def test_label_does_not_affect_timing(self):
        with timed_operation("alpha") as t:
            pass
        self.assertGreaterEqual(t["elapsed"], 0.0)


class TestCheckAnalysisTime(unittest.TestCase):
    """Tests for analysis time budget enforcement."""

    def test_within_budget(self):
        self.assertTrue(check_analysis_time(1.0))
        self.assertTrue(check_analysis_time(29.9))
        self.assertTrue(check_analysis_time(30.0))

    def test_exceeds_budget(self):
        self.assertFalse(check_analysis_time(30.1))
        self.assertFalse(check_analysis_time(60.0))

    def test_timeout_constant(self):
        self.assertEqual(ANALYSIS_TIMEOUT_SECONDS, 30)


class TestMemory(unittest.TestCase):
    """Tests for memory monitoring."""

    def test_get_memory_returns_non_negative(self):
        usage = get_memory_usage_mb()
        self.assertGreaterEqual(usage, 0.0)

    def test_check_memory_usage_passes(self):
        self.assertTrue(check_memory_usage())

    def test_memory_limit_constant(self):
        self.assertEqual(MEMORY_LIMIT_MB, 256)


class TestNoExternalApis(unittest.TestCase):
    """Tests that core modules have no external API dependencies."""

    def test_no_network_imports_in_core(self):
        # Import all core modules so they appear in sys.modules
        import organism  # noqa: F401
        import models  # noqa: F401
        import analyzers  # noqa: F401
        import perspectives  # noqa: F401
        import diagnostics  # noqa: F401
        import formatters  # noqa: F401
        import user_perspective  # noqa: F401
        import increment_tracker  # noqa: F401
        import performance  # noqa: F401

        results = verify_no_external_apis()
        for mod_name, is_clean in results.items():
            with self.subTest(module=mod_name):
                self.assertTrue(
                    is_clean,
                    f"Module '{mod_name}' has external API dependencies",
                )

    def test_no_requests_in_sys_modules(self):
        """Verify that requests/httpx are not loaded by core imports."""
        network_libs = ["requests", "httpx", "urllib3", "aiohttp", "boto3"]
        for lib in network_libs:
            self.assertNotIn(
                lib,
                sys.modules,
                f"Network library '{lib}' should not be imported by core",
            )


class TestFullAnalysisPerformance(unittest.TestCase):
    """Integration test: full analysis within 30-second budget."""

    def test_selfdev_analysis_within_budget(self):
        """Run full analysis on the selfdev codebase and verify timing."""
        from organism import SelfDevelopmentOrganism

        root_dir = Path(__file__).resolve().parent.parent
        organism = SelfDevelopmentOrganism(root_dir=root_dir)

        with timed_operation("full_analysis") as t:
            organism.run_all_perspectives()

        self.assertTrue(
            check_analysis_time(t["elapsed"]),
            f"Analysis took {t['elapsed']:.1f}s, exceeds {ANALYSIS_TIMEOUT_SECONDS}s budget",
        )

    def test_single_perspective_fast(self):
        """Each perspective should complete in under 10 seconds."""
        from organism import SelfDevelopmentOrganism
        from models import Perspective

        root_dir = Path(__file__).resolve().parent.parent
        organism = SelfDevelopmentOrganism(root_dir=root_dir)

        for perspective in Perspective:
            with self.subTest(perspective=perspective.value):
                with timed_operation(perspective.value) as t:
                    organism.run_perspective(perspective, print_results=False)
                self.assertLess(
                    t["elapsed"],
                    10.0,
                    f"{perspective.value} took {t['elapsed']:.1f}s",
                )

    def test_memory_stays_bounded(self):
        """Memory should stay within limits after full analysis."""
        from organism import SelfDevelopmentOrganism

        root_dir = Path(__file__).resolve().parent.parent
        organism = SelfDevelopmentOrganism(root_dir=root_dir)
        organism.run_all_perspectives()

        self.assertTrue(
            check_memory_usage(),
            f"Memory usage {get_memory_usage_mb():.1f} MB exceeds {MEMORY_LIMIT_MB} MB limit",
        )


if __name__ == "__main__":
    unittest.main()
