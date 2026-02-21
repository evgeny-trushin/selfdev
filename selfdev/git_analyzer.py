"""
Git analyzer for the Self-Development Organism system.
"""

import subprocess
from pathlib import Path
from typing import Dict, List

class GitAnalyzer:
    """Analyzes Git history and state"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

    def get_current_hash(self) -> str:
        """Get current commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()[:8]
        except Exception:
            return ""

    def get_recent_commits(self, count: int = 10) -> List[Dict]:
        """Get recent commits"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--pretty=format:%H|%s|%ad", "--date=iso"],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            commits = []
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|", 2)
                    commits.append({
                        "hash": parts[0][:8],
                        "message": parts[1] if len(parts) > 1 else "",
                        "date": parts[2] if len(parts) > 2 else ""
                    })
            return commits
        except Exception:
            return []

    def get_uncommitted_changes(self) -> List[str]:
        """Get list of uncommitted files"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        except Exception:
            return []

    def get_branch(self) -> str:
        """Get current branch name"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.root_dir,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"
