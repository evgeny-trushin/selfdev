# Self-Development Organism

A biological-inspired code evolution system that analyzes your codebase from multiple perspectives and generates actionable development prompts. Uses lateral thinking principles and embryomorphic engineering to guide software development.

## Quick Start

```bash
# Run all perspectives
./selfdev/develop.sh

# Run specific perspective
./selfdev/develop.sh --user    # User experience & documentation
./selfdev/develop.sh --test    # Test coverage & quality
./selfdev/develop.sh --system  # Architecture & complexity
./selfdev/develop.sh --analytics  # Trends & patterns
./selfdev/develop.sh --debug   # Bugs, TODOs, issues

# Show current organism state
./selfdev/develop.sh --state

# Advance to next generation after implementing prompts
./selfdev/develop.sh --advance
```

## Architecture

```
selfdev/
├── develop.sh          # Main entry point (bash wrapper)
├── organism.py         # Core analysis engine (Python)
├── organism_state.json # Evolutionary state persistence
├── principles.md       # Lateral thinking & development principles
├── requirements.md     # System requirements specification
└── deepresearch/       # AI model research documents
```

## Core Concepts

### Biological Metaphors
| Biological Concept | Software Equivalent |
|-------------------|---------------------|
| Genome | Git repository (immutable history) |
| Phenotype | Running application (expressed behavior) |
| Cells | Modules/classes (functional units) |
| Morphogens | Code metrics (positional signals) |
| Immune System | Test suite (quality gates) |
| Differentiation | Component specialization based on fitness |

### Development Stages
| Stage | Generations | Focus |
|-------|------------|-------|
| Embryonic | 0-3 | Basic functionality, survival |
| Growth | 4-10 | Optimization, specialization |
| Maturation | 11-20 | Refinement, stability |
| Homeostasis | 21+ | Maintenance, evolution |

### Fitness Scores
Each perspective calculates fitness (0.0 - 1.0):
- **User**: Documentation quality, feature completeness
- **Test**: Coverage ratio, test quality
- **System**: Complexity, coupling, cohesion
- **Analytics**: Trend direction, pattern health
- **Debug**: Issue count, severity

---

## Practical Use Cases

### Full Stack Development

#### Use Case 1: New Feature Development Workflow
```bash
# 1. Analyze current state before starting
./selfdev/develop.sh --user --system

# 2. Prompts generated might include:
#    - "Add API documentation for /users endpoint"
#    - "Reduce complexity in UserController.ts (complexity=15)"
#    - "Create integration tests for auth flow"

# 3. After implementing feature, run all perspectives
./selfdev/develop.sh

# 4. Advance generation to track progress
./selfdev/develop.sh --advance
```

#### Use Case 2: Technical Debt Reduction Sprint
```bash
# Identify all system-level issues
./selfdev/develop.sh --system

# Example output prompts:
# [MEDIUM] Refactor src/services/payment.py (450 lines > 300 max)
# [MEDIUM] Reduce complexity in src/utils/validators.py (complexity=12)
# [HIGH] Extract common logic from duplicate handlers
```

#### Use Case 3: Pre-Release Quality Check
```bash
# Run comprehensive analysis
./selfdev/develop.sh --test --debug --user

# Ensures:
# - Test coverage is adequate
# - No critical TODOs/FIXMEs remain
# - Documentation is complete
# - No syntax errors in codebase
```

---

### Frontend Development

#### Use Case 4: Component Library Audit
```bash
# Check system architecture
./selfdev/develop.sh --system

# Prompts for frontend:
# [MEDIUM] Refactor components/Form/FormField.tsx (380 lines)
# [LOW] Extract validation logic from InputComponent
# [MEDIUM] Reduce prop drilling depth in Dashboard
```

#### Use Case 5: Accessibility & UX Review
```bash
# User perspective focuses on experience
./selfdev/develop.sh --user

# Example prompts:
# [HIGH] Enhance README documentation (current: 200 chars, target: 2000)
# [MEDIUM] Add usage examples for DatePicker component
# [LOW] Create CHANGELOG.md for version tracking
```

#### Use Case 6: React/Vue Component Optimization
```bash
# Analyze complexity of component files
./selfdev/develop.sh --system

# Actionable prompts:
# [HIGH] Split UserDashboard.tsx into smaller components
# [MEDIUM] Extract hooks from ProfilePage (complexity=18)
# [LOW] Consider lazy loading for SettingsPanel
```

#### Use Case 7: Storybook Documentation Gap Analysis
```bash
./selfdev/develop.sh --user --test

# Identifies:
# Components without stories
# Missing prop documentation
# Untested user interactions
```

---

### Backend Development

#### Use Case 8: API Endpoint Coverage
```bash
# Test perspective for backend
./selfdev/develop.sh --test

# Prompts:
# [CRITICAL] Create test directory
# [HIGH] Add tests for src/routes/orders.py (complexity=14)
# [HIGH] Increase test coverage (3 test files for 12 source files)
```

#### Use Case 9: Database Service Refactoring
```bash
# System perspective for complexity
./selfdev/develop.sh --system

# Example output:
# [MEDIUM] Refactor src/db/queries.py (520 lines > 300 max)
#   - Extract related functions into separate modules
#   - Keep file under 300 lines
#   - Maintain single responsibility
```

#### Use Case 10: Microservice Health Check
```bash
# Run debug perspective for each service
cd services/user-service && ../selfdev/develop.sh --debug
cd services/order-service && ../selfdev/develop.sh --debug
cd services/payment-service && ../selfdev/develop.sh --debug

# Identifies per-service:
# - TODO/FIXME comments
# - Uncommitted changes
# - Syntax errors
# - High-severity issues
```

