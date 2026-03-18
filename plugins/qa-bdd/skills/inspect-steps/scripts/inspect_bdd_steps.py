"""BDD step assertion completeness inspector (v2 -- context-aware).

Three-pass pipeline:
  Pass 0: AST extraction + Gherkin parsing -> step-to-scenario mapping
  Pass 1 (Sonnet): Context-aware triage -- each Then step is shown IN its
      scenario(s) so the AI can assess whether the assertion matches the
      scenario's INTENT, not just the step text.
  Pass 2 (Opus): Deep trace -- what should the correct assertion be?

New in v2:
  --gherkin-quality: Inspect Gherkin scenarios for specification weakness
      (e.g., "validation should result in valid" is input-acceptance, not behavioral).

Usage:
  python inspect_bdd_steps.py [--pass1-only] [--gherkin-quality]
  python inspect_bdd_steps.py --steps-dir path/to/steps --features-dir path/to/features
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

STEP_DECORATOR_NAMES = {"given", "when", "then"}


# -- Data classes ----------------------------------------------------------


@dataclass
class GherkinScenario:
    """A single Gherkin scenario extracted from a .feature file."""

    feature_file: str
    feature_title: str
    feature_postconditions: list[str]
    scenario_name: str
    tags: list[str]
    steps: list[tuple[str, str]]  # [(keyword, text), ...] -- Given/When/Then/And
    examples_header: list[str]
    examples_rows: list[list[str]]
    line_number: int


@dataclass
class BddStepInfo:
    """Metadata for a single BDD step function."""

    file_path: str
    line_number: int
    step_type: str  # "given", "when", or "then"
    step_text: str
    function_name: str
    source_text: str
    scenarios: list[GherkinScenario] = field(default_factory=list)


@dataclass
class TriageResult:
    """Result from Pass 1 triage."""

    step: BddStepInfo
    verdict: str  # "PASS" or "FLAG"
    reason: str


@dataclass
class DeepTraceResult:
    """Result from Pass 2 deep trace."""

    step: BddStepInfo
    claims: str
    actually_tests: str
    recommendation: str
    severity: str  # "COSMETIC", "WEAK", "MISSING"


@dataclass
class GherkinQualityIssue:
    """A quality issue found in a Gherkin scenario specification."""

    scenario: GherkinScenario
    step_keyword: str
    step_text: str
    issue_type: str  # "VAGUE_OUTCOME", "INPUT_ACCEPTANCE_ONLY", "GENERIC_THEN"
    reason: str


# -- Pass 0a: AST extraction ----------------------------------------------


def _extract_step_text(decorator: ast.Call) -> str | None:
    """Extract the step text string from a @given/@when/@then decorator call."""
    if not decorator.args:
        return None
    arg = decorator.args[0]
    # Form A: @then("plain string")
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value
    # Form B: @then(parsers.parse("string with {params}"))
    if isinstance(arg, ast.Call):
        if (
            isinstance(arg.func, ast.Attribute)
            and arg.func.attr == "parse"
            and arg.args
            and isinstance(arg.args[0], ast.Constant)
        ):
            return arg.args[0].value
    # Form C: @then(parsers.re(r"regex pattern"))
    if isinstance(arg, ast.Call):
        if (
            isinstance(arg.func, ast.Attribute)
            and arg.func.attr == "re"
            and arg.args
            and isinstance(arg.args[0], ast.Constant)
        ):
            return arg.args[0].value
    return None


def _get_decorator_step_type(decorator: ast.expr) -> str | None:
    """Get the step type (given/when/then) from a decorator node."""
    if not isinstance(decorator, ast.Call):
        return None
    func = decorator.func
    if isinstance(func, ast.Name) and func.id in STEP_DECORATOR_NAMES:
        return func.id
    if isinstance(func, ast.Attribute) and func.attr in STEP_DECORATOR_NAMES:
        return func.attr
    return None


def extract_bdd_steps(directory: Path) -> list[BddStepInfo]:
    """Extract all BDD step functions from Python files in directory."""
    results: list[BddStepInfo] = []

    for py_file in sorted(directory.rglob("*.py")):
        try:
            source = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue

        source_lines = source.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                step_type = _get_decorator_step_type(decorator)
                if step_type is None:
                    continue
                step_text = _extract_step_text(decorator)  # type: ignore[arg-type]
                if step_text is None:
                    continue
                body = "\n".join(source_lines[node.lineno - 1 : node.end_lineno])
                results.append(
                    BddStepInfo(
                        file_path=str(py_file),
                        line_number=node.lineno,
                        step_type=step_type,
                        step_text=step_text,
                        function_name=node.name,
                        source_text=body,
                    )
                )
                break

    return results


# -- Pass 0b: Gherkin parsing ---------------------------------------------


def parse_feature_files(features_dir: Path) -> list[GherkinScenario]:
    """Parse all .feature files and extract scenarios with full context."""
    scenarios: list[GherkinScenario] = []

    for feature_file in sorted(features_dir.glob("*.feature")):
        try:
            content = feature_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        scenarios.extend(_parse_single_feature(str(feature_file), content))

    return scenarios


def _parse_single_feature(file_path: str, content: str) -> list[GherkinScenario]:
    """Parse a single .feature file into scenarios."""
    lines = content.splitlines()
    scenarios: list[GherkinScenario] = []

    feature_title = ""
    feature_postconditions: list[str] = []
    background_steps: list[tuple[str, str]] = []

    # State machine
    in_background = False
    in_scenario = False
    in_examples = False
    current_tags: list[str] = []
    current_scenario_name = ""
    current_scenario_line = 0
    current_steps: list[tuple[str, str]] = []
    current_examples_header: list[str] = []
    current_examples_rows: list[list[str]] = []
    last_keyword = ""
    pending_tags: list[str] = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip empty lines and pure comments (but capture postcondition comments)
        if not stripped:
            continue

        # Feature title
        if stripped.startswith("Feature:"):
            feature_title = stripped[len("Feature:") :].strip()
            continue

        # Postcondition comments at feature level
        if stripped.startswith("#") and not in_scenario and not in_background:
            post_match = re.match(r"#\s+(POST-[A-Z]\d+:.+)", stripped)
            if post_match:
                feature_postconditions.append(post_match.group(1))
            continue

        # Tags
        if stripped.startswith("@"):
            pending_tags.extend(re.findall(r"@([\w-]+)", stripped))
            continue

        # Background
        if stripped.startswith("Background:"):
            in_background = True
            in_scenario = False
            pending_tags = []
            continue

        # Scenario / Scenario Outline
        if stripped.startswith("Scenario Outline:") or stripped.startswith("Scenario:"):
            # Save previous scenario
            if in_scenario and current_scenario_name:
                scenarios.append(
                    GherkinScenario(
                        feature_file=file_path,
                        feature_title=feature_title,
                        feature_postconditions=list(feature_postconditions),
                        scenario_name=current_scenario_name,
                        tags=list(current_tags),
                        steps=list(background_steps) + list(current_steps),
                        examples_header=list(current_examples_header),
                        examples_rows=list(current_examples_rows),
                        line_number=current_scenario_line,
                    )
                )

            in_background = False
            in_scenario = True
            in_examples = False
            current_tags = list(pending_tags)
            pending_tags = []
            current_scenario_name = stripped.split(":", 1)[1].strip()
            current_scenario_line = i
            current_steps = []
            current_examples_header = []
            current_examples_rows = []
            last_keyword = ""
            continue

        # Examples header
        if stripped.startswith("Examples:"):
            in_examples = True
            continue

        # Table rows (in Examples section)
        if in_examples and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not current_examples_header:
                current_examples_header = cells
            else:
                current_examples_rows.append(cells)
            continue

        # Non-table line ends Examples section
        if in_examples and not stripped.startswith("|") and not stripped.startswith("#"):
            in_examples = False

        # Step lines (Given/When/Then/And/But)
        step_match = re.match(r"(Given|When|Then|And|But)\s+(.*)", stripped)
        if step_match:
            keyword = step_match.group(1)
            text = step_match.group(2)

            # "And"/"But" inherit the last keyword
            if keyword in ("And", "But"):
                keyword = last_keyword or "Given"
            else:
                last_keyword = keyword

            if in_background:
                background_steps.append((keyword, text))
            elif in_scenario:
                current_steps.append((keyword, text))
            continue

        # Inline comment in scenario -- might reference postconditions/rules
        if stripped.startswith("#") and in_scenario:
            continue

    # Save last scenario
    if in_scenario and current_scenario_name:
        scenarios.append(
            GherkinScenario(
                feature_file=file_path,
                feature_title=feature_title,
                feature_postconditions=list(feature_postconditions),
                scenario_name=current_scenario_name,
                tags=list(current_tags),
                steps=list(background_steps) + list(current_steps),
                examples_header=list(current_examples_header),
                examples_rows=list(current_examples_rows),
                line_number=current_scenario_line,
            )
        )

    return scenarios


# -- Pass 0c: Link steps to scenarios -------------------------------------


def _step_text_matches(step_text: str, gherkin_text: str) -> bool:
    """Check if a step definition's text pattern matches a Gherkin step text.

    Handles:
    - Exact match
    - Parser patterns with {param} placeholders
    - Regex patterns (basic: match against the gherkin text)
    - Scenario Outline <param> substitution (treat <x> as wildcard)
    """
    # Normalize gherkin text: replace <param> with placeholder
    normalized_gherkin = re.sub(r"<\w+>", "__PLACEHOLDER__", gherkin_text)
    # Also replace quoted values with placeholder for parser matching
    normalized_gherkin_quoted = re.sub(r'"[^"]*"', '"__Q__"', normalized_gherkin)

    # Exact match
    if step_text == gherkin_text:
        return True

    # Parser pattern: convert {param} to regex
    if "{" in step_text:
        pattern = re.escape(step_text)
        pattern = re.sub(r"\\{[^}]+\\}", ".+", pattern)
        if re.fullmatch(pattern, gherkin_text) or re.fullmatch(pattern, normalized_gherkin):
            return True

    # Regex pattern: try direct match
    try:
        if re.fullmatch(step_text, gherkin_text):
            return True
        if re.fullmatch(step_text, normalized_gherkin):
            return True
        if re.fullmatch(step_text, normalized_gherkin_quoted):
            return True
    except re.error:
        pass

    return False


def link_steps_to_scenarios(
    steps: list[BddStepInfo],
    scenarios: list[GherkinScenario],
) -> None:
    """Populate each step's .scenarios list with matching Gherkin scenarios."""
    # Build Then-step lookup for efficiency
    then_steps = [s for s in steps if s.step_type == "then"]

    for scenario in scenarios:
        then_texts = [text for kw, text in scenario.steps if kw == "Then"]
        for gherkin_text in then_texts:
            for step in then_steps:
                if _step_text_matches(step.step_text, gherkin_text):
                    if scenario not in step.scenarios:
                        step.scenarios.append(scenario)


