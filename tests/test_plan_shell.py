"""Tests for the plan.sh launcher."""

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLAN_SH = PROJECT_ROOT / "plan.sh"
PLAN_PY = PROJECT_ROOT / "plan.py"


class PlanShellTests(unittest.TestCase):
    def test_help_is_delegated_to_plan_py(self):
        shell_help = subprocess.run(
            [str(PLAN_SH), "--help"],
            cwd="/tmp",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        python_help = subprocess.run(
            [sys.executable, str(PLAN_PY), "--help"],
            cwd="/tmp",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(python_help.returncode, 0, python_help.stderr)
        self.assertEqual(shell_help.returncode, 0, shell_help.stderr)
        self.assertEqual(shell_help.stdout, python_help.stdout)
        self.assertEqual(shell_help.stderr, python_help.stderr)


if __name__ == "__main__":
    unittest.main()
