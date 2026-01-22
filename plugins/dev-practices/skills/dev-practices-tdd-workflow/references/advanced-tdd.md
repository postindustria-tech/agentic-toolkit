# Advanced TDD Techniques

## Testing Strategy by Code Type

### Pure Functions

**Characteristics**:
- No side effects
- Same input always produces same output
- No external dependencies

**Testing approach**:
- Direct input/output testing
- Parameterized tests for edge cases
- No mocking needed

**Example**:
```python
# Pure function
def calculate_discount(price: float, discount_percent: float) -> float:
    return price * (1 - discount_percent / 100)

# Test
@pytest.mark.parametrize("price,discount,expected", [
    (100.0, 10.0, 90.0),
    (50.0, 20.0, 40.0),
    (100.0, 0.0, 100.0),
    (0.0, 10.0, 0.0),
])
def test_calculate_discount(price, discount, expected):
    """Test discount calculation for various inputs.

    Requirement: Discount applies percentage reduction to price.
    """
    result = calculate_discount(price, discount)
    assert result == pytest.approx(expected)
```

---

### Functions with External Dependencies

**Characteristics**:
- Calls APIs, databases, file systems
- Has side effects
- Non-deterministic behavior

**Testing approach**:
- Mock external dependencies
- Test behavior, not implementation
- Verify interactions with dependencies

**Example**:
```python
# Function with external dependency
def get_user_profile(user_id: str, api_client: APIClient) -> dict:
    response = api_client.get(f"/users/{user_id}")
    return response.json()

# Test with mock
def test_get_user_profile(monkeypatch):
    """Test user profile retrieval.

    Requirement: Fetches user data from API.
    """
    # Arrange - mock API client
    mock_response = Mock()
    mock_response.json.return_value = {"id": "123", "name": "Test User"}
    mock_client = Mock()
    mock_client.get.return_value = mock_response

    # Act
    profile = get_user_profile("123", mock_client)

    # Assert
    assert profile["id"] == "123"
    assert profile["name"] == "Test User"
    mock_client.get.assert_called_once_with("/users/123")
```

---

### Stateful Objects

**Characteristics**:
- Maintains internal state
- Behavior depends on history of operations
- State transitions

**Testing approach**:
- Test state transitions explicitly
- Verify invariants maintained
- Test edge cases in state machine

**Example**:
```python
# Stateful object
class ShoppingCart:
    def __init__(self):
        self.items = []

    def add_item(self, item, quantity=1):
        self.items.append({"item": item, "quantity": quantity})

    def total(self):
        return sum(i["item"]["price"] * i["quantity"] for i in self.items)

# Tests for state transitions
def test_cart_starts_empty():
    """Test initial cart state.

    Requirement: New cart has no items.
    """
    cart = ShoppingCart()
    assert len(cart.items) == 0
    assert cart.total() == 0

def test_cart_add_item_updates_state():
    """Test adding item changes cart state.

    Requirement: Adding item increases cart contents.
    """
    cart = ShoppingCart()
    item = {"name": "Widget", "price": 10.0}

    cart.add_item(item, quantity=2)

    assert len(cart.items) == 1
    assert cart.total() == 20.0
```

---

### Workflow/Graph Systems

**Characteristics**:
- Multiple steps/nodes
- Conditional routing
- State transformations

**Testing approach**:
- Test each node in isolation (unit tests)
- Test routing logic separately
- Test full workflows (integration tests)
- Mock expensive operations

**Example**:
```python
# Node function
def validate_input_node(state: WorkflowState) -> dict:
    if not state["input"]:
        return {"error": "Input required"}
    return {"validated_input": state["input"]}

# Unit test for node
def test_validate_input_node_with_valid_input():
    """Test validation node with valid input.

    Requirement: Validation passes valid input through.
    """
    state = {"input": "test data"}
    result = validate_input_node(state)
    assert result["validated_input"] == "test data"
    assert "error" not in result

# Integration test for workflow
def test_full_workflow_success(mock_external_api):
    """Test complete workflow execution.

    Requirement: Workflow processes input through all stages.
    """
    # Arrange
    input_state = {"input": "test data"}
    mock_external_api.process.return_value = {"result": "processed"}

    # Act
    final_state = run_workflow(input_state)

    # Assert
    assert final_state["result"] == "processed"
    assert final_state["error"] is None
```

---

## Test Doubles: Mocks, Stubs, Fakes

### Stub

**Purpose**: Provide predetermined responses.

**When to use**: Need to control return values from dependency.

**Example**:
```python
class StubDatabase:
    def get_user(self, user_id):
        # Always returns same test data
        return {"id": user_id, "name": "Test User"}

def test_with_stub():
    db = StubDatabase()
    user = db.get_user("123")
    assert user["name"] == "Test User"
```

---

### Mock

**Purpose**: Record interactions for verification.

**When to use**: Need to verify function called dependency correctly.

