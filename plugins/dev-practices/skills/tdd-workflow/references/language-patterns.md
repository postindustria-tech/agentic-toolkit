# TDD Language-Specific Patterns

## Python (pytest)

### Basic Test Structure

```python
import pytest

def test_function_name():
    """Test description.

    Requirement: [Reference to requirement]
    Given [condition], when [action], then [expected result].
    """
    # Arrange
    input_data = prepare_input()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_value
```

### Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("valid_input", "valid_output"),
    ("edge_case", "edge_output"),
    ("empty", None),
])
def test_multiple_cases(input, expected):
    """Test function with multiple input cases.

    Requirement: Function handles various input types.
    """
    result = function_under_test(input)
    assert result == expected
```

### Using Fixtures

```python
@pytest.fixture
def sample_data():
    """Prepare reusable test data."""
    return {"key": "value", "count": 42}

def test_with_fixture(sample_data):
    """Test using fixture for setup."""
    result = process_data(sample_data)
    assert result["count"] == 42
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mock(monkeypatch):
    """Test function with mocked external API.

    Requirement: Function handles API responses correctly.
    """
    # Arrange - mock external dependency
    mock_api = Mock(return_value={"status": "success"})
    monkeypatch.setattr("module.external_api_call", mock_api)

    # Act
    result = function_that_calls_api()

    # Assert
    assert result["status"] == "success"
    mock_api.assert_called_once()
