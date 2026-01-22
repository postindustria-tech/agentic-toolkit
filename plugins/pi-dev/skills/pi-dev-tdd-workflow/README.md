# TDD Workflow Skill

A universal, reusable skill for Test-Driven Development (TDD) following the red-green-refactor cycle.

## Overview

This skill provides comprehensive guidance for TDD across multiple programming languages and contexts. It emphasizes the **Golden Rule**: tests are grounded in requirements, not implementation guesses.

## Structure

```
tdd-workflow/
├── SKILL.md                      # Main skill file (use this)
├── README.md                     # This file
├── examples/                     # Working code examples
│   ├── python-tdd-example.py     # Complete Python/pytest TDD cycle
│   └── javascript-tdd-example.js # Complete JavaScript/Jest TDD cycle
└── references/                   # Deep-dive documentation
    ├── language-patterns.md      # Language-specific patterns
    └── advanced-tdd.md           # Advanced techniques
```

## Quick Start

### Invoking the Skill

The skill triggers when users mention:
- "use TDD"
- "test-driven development"
- "write tests first"
- "red green refactor"
- "never adjust tests to match code"
- "fix a bug with TDD"
- "refactor with tests"

### Core Principles

1. **Requirements First**: Tests derive from requirements documentation
2. **Fail Then Pass**: Write failing test, then make it pass
3. **Tests Define Contract**: If test fails, code is wrong (unless requirements changed)
4. **Never Adjust Tests**: Only change tests when requirements actually change
5. **Fast Feedback**: Run tests frequently
6. **Green Refactoring**: Only refactor when tests pass

## The 4-Step TDD Loop

```
1. RED: Write failing test
   ↓
2. GREEN: Write minimum code to pass
   ↓
3. VERIFY: Run tests (should pass)
   ↓
4. REFACTOR: Improve code (keep tests green)
   ↓
   Repeat
```

## Sacred Rule: Never Adjust Tests to Match Code

**When test fails during implementation**:

✅ **CORRECT**: "Code is wrong - fixing implementation"

❌ **FORBIDDEN**: "Adjusting test to match code"

**Exception**: Only adjust test if requirements **actually changed** (user confirmed).

## File Descriptions

### SKILL.md

Main skill file containing:
- Golden Rule (tests grounded in requirements)
- 4-step TDD loop
- Sacred Rule enforcement
- Quick workflows
- Key principles

**Use this file** when applying TDD workflow.

### examples/python-tdd-example.py

Complete Python TDD example showing:
- Email validator implementation
- Step-by-step TDD cycle
- Red-Green-Refactor pattern
- Parameterized tests
- Sacred Rule demonstration

**Run**: `pytest examples/python-tdd-example.py -v`

### examples/javascript-tdd-example.js

Complete JavaScript TDD example showing:
- Shopping cart implementation
- Jest testing patterns
- Feature development with TDD
- Refactoring with test safety net
- Sacred Rule demonstration

**Run**: `npm test -- javascript-tdd-example.js`

### references/language-patterns.md

Language-specific test patterns for:
- Python (pytest)
- JavaScript (Jest)
- TypeScript (Jest)
- Go (testing package)
- Generic patterns

Includes:
- Basic test structure
- Parameterized tests
- Mocking strategies
- Async testing
- Best practices

### references/advanced-tdd.md

Advanced TDD techniques:
- Testing strategy by code type
- Test doubles (mocks, stubs, fakes)
- Parameterized testing
- Integration vs unit testing
- Coverage requirements
- Property-based testing
- Test organization

## Usage Examples

### New Feature Development

```
1. Review requirements in documentation
2. Plan tests from acceptance criteria
3. Write first failing test
4. Implement minimum code to pass
5. Verify test passes
6. Repeat for next criterion
7. Refactor when all tests green
```

### Bug Fix

```
1. Write regression test (should FAIL)
2. Verify test reproduces bug
3. Fix the code
4. Verify test PASSES
5. Keep test as regression guard
```

### Refactoring

```
1. Ensure all tests PASS before starting
2. Make small refactoring change
3. Run tests (should still PASS)
4. If tests fail, revert or fix
5. Repeat until refactoring complete
```

## Integration with Project Workflows

This skill is framework-agnostic and can integrate with:
- Beads workflow (task tracking)
- Quality gates (pre-commit checks)
- CI/CD pipelines (automated testing)
- Documentation requirements

## Version History

- **0.1.0** (2026-01-20): Initial extraction from imagefactory-v2 project
  - Universal skill structure
  - Multi-language examples
  - Sacred Rule enforcement
  - Comprehensive references

## License

Part of the pi-dev plugin for Claude Code plugin development.

## Contributing

When updating this skill:
1. Keep SKILL.md focused and actionable
2. Add detailed examples to `examples/`
3. Move complex topics to `references/`
4. Maintain language-agnostic principles
5. Update version number in frontmatter