**Example**:
```python
def test_with_mock():
    # Mock records calls
    mock_emailer = Mock()

    # Function under test
    send_welcome_email("user@example.com", mock_emailer)

    # Verify interaction
    mock_emailer.send.assert_called_once_with(
        to="user@example.com",
        subject="Welcome",
        body=ANY
    )
```

---

### Fake

**Purpose**: Working implementation with shortcuts.

**When to use**: Need realistic behavior without external dependencies.

**Example**:
```python
class FakeDatabase:
    def __init__(self):
        self.data = {}

    def save(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)

def test_with_fake():
    """Test with in-memory fake database.

    Requirement: Data persists within transaction.
    """
    db = FakeDatabase()

    # Use like real database
    db.save("user:123", {"name": "Test"})
    user = db.get("user:123")

    assert user["name"] == "Test"
```

---

## Parameterized Testing

### Why Parameterized Tests

**Benefits**:
- Test multiple cases without duplication
- Clear documentation of edge cases
- Easy to add new test cases

### Python (pytest)

```python
@pytest.mark.parametrize("input,expected", [
    # Happy path
    ("valid@email.com", True),

    # Edge cases
    ("", False),
    ("no-at-sign", False),
    ("@no-local-part.com", False),
    ("no-domain@", False),

    # Special cases
    ("user+tag@domain.com", True),
    ("user.name@domain.co.uk", True),
])
def test_email_validation(input, expected):
    """Test email validation with various inputs.

    Requirement: Validates email format per RFC 5322.
    """
    result = is_valid_email(input)
    assert result == expected
```

### JavaScript (Jest)

```javascript
test.each([
  ['valid@email.com', true],
  ['', false],
  ['no-at-sign', false],
  ['@no-local-part.com', false],
])('validates email %s as %s', (input, expected) => {
  const result = isValidEmail(input);
  expect(result).toBe(expected);
});
```

### Go

```go
func TestEmailValidation(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected bool
    }{
        {"valid email", "valid@email.com", true},
        {"empty string", "", false},
        {"no at sign", "no-at-sign", false},
        {"no local part", "@no-local-part.com", false},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := IsValidEmail(tt.input)
            if result != tt.expected {
                t.Errorf("got %v; want %v", result, tt.expected)
            }
        })
    }
}
```

---

## Testing Async Code

### Python (pytest-asyncio)

```python
@pytest.mark.asyncio
async def test_async_data_fetch():
    """Test async data fetching.

    Requirement: Fetches data asynchronously without blocking.
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.fetch.return_value = {"data": "test"}

    # Act
    result = await fetch_data("endpoint", mock_client)

    # Assert
    assert result["data"] == "test"
    mock_client.fetch.assert_awaited_once()
```

### JavaScript (async/await)

```javascript
test('async data fetch', async () => {
  // Requirement: Fetches data asynchronously

  // Arrange
  const mockFetch = jest.fn().mockResolvedValue({
    json: () => Promise.resolve({ data: 'test' })
  });

  // Act
  const result = await fetchData('endpoint', mockFetch);

  // Assert
  expect(result.data).toBe('test');
  expect(mockFetch).toHaveBeenCalled();
});
```

---

## Integration Testing

### Unit vs Integration Tests

**Unit Test**:
- Tests single component in isolation
- Mocks all dependencies
- Fast execution
- High test count

**Integration Test**:
- Tests multiple components together
- Mocks only external services (APIs, databases)
- Slower execution
- Fewer tests, critical paths

### Example: Integration Test

```python
def test_user_registration_flow(test_db, mock_email_service):
    """Integration test for user registration.

    Requirement: Registration creates user and sends confirmation email.

    Components tested together:
    - UserService
    - Database (test database)
    - EmailService (mocked)
    """
    # Arrange
    user_service = UserService(db=test_db, emailer=mock_email_service)
    registration_data = {
        "email": "new@example.com",
        "password": "secure123"
    }

    # Act
    user = user_service.register(registration_data)

    # Assert - verify database interaction
    saved_user = test_db.get_user_by_email("new@example.com")
    assert saved_user is not None
    assert saved_user.email == "new@example.com"

    # Assert - verify email sent
    mock_email_service.send.assert_called_once()
    call_args = mock_email_service.send.call_args
    assert "confirmation" in call_args.kwargs["subject"].lower()
```

---

## Test Coverage Requirements

### Minimum Coverage Guidelines

**Critical components**: 90-100% coverage
- Security-related code
- Data validation
- Business logic
- Routing/control flow

**Standard components**: 80-90% coverage
- Feature implementation
- API endpoints
- Core utilities

**Lower priority**: 60-80% coverage
- UI components
- Configuration
- Scripts

### Coverage is NOT Completeness

**High coverage doesn't guarantee**:
- All requirements tested
- All edge cases covered
- Quality of assertions

**Example of poor test**:
```python
def test_process_data():
    """Test has 100% code coverage but poor assertions."""
    result = process_data({"input": "test"})
    assert result is not None  # Weak assertion!
```

