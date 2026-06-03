#!/usr/bin/env python3
"""Structural wiring guard for the `code-review --targeted` in-loop scan (PROC-3).

Proves the targeted single-disease scan is actually WIRED IN and callable --
not just a markdown file nobody invokes. Exits non-zero (listing every gap) if
any wiring condition is unmet, so it can run as a phase-gate / CI check.

Checks:
  (a) skills/code-review/SKILL.md documents the `--targeted` mode + arg contract.
  (b) agents/review-disease-scan.md exists (the purpose-built disease-scan agent).
  (c) both molecule formulas (task-execute.yaml, bug-triage.yaml) reference
      `code-review --targeted` in their codebase-scan atom.
  (d) the codebase-scan atom makes the `.claude/code-review/<ticket-id>/`
      disposition artifact a requirement of the gate (structural un-skippability).

Run: python3 check_targeted_wiring.py   (from anywhere; paths resolve from here)
"""

from __future__ import annotations

import pathlib
import sys

# scripts/ -> code-review/ -> skills/ -> dev-practices/ (plugin root)
PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL_MD = PLUGIN_ROOT / "skills" / "code-review" / "SKILL.md"
AGENT_MD = PLUGIN_ROOT / "agents" / "review-disease-scan.md"
FORMULAS = [
    PLUGIN_ROOT / "skills" / "execute" / "formulas" / "task-execute.yaml",
    PLUGIN_ROOT / "skills" / "execute" / "formulas" / "bug-triage.yaml",
]


def _check() -> list[str]:
    problems: list[str] = []

    # (a) SKILL.md documents the --targeted mode + arg contract.
    if not SKILL_MD.exists():
        problems.append(f"missing {SKILL_MD}")
    else:
        text = SKILL_MD.read_text()
        if "--targeted" not in text:
            problems.append("code-review SKILL.md does not document the `--targeted` mode")
        if "review-disease-scan" not in text:
            problems.append(
                "code-review SKILL.md does not reference the review-disease-scan agent "
                "for targeted mode"
            )

    # (b) the purpose-built agent exists.
    if not AGENT_MD.exists():
        problems.append(f"missing agent definition {AGENT_MD}")

    # (c) both formulas' codebase-scan atom invokes the targeted mode.
    for formula in FORMULAS:
        if not formula.exists():
            problems.append(f"missing formula {formula}")
            continue
        ftext = formula.read_text()
        if "code-review --targeted" not in ftext:
            problems.append(
                f"{formula.name} codebase-scan atom does not invoke "
                "`code-review --targeted`"
            )
        # (d) structural artifact-existence gate.
        if ".claude/code-review/" not in ftext:
            problems.append(
                f"{formula.name} does not require the .claude/code-review/<ticket-id>/ "
                "disposition artifact (gate is not structurally un-skippable)"
            )

    return problems


def main() -> int:
    problems = _check()
    if problems:
        print("code-review --targeted wiring INCOMPLETE (PROC-3):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("code-review --targeted wiring OK: mode + agent + both formulas + artifact gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
