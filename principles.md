# Self-Development Principles

## Lateral Thinking Principles

### P1: Challenge Assumptions
Before generating prompts, question the obvious:
- Why does this code exist in its current form?
- What if we approached this problem from the opposite direction?
- Are we solving the right problem?


### P2: Random Entry Point
Each perspective starts from a different "entry point" into the codebase:
- User: Starts from the end user's first interaction and works backward to implementation
- Test: Starts from edge cases and works toward happy paths
- System: Starts from infrastructure dependencies and works toward application logic
- Analytics: Starts from user outcomes and business metrics and works toward causes
- Debug: Starts from symptoms (failed integrations, unexpected state, deployment failures) and works toward root causes

### P3: Escape Patterns
Recognize and escape from local optima:
- If tests pass but users disengage, user perspective takes precedence
- If code is clean but loads slowly, system perspective flags performance
- If everything works but key goals aren't met, analytics perspective triggers flow redesign

## Biological Development Principles

### B1: Morphogenesis Through Gradients
Each perspective creates a "gradient" of priority:
```
High Priority <-------------------> Low Priority
Critical Bugs    Minor Issues    Nice-to-haves
```

### B2: Differentiation Over Time
As the system matures, perspectives specialize:
- Generation 0-3: All perspectives focus on survival (basic functionality)
- Generation 4-10: Perspectives begin specializing (feature completeness, robustness)
- Generation 11-20: Perspectives refine (optimization, analytics-driven iteration)
- Generation 21+: Perspectives reach homeostasis (maintenance, reliability)

### B3: Apoptosis (Programmed Death)
Remove what doesn't serve the organism:
- Dead code flagged by static analysis
- Unused dependencies
- Obsolete tests
- Stale documentation

### B4: Feedback Loops
Negative feedback for stability:
- Rising complexity triggers refactoring prompts
- Falling test coverage triggers test prompts
- Increasing error rates trigger debug prompts

Positive feedback for growth:
- High fitness scores unlock new feature prompts
- Good test coverage enables refactoring prompts
- Clean architecture enables optimization prompts



## Prompt Generation Principles

### G1: Context-Aware
Every prompt includes:
- Current state summary
- Relevant metrics
- Historical trend
- Specific action requested


### G2: Actionable
Prompts must be immediately actionable:
- BAD: "Improve test coverage"
- GOOD: "Add tests for UserService.authenticate() - currently 0% covered"
- GOOD: "Add missing error handling to api_client.py"

### G3: Prioritized
Prompts are ranked by:
1. Impact on overall fitness
2. Effort required
3. Dependencies on other changes
4. Historical success rate
5. User impact

### G4: Measurable
Each prompt includes acceptance criteria:
- Specific metric threshold to achieve
- File or function to modify
- Test to pass

## Perspective-Specific Principles

### User Perspective (--user)
- Empathy: What pain points exist for users?
- Journey: What is the user trying to accomplish?
- Friction: Where does the experience break down?
- Value: What delivers the most benefit to the user?

### Test Perspective (--test)
- Coverage: What code paths are untested?
- Robustness: What edge cases are missing?
- Mutation: Would bugs be caught?
- Speed: Are tests fast enough for CI?


### System Perspective (--system)
- Coupling: Are modules too interdependent?
- Cohesion: Are responsibilities well-grouped?
- Complexity: Is the code understandable?
- Performance: Are there bottlenecks?
- Infrastructure: Is the configuration consistent?

### Analytics Perspective (--analytics)
- Trends: What is changing over time?
- Patterns: What recurring issues exist?
- Predictions: What problems are likely?
- Correlations: What changes together?
- Conversion: Are users completing key flows?

### Debug Perspective (--debug)
- Symptoms: What errors are occurring?
- Traces: Where do errors originate?
- Frequency: How often do issues happen?
- Severity: What is the impact?




## Evolution Principles

### E1: Small Mutations
Prefer many small changes over few large ones:
- Each prompt should target a focused change
- Changes should be independently testable
- Rollback should be easy

### E2: Selection Pressure
Only accept changes that improve fitness:
- All tests must pass
- Metrics must not regress significantly
- Code review (human or automated) approves

### E3: Memory
Learn from history:
- Track which prompts led to improvements
- Avoid repeating failed approaches
- Build on successful patterns

### E4: Diversity
Maintain genetic diversity:
- Don't over-optimize for one perspective
- Allow experimental branches
- Preserve alternative solutions

## Meta-Principles

### M1: Self-Application
These principles apply to the self-development system itself:
- The system should improve its own prompt generation
- Fitness functions can evolve
- New perspectives can emerge

### M2: Bounded Evolution
Evolution operates within constraints:
- Only modify files in allowed directories
- Respect max changes per generation
- Maintain system integrity

### M3: Transparency
All decisions are logged and explainable:
- Why was this prompt generated?
- What metrics influenced the priority?
- What is the expected outcome?

## Deliberative Dialogue Principles

### D1: Pre-Solution Questioning
Before writing any solution, complete internal Q&A:
- Q1: What is the function supposed to do in detail?
- Q2: What are the edge cases or inputs to consider?
- Q3: What approach will handle those cases?

### D2: Required Cognitive Behaviors

- Ask "Why would we need...?"
- Ask "What if the input is...?"
- Answer each question explicitly before proceeding

**Perspective Shift**
- Say "Let me try a different approach..."
- Say "Alternatively, we could..."
- Say "From a user's perspective, this would..."
- Explore at least 2 different approaches

**Conflict Detection**
- Use "Wait, that can't be right because..."
- Use "No, actually... this breaks when..."
- Actively look for flaws in reasoning

**Reconciliation**
- Use "Combining these insights..."
- Use "This resolves the edge case by..."
- Synthesize best elements from different approaches

### D3: Socio-Emotional Reasoning

**Give Suggestions**
- "We should consider..."
- "Let us approach this by..."

**Ask for Opinions**
- "Is this the right approach?"
- "Does this handle all cases?"

**Show Disagreement**
- "But that would break when..."
- "However, this fails if..."

**Show Agreement**
- "Yes, that's correct because..."
- "This works well since..."

### D4: Step-by-Step Deliberation
Think through problems by debating alternatives:
1. State the problem clearly
2. Generate multiple candidate solutions
3. Evaluate each against edge cases
4. Identify conflicts between approaches
5. Reconcile into final solution
6. Verify against original requirements
