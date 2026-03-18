---
name: tdd-workflow
description: This skill should be used when the user asks to "use TDD", "test-driven development", "write tests first", "red green refactor", "never adjust tests to match code", "fix a bug with TDD", "refactor with tests", "how should I write tests", "test first development", "testing workflow", "write code with tests", "tests before code", mentions "tests define requirements", or discusses test-driven development workflow. Provides comprehensive 4-step TDD loop with sacred rule enforcement that tests are grounded in requirements. Integrates with beads workflow during implementation phase.
version: 0.1.0
---

# TDD Workflow Skill

## Overview

This skill is typically used as part of the broader development workflow managed by the beads plugin (`/beads:workflow`). TDD is the core implementation practice within Step 3 (Claim & Work) of the beads workflow, providing the requirements → tests → implementation cycle.

---

## GOLDEN RULE: Tests Are Grounded in Requirements

**Core Principle**: Tests are derived from **requirements documentation**, not implementation details or guesswork.

**When implementation doesn't match tests**: Implementation is wrong.

**When tests seem illogical**: Requirements need clarification with the user.

**NEVER adjust tests to match code** - tests define the contract that code must fulfill.

---

## The 4-Step TDD Loop

### Step 1: Write Failing Test First

**Ground test in requirements**:
1. Review requirements documentation for acceptance criteria
2. Identify specific, testable requirement
3. Write test that validates that requirement
4. Run test - verify it FAILS (proving test is actually testing something)

**Pattern - Arrange, Act, Assert**:
```
def test_feature_behavior():
    """Test feature behavior.

    Requirement: [Reference to requirement document]
    Given [precondition], when [action], then [expected outcome].
    """
    # Arrange - Set up test conditions from requirements
    input = prepare_test_input()

    # Act - Execute behavior under test
    result = function_under_test(input)

    # Assert - Verify requirement is met
    assert result == expected_value_from_requirements
```

**Verify test FAILS**: A test that passes before implementation exists is either:
- Testing nothing (false positive)
- Testing existing code (not new functionality)

---

### Step 2: Implement Minimum Code to Pass Test

**Write ONLY enough code** to make the test pass:
- Implement exactly what requirements specify
- No extra features
- No premature optimization
- No "nice to have" additions

**Anti-patterns to avoid**:
- Adding features not in requirements
- Optimizing before it works
- Implementing "obvious" future features
- Over-engineering the solution

---

### Step 3: Verify Test Passes

Run test suite and verify:
1. New test PASSES
2. All existing tests STILL PASS
3. No regressions introduced

**If test fails**: Fix the code, not the test (unless requirements actually changed).

---

### Step 4: Refactor (Optional)

**Improve code quality** while keeping tests green:
- Extract duplicated code
- Improve naming for clarity
- Simplify complex logic
- Add type annotations/documentation
- Apply design patterns

**After EACH refactoring step**:
1. Run full test suite
2. Verify ALL tests still pass
3. If tests fail, revert or fix the refactoring

**Rule**: Tests must remain green throughout refactoring.

---

## Sacred Rule: NEVER Adjust Tests to Match Code

### When Test Fails During Implementation

**Only two valid responses**:

#### ✅ CORRECT Response
"Test expects X, code produces Y. **Code is wrong - fixing implementation.**"

#### ❌ FORBIDDEN Response
"Test expects X, code produces Y. **Adjusting test to expect Y.**"

---

### When Tests Seem Wrong

**If test expectations seem illogical or incorrect**:

1. **STOP** - Do NOT adjust the test
2. **Review requirements** - Is requirement actually wrong?
3. **Ask user** to clarify requirements
4. **Wait for confirmation** - Only change test if requirements document is updated

**Red flag phrases that require user confirmation**:
- "I'll adjust the test to match..."
- "Updating test expectations..."
- "The test needs to expect..."
- "Let me fix the test..."

**Example**:
```
# Test expects function to return 3 items
# Code returns 4 items

❌ WRONG: "I'll update the test to expect 4 items"
   (Assumes code is correct, test is wrong)

✅ CORRECT: "Test expects 3 items per requirement, code returns 4.
             Investigating why code produces extra item."
   (Assumes test reflects requirements, code has bug)
```

---

## Quick Workflows

### Write Tests for New Feature

