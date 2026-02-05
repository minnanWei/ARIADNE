CODEGEN_PROMPT_TEMPLATE = """You are an expert competitive programmer.

TASK
Write a correct and efficient Python 3 solution for the problem below.

PROBLEM STATEMENT
{problem_statement}

INPUT/OUTPUT SPEC
{io_spec}

CONSTRAINTS
{constraints}

REQUIRED INVARIANTS / CORRECTNESS CONDITIONS
{invariants}

EDGE CASE CHECKLIST
{edge_cases}

KNOWN FAILING / TRICKY CASES (from blackboard)
{counterexamples}

RULES
- Output MUST be ONLY valid Python code (no markdown, no explanation).
- The solution MUST read from stdin and write to stdout.
- Be robust to extra spaces/newlines.
- Ensure time complexity fits constraints.
- Prefer simple, standard-library-only code.
- Add minimal comments only where needed for correctness.

Return ONLY the final Python code.
"""

REPAIR_PROMPT_TEMPLATE = """You are a senior engineer fixing a competitive programming solution.

PROBLEM (for reference)
{problem_statement}

CURRENT CODE
{current_code}

FAILURE DIAGNOSTICS
- status: {status}
- error_type: {error_type}
- failing_tests:
{failing_tests}

PATCH PROPOSALS (apply the best subset, respect constraints)
{patch_proposals}

RULES
- Return ONLY valid Python code (no markdown, no explanation).
- Preserve working parts; change minimal lines necessary.
- Ensure the fix addresses the failing tests.
- Do NOT introduce new I/O format changes.
- Keep complexity within constraints.
- If multiple patches conflict, choose the safer one.

Return ONLY the repaired Python code.
"""

STRATEGY_PROMPT_TEMPLATE = """You are a competitive programming strategist.

Given the problem and observed evidence, propose algorithmic strategies.

PROBLEM SUMMARY
{problem_summary}

CONSTRAINTS
{constraints}

EVIDENCE FROM EXECUTION
- recent_statuses: {recent_statuses}
- common_failure_patterns: {failure_patterns}
- representative_counterexamples:
{counterexamples}

OUTPUT FORMAT (STRICT JSON)
Return a JSON object with key "strategies", value is a list of strategies.
Each strategy must contain:
- "id": short snake_case id
- "name": short name
- "applicability_conditions": list of strings
- "complexity_upper_bound": string like "O(n log n)"
- "risk_flags": list of strings
- "minimal_evidence_set": list of strings
- "notes": string
- "bid": {{ "p": float in [0,1], "c": float in [0,1], "r": float in [0,1] }}
Also include "recommended_active_id": one of the ids.

RULES
- Provide 2 to 4 strategies.
- If uncertain, include a baseline safe strategy.
- Use constraints to justify complexity bounds.
Return ONLY JSON.
"""

TESTGEN_PROMPT_TEMPLATE = """You are a test engineer for competitive programming solutions.

PROBLEM
{problem_statement}

INPUT/OUTPUT SPEC
{io_spec}

CONSTRAINTS
{constraints}

EDGE CASE CHECKLIST
{edge_cases}

KNOWN COUNTEREXAMPLES (inputs that broke solutions)
{counterexamples}

TASK
Propose additional test cases that are likely to reveal bugs:
- extreme values
- boundary conditions
- tricky formatting
- small exhaustive cases if applicable

OUTPUT FORMAT (STRICT JSON)
Return a JSON object with key "tests", value is a list.
Each item:
- "input": string (must end with newline)
- "expected_output": optional string (if you can deduce it confidently; else null)
- "origin": one of ["GENERATED_EXTREME","GENERATED_RANDOM","GENERATED_ENUM","MINIMIZATION_HINT"]
- "rationale": short string

RULES
- Provide 6 to 12 tests.
- At least 3 must be extreme/boundary.
- If expected_output is unknown, set it to null.
Return ONLY JSON.
"""
