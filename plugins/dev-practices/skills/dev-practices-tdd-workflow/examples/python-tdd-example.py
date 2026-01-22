"""
Complete TDD Example: Email Validator

This file demonstrates a full TDD cycle from start to finish.

Requirement:
Create an email validator that:
1. Returns True for valid email addresses
2. Returns False for invalid email addresses
3. Valid format: local@domain.tld (simplified RFC 5322)
4. Must have exactly one @ symbol
5. Must have non-empty local and domain parts
6. Domain must contain at least one dot
"""

# =============================================================================
# STEP 1: WRITE FAILING TEST
# =============================================================================

import pytest


# First test - will fail because function doesn't exist yet
def test_valid_email_returns_true():
    """Test valid email returns True.

    Requirement: Valid email format returns True.
    Given a properly formatted email, when validated, then returns True.
    """
    result = is_valid_email("user@example.com")
    assert result is True


# Run: pytest examples/python-tdd-example.py -v
# Expected: FAILED - NameError: name 'is_valid_email' is not defined


# =============================================================================
# STEP 2: IMPLEMENT MINIMUM CODE TO PASS
# =============================================================================


def is_valid_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    # Minimum implementation to make first test pass
    return True


# Run: pytest examples/python-tdd-example.py::test_valid_email_returns_true -v
# Expected: PASSED


# =============================================================================
# STEP 3: WRITE NEXT FAILING TEST
# =============================================================================


def test_empty_email_returns_false():
    """Test empty email returns False.

    Requirement: Invalid emails return False.
    Given empty string, when validated, then returns False.
    """
    result = is_valid_email("")
    assert result is False


# Run: pytest examples/python-tdd-example.py::test_empty_email_returns_false -v
# Expected: FAILED - assertion error (function returns True for everything)


# =============================================================================
# STEP 4: UPDATE CODE TO PASS NEW TEST
# =============================================================================


def is_valid_email_v2(email: str) -> bool:
    """Validate email address format (version 2)."""
    # Now check for empty string
    if not email:
        return False
    return True


# Update test to use v2
def test_empty_email_v2():
    result = is_valid_email_v2("")
    assert result is False


def test_valid_email_v2():
    result = is_valid_email_v2("user@example.com")
    assert result is True


# Run: pytest examples/python-tdd-example.py -k "v2" -v
# Expected: BOTH PASS


# =============================================================================
# STEP 5: ADD MORE TESTS (CONTINUE TDD CYCLE)
# =============================================================================


def test_email_without_at_returns_false():
    """Test email without @ returns False.

    Requirement: Must contain exactly one @ symbol.
    Given email without @, when validated, then returns False.
    """
    result = is_valid_email_v3("userexample.com")
    assert result is False


def test_email_with_multiple_at_returns_false():
    """Test email with multiple @ returns False.

    Requirement: Must contain exactly one @ symbol.
    Given email with multiple @, when validated, then returns False.
    """
    result = is_valid_email_v3("user@@example.com")
    assert result is False


# =============================================================================
# STEP 6: IMPLEMENT TO PASS NEW TESTS
# =============================================================================


def is_valid_email_v3(email: str) -> bool:
    """Validate email address format (version 3)."""
    if not email:
        return False

    # Check for exactly one @ symbol
    if email.count("@") != 1:
        return False

    return True


# Verify all tests pass
def test_valid_email_v3():
    result = is_valid_email_v3("user@example.com")
    assert result is True


def test_empty_email_v3():
    result = is_valid_email_v3("")
    assert result is False


# Run: pytest examples/python-tdd-example.py -k "v3" -v
# Expected: ALL PASS


# =============================================================================
# STEP 7: ADD TESTS FOR DOMAIN VALIDATION
# =============================================================================


def test_email_with_empty_local_part_returns_false():
    """Test email with empty local part returns False.

    Requirement: Local part must be non-empty.
    Given email like @example.com, when validated, then returns False.
    """
    result = is_valid_email_v4("@example.com")
    assert result is False


def test_email_with_empty_domain_returns_false():
    """Test email with empty domain returns False.

    Requirement: Domain must be non-empty.
    Given email like user@, when validated, then returns False.
    """
    result = is_valid_email_v4("user@")
    assert result is False


def test_email_with_no_dot_in_domain_returns_false():
    """Test email without dot in domain returns False.

    Requirement: Domain must contain at least one dot.
    Given email like user@example, when validated, then returns False.
    """
    result = is_valid_email_v4("user@example")
    assert result is False


# =============================================================================
# STEP 8: IMPLEMENT COMPLETE VALIDATION
# =============================================================================


def is_valid_email_v4(email: str) -> bool:
    """Validate email address format (version 4 - complete)."""
    if not email:
        return False

    # Check for exactly one @ symbol
    if email.count("@") != 1:
        return False

    # Split into local and domain parts
    local, domain = email.split("@")

    # Validate local part is non-empty
    if not local:
        return False

    # Validate domain is non-empty and contains dot
    if not domain or "." not in domain:
        return False

    return True