# -- Pass 1: Context-aware triage (Sonnet) ---------------------------------


TRIAGE_PROMPT_TEMPLATE = """You are reviewing BDD Then step definitions for assertion completeness.

CRITICAL: You must evaluate each step IN THE CONTEXT of the scenario(s) that use it.
A step that checks "response exists, no error" might be PASS for a scenario testing
error handling, but FLAG for a scenario testing whether a feature WORKS.

For each step below, answer FLAG or PASS:

- FLAG: The assertion is WEAKER than what the scenario INTENDS to verify.
  Examples:
  - Scenario tests whether a feature affects the response, but Then step
    only checks "got a response" without verifying the feature's effect.
  - Scenario tests status filtering, but Then step doesn't verify which statuses
    were returned.
  - Then step checks what the TEST SETUP injected rather than what PRODUCTION generated.
  - Then step text says "validation should result in valid" for a scenario that's
    testing whether a FEATURE works (not just input acceptance).

- PASS: The assertion matches the scenario's intent.
  Examples:
  - Scenario tests error handling, Then step verifies error type and code.
  - Scenario tests retry behavior, Then step verifies retry count and backoff intervals.
  - Then step accesses specific response attributes matching the scenario's purpose.

Respond with EXACTLY one line per step in format: <number>|<FLAG or PASS>|<reason>

{steps_block}"""