```

### Testing Exceptions

```python
def test_function_raises_error():
    """Test function raises appropriate error.

    Requirement: Function validates input and raises ValueError for invalid data.
    """
    with pytest.raises(ValueError, match="invalid input"):
        function_under_test(invalid_input)
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function behavior.

    Requirement: Async function processes data correctly.
    """
    # Arrange
    input_data = {"id": 1}

    # Act
    result = await async_function(input_data)

    # Assert
    assert result["processed"] is True
```

---

## JavaScript (Jest)

### Basic Test Structure

```javascript
describe('functionName', () => {
  test('should return expected value', () => {
    // Requirement: [Reference to requirement]
    // Given [condition], when [action], then [expected result]

    // Arrange
    const input = 'test input';

    // Act
    const result = functionUnderTest(input);

    // Assert
    expect(result).toBe('expected output');
  });
});
```

### Parameterized Tests

```javascript
describe('functionName with multiple inputs', () => {
  test.each([
    ['input1', 'output1'],
    ['input2', 'output2'],
    ['edge_case', null],
  ])('given %s, returns %s', (input, expected) => {
    const result = functionUnderTest(input);
    expect(result).toBe(expected);
  });
});
```

### Setup and Teardown

```javascript
describe('Feature tests', () => {
  let testData;

  beforeEach(() => {
    // Setup before each test
    testData = { count: 0 };
  });

  afterEach(() => {
    // Cleanup after each test
    testData = null;
  });

  test('should increment count', () => {
    incrementCount(testData);
    expect(testData.count).toBe(1);
  });
});
```

### Mocking Functions

```javascript
describe('function with dependencies', () => {
  test('should call external API', async () => {
    // Requirement: Function calls API with correct parameters

    // Arrange - create mock
    const mockFetch = jest.fn().mockResolvedValue({
      json: () => Promise.resolve({ status: 'success' })
    });
    global.fetch = mockFetch;

    // Act
    const result = await functionThatCallsAPI();

    // Assert
    expect(result.status).toBe('success');
    expect(mockFetch).toHaveBeenCalledWith('/api/endpoint');
  });
});
```

### Testing Exceptions

```javascript
test('should throw error for invalid input', () => {
  // Requirement: Function validates input

  expect(() => {
    functionUnderTest(invalidInput);
  }).toThrow('invalid input');
});
```

### Async Tests

```javascript
test('should handle async operation', async () => {
  // Requirement: Async function processes data correctly

  // Arrange
  const input = { id: 1 };

  // Act
  const result = await asyncFunction(input);

  // Assert
  expect(result.processed).toBe(true);
});
```

---

## Go (testing package)

### Basic Test Structure

```go
package mypackage

import "testing"

func TestFunctionName(t *testing.T) {
    // Requirement: [Reference to requirement]
    // Given [condition], when [action], then [expected result]

    // Arrange
    input := "test input"

    // Act
    result := FunctionUnderTest(input)

    // Assert
    expected := "expected output"
    if result != expected {
        t.Errorf("FunctionUnderTest(%q) = %q; want %q", input, result, expected)
    }
}
```

### Table-Driven Tests

```go
func TestMultipleCases(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
    }{
        {"valid input", "test", "result"},
        {"empty input", "", ""},
        {"edge case", "edge", "special"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Requirement: Function handles various inputs

            result := FunctionUnderTest(tt.input)

            if result != tt.expected {
                t.Errorf("got %q; want %q", result, tt.expected)
            }
        })
    }
}
```

### Testing with Interfaces (Dependency Injection)

```go
// Interface for external dependency
type DataStore interface {
    Get(key string) (string, error)
}

// Mock implementation
type MockDataStore struct {
    GetFunc func(key string) (string, error)
}

func (m *MockDataStore) Get(key string) (string, error) {
    return m.GetFunc(key)
}

func TestWithMock(t *testing.T) {
    // Requirement: Function retrieves data from store

    // Arrange - create mock
    mock := &MockDataStore{
        GetFunc: func(key string) (string, error) {
            return "mocked value", nil
        },
    }

    // Act
    result, err := FunctionThatUsesStore(mock, "key")

    // Assert
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if result != "mocked value" {
        t.Errorf("got %q; want %q", result, "mocked value")
    }
}
```

### Testing Error Cases

```go
func TestFunctionReturnsError(t *testing.T) {
    // Requirement: Function validates input and returns error

    // Act
    _, err := FunctionUnderTest(invalidInput)

    // Assert
    if err == nil {
        t.Error("expected error for invalid input; got nil")
    }

    expectedMsg := "invalid input"
    if err.Error() != expectedMsg {
        t.Errorf("error message = %q; want %q", err.Error(), expectedMsg)
    }
}
```

### Subtests

```go
func TestFeature(t *testing.T) {
    t.Run("success case", func(t *testing.T) {
        result := FunctionUnderTest(validInput)
        if result != expected {
            t.Errorf("got %v; want %v", result, expected)
        }
    })

    t.Run("error case", func(t *testing.T) {
        _, err := FunctionUnderTest(invalidInput)
        if err == nil {
            t.Error("expected error; got nil")
        }
    })
}
```

---

## TypeScript (Jest)

### Basic Test Structure

```typescript
describe('functionName', () => {
  it('should return expected value', () => {
    // Requirement: [Reference to requirement]
    // Given [condition], when [action], then [expected result]

    // Arrange
    const input: string = 'test input';

    // Act
    const result: string = functionUnderTest(input);

    // Assert
    expect(result).toBe('expected output');
  });
});
```

### Testing with Type Safety

```typescript
interface TestData {
  id: number;
  name: string;
}

describe('typed function', () => {
  it('should process typed data', () => {
    // Requirement: Function processes data with type safety

    // Arrange
    const input: TestData = { id: 1, name: 'test' };

    // Act
    const result = processData(input);

    // Assert
    expect(result.id).toBe(1);
    expect(result.name).toBe('test');
  });
});
```

### Mocking with Type Support

```typescript
import { jest } from '@jest/globals';

describe('function with typed mock', () => {
  it('should call API with correct types', async () => {
    // Requirement: Function calls typed API

    // Arrange
    const mockFetch = jest.fn<typeof fetch>().mockResolvedValue({
      json: () => Promise.resolve({ status: 'success' }),
    } as Response);

    global.fetch = mockFetch;

    // Act
    const result = await callTypedAPI();

    // Assert
    expect(result.status).toBe('success');
    expect(mockFetch).toHaveBeenCalled();
  });
});
```

---

## Generic Patterns (Language-Agnostic)

### Test Structure Template

```
test "feature behavior":
  # Requirement: [Reference to requirement doc]
  # Given [precondition], when [action], then [expected outcome]

  # Arrange - Set up test conditions
  input = prepare_test_data()

  # Act - Execute behavior under test
  result = function_under_test(input)

  # Assert - Verify expected outcome
  assert result equals expected_value
```

### Naming Convention

**Pattern**: `test_<function>_<scenario>_<expected_result>`

**Examples**:
- `test_calculate_total_with_valid_input_returns_sum`
- `test_parse_json_with_invalid_json_raises_error`
- `test_authenticate_user_with_wrong_password_returns_false`

### Test Organization

```
tests/
├── unit/              # Pure functions, isolated components
├── integration/       # Multiple components working together
├── e2e/               # Full user workflows
└── fixtures/          # Reusable test data
```

### Given-When-Then Pattern

```
Given [initial context/precondition]
When [action/event occurs]
Then [expected outcome/behavior]

Example:
Given user is logged in
When user clicks logout button
Then user session is terminated and redirect to login page
```

### Arrange-Act-Assert Pattern

```
# Arrange - Set up test preconditions
# Act - Execute the behavior being tested
# Assert - Verify expected outcome

More explicit about test phases than Given-When-Then.
```

---

## Best Practices Across Languages

### 1. Clear Test Names

**Good**: `test_calculate_discount_applies_20_percent_for_premium_users`

**Bad**: `test_discount` or `test1`

### 2. One Assert Per Test (Guideline)

Prefer focused tests that verify one behavior:

```python
# Good - focused
def test_user_registration_creates_user():
    user = register_user(email, password)
    assert user is not None

def test_user_registration_sends_email():
    register_user(email, password)
    assert email_was_sent(email)

# Acceptable - related assertions
def test_user_registration():
    user = register_user(email, password)
    assert user is not None
    assert user.email == email
```

### 3. Test Data Builders

Create reusable builders for complex test data:

```python
class UserBuilder:
    def __init__(self):
        self.email = "default@example.com"
        self.role = "user"

    def with_email(self, email):
        self.email = email
        return self

    def as_admin(self):
        self.role = "admin"
        return self

    def build(self):
        return User(email=self.email, role=self.role)

# Usage
def test_admin_access():
    user = UserBuilder().as_admin().build()
    assert user.can_access_admin_panel()
```

### 4. Isolation

Each test should be independent:
- No shared mutable state between tests
- No dependency on test execution order
- Clean setup and teardown

### 5. Fast Feedback

- Mock external dependencies (APIs, databases)
- Use in-memory alternatives for integration tests
- Separate fast tests from slow tests
- Run fast tests frequently, slow tests in CI