# Comprehensive test suite
def test_valid_email_v4():
    result = is_valid_email_v4("user@example.com")
    assert result is True


def test_empty_email_v4():
    result = is_valid_email_v4("")
    assert result is False


def test_no_at_v4():
    result = is_valid_email_v4("userexample.com")
    assert result is False


def test_multiple_at_v4():
    result = is_valid_email_v4("user@@example.com")
    assert result is False


def test_empty_local_v4():
    result = is_valid_email_v4("@example.com")
    assert result is False


def test_empty_domain_v4():
    result = is_valid_email_v4("user@")
    assert result is False


def test_no_dot_in_domain_v4():
    result = is_valid_email_v4("user@example")
    assert result is False


# Run: pytest examples/python-tdd-example.py -k "v4" -v
# Expected: ALL 7 TESTS PASS


# =============================================================================
# STEP 9: REFACTOR (KEEPING TESTS GREEN)
# =============================================================================


def is_valid_email_final(email: str) -> bool:
    """Validate email address format (final refactored version).

    Args:
        email: Email address to validate

    Returns:
        True if email matches simplified RFC 5322 format, False otherwise

    Validates:
    - Non-empty email
    - Exactly one @ symbol
    - Non-empty local part
    - Non-empty domain with at least one dot
    """
    # Early return for empty input
    if not email:
        return False

    # Validate @ symbol count
    if email.count("@") != 1:
        return False

    # Destructure and validate parts
    local, domain = email.split("@")

    # Validate local part
    if not local:
        return False

    # Validate domain (must exist and contain dot)
    if not domain or "." not in domain:
        return False

    return True


# =============================================================================
# STEP 10: PARAMETERIZED TESTS (BONUS)
# =============================================================================


@pytest.mark.parametrize(
    "email,expected",
    [
        # Valid cases
        ("user@example.com", True),
        ("test.user@example.com", True),
        ("user+tag@example.co.uk", True),
        # Invalid cases - empty
        ("", False),
        # Invalid cases - @ issues
        ("userexample.com", False),
        ("user@@example.com", False),
        ("user@example@com", False),
        # Invalid cases - missing parts
        ("@example.com", False),
        ("user@", False),
        # Invalid cases - domain without dot
        ("user@example", False),
    ],
)
def test_email_validation_comprehensive(email, expected):
    """Comprehensive email validation test.

    Requirement: Email validator handles all specified cases.
    Tests valid formats and various invalid formats.
    """
    result = is_valid_email_final(email)
    assert result == expected


# Run: pytest examples/python-tdd-example.py::test_email_validation_comprehensive -v
# Expected: ALL PARAMETERIZED CASES PASS (11 test cases)


# =============================================================================
# STEP 11: DEMONSTRATE SACRED RULE - NEVER ADJUST TESTS
# =============================================================================


def test_example_sacred_rule_violation():
    """Example: What NOT to do when test fails.

    Scenario: Developer implements is_valid_email_broken that incorrectly
    returns True for emails without dots in domain.
    """
    # This test is based on requirement
    email = "user@example"  # No dot in domain

    # Test expects False (per requirements)
    expected = False

    # But broken implementation returns True
    result = is_valid_email_broken(email)

    # ❌ WRONG RESPONSE: "I'll adjust the test to expect True"
    # ✅ CORRECT RESPONSE: "Code is wrong - fixing implementation"

    assert result == expected  # Test stays unchanged!


def is_valid_email_broken(email: str) -> bool:
    """Broken implementation (for demonstration).

    Bug: Doesn't check for dot in domain.
    """
    if not email or email.count("@") != 1:
        return False

    local, domain = email.split("@")

    # BUG: Missing dot check
    if not local or not domain:
        return False

    return True  # Returns True even without dot in domain


# Run: pytest examples/python-tdd-example.py::test_example_sacred_rule_violation -v
# Expected: FAILED
# Action: Fix is_valid_email_broken, NOT the test


# =============================================================================
# SUMMARY: TDD CYCLE DEMONSTRATED
# =============================================================================

"""
TDD Cycle Summary:

1. Write failing test (test_valid_email_returns_true)
2. Write minimum code to pass (return True)
3. Write next test (test_empty_email_returns_false)
4. Update code to pass (check for empty)
5. Continue cycle:
   - Test for @ symbol
   - Test for local/domain parts
   - Test for dot in domain
6. Refactor with tests as safety net
7. Add parameterized tests for comprehensive coverage
8. Demonstrate sacred rule: never adjust tests to match code

Key Principles Demonstrated:
- Tests derived from requirements
- Write failing test first
- Minimum code to pass
- Refactor with green tests
- Tests define contract
- Code must match tests, not vice versa
"""

# Run full test suite:
# pytest examples/python-tdd-example.py -v

# Run with coverage:
# pytest examples/python-tdd-example.py --cov=. --cov-report=term-missing
