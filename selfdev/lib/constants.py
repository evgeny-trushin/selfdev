from pathlib import Path

# Paths
# selfdev/lib/constants.py -> selfdev/lib -> selfdev
SELFDEV_ROOT = Path(__file__).resolve().parent.parent
ROOT_DIR = SELFDEV_ROOT.parent  # Default root to analyze if not specified (repository root)
STATE_FILE = SELFDEV_ROOT / "organism_state.json"
REQUIREMENTS_FILE = SELFDEV_ROOT / "requirements.md"
PRINCIPLES_FILE = SELFDEV_ROOT / "principles.md"

# Directories to analyze
ANALYZABLE_DIRS = ["selfdev", "src", "components", "pages", "lib", "utils", "services"]
TEST_DIRS = ["selfdev/tests", "tests", "__tests__", "test", "spec"]

# Thresholds
COMPLEXITY_THRESHOLD = 10  # McCabe complexity
COVERAGE_TARGET = 80  # Percentage
MAX_FILE_LINES = 300
MAX_FUNCTION_LINES = 50
