# Verification Patterns Reference

Language-specific verification patterns for session completion.

---

## Overview

Before committing code, run verification steps to ensure:
- Code style consistency (linters)
- Type correctness (type checkers)
- Functionality (tests)
- No regressions

---

## Python Projects

### Standard Verification

```bash
# Using Makefile (recommended)
make quality

# Or manual commands
ruff check .                # Linting + formatting
mypy src/                   # Type checking
pytest tests/ -v            # Tests
```

### Auto-Fix Issues

```bash
# Auto-fix safe violations
ruff check --fix .

# Format code
ruff format .

# Fix import sorting
ruff check --fix --select I .
```

### Configuration Files

**pyproject.toml** (Ruff):
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "PLR", "PLC", "PLE"]
ignore = []

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["PLR2004"]  # Magic numbers OK in tests
```

**pyproject.toml** (MyPy):
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
strict_optional = true
```

### Common Violations

**Complexity issues**:
```python
# PLR0915: Too many statements
# Fix: Extract to smaller functions

# C901: Too complex
# Fix: Simplify logic, use early returns

# PLR0913: Too many arguments
# Fix: Use Pydantic models or dataclasses
```

**Type issues**:
```python
# Missing return type
def process(data: dict) -> dict[str, object]:
    return {"result": data}

# Using Any explicitly
# Fix: Use specific types or object
from typing import Any  # Avoid
def process(data: dict[str, str]) -> dict[str, object]:
    ...
```

---

## JavaScript/TypeScript Projects

### Standard Verification

```bash
# Using npm scripts
npm run lint                # ESLint
npm run type-check          # TypeScript
npm test                    # Jest/Vitest
npm run build               # Build verification
```

### Auto-Fix Issues

```bash
# Auto-fix ESLint issues
npm run lint -- --fix

# Format with Prettier
npm run format

# Fix specific file
npx eslint src/file.ts --fix
```

### Configuration Files

**.eslintrc.js**:
```javascript
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'prettier'
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module'
  },
  rules: {
    'no-console': 'warn',
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/explicit-function-return-type': 'warn'
  }
}
```

**tsconfig.json**:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

**package.json scripts**:
```json
{
  "scripts": {
    "lint": "eslint src --ext .ts,.tsx",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "format": "prettier --write src/**/*.{ts,tsx}",
    "quality": "npm run lint && npm run type-check && npm test"
  }
}
```

---

## Rust Projects

### Standard Verification

```bash
# Using cargo
cargo fmt --check           # Formatting
cargo clippy                # Linting
cargo test                  # Tests
cargo build                 # Build verification
```

### Auto-Fix Issues

```bash
# Auto-format
cargo fmt

# Auto-fix clippy warnings (some)
cargo clippy --fix
```

### Configuration Files

**Cargo.toml**:
```toml
[package]
name = "my-project"
version = "0.1.0"
edition = "2021"

[dependencies]
# ... dependencies ...

[dev-dependencies]
# ... dev dependencies ...

[profile.dev]
opt-level = 0

[profile.release]
opt-level = 3
lto = true
```

**.clippy.toml**:
```toml
# Clippy configuration
cognitive-complexity-threshold = 10
```

### Common Issues

```rust
// Unused variables
let x = 5;  // Warning: unused variable
// Fix: Prefix with underscore or remove
let _x = 5;

// Missing error handling
let result = file.read_to_string(&mut contents);  // Warning
// Fix: Use ? or handle error
let result = file.read_to_string(&mut contents)?;

// Unnecessary clone
let s = my_string.clone();
process(s);
// Fix: Move or borrow
process(my_string);
```

---

## Go Projects

### Standard Verification

```bash
# Using go tools
go fmt ./...                # Formatting
go vet ./...                # Linting
golangci-lint run           # Additional linting
go test ./...               # Tests
go build                    # Build verification
```

### Auto-Fix Issues

```bash
# Auto-format
go fmt ./...

# Fix imports
goimports -w .
```

### Configuration Files

**.golangci.yml**:
```yaml
linters:
  enable:
    - gofmt
    - govet
    - errcheck
    - staticcheck
    - unused
    - gosimple
    - ineffassign

linters-settings:
  gofmt:
    simplify: true
  govet:
    check-shadowing: true

issues:
  exclude-use-default: false
```

