"""Path-name constants live in one place."""
import unittest
import models


class TestPathConstants(unittest.TestCase):

    def test_todo_dirname_constant_exists(self):
        self.assertEqual(models.TODO_DIRNAME, "todo")

    def test_how_dirname_constant_exists(self):
        self.assertEqual(models.HOW_DIRNAME, "how")

    def test_todo_dir_uses_dirname_constant(self):
        self.assertTrue(str(models.TODO_DIR).endswith(models.TODO_DIRNAME))

    def test_how_dir_uses_dirname_constant(self):
        self.assertTrue(str(models.HOW_DIR).endswith(models.HOW_DIRNAME))


if __name__ == "__main__":
    unittest.main()