#### Use Case 11: API Documentation Completeness
```bash
./selfdev/develop.sh --user

# Prompts for API docs:
# [CRITICAL] Create README.md for service
# [HIGH] Add OpenAPI/Swagger documentation
# [MEDIUM] Document environment variables
```

#### Use Case 12: Performance Bottleneck Identification
```bash
./selfdev/develop.sh --system --analytics

# System perspective identifies:
# - High complexity functions (potential N+1 queries)
# - Large files (monolithic services)
# Analytics shows:
# - Trend of increasing complexity
# - High fix commit rate (stability issues)
```

---

### DevOps & Infrastructure

#### Use Case 13: CI/CD Pipeline Quality
```bash
# Debug perspective for infrastructure code
./selfdev/develop.sh --debug

# Scans for:
# [HIGH] FIXME: Race condition in deployment script
# [MEDIUM] TODO: Add rollback mechanism
# [LOW] TODO: Parameterize environment variables
```

#### Use Case 14: Infrastructure-as-Code Review
```bash
# System perspective for Terraform/Ansible complexity
./selfdev/develop.sh --system

# Prompts:
# [MEDIUM] Refactor terraform/main.tf (400 lines)
# [HIGH] Reduce complexity in ansible/deploy.yml
# [LOW] Extract common modules from duplicate configs
```

#### Use Case 15: Docker/Kubernetes Configuration Audit
```bash
./selfdev/develop.sh --user --system

# User perspective:
# - Missing README for container setup
# - No documented environment variables
# System perspective:
# - Complex Dockerfile (multi-stage build refactoring)
# - Large Helm chart files
```

#### Use Case 16: Monitoring & Alerting Gap Analysis
```bash
./selfdev/develop.sh --analytics

# Analytics perspective over time reveals:
# - Error rate trends
# - Recurring issues in specific components
# - Fitness regression after deployments
```

#### Use Case 17: Security Scan Preparation
```bash
./selfdev/develop.sh --debug --system

# Identifies:
# [HIGH] TODO: Remove hardcoded credentials
# [CRITICAL] FIXME: SQL injection vulnerability
# [MEDIUM] High complexity in auth module (attack surface)
```

#### Use Case 18: Release Readiness Assessment
```bash
# Comprehensive pre-release check
./selfdev/develop.sh

# Generates report across all perspectives:
# User: Documentation complete? ✓
# Test: Coverage adequate? ✗ (40% < 80% target)
# System: Complexity acceptable? ✓
# Debug: Critical issues resolved? ✗ (2 FIXMEs remain)
# Analytics: Positive trend? ✓
```

---

## Integration Examples

### GitHub Actions Integration
```yaml
name: Self-Development Check
on: [push, pull_request]

jobs:
  organism-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run Self-Development Analysis
        run: ./selfdev/develop.sh --test --system --debug
      - name: Check for Critical Issues
        run: |
          if grep -q "CRITICAL" organism_output.txt; then
            exit 1
          fi
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running self-development check..."
./selfdev/develop.sh --debug --no-color

# Block commit if critical issues exist
if [ $? -ne 0 ]; then
    echo "Critical issues detected. Fix before committing."
    exit 1
fi
```

### VS Code Task
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Self-Dev: Full Analysis",
      "type": "shell",
      "command": "./selfdev/develop.sh",
      "problemMatcher": []
    },
    {
      "label": "Self-Dev: Quick Debug Check",
      "type": "shell", 
      "command": "./selfdev/develop.sh --debug",
      "problemMatcher": []
    }
  ]
}
```

---

## Principles Reference

See [principles.md](principles.md) for detailed documentation on:
- **Lateral Thinking Principles** (P1-P3): Challenge assumptions, random entry points, escape patterns
- **Biological Development Principles** (B1-B4): Morphogenesis, differentiation, apoptosis, feedback loops
- **Prompt Generation Principles** (G1-G4): Context-aware, actionable, prioritized, measurable
- **Perspective-Specific Principles**: User, Test, System, Analytics, Debug
- **Evolution Principles** (E1-E4): Small mutations, selection pressure, memory, diversity
- **Meta-Principles** (M1-M3): Self-application, bounded evolution, transparency
- **Deliberative Dialogue Principles** (D1-D4): Pre-solution questioning, cognitive behaviors, socio-emotional reasoning

---

## Fitness History Tracking

The system tracks evolutionary progress in `organism_state.json`:

```json
{
  "generation": 5,
  "development_stage": "growth",
  "fitness_scores": {
    "user": 0.85,
    "test": 0.60,
    "system": 0.70,
    "analytics": 0.50,
    "debug": 0.90
  },
  "fitness_history": [
    {"generation": 1, "overall": 0.45},
    {"generation": 2, "overall": 0.52},
    {"generation": 3, "overall": 0.61}
  ]
}
```

Use this to track improvement over time and identify regression patterns.

---

## Extending the System

### Adding Custom Perspectives
Create a new class extending `PerspectiveAnalyzer` in `organism.py`:

```python
class SecurityPerspective(PerspectiveAnalyzer):
    def get_perspective(self) -> Perspective:
        return Perspective.SECURITY  # Add to Perspective enum
    
    def analyze(self) -> Tuple[float, List[Prompt]]:
        # Scan for security patterns
        # Return (fitness_score, list_of_prompts)
        pass
```

### Customizing Thresholds
Edit constants in `organism.py`:

```python
COMPLEXITY_THRESHOLD = 10  # McCabe complexity max
COVERAGE_TARGET = 80       # 80% coverage goal
MAX_FILE_LINES = 300       # Max lines per file
MAX_FUNCTION_LINES = 50    # Max lines per function
```
