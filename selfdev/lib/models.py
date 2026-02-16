import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from enum import Enum

class DevelopmentStage(Enum):
    EMBRYONIC = "embryonic"      # Generation 0-3
    GROWTH = "growth"            # Generation 4-10
    MATURATION = "maturation"    # Generation 11-20
    HOMEOSTASIS = "homeostasis"  # Generation 21+


class Perspective(Enum):
    USER = "user"
    TEST = "test"
    SYSTEM = "system"
    ANALYTICS = "analytics"
    DEBUG = "debug"


class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


@dataclass
class Prompt:
    """A generated development prompt"""
    perspective: Perspective
    priority: Priority
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    metric_current: Optional[float] = None
    metric_target: Optional[float] = None
    acceptance_criteria: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class FileAnalysis:
    """Analysis results for a single file"""
    path: str
    lines: int
    functions: int
    classes: int
    imports: int
    complexity: float
    has_tests: bool
    issues: List[str] = field(default_factory=list)


@dataclass
class OrganismState:
    """Current state of the self-developing organism"""
    generation: int = 0
    created_at: str = ""
    last_updated: str = ""
    development_stage: str = "embryonic"
    fitness_scores: Dict[str, float] = field(default_factory=dict)
    fitness_history: List[Dict] = field(default_factory=list)
    prompts_generated: int = 0
    prompts_completed: int = 0
    last_git_hash: str = ""

    @classmethod
    def load(cls, path: Path) -> "OrganismState":
        """Load state from file or create new"""
        if path.exists():
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                # Convert string keys/values to appropriate types if necessary
                # But here it's mostly primitives so generic dict is fine for load
                # except enums if stored as strings?
                # The original code just did cls(**data).
                return cls(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return cls(created_at=datetime.now(timezone.utc).isoformat())

    def save(self, path: Path) -> None:
        """Save state to file"""
        self.last_updated = datetime.now(timezone.utc).isoformat()
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def get_stage(self) -> DevelopmentStage:
        """Get current development stage based on generation"""
        if self.generation <= 3:
            return DevelopmentStage.EMBRYONIC
        elif self.generation <= 10:
            return DevelopmentStage.GROWTH
        elif self.generation <= 20:
            return DevelopmentStage.MATURATION
        else:
            return DevelopmentStage.HOMEOSTASIS