def _format_scenario_context(scenario: GherkinScenario, max_examples: int = 3) -> str:
    """Format a scenario for inclusion in the triage prompt."""
    parts = [f"  Scenario: {scenario.scenario_name}"]
    parts.append(f"  Tags: {' '.join('@' + t for t in scenario.tags)}")

    # Relevant postconditions (from feature header)
    if scenario.feature_postconditions:
        parts.append(f"  Feature postconditions: {'; '.join(scenario.feature_postconditions[:5])}")

    # Steps
    for kw, text in scenario.steps:
        parts.append(f"    {kw} {text}")

    # Examples (first few rows)
    if scenario.examples_header:
        parts.append(f"  Examples columns: {scenario.examples_header}")
        for row in scenario.examples_rows[:max_examples]:
            parts.append(f"    | {' | '.join(row)} |")
        if len(scenario.examples_rows) > max_examples:
            parts.append(f"    ... +{len(scenario.examples_rows) - max_examples} more rows")

    return "\n".join(parts)


def _format_steps_for_triage(steps: list[BddStepInfo]) -> str:
    """Format steps with scenario context for the triage prompt."""
    parts = []
    for i, step in enumerate(steps, 1):
        part = f'--- Step {i} ---\nStep text: "{step.step_text}"\nFunction:\n{step.source_text}\n'

        # Add scenario context
        if step.scenarios:
            part += "\nScenario(s) using this step:\n"
            # Show up to 3 representative scenarios
            for sc in step.scenarios[:3]:
                part += _format_scenario_context(sc) + "\n"
            if len(step.scenarios) > 3:
                part += f"  ... and {len(step.scenarios) - 3} more scenarios\n"
        else:
            part += "\n(No Gherkin scenario linked -- step may be unused or matching failed)\n"

        parts.append(part)
    return "\n".join(parts)


