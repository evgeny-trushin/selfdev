#!/bin/bash
#
# Self-Development System
# Analyzes codebase state and generates prompts from multiple perspectives
#
# Usage:
#   ./develop.sh           # Run all perspectives
#   ./develop.sh --user    # User perspective: features, UX, documentation
#   ./develop.sh --test    # Test perspective: coverage, robustness
#   ./develop.sh --system  # System perspective: architecture, complexity
#   ./develop.sh --analytics # Analytics perspective: trends, patterns
#   ./develop.sh --debug   # Debug perspective: issues, TODOs

#
# Additional options:
#   --state     Show current organism state
#   --advance   Advance to next generation
#   --selfdev   Analyze the selfdev system itself
#   --root DIR  Analyze a specific directory
#   --help      Show this help message
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/organism.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
show_banner() {
    echo -e "${CYAN}"
    echo "  ╔══════════════════════════════════════════════════════════╗"
    echo "  ║     SELF-DEVELOPMENT ORGANISM                            ║"
    echo "  ║     Biological Development Principles for Software       ║"
    echo "  ║     https://github.com/evgeny-trushin/selfdev            ║"
    echo "  ╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Help message
show_help() {
    show_banner
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "Perspectives (run one or more):"
    echo "  --user       Analyze from user's point of view"
    echo "               Features, documentation, UX, onboarding"
    echo ""
    echo "  --test       Analyze test coverage and quality"
    echo "               Coverage ratio, missing tests, robustness"
    echo ""
    echo "  --system     Analyze architecture and code quality"
    echo "               Complexity, coupling, cohesion, patterns"
    echo ""
    echo "  --analytics  Analyze trends and patterns over time"
    echo "               Fitness trends, commit patterns, predictions"
    echo ""
    echo "  --debug      Analyze for bugs and issues"
    echo "               TODOs, FIXMEs, errors, uncommitted changes"
    echo ""

    echo "Options:"
    echo "  --all        Run all perspectives (default if no perspective specified)"
    echo "  --state      Show current organism state"
    echo "  --advance    Advance to next generation after analysis"
    echo "  --selfdev    Analyze the selfdev system itself (instead of the project)"
    echo "  --root DIR   Analyze a specific directory"
    echo "  --no-color   Disable colored output"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0")               # Run all perspectives"
    echo "  $(basename "$0") --user --test # Run user and test perspectives"
    echo "  $(basename "$0") --debug       # Only debug perspective"
    echo "  $(basename "$0") --state       # Show current state"
    echo "  $(basename "$0") --selfdev     # Analyze the selfdev system itself"
    echo "  $(basename "$0") --root /path  # Analyze a specific project"
    echo ""
    echo "The system generates development prompts based on:"
    echo "  - Current codebase state"
    echo "  - Evolutionary history (stored in organism_state.json)"
    echo "  - Development principles (from principles.md)"
    echo ""
}

# Check Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}Error: Python not found. Please install Python 3.8+${NC}"
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')

    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
        echo -e "${YELLOW}Warning: Python 3.8+ recommended. Found Python ${PYTHON_VERSION}${NC}"
    fi
}

# Check if the Python script exists
check_script() {
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        echo -e "${RED}Error: organism.py not found at ${PYTHON_SCRIPT}${NC}"
        echo "Please ensure the Self-Development System is properly installed."
        exit 1
    fi
}

