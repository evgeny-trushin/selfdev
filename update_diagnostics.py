import re

with open("selfdev/diagnostics.py", "r") as f:
    content = f.read()

content = content.replace(
"""from models import (
    OrganismState,
    Perspective,
    Priority,
    Prompt,
    ANALYZABLE_DIRS,
)""",
"""from models import (
    OrganismState,
    Perspective,
    Priority,
    Prompt,
)""")

old_find_todo = """    def _find_todo_comments(self) -> List[dict]:
        \"\"\"Scan source directories for TODO/FIXME comments\"\"\"
        todo_pattern = re.compile(r'#\\s*(TODO|FIXME|XXX|HACK|BUG)[\\s:]*(.*)', re.IGNORECASE)
        todos = []

        for dir_name in ANALYZABLE_DIRS:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                continue
            for file_path in dir_path.rglob("*.py"):
                if "__pycache__" in str(file_path):
                    continue
                try:
                    content = file_path.read_text()
                    for i, line in enumerate(content.splitlines(), 1):
                        match = todo_pattern.search(line)
                        if match:
                            todos.append({
                                "file": str(file_path.relative_to(self.root_dir)),
                                "line": i,
                                "type": match.group(1).upper(),
                                "text": match.group(2).strip()
                            })
                except Exception:
                    continue

        return todos"""

new_find_todo = """    def _find_todo_comments(self) -> List[dict]:
        \"\"\"Scan source directories for TODO/FIXME comments\"\"\"
        todo_pattern = re.compile(r'#\\s*(TODO|FIXME|XXX|HACK|BUG)[\\s:]*(.*)', re.IGNORECASE)
        todos = []

        analyses = self.code_analyzer.get_all_analyses()

        for rel_path in analyses.keys():
            file_path = self.root_dir / rel_path
            if not file_path.exists() or "__pycache__" in str(file_path):
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
                for i, line in enumerate(content.splitlines(), 1):
                    match = todo_pattern.search(line)
                    if match:
                        todos.append({
                            "file": rel_path,
                            "line": i,
                            "type": match.group(1).upper(),
                            "text": match.group(2).strip()
                        })
            except Exception:
                continue

        return todos"""

content = content.replace(old_find_todo, new_find_todo)

with open("selfdev/diagnostics.py", "w") as f:
    f.write(content)