def _run_claude(prompt: str, model: str = "sonnet") -> str:
    """Run claude -p and return the text output."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", model, "--output-format", "text"],
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )
    return result.stdout.strip()


def run_pass1_triage(steps: list[BddStepInfo], batch_size: int = 5) -> list[TriageResult]:
    """Run Pass 1 triage on steps, batched for efficiency.

    Batch size reduced from 10 to 5 because each step now includes
    scenario context, making prompts larger.
    """
    results: list[TriageResult] = []

    for batch_start in range(0, len(steps), batch_size):
        batch = steps[batch_start : batch_start + batch_size]
        prompt = TRIAGE_PROMPT_TEMPLATE.format(steps_block=_format_steps_for_triage(batch))

        output = _run_claude(prompt, model="sonnet")

        for line in output.splitlines():
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = line.split("|", 2)
            if len(parts) < 2:
                continue
            try:
                idx = int(parts[0].strip()) - 1
            except (ValueError, IndexError):
                continue
            if 0 <= idx < len(batch):
                verdict = parts[1].strip().upper()
                reason = parts[2].strip() if len(parts) > 2 else ""
                if verdict in ("FLAG", "PASS"):
                    results.append(TriageResult(step=batch[idx], verdict=verdict, reason=reason))

    return results


# -- Pass 2: Deep trace (Opus) ---------------------------------------------


DEEP_TRACE_PROMPT_TEMPLATE = """You are an expert reviewing a BDD Then step definition that was flagged
as potentially NOT implementing what its SCENARIO intends to verify.

Your job is to make an ARCHITECTURAL JUDGMENT: what should this function
actually verify, given the scenario context?

## Flagged Function

Step text: "{step_text}"
Function name: {func_name}
File: {file_path}:{line_number}

```python
{source_text}
```

## Triage Reason
{triage_reason}

## Scenario Context
{scenario_context}

## Production Context
{production_context}

## Instructions

Analyze and respond with EXACTLY this format (no markdown, no extra text):

CLAIMS: <what the scenario intends this step to verify -- consider the full Given/When/Then chain>
ACTUALLY_TESTS: <what the function body actually tests>
SEVERITY: <COSMETIC|WEAK|MISSING>
RECOMMENDATION: <what the correct assertion should be -- describe the semantic check, not code>

Severity guide:
- COSMETIC: naming/wording mismatch but the assertion is functionally correct for the scenario
- WEAK: assertion checks something related but is significantly weaker than the scenario requires
- MISSING: assertion doesn't verify what the scenario intends (existence check for behavioral claim)"""