# Read a JSON field from organism_state.json using Python
# Usage: read_json_field <field_name> [default_value]
read_json_field() {
    local field="$1"
    local default_val="${2:-}"
    local state_file="${SCRIPT_DIR}/../organism_state.json"

    if [ ! -f "$state_file" ]; then
        echo "$default_val"
        return
    fi

    local value
    value=$($PYTHON_CMD -c "
import json, sys
try:
    with open('$state_file') as f:
        data = json.load(f)
    val = data.get('$field', '')
    print(val if val else '')
except Exception:
    print('')
" 2>/dev/null)

    if [ -z "$value" ]; then
        echo "$default_val"
    else
        echo "$value"
    fi
}

# Convert an ISO 8601 date to epoch seconds using Python
# Usage: date_to_epoch <iso_date_string>
date_to_epoch() {
    local date_str="$1"
    if [ -z "$date_str" ]; then
        echo "0"
        return
    fi
    $PYTHON_CMD -c "
from datetime import datetime, timezone
import sys
try:
    s = '$date_str'
    # Handle timezone offset formats
    if '+' in s[10:] or s.endswith('Z'):
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        # Python 3.7+ fromisoformat with timezone
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            # Fallback for formats like 2026-02-16T22:52:38+11:00
            from email.utils import parsedate_to_datetime
            dt = datetime.fromisoformat(s)
    else:
        dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    print(int(dt.timestamp()))
except Exception as e:
    print('0', file=sys.stderr)
    print('0')
" 2>/dev/null
}

# Get the latest git commit ISO date for a file
# Usage: get_git_file_date <file_path>
get_git_file_date() {
    local file_path="$1"
    if [ ! -f "$file_path" ]; then
        echo ""
        return
    fi
    git log -1 --format="%aI" -- "$file_path" 2>/dev/null || echo ""
}

# Get git commits for a file since a given ISO date
# Usage: get_git_commits_since <file_path> <since_iso_date>
get_git_commits_since() {
    local file_path="$1"
    local since_date="$2"
    if [ -z "$since_date" ] || [ "$since_date" = "0" ]; then
        git log --format="%H|%aI|%s" -- "$file_path" 2>/dev/null
    else
        git log --since="$since_date" --format="%H|%aI|%s" -- "$file_path" 2>/dev/null
    fi
}

# Collect a human-readable summary of git changes for a foundational file.
# Appends to the variable named by $3.
# Usage: collect_change_summary <file_path> <since_iso_date> <var_name>
collect_change_summary() {
    local file_path="$1"
    local since_date="$2"
    local var_name="$3"
    local summary=""

    while IFS='|' read -r commit_hash commit_date commit_msg; do
        if [ -n "$commit_hash" ]; then
            summary+="  - ${commit_hash:0:8} ${commit_date} ${commit_msg}"$'\n'
            local diff_lines
            diff_lines=$(git diff "${commit_hash}^..${commit_hash}" -- "$file_path" 2>/dev/null | \
                grep -E '^\+[^+]|^-[^-]' | head -10)
            if [ -n "$diff_lines" ]; then
                while IFS= read -r line; do
                    summary+="    ${line}"$'\n'
                done <<< "$diff_lines"
            fi
        fi
    done <<< "$(get_git_commits_since "$file_path" "$since_date")"

    # Append to the caller's variable
    eval "$var_name+=\"\$summary\""
}

# Auto-adapt: append a changelog entry summarising foundational changes
# Usage: auto_update_changelog <changelog_file> <change_summary_text>
auto_update_changelog() {
    local changelog_file="$1"
    local summary_text="$2"
    local now_iso
    now_iso=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
    local today
    today=$(date -u +"%Y-%m-%d")

    local entry=""
    entry+="### Adapted (${today})"$'\n'
    entry+="- **Auto-adapted** to foundational document changes detected at ${now_iso}."$'\n'
    entry+="${summary_text}"$'\n'

    # Insert the entry after the "## [Unreleased]" line (or after the header if present)
    if [ -f "$changelog_file" ]; then
        $PYTHON_CMD - "$changelog_file" "$entry" <<'PYEOF'
import sys, re
path, entry = sys.argv[1], sys.argv[2]
with open(path, "r") as f:
    content = f.read()
marker = "## [Unreleased]"
idx = content.find(marker)
if idx != -1:
    insert_pos = idx + len(marker)
    # skip any trailing newlines after the marker line
    while insert_pos < len(content) and content[insert_pos] == '\n':
        insert_pos += 1
    new_content = content[:insert_pos] + "\n" + entry + "\n" + content[insert_pos:]
else:
    new_content = content + "\n" + entry + "\n"
with open(path, "w") as f:
    f.write(new_content)
PYEOF
    else
        echo -e "# Changelog\n\n## [Unreleased]\n\n${entry}\n" > "$changelog_file"
    fi
}

# Auto-adapt: update requirements_last_checked and principles_last_checked in organism_state.json
# Usage: auto_update_state <state_file> <update_req> <update_prin>
auto_update_state() {
    local state_file="$1"
    local update_req="$2"     # "1" to update requirements_last_checked
    local update_prin="$3"    # "1" to update principles_last_checked

    $PYTHON_CMD - "$state_file" "$update_req" "$update_prin" <<'PYEOF'
import json, sys
from datetime import datetime, timezone

path = sys.argv[1]
update_req = sys.argv[2] == "1"
update_prin = sys.argv[3] == "1"
now = datetime.now(timezone.utc).isoformat()

with open(path, "r") as f:
    data = json.load(f)

if update_req:
    data["requirements_last_checked"] = now
if update_prin:
    data["principles_last_checked"] = now

with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF
}

# Check git history dates of requirements.md and principles.md against organism_state.json
# If foundational documents changed, auto-adapt: log to CHANGELOG and update tracked dates.
check_git_history() {
    local state_file="${SCRIPT_DIR}/../organism_state.json"
    local requirements_file="${SCRIPT_DIR}/../requirements.md"
    local principles_file="${SCRIPT_DIR}/../principles.md"
    local changelog_file="${SCRIPT_DIR}/CHANGELOG.md"
    local found_req=0
    local found_prin=0
    local change_summary=""

    # Verify we're in a git repository
    if ! git rev-parse --is-inside-work-tree &>/dev/null; then
        return 0
    fi

    # Read tracked dates from organism_state.json
    local req_last_checked
    local prin_last_checked
    req_last_checked=$(read_json_field "requirements_last_checked")
    prin_last_checked=$(read_json_field "principles_last_checked")

    if [ -z "$req_last_checked" ]; then
        req_last_checked=""
    fi
    if [ -z "$prin_last_checked" ]; then
        prin_last_checked=""
    fi

    local req_tracked_epoch
    local prin_tracked_epoch
    req_tracked_epoch=$(date_to_epoch "$req_last_checked")
    prin_tracked_epoch=$(date_to_epoch "$prin_last_checked")

    # Get latest git commit dates for each file
    local req_git_date
    local prin_git_date
    req_git_date=$(get_git_file_date "$requirements_file")
    prin_git_date=$(get_git_file_date "$principles_file")

    local req_git_epoch
    local prin_git_epoch
    req_git_epoch=$(date_to_epoch "$req_git_date")
    prin_git_epoch=$(date_to_epoch "$prin_git_date")

    # Check requirements.md
    if [ "$req_git_epoch" -gt "$req_tracked_epoch" ] 2>/dev/null; then
        found_req=1
        echo ""
        echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║  Foundational change detected: requirements.md                      ║${NC}"
        echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${YELLOW}Last tracked: ${req_last_checked:-never}  →  Latest git: ${req_git_date}${NC}"
        echo ""

        change_summary+="- **requirements.md** changes:"$'\n'

        while IFS='|' read -r commit_hash commit_date commit_msg; do
            if [ -n "$commit_hash" ]; then
                echo -e "  ${CYAN}${commit_hash:0:8}${NC} ${commit_date} ${commit_msg}"
                git diff "${commit_hash}^..${commit_hash}" -- "$requirements_file" 2>/dev/null | \
                    grep -E '^\+[^+]|^-[^-]' | head -20 | while IFS= read -r line; do
                        if [[ "$line" == +* ]]; then
                            echo -e "    ${GREEN}${line}${NC}"
                        else
                            echo -e "    ${RED}${line}${NC}"
                        fi
                    done
                echo ""
            fi
        done <<< "$(get_git_commits_since "$requirements_file" "$req_last_checked")"

        collect_change_summary "$requirements_file" "$req_last_checked" change_summary
    fi

    # Check principles.md
    if [ "$prin_git_epoch" -gt "$prin_tracked_epoch" ] 2>/dev/null; then
        found_prin=1
        echo ""
        echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║  Foundational change detected: principles.md                        ║${NC}"
        echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${YELLOW}Last tracked: ${prin_last_checked:-never}  →  Latest git: ${prin_git_date}${NC}"
        echo ""

        change_summary+="- **principles.md** changes:"$'\n'

        while IFS='|' read -r commit_hash commit_date commit_msg; do
            if [ -n "$commit_hash" ]; then
                echo -e "  ${CYAN}${commit_hash:0:8}${NC} ${commit_date} ${commit_msg}"
                git diff "${commit_hash}^..${commit_hash}" -- "$principles_file" 2>/dev/null | \
                    grep -E '^\+[^+]|^-[^-]' | head -20 | while IFS= read -r line; do
                        if [[ "$line" == +* ]]; then
                            echo -e "    ${GREEN}${line}${NC}"
                        else
                            echo -e "    ${RED}${line}${NC}"
                        fi
                    done
                echo ""
            fi
        done <<< "$(get_git_commits_since "$principles_file" "$prin_last_checked")"

        collect_change_summary "$principles_file" "$prin_last_checked" change_summary
    fi

    # Auto-adapt if any changes were found
    if [ "$found_req" -eq 1 ] || [ "$found_prin" -eq 1 ]; then
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  AUTO-ADAPTING — incorporating foundational changes                  ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""

        # 1. Update CHANGELOG.md with a summary of the changes
        auto_update_changelog "$changelog_file" "$change_summary"
        echo -e "  ${GREEN}✓${NC} Updated ${BLUE}CHANGELOG.md${NC} with change summary"

        # 2. Update tracked dates in organism_state.json
        auto_update_state "$state_file" "$found_req" "$found_prin"
        echo -e "  ${GREEN}✓${NC} Updated ${BLUE}organism_state.json${NC} timestamps"
        if [ "$found_req" -eq 1 ]; then
            echo -e "    • requirements_last_checked → now"
        fi
        if [ "$found_prin" -eq 1 ]; then
            echo -e "    • principles_last_checked  → now"
        fi

        echo ""
        echo -e "${GREEN}Adaptation complete. Continuing with analysis...${NC}"
        echo ""
    fi

    return 0
}

# Main function
main() {
    # Handle help first
    for arg in "$@"; do
        if [ "$arg" = "--help" ] || [ "$arg" = "-h" ]; then
            show_help
            exit 0
        fi
    done

    # Check prerequisites
    check_python
    check_script

    # Show banner unless --no-color is specified
    if [[ ! " $* " =~ " --no-color " ]]; then
        show_banner
    fi

    # Check git history for untracked changes to requirements.md and principles.md.
    # If foundational changes are detected, auto-adapt: log to CHANGELOG and update state.
    check_git_history

    # Pass all arguments to Python script
    $PYTHON_CMD "$PYTHON_SCRIPT" "$@"

    # Capture exit code
    EXIT_CODE=$?

    # Show footer message if successful
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}Analysis complete. Prompts generated based on current state.${NC}"
        echo -e "${CYAN}Tip: Use --advance after implementing prompts to track progress.${NC}"
    fi

    exit $EXIT_CODE
}

# Run main with all arguments
main "$@"