1. **Review requirements** - Find acceptance criteria in requirements documentation
2. **Plan tests** - Derive test cases from each acceptance criterion
3. **Write first failing test** - Implement one test case
4. **Verify FAILS** - Run test, confirm failure
5. **Implement minimum code** - Make test pass
6. **Verify PASSES** - Run test, confirm success
7. **Repeat** - Continue with next acceptance criterion
8. **Refactor** - Clean up code while keeping tests green

---

### Fix Bug with TDD

1. **Write regression test** - Create test that reproduces bug (should FAIL)
2. **Verify test FAILS** - Confirms test actually catches the bug
3. **Fix the code** - Implement fix
4. **Verify test PASSES** - Confirms bug is fixed
5. **Keep test** - Regression test prevents bug from returning

---

### Refactor Existing Code

1. **Verify tests pass** - BEFORE refactoring, all tests must be green
2. **Refactor incrementally** - Small changes, run tests frequently
3. **Verify tests still pass** - AFTER each change
4. **If tests fail** - Either revert refactoring or fix the bug introduced
5. **Never adjust tests** - Unless requirements actually changed

---

## Test Execution Requirements

### Before Every Commit

Run fast test suite to catch regressions:
```bash
# Run unit and integration tests (mocked dependencies)
pytest tests/ -v -m "not slow and not e2e"

# Or run quality gates (includes tests + linting + type checking)
make quality
```

**All tests must pass** before committing code.

---

### Before Pull Request

Run full test suite including slow/expensive tests:
```bash
pytest tests/ -v
```

Ensures no regressions in any test category.

---

### During Development

Run test frequently:
- After writing new test (should FAIL)
- After implementing code (should PASS)
- After each refactoring step (should stay PASS)

**Fast feedback loop** = better productivity.

---

## Test Coverage Guidelines

**Coverage is NOT completeness**:
- 90% code coverage ≠ all requirements tested
- Coverage measures code execution, not requirement validation

**Use coverage to find gaps**:
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

Shows untested code paths that might need tests.

**But verify requirements coverage separately**:
- Check each acceptance criterion has corresponding test
- Verify edge cases from requirements are tested
- Ensure test names/docstrings reference requirements

---

## Common Anti-Patterns

### Writing Tests After Code

**Problem**: Tests become implementation tests, not requirement tests.

**Solution**: Always write test BEFORE code. Test defines what code must do.

---

### Adjusting Tests to Match Code

**Problem**: Defeats purpose of TDD - code now defines requirements instead of vice versa.

**Solution**: If test fails, fix code. Only adjust test if requirements actually changed (user confirmed).

---

### Testing Implementation Details

**Problem**: Tests break when refactoring, even though behavior unchanged.

**Solution**: Test public API and behavior, not internal implementation.

---

### Writing Multiple Tests Before Implementing

**Problem**: Lose fast feedback, harder to debug when multiple tests fail.

**Solution**: Write ONE test, implement, verify pass, then write NEXT test.

---

### Skipping Failing Test Verification

**Problem**: Test might be broken or not testing anything.

**Solution**: Always run test and verify it FAILS before implementing.

---

## References

### Language-Specific Patterns
See `references/language-patterns.md` for examples in:
- Python (pytest)
- JavaScript (Jest)
- Go (testing package)
- Generic patterns

### Advanced TDD Techniques
See `references/advanced-tdd.md` for:
- Testing strategy by code type
- Parameterized testing
- Test doubles (mocks, stubs, fakes)
- Integration vs unit testing
- Coverage requirements

### Working Examples
See `examples/` directory for:
- Complete TDD cycles in different languages
- Bug fix with regression test
- Refactoring with test safety net

---

## Key Principles Summary

1. **Requirements First**: Tests derive from requirements, not implementation guesses
2. **Fail Then Pass**: Write failing test, then make it pass with minimum code
3. **Tests Define Contract**: If test fails, code is wrong (unless requirements changed)
4. **Never Adjust Tests**: Only change tests when requirements actually change
5. **Fast Feedback**: Run tests frequently during development
6. **Green Refactoring**: Only refactor when all tests pass, keep them passing
7. **One Test at a Time**: Write one test, implement, pass, then next test
8. **Coverage ≠ Completeness**: Use coverage to find gaps, but verify requirements separately

---

## When to Ask for Clarification

**Ask user to clarify requirements when**:
- Test expectations seem illogical
- Requirements document is ambiguous
- Multiple valid interpretations exist
- Edge cases not specified

**Do NOT**:
- Assume code is right and test is wrong
- Adjust tests without user confirmation
- Implement features not in requirements
- Skip tests because requirements are unclear

**Remember**: Unclear requirements = stop and ask, don't guess.