def _collect_production_context(step: BddStepInfo) -> str:
    """Collect production schema/model context for a flagged step."""
    context_parts: list[str] = []

    try:
        full_source = Path(step.file_path).read_text()
        lines = full_source.splitlines()
        imports = [line for line in lines if line.startswith(("import ", "from "))]
        if imports:
            context_parts.append("## Imports in step file\n" + "\n".join(imports))
    except OSError:
        pass

    # Find helper functions called by the step
    # Look for _helper_name( calls in the source
    helper_calls = re.findall(r"(_\w+)\(", step.source_text)
    if helper_calls:
        try:
            full_source = Path(step.file_path).read_text()
            for helper_name in set(helper_calls):
                # Find the helper function definition
                pattern = rf"def {re.escape(helper_name)}\("
                match = re.search(pattern, full_source)
                if match:
                    # Extract the function (rough: take lines until next def or end)
                    start_pos = match.start()
                    func_start = full_source.rfind("\n", 0, start_pos) + 1
                    # Find end: next top-level def or end of file
                    rest = full_source[start_pos:]
                    next_def = re.search(r"\n(?=def |class )", rest[1:])
                    if next_def:
                        func_end = start_pos + 1 + next_def.start()
                    else:
                        func_end = len(full_source)
                    helper_source = full_source[func_start:func_end].strip()
                    context_parts.append(f"## Helper: {helper_name}\n```python\n{helper_source}\n```")
        except OSError:
            pass

    return "\n\n".join(context_parts) if context_parts else "No additional context available."


def run_pass2_deep_trace(flagged: list[TriageResult]) -> list[DeepTraceResult]:
    """Run Pass 2 deep trace on flagged steps with Opus."""
    results: list[DeepTraceResult] = []

    for triage in flagged:
        step = triage.step

        # Build scenario context
        scenario_parts = []
        for sc in step.scenarios[:3]:
            scenario_parts.append(_format_scenario_context(sc, max_examples=5))
        scenario_context = "\n\n".join(scenario_parts) if scenario_parts else "No scenario context."

        production_context = _collect_production_context(step)

        prompt = DEEP_TRACE_PROMPT_TEMPLATE.format(
            step_text=step.step_text,
            func_name=step.function_name,
            file_path=step.file_path,
            line_number=step.line_number,
            source_text=step.source_text,
            triage_reason=triage.reason,
            scenario_context=scenario_context,
            production_context=production_context,
        )

        output = _run_claude(prompt, model="opus")

        claims = ""
        actually_tests = ""
        severity = "WEAK"
        recommendation = ""

        for line in output.splitlines():
            line = line.strip()
            if line.startswith("CLAIMS:"):
                claims = line[7:].strip()
            elif line.startswith("ACTUALLY_TESTS:"):
                actually_tests = line[15:].strip()
            elif line.startswith("SEVERITY:"):
                severity = line[9:].strip()
            elif line.startswith("RECOMMENDATION:"):
                recommendation = line[15:].strip()

        results.append(
            DeepTraceResult(
                step=step,
                claims=claims,
                actually_tests=actually_tests,
                recommendation=recommendation,
                severity=severity,
            )
        )

    return results


# -- Gherkin quality inspection --------------------------------------------


GHERKIN_QUALITY_PROMPT = """You are reviewing BDD Gherkin scenarios for SPECIFICATION quality.

This is NOT about step implementations -- it's about whether the Gherkin SPECIFICATION
is precise enough that a correct implementation is even possible.

For each scenario, answer FLAG or PASS:

- FLAG: The specification is too vague or tests the wrong thing.
  Examples:
  - Then step says "validation should result in valid" -- this only specifies
    input acceptance, not behavioral verification. A correct impl would just
    check "no error", which proves nothing about whether the feature WORKS.
  - Then step says "the result should be correct" -- what does "correct" mean?
  - Scenario claims to test a feature but Then steps don't verify the feature's
    observable effect on the response.

- PASS: The specification is precise enough to write a meaningful assertion.
  Examples:
  - "Then the response should include only items with status X" -- clear observable
  - "Then the system should retry up to 3 times" -- verifiable count
  - "Then the error message should contain 'invalid_field'" -- specific check

Respond with EXACTLY one line per scenario: <number>|<FLAG or PASS>|<reason>

{scenarios_block}"""


