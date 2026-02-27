
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Adjust path so we can import from selfdev/
sys.path.append(str(Path(__file__).resolve().parent.parent))

from models import (
    OrganismState,
    Perspective,
    Priority,
    Prompt,
    FileAnalysis,
)
from organism import SelfDevelopmentOrganism
from perspectives import TestPerspective, SystemPerspective
from user_perspective import UserPerspective
from diagnostics import AnalyticsPerspective, DebugPerspective


class TestPerspectivesIntegration(unittest.TestCase):
    """Integration tests to verify multi-perspective validation requirements"""

    def setUp(self):
        # Setup mock dependencies
        self.root_dir = Path("/tmp/mock_project")
        self.state = OrganismState()

        # Create a mock organism with mocked components
        # We need to mock the file loading in OrganismState to avoid FileNotFoundError
        with patch('models.OrganismState.load', return_value=self.state):
            self.organism = SelfDevelopmentOrganism(root_dir=self.root_dir)
            self.organism.state = self.state

    def test_perspectives_exist(self):
        """Verify all 5 perspectives are registered"""
        expected_perspectives = {
            Perspective.USER,
            Perspective.TEST,
            Perspective.SYSTEM,
            Perspective.ANALYTICS,
            Perspective.DEBUG
        }
        self.assertEqual(set(self.organism.perspectives.keys()), expected_perspectives)

    def test_user_perspective_execution(self):
        """Verify UserPerspective returns fitness and prompts"""
        analyzer = self.organism.perspectives[Perspective.USER]

        # Mock the internal checks
        with patch.object(analyzer, '_check_readme') as mock_readme:
            with patch.object(analyzer, '_check_package_json') as mock_pkg:

                # We need to ensure _check_readme appends to the list passed to it
                def side_effect_readme(fitness_components, prompts):
                    fitness_components.append(1.0)
                mock_readme.side_effect = side_effect_readme

                def side_effect_pkg(fitness_components, prompts):
                    fitness_components.append(1.0)
                mock_pkg.side_effect = side_effect_pkg

                fitness, prompts = analyzer.analyze()

                self.assertIsInstance(fitness, float)
                self.assertTrue(0.0 <= fitness <= 1.0)
                self.assertIsInstance(prompts, list)
                mock_readme.assert_called_once()
                mock_pkg.assert_called_once()

    def test_test_perspective_execution(self):
        """Verify TestPerspective returns fitness and prompts"""
        analyzer = self.organism.perspectives[Perspective.TEST]

        # Mock code analyzer
        mock_analyses = {
            "src/main.py": FileAnalysis("src/main.py", 10, 1, 0, 0, 1.0, False, []),
            "tests/test_main.py": FileAnalysis("tests/test_main.py", 20, 1, 0, 0, 1.0, True, [])
        }

        with patch.object(analyzer.code_analyzer, 'get_all_analyses', return_value=mock_analyses):
            # Also mock directory checks
            with patch('pathlib.Path.exists', return_value=True):
                 fitness, prompts = analyzer.analyze()

            self.assertIsInstance(fitness, float)
            self.assertIsInstance(prompts, list)

    def test_system_perspective_execution(self):
        """Verify SystemPerspective returns fitness and prompts"""
        analyzer = self.organism.perspectives[Perspective.SYSTEM]

        # Create a mock analysis with high complexity
        complex_analysis = FileAnalysis("src/complex.py", 100, 5, 0, 0, 15.0, False, [])
        mock_analyses = {
            "src/complex.py": complex_analysis
        }

        with patch.object(analyzer.code_analyzer, 'get_all_analyses', return_value=mock_analyses):
            fitness, prompts = analyzer.analyze()

            self.assertIsInstance(fitness, float)
            self.assertIsInstance(prompts, list)
            # Expect complexity prompt
            self.assertTrue(any(p.perspective == Perspective.SYSTEM for p in prompts))

    def test_analytics_perspective_execution(self):
        """Verify AnalyticsPerspective returns fitness and prompts"""
        analyzer = self.organism.perspectives[Perspective.ANALYTICS]

        # Mock git history and state
        analyzer.state.fitness_history = [{"overall": 0.5}] * 5

        with patch.object(analyzer.git_analyzer, 'get_recent_commits', return_value=[]):
            fitness, prompts = analyzer.analyze()

            self.assertIsInstance(fitness, float)
            self.assertIsInstance(prompts, list)

    def test_debug_perspective_execution(self):
        """Verify DebugPerspective returns fitness and prompts"""
        analyzer = self.organism.perspectives[Perspective.DEBUG]

        mock_analyses = {
            "src/buggy.py": FileAnalysis("src/buggy.py", 10, 0, 0, 0, 1.0, False, ["Syntax error"])
        }

        with patch.object(analyzer.code_analyzer, 'get_all_analyses', return_value=mock_analyses):
            with patch.object(analyzer, '_find_todo_comments', return_value=[]):
                with patch.object(analyzer.git_analyzer, 'get_uncommitted_changes', return_value=[]):
                    fitness, prompts = analyzer.analyze()

                    self.assertIsInstance(fitness, float)
                    self.assertIsInstance(prompts, list)
                    # Expect code issue prompt
                    self.assertTrue(any("Code issue" in p.title for p in prompts))

    def test_organism_run_all_perspectives(self):
        """Verify run_all_perspectives runs all analyzers"""

        # Mock all analyzers
        for p in Perspective:
            # Create a fresh mock for each perspective analyzer
            mock_analyzer = MagicMock()
            mock_analyzer.analyze.return_value = (0.9, [])
            self.organism.perspectives[p] = mock_analyzer

        with patch('builtins.print'):
            self.organism.run_all_perspectives()

        for p in Perspective:
            self.organism.perspectives[p].analyze.assert_called()


if __name__ == "__main__":
    unittest.main()
