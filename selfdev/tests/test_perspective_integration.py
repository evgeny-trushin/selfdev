
import unittest
import shutil
import tempfile
from pathlib import Path
from selfdev.models import Perspective, Prompt, OrganismState, STATE_FILE
from selfdev.organism import SelfDevelopmentOrganism

class TestPerspectiveIntegration(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for tests
        self.test_dir = Path(tempfile.mkdtemp())
        self.root_dir = self.test_dir

        # Create a mock STATE_FILE
        self.state_file = self.root_dir / "organism_state.json"
        OrganismState().save(self.state_file)

        # Create some dummy files to analyze
        (self.root_dir / "README.md").write_text("# Test Project\n\nA test project.")
        (self.root_dir / "src").mkdir()
        (self.root_dir / "src/main.py").write_text("def hello():\n    print('Hello')\n")
        (self.root_dir / "tests").mkdir()
        (self.root_dir / "tests/test_main.py").write_text("def test_hello():\n    assert True\n")

        self.organism = SelfDevelopmentOrganism(root_dir=self.root_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_user_perspective(self):
        prompts = self.organism.run_perspective(Perspective.USER, print_results=False)
        self.assertIsInstance(prompts, list)
        self.assertIsInstance(self.organism.state.fitness_scores[Perspective.USER.value], float)

    def test_test_perspective(self):
        prompts = self.organism.run_perspective(Perspective.TEST, print_results=False)
        self.assertIsInstance(prompts, list)
        self.assertIsInstance(self.organism.state.fitness_scores[Perspective.TEST.value], float)

    def test_system_perspective(self):
        prompts = self.organism.run_perspective(Perspective.SYSTEM, print_results=False)
        self.assertIsInstance(prompts, list)
        self.assertIsInstance(self.organism.state.fitness_scores[Perspective.SYSTEM.value], float)

    def test_analytics_perspective(self):
        prompts = self.organism.run_perspective(Perspective.ANALYTICS, print_results=False)
        self.assertIsInstance(prompts, list)
        self.assertIsInstance(self.organism.state.fitness_scores[Perspective.ANALYTICS.value], float)

    def test_debug_perspective(self):
        prompts = self.organism.run_perspective(Perspective.DEBUG, print_results=False)
        self.assertIsInstance(prompts, list)
        self.assertIsInstance(self.organism.state.fitness_scores[Perspective.DEBUG.value], float)

    def test_run_all_perspectives(self):
        prompts = self.organism.run_all_perspectives()
        self.assertIsInstance(prompts, list)
        for p in Perspective:
            self.assertIn(p.value, self.organism.state.fitness_scores)
            self.assertIsInstance(self.organism.state.fitness_scores[p.value], float)

if __name__ == '__main__':
    unittest.main()
