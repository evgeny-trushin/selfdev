"""
Data models, constants, and enums for the Self-Development Organism system.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from enum import Enum


# ==================== Constants ====================

SELFDEV_DIR = Path(__file__).resolve().parent
ROOT_DIR = SELFDEV_DIR.parent  # default: analyze the project (../), not selfdev itself
STATE_FILE = ROOT_DIR / "organism_state.json"
REQUIREMENTS_DIR = ROOT_DIR / "requirements"
PRINCIPLES_DIR = ROOT_DIR / "principles"

# Directories to analyze
ANALYZABLE_DIRS = ["src", "components", "pages", "lib", "utils", "services"]
TEST_DIRS = ["tests", "__tests__", "test", "spec"]

# Default thresholds (overridable via selfdev_config.json)
COMPLEXITY_THRESHOLD = 10  # McCabe complexity
COVERAGE_TARGET = 80  # Percentage
MAX_FILE_LINES = 300
MAX_FUNCTION_LINES = 50


def load_config(root_dir: Path = None) -> dict:
    """Load configuration from selfdev_config.json, falling back to defaults."""
    defaults = {
        "complexity_threshold": COMPLEXITY_THRESHOLD,
        "coverage_target": COVERAGE_TARGET,
        "max_file_lines": MAX_FILE_LINES,
        "max_function_lines": MAX_FUNCTION_LINES,
        "analyzable_dirs": ANALYZABLE_DIRS,
        "test_dirs": TEST_DIRS,
        "prompt_templates": {},
    }
    if root_dir is None:
        root_dir = SELFDEV_DIR
    config_path = root_dir / "selfdev_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                user_config = json.load(f)
            defaults.update(user_config)
        except (json.JSONDecodeError, TypeError, OSError):
            pass
    return defaults


# ==================== Enums ====================

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


class Layer(Enum):
    UI = "ui"
    CLIENT = "client"
    SERVICE = "service"
    CROSS_LAYER = "cross_layer"


# ==================== Data Classes ====================

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
    evaluative_evidence: Optional[str] = None
    directive_evidence: Optional[str] = None
    expected_next_state: Optional[str] = None

    # Layered Architecture details
    layer: Optional[Layer] = None
    ui_details: Optional[str] = None
    client_details: Optional[str] = None
    service_details: Optional[str] = None
    boundary_details: Optional[str] = None
    affected_view: Optional[str] = None
    route: Optional[str] = None
    contract: Optional[str] = None
    state_transition: Optional[str] = None

    acceptance_criteria: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    reason: str = ""

    def __post_init__(self):
        if self.layer == Layer.CROSS_LAYER:
            cross_layer_msg = "Verify both caller and callee behavior"
            if cross_layer_msg not in self.acceptance_criteria:
                self.acceptance_criteria.append(cross_layer_msg)


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
    last_increment_shown: int = 0

    @classmethod
    def load(cls, path: Path) -> "OrganismState":
        """Load state from file or create new"""
        if path.exists():
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                # Filter to only known fields to avoid TypeError on unknown keys
                known_fields = {f.name for f in cls.__dataclass_fields__.values()}
                filtered = {k: v for k, v in data.items() if k in known_fields}
                return cls(**filtered)
            except (json.JSONDecodeError, TypeError, OSError):
                pass
        return cls(created_at=datetime.now(timezone.utc).isoformat())

    def save(self, path: Path) -> None:
        """Save state to file"""
        self.last_updated = datetime.now(timezone.utc).isoformat()
        try:
            with open(path, "w") as f:
                json.dump(asdict(self), f, indent=2)
        except OSError as e:
            print(f"Warning: Could not save state to {path}: {e}")

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
