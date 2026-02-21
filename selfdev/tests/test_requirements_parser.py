"""Tests for RequirementsParser."""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import Priority
from requirements_parser import RequirementsParser


class TestRequirementsParser(unittest.TestCase):

    def test_parse_simple_requirement(self):
        content = """
### R1: Core Feature
This is a core feature description.

**Acceptance Criteria:**
- Criteria 1
- Criteria 2
"""
        reqs = RequirementsParser.parse_requirements(content)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]['id'], 'R1')
        self.assertEqual(reqs[0]['title'], 'Core Feature')
        self.assertEqual(reqs[0]['description'], 'This is a core feature description.')
        self.assertEqual(len(reqs[0]['acceptance_criteria']), 2)
        self.assertEqual(reqs[0]['acceptance_criteria'][0], 'Criteria 1')

    def test_parse_multiple_requirements(self):
        content = """
### R1: First
Desc 1.

### R2: Second
Desc 2.
"""
        reqs = RequirementsParser.parse_requirements(content)
        self.assertEqual(len(reqs), 2)
        self.assertEqual(reqs[0]['id'], 'R1')
        self.assertEqual(reqs[1]['id'], 'R2')

    def test_classify_priority(self):
        self.assertEqual(RequirementsParser.classify_priority('R1'), Priority.CRITICAL)
        self.assertEqual(RequirementsParser.classify_priority('FR5'), Priority.CRITICAL)
        self.assertEqual(RequirementsParser.classify_priority('W2'), Priority.HIGH)
        self.assertEqual(RequirementsParser.classify_priority('D1'), Priority.HIGH)
        self.assertEqual(RequirementsParser.classify_priority('T3'), Priority.MEDIUM)
        self.assertEqual(RequirementsParser.classify_priority('NFR1'), Priority.MEDIUM)
        self.assertEqual(RequirementsParser.classify_priority('OA-R1'), Priority.LOW)
        self.assertEqual(RequirementsParser.classify_priority('UNKNOWN'), Priority.MEDIUM)

    def test_parse_ignores_tables_and_code(self):
        content = """
### R1: Complex Feature
This is the description.

| Table | Header |
|-------|--------|
| Row   | Data   |

```python
code block
```

**Acceptance Criteria:**
- Criterion
"""
        reqs = RequirementsParser.parse_requirements(content)
        self.assertEqual(reqs[0]['description'], 'This is the description.')
        self.assertEqual(len(reqs[0]['acceptance_criteria']), 1)

    def test_parse_acceptance_criteria_alternative_syntax(self):
        content = """
### R1: Feature
Desc.

**Acceptance Criteria**
- C1
"""
        reqs = RequirementsParser.parse_requirements(content)
        # The regex expects "**Acceptance Criteria:?**" followed by newline and bullets
        # My input above lacks colon but has newline. Regex: \*\*Acceptance Criteria:?\*\*\s*\n
        self.assertEqual(len(reqs[0]['acceptance_criteria']), 1)
        self.assertEqual(reqs[0]['acceptance_criteria'][0], 'C1')


if __name__ == "__main__":
    unittest.main()
