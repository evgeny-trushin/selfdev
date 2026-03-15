## Core Purpose
Execute the current `_todo_` increment from `requirements/` EXACTLY as specified—NO deviations without approval.

## Critical Rules
1. **NEVER** deviate from the requirement's acceptance criteria
2. **NEVER** add improvements not specified in the increment
3. **ALWAYS** request approval for any changes beyond scope
4. **STRICTLY** follow each acceptance criterion as written
5. **HALT** if ambiguity detected

## Workflow (4 Steps)

### 1. Knowledge Base Prep
- Read relevant `principles/` files for domain context and coding standards
- Read `organism_state.json` for current generation and development stage
- Run `./selfdev/develop.sh` to see the current TODO increment
- Understand HOW to implement (not WHAT) by consulting principle categories:
  - `B1-B4`: Biological development principles
  - `G1-G4`: Prompt generation principles
  - `E1-E4`: Evolution principles
  - `D1-D2`: Deliberative dialogue principles
  - `CLN`: Output formatting standards

### 2. Task Validation
**Pre-Implementation Checklist:**
- [x] Read the current `_todo_` increment file from `requirements/`
- [x] Consulted relevant `principles/` files
- [x] Checked `organism_state.json` for current state
- [x] Confirmed NO ambiguities in acceptance criteria
- [x] Verified approach matches requirement EXACTLY
- [x] Will follow WITHOUT modifications

### 3. Strict Implementation
For each acceptance criterion:
1. Read the specific criterion from the requirement file
2. Consult relevant `principles/` files for approach guidance
3. Implement EXACTLY as specified
4. Run tests: `python3 -m pytest selfdev/tests/`
5. Update criterion checkbox: `- [ ]` → `- [x]`
6. Commit: `git add -A && git commit -m "INCREMENT NNNN: description"`

### 4. Deviation Protocol (if blocked)
```
### DEVIATION REQUEST
**Step:** [Current acceptance criterion]
**Increment:** [Number from requirements/]
**Issue:** [Blocker]
**Original Spec:** [What the requirement says]
**Principle Context:** [From principles/ files]
**Why Impossible:** [Technical reason]
**Proposed Alternative:** [Minimal change]
**Impact:** [Effects on other increments]

**AWAITING USER APPROVAL**
```

## Checkpoint Update Pattern
```markdown
- [x] Acceptance criterion: [Description]
  **Completed:** [Timestamp]
  **Implementation:** EXACTLY as specified
  **Principle Reference:** principles/E1.md — Small Mutations
  **No Deviations:** ✓
  **Files:** `selfdev/module.py`
  **Commit:** `a1b2c3d - INCREMENT NNNN: description`
```

## Knowledge Integration Rules
**Principles:** Coding standards, design patterns, perspective-specific guidance
**Organism State:** Current generation, development stage, fitness history
**Usage:** Inform HOW to implement—NEVER override WHAT the requirement specifies

## Response Patterns

### When Ambiguous
```
⚠️ **Implementation Paused - Clarification Needed**
**Criterion:** [From requirement file]
**Unclear:** [Quote from increment]
**Principle Context:** [Relevant principles/ guidance]
**Options:** 1) [A], 2) [B]
Please clarify before I proceed.
```

### When Tempted to Improve
```
📋 **Adherence Check**
Notice opportunity to [improvement] per principles/[file],
but NOT specified in the increment requirement.
**Action:** Implementing ONLY what's specified.
Create separate increment requirement?
```

## I/O Locations
- **Input:** `requirements/increment_NNNN_todo_*.md` (current TODO increment)
- **Output:** Implemented code in `selfdev/`, validated by `python3 -m pytest selfdev/tests/`
- **Verification:** `./selfdev/develop.sh` confirms increment is done

## Essential Standards
✓ Match requirement acceptance criteria exactly
✓ Principles inform approach only
✓ NO improvements beyond the increment scope
✓ ALL deviations need approval
✓ Update acceptance criteria checkboxes in real-time
✓ Follow `principles/CLN.md` for output formatting
✓ Run `python3 -m pytest selfdev/tests/` before every commit

## Deviation Log Template
```markdown
## Deviations from Original Increment

### Approved
1. **Criterion X Modification**
   - Original: [Requirement spec]
   - Actual: [Implemented]
   - Reason: [Why necessary]
   - Principle Reference: [principles/ source]
   - Approved: [Timestamp]

### Pending
1. **Criterion Y Blocker**
   - Issue: [Description]
   - Proposed: [Solution]
   - Status: AWAITING APPROVAL