def _format_scenarios_for_quality(scenarios: list[GherkinScenario]) -> str:
    """Format scenarios for the Gherkin quality prompt."""
    parts = []
    for i, sc in enumerate(scenarios, 1):
        part = f"--- Scenario {i} ---\n"
        part += f"Name: {sc.scenario_name}\n"
        part += f"Tags: {' '.join('@' + t for t in sc.tags)}\n"
        part += "Steps:\n"
        for kw, text in sc.steps:
            part += f"  {kw} {text}\n"
        if sc.examples_header:
            part += f"Examples: {sc.examples_header}\n"
            for row in sc.examples_rows[:3]:
                part += f"  | {' | '.join(row)} |\n"
        parts.append(part)
    return "\n".join(parts)


def run_gherkin_quality(scenarios: list[GherkinScenario], batch_size: int = 8) -> list[GherkinQualityIssue]:
    """Inspect Gherkin scenarios for specification quality issues."""
    # Focus on scenarios with @pending tag (the ones being implemented)
    pending = [s for s in scenarios if "pending" in s.tags]
    if not pending:
        pending = scenarios  # Fall back to all if no pending

    results: list[GherkinQualityIssue] = []

    for batch_start in range(0, len(pending), batch_size):
        batch = pending[batch_start : batch_start + batch_size]
        prompt = GHERKIN_QUALITY_PROMPT.format(scenarios_block=_format_scenarios_for_quality(batch))

        output = _run_claude(prompt, model="sonnet")

        for line in output.splitlines():
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = line.split("|", 2)
            if len(parts) < 2:
                continue
            try:
                idx = int(parts[0].strip()) - 1
            except (ValueError, IndexError):
                continue
            if 0 <= idx < len(batch):
                verdict = parts[1].strip().upper()
                reason = parts[2].strip() if len(parts) > 2 else ""
                if verdict == "FLAG":
                    sc = batch[idx]
                    # Find the Then steps
                    then_steps = [(kw, text) for kw, text in sc.steps if kw == "Then"]
                    for kw, text in then_steps:
                        results.append(
                            GherkinQualityIssue(
                                scenario=sc,
                                step_keyword=kw,
                                step_text=text,
                                issue_type="VAGUE_OUTCOME",
                                reason=reason,
                            )
                        )

    return results


# -- Report generation -----------------------------------------------------


def generate_report(
    all_steps: list[BddStepInfo],
    triage_results: list[TriageResult],
    deep_results: list[DeepTraceResult],
    gherkin_issues: list[GherkinQualityIssue],
    output_path: Path,
) -> None:
    """Generate a markdown report of the inspection results."""
    flagged = [r for r in triage_results if r.verdict == "FLAG"]
    passed = [r for r in triage_results if r.verdict == "PASS"]

    lines = [
        "# BDD Inspection Report (v2 -- Context-Aware)",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Summary",
        "",
        f"- **Steps scanned**: {len(all_steps)}",
        f"- **Then steps analyzed**: {len(triage_results)}",
        f"- **Passed triage**: {len(passed)}",
        f"- **Flagged for deep inspection**: {len(flagged)}",
        f"- **Confirmed issues**: {len(deep_results)}",
        f"- **Gherkin quality issues**: {len(gherkin_issues)}",
        "",
    ]

    if deep_results:
        by_severity: dict[str, list[DeepTraceResult]] = {}
        for r in deep_results:
            by_severity.setdefault(r.severity, []).append(r)

        lines.append("## Step Assertion Issues (by Severity)")
        lines.append("")

        for severity in ["MISSING", "WEAK", "COSMETIC"]:
            items = by_severity.get(severity, [])
            if not items:
                continue
            lines.append(f"### {severity} ({len(items)})")
            lines.append("")
            for r in items:
                rel_path = r.step.file_path
                try:
                    rel_path = str(Path(r.step.file_path).relative_to(Path.cwd()))
                except ValueError:
                    pass
                lines.extend(
                    [
                        f"#### `{r.step.function_name}` ({rel_path}:{r.step.line_number})",
                        "",
                        f'**Step text**: "{r.step.step_text}"',
                        "",
                        f"**Claims** (from scenario context): {r.claims}",
                        "",
                        f"**Actually tests**: {r.actually_tests}",
                        "",
                        f"**Recommendation**: {r.recommendation}",
                        "",
                    ]
                )

    if gherkin_issues:
        lines.append("## Gherkin Specification Quality Issues")
        lines.append("")
        lines.append("These are upstream problems -- the Gherkin specification itself is too")
        lines.append("vague for a meaningful step implementation to exist.")
        lines.append("")
        lines.append("| Scenario | Then Step | Issue |")
        lines.append("|----------|----------|-------|")
        for issue in gherkin_issues:
            sc_name = issue.scenario.scenario_name[:40]
            step_text = issue.step_text[:50]
            lines.append(f"| {sc_name} | {step_text} | {issue.reason} |")
        lines.append("")

    if flagged:
        lines.append("## All Flagged Steps (Pass 1)")
        lines.append("")
        lines.append("| # | Function | Step Text | Reason |")
        lines.append("|---|----------|-----------|--------|")
        for i, r in enumerate(flagged, 1):
            step_text_short = r.step.step_text[:60] + "..." if len(r.step.step_text) > 60 else r.step.step_text
            lines.append(f"| {i} | `{r.step.function_name}` | {step_text_short} | {r.reason} |")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))