**Makefile**:
```makefile
.PHONY: quality
quality:
	go fmt ./...
	go vet ./...
	golangci-lint run
	go test ./... -v
```

### Common Issues

```go
// Unused imports
import (
    "fmt"  // Warning: imported but not used
)
// Fix: Remove or use

// Error not checked
file, _ := os.Open("file.txt")  // Warning
// Fix: Handle error
file, err := os.Open("file.txt")
if err != nil {
    return err
}

// Variable shadowing
func example() {
    x := 1
    if true {
        x := 2  // Warning: shadows variable
        fmt.Println(x)
    }
}
// Fix: Rename or use assignment
```

---

## Ruby Projects

### Standard Verification

```bash
# Using RuboCop
rubocop                     # Linting + formatting
rspec                       # Tests
bundle exec rails test      # Rails tests
```

### Auto-Fix Issues

```bash
# Auto-fix safe violations
rubocop -a

# Auto-fix including unsafe
rubocop -A
```

### Configuration Files

**.rubocop.yml**:
```yaml
AllCops:
  TargetRubyVersion: 3.2
  NewCops: enable

Style/StringLiterals:
  EnforcedStyle: double_quotes

Layout/LineLength:
  Max: 120

Metrics/MethodLength:
  Max: 20

Metrics/BlockLength:
  Exclude:
    - 'spec/**/*'
```

**Gemfile**:
```ruby
group :development, :test do
  gem 'rubocop'
  gem 'rubocop-rails'
  gem 'rspec-rails'
end
```

---

## Java Projects

### Standard Verification

```bash
# Using Maven
mvn checkstyle:check        # Code style
mvn test                    # Tests
mvn verify                  # Full verification

# Using Gradle
./gradlew check             # All checks
./gradlew test              # Tests
./gradlew build             # Build + tests
```

### Auto-Fix Issues

```bash
# Using Google Java Format
java -jar google-java-format.jar --replace src/**/*.java
```

### Configuration Files

**checkstyle.xml**:
```xml
<?xml version="1.0"?>
<!DOCTYPE module PUBLIC
  "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
  "https://checkstyle.org/dtds/configuration_1_3.dtd">

<module name="Checker">
  <module name="TreeWalker">
    <module name="LineLength">
      <property name="max" value="120"/>
    </module>
    <module name="MethodLength">
      <property name="max" value="50"/>
    </module>
  </module>
</module>
```

**pom.xml** (Maven):
```xml
<build>
  <plugins>
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-checkstyle-plugin</artifactId>
      <version>3.3.0</version>
    </plugin>
  </plugins>
</build>
```

---

## CI/CD Integration

### GitHub Actions

**Python**:
```yaml
name: Quality Gates
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install ruff mypy pytest
      - run: ruff check .
      - run: mypy src/
      - run: pytest tests/
```

**JavaScript/TypeScript**:
```yaml
name: Quality Gates
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm test
```

**Rust**:
```yaml
name: Quality Gates
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - run: cargo fmt --check
      - run: cargo clippy
      - run: cargo test
```

---

## Pre-commit Hooks

### Python

**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
```

### JavaScript/TypeScript

**.husky/pre-commit**:
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npm run lint
npm run type-check
npm test -- --bail --findRelatedTests
```

### Multi-language

**.git/hooks/pre-commit**:
```bash
#!/bin/bash
set -e

echo "Running quality gates..."

# Python
if [ -f "pyproject.toml" ]; then
    ruff check .
    mypy src/
    pytest tests/ -m "not slow"
fi

# JavaScript/TypeScript
if [ -f "package.json" ]; then
    npm run lint
    npm run type-check
    npm test -- --bail
fi

# Rust
if [ -f "Cargo.toml" ]; then
    cargo fmt --check
    cargo clippy
    cargo test
fi

echo "✅ All quality gates passed!"
```

---

## References

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [ESLint Documentation](https://eslint.org/docs/latest/)
- [Clippy Documentation](https://doc.rust-lang.org/clippy/)
- [GolangCI-Lint Documentation](https://golangci-lint.run/)
- [RuboCop Documentation](https://rubocop.org/)
- [Checkstyle Documentation](https://checkstyle.org/)
