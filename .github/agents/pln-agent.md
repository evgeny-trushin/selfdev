### Rapid Workflow (5 Steps)

**0. Load Knowledge** (with error handling)
- Read relevant `principles/` files for domain patterns and standards
- Check `organism_state.json` for current generation and development stage
- Run `./selfdev/develop.sh` to see current TODO increment
- Scan existing `requirements/` files for format conventions

**1. Clarify Task**
- Capture requirement precisely
- Cross-reference `principles/` for related guidance (perspectives: USR, TST, SYS, ANL, DBG)
- Ask targeted questions if unclear
- Establish success criteria aligned with existing acceptance criteria patterns

**2. Analyse Codebase**
- Identify relevant files/modules in `selfdev/`
- Verify architecture alignment with documented `principles/` patterns
- Assess dependencies and constraints across existing increments
- Create requirement file: `requirements/increment_NNNN_todo_<slug>.md`

**3. Review Git History**
- Search commits for similar implementations
- Cross-reference with `principles/` documentation
- Extract successful patterns, avoid documented failures
- Verify conventions from completed (`_done_`) increments in `requirements/`

**4. Create Execution Plan**
- Apply relevant principles from `principles/` (E1: Small Mutations, D1: Pre-Solution Questioning)
- Include lateral thinking alternatives within constraints (P1: Challenge Assumptions)
- Provide step-by-step implementation with specific file paths in `selfdev/`
- Reference principle files throughout
- Structure plan as acceptance criteria in the requirement file

### Essential Checklist
✓ All steps reference specific files in `selfdev/` and `principles/`
✓ Align with relevant `principles/` patterns
✓ Follow existing `requirements/` format conventions
✓ Avoid pitfalls documented in principles (B3: Apoptosis, M2: Bounded Evolution)
✓ Plan validated against `./selfdev/develop.sh` output
                                                                          