# -- Main ------------------------------------------------------------------


def main() -> None:
    """Run the BDD inspection pipeline."""
    parser = argparse.ArgumentParser(description="BDD step assertion completeness inspector (v2)")
    parser.add_argument(
        "--steps-dir",
        type=Path,
        default=Path("tests/bdd/steps"),
        help="Directory containing BDD step definitions (default: tests/bdd/steps)",
    )
    parser.add_argument(
        "--features-dir",
        type=Path,
        default=Path("tests/bdd/features"),
        help="Directory containing .feature files (default: tests/bdd/features)",
    )
    parser.add_argument("--pass1-only", action="store_true", help="Skip Pass 2 deep trace")
    parser.add_argument(
        "--gherkin-quality",
        action="store_true",
        help="Also inspect Gherkin scenarios for specification quality",
    )
    parser.add_argument("--output", type=Path, default=None, help="Output report path")
    parser.add_argument("--then-only", action="store_true", default=True)
    args = parser.parse_args()

    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        args.output = Path(f".claude/reports/bdd-step-audit-{timestamp}.md")

    # Pass 0a: Extract step functions
    print(f"Scanning {args.steps_dir} for BDD step functions...")
    all_steps = extract_bdd_steps(args.steps_dir)
    print(f"  Found {len(all_steps)} step functions total")

    # Pass 0b: Parse Gherkin feature files
    print(f"Parsing {args.features_dir} for Gherkin scenarios...")
    scenarios = parse_feature_files(args.features_dir)
    print(f"  Found {len(scenarios)} scenarios")

    # Pass 0c: Link steps to scenarios
    print("Linking Then steps to Gherkin scenarios...")
    link_steps_to_scenarios(all_steps, scenarios)
    then_steps = [s for s in all_steps if s.step_type == "then"]
    linked = sum(1 for s in then_steps if s.scenarios)
    print(f"  {linked}/{len(then_steps)} Then steps linked to scenarios")

    # Filter targets
    if args.then_only:
        target_steps = then_steps
        print(f"  Targeting {len(target_steps)} Then steps for triage")
    else:
        target_steps = all_steps

    # Pass 1: Context-aware triage
    print(f"\n=== Pass 1: Context-Aware Triage (Sonnet) -- {len(target_steps)} steps ===")
    triage_results = run_pass1_triage(target_steps)
    flagged = [r for r in triage_results if r.verdict == "FLAG"]
    print(f"  {len(flagged)} flagged, {len(triage_results) - len(flagged)} passed")

    # Pass 2: Deep trace
    deep_results: list[DeepTraceResult] = []
    if not args.pass1_only and flagged:
        print(f"\n=== Pass 2: Deep Trace (Opus) -- {len(flagged)} functions ===")
        deep_results = run_pass2_deep_trace(flagged)
        for r in deep_results:
            print(f"  [{r.severity}] {r.step.function_name}: {r.recommendation[:80]}")

    # Gherkin quality inspection
    gherkin_issues: list[GherkinQualityIssue] = []
    if args.gherkin_quality:
        print(f"\n=== Gherkin Quality Inspection (Sonnet) -- {len(scenarios)} scenarios ===")
        gherkin_issues = run_gherkin_quality(scenarios)
        print(f"  {len(gherkin_issues)} specification quality issues found")

    # Generate report
    generate_report(all_steps, triage_results, deep_results, gherkin_issues, args.output)
    print(f"\nReport written to {args.output}")


if __name__ == "__main__":
    main()