**Better test**:
```python
def test_process_data_transforms_correctly():
    """Test with specific assertions based on requirements.

    Requirement: process_data converts input to uppercase.
    """
    result = process_data({"input": "test"})
    assert result["output"] == "TEST"  # Specific assertion
    assert result["error"] is None
```

### Using Coverage to Find Gaps

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Review report
open htmlcov/index.html

# Look for:
# - Untested error handling paths
# - Edge cases not covered
# - Dead code that can be removed
```

---

## Test Organization

### Directory Structure

```
tests/
├── unit/                    # Pure unit tests (fast, mocked)
│   ├── test_calculations.py
│   ├── test_validators.py
│   └── test_parsers.py
├── integration/             # Integration tests (medium speed)
│   ├── test_workflows.py
│   ├── test_api_endpoints.py
│   └── test_database.py
├── e2e/                     # End-to-end tests (slow, expensive)
│   ├── test_user_flows.py
│   └── test_critical_paths.py
├── fixtures/                # Reusable test data and builders
│   ├── __init__.py
│   ├── builders.py
│   └── sample_data.py
└── conftest.py              # Shared pytest fixtures
```

### Test Markers

Use markers to categorize and run specific test suites:

```python
# conftest.py or pytest.ini
pytest_configure = """
[pytest]
markers =
    unit: Unit tests (fast, mocked)
    integration: Integration tests (medium speed)
    slow: Tests with real external calls
    e2e: End-to-end tests
    smoke: Critical smoke tests
"""

# In test files
@pytest.mark.unit
def test_calculation():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_api_integration():
    pass

# Run specific categories
# pytest -m "unit"              # Fast tests only
# pytest -m "not slow"          # Exclude slow tests
# pytest -m "smoke"             # Critical tests only
```

---

## Common TDD Patterns

### Red-Green-Refactor Cycle

```
1. RED: Write failing test
   ↓
2. GREEN: Write minimum code to pass
   ↓
3. REFACTOR: Improve code while keeping tests green
   ↓
   Repeat
```

### Test-First Bug Fixing

```
1. Write test that reproduces bug (fails)
   ↓
2. Fix the code
   ↓
3. Verify test passes
   ↓
4. Keep test as regression test
```

### Outside-In TDD

**Start from user-facing interface, work inward**:

```
1. Write acceptance test (E2E, will fail)
   ↓
2. Write integration tests for components (will fail)
   ↓
3. Write unit tests for individual functions (will fail)
   ↓
4. Implement functions (unit tests pass)
   ↓
5. Integration tests pass
   ↓
6. Acceptance test passes
```

### Inside-Out TDD

**Start from low-level components, build up**:

```
1. Write unit test for utility function
   ↓
2. Implement function
   ↓
3. Write test for component using utility
   ↓
4. Implement component
   ↓
5. Write integration test
   ↓
6. Wire components together
```

---

## Advanced Assertions

### Property-Based Testing

Instead of specific examples, test properties that should always hold:

```python
from hypothesis import given, strategies as st

@given(st.integers(), st.integers())
def test_addition_is_commutative(a, b):
    """Property: a + b should equal b + a."""
    assert add(a, b) == add(b, a)

@given(st.lists(st.integers()))
def test_sorting_is_idempotent(lst):
    """Property: sorting twice should equal sorting once."""
    sorted_once = sorted(lst)
    sorted_twice = sorted(sorted_once)
    assert sorted_once == sorted_twice
```

### Snapshot Testing

Capture complex output and detect changes:

```python
def test_render_output_matches_snapshot(snapshot):
    """Test rendered output matches known-good snapshot.

    Requirement: Template rendering produces expected HTML.
    """
    result = render_template("user_profile.html", user=test_user)
    snapshot.assert_match(result)
```

### Fuzzing

Test with random/malformed input:

```python
import random
import string

def test_parser_handles_random_input():
    """Test parser doesn't crash on random input.

    Requirement: Parser gracefully handles invalid input.
    """
    for _ in range(100):
        # Generate random string
        random_input = ''.join(
            random.choices(string.printable, k=random.randint(0, 1000))
        )

        # Should not crash (may return error)
        try:
            result = parse(random_input)
        except ValueError:
            pass  # Expected for invalid input
```

---

## Resources

### Books
- "Test Driven Development: By Example" - Kent Beck
- "Growing Object-Oriented Software, Guided by Tests" - Freeman & Pryce

### Frameworks
- Python: pytest, unittest
- JavaScript: Jest, Mocha, Jasmine
- Go: testing package
- Java: JUnit, TestNG
- Ruby: RSpec, Minitest

### Tools
- Coverage: coverage.py, Istanbul, gcov
- Mocking: unittest.mock, Jest mocks, testify/mock
- Property testing: Hypothesis (Python), fast-check (JS)
- Mutation testing: mutmut (Python), Stryker (JS)
