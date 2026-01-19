# LangGraph Subgraph Composition Examples

This directory contains 6 runnable examples demonstrating subgraph composition patterns in LangGraph 1.x.

## Prerequisites

### Environment Setup

```bash
# Navigate to the skill directory
cd langgraph-dev/skills/subgraphs-and-composition

# Create isolated test environment
uv init --no-readme --no-workspace test-env
cd test-env

# Install dependencies
uv add langgraph langchain-core

# Verify installation
uv run python -c "import langgraph; print(f'LangGraph version: {langgraph.__version__}')"
```

### Expected Versions

- **LangGraph**: 1.0.6+
- **LangChain Core**: 1.2.7+
- **Python**: 3.12+

## Running Examples

### Quick Run

```bash
# From test-env directory
uv run python ../examples/01_basic_subgraph_shared_state.py
```

### All Examples

```bash
# Run all examples in sequence
for file in ../examples/*.py; do
    echo "Running $(basename $file)..."
    uv run python "$file"
    echo "---"
done
```

## Example 01: Basic Subgraph with Shared State

**File**: `01_basic_subgraph_shared_state.py` (~170 lines)

### Purpose

Demonstrates the simplest subgraph pattern: adding a compiled `StateGraph` as a node when parent and child share the same state schema (`MessagesState`).

### Key Concepts

- Compiled graphs are callable and can be used as nodes
- Shared `MessagesState` schema requires no transformation
- Subgraph modifies state that flows back to parent

### What It Demonstrates

- Creating a sentiment analysis subgraph
- Integrating subgraph into chatbot parent graph
- Direct composition without wrapper functions

### How to Run

```bash
uv run python ../examples/01_basic_subgraph_shared_state.py
```

### Expected Output

```
→ Chatbot: Processing message 'I'm having a wonderful day!'
  Sentiment Analyzer → Detected: positive
  Response Generator → Generated response using positive sentiment

Final Conversation:
HumanMessage: I'm having a wonderful day!
SystemMessage: [Sentiment Analysis: positive]
AIMessage: That's great to hear! How can I help you today?
```

### What to Learn

- How to create a simple subgraph with `MessagesState`
- How to add a compiled graph as a node
- How state flows automatically between parent and child

## Example 02: Subgraph with Different Schema

**File**: `02_subgraph_different_schema.py` (~180 lines)

### Purpose

Demonstrates state transformation when parent and child have different state schemas.

### Key Concepts

- Wrapper functions bridge different schemas
- Transformation: ParentState → ChildState → ParentState
- Partial state extraction and aggregation

### What It Demonstrates

- Document processing subgraph with `DocumentState`
- Parent workflow with `WorkflowState`
- Batch processing through state transformation

### How to Run

```bash
uv run python ../examples/02_subgraph_different_schema.py
```

### Expected Output

```
→ Document Processor: Processing batch of 4 documents
  Document Processor → Processed: "The quick brown fox..." (9 words)
  Document Processor → Processed: "LangGraph enables..." (12 words)
  Document Processor → Processed: "Subgraphs..." (3 words)
  Document Processor → Processed: "State transformation..." (19 words)

Workflow Results:
- Processed 4 documents
- Total word count: 43 words
- Average words per document: 10.8
```

### What to Learn

- How to create wrapper functions for schema transformation
- How to batch process through a subgraph
- How to aggregate results back to parent state

## Example 03: Multi-Level Nesting

**File**: `03_multi_level_nesting.py` (~190 lines)

### Purpose

Demonstrates hierarchical composition with 3 levels: parent → child → grandchild.

### Key Concepts

- Subgraphs can contain other subgraphs
- State flows through multiple levels
- Each level processes and adds to state

### What It Demonstrates

- Parent: Research Coordinator
- Child: Topic Analyzer (contains grandchild)
- Grandchild: Keyword Extractor

### How to Run

```bash
uv run python ../examples/03_multi_level_nesting.py
```

### Expected Output

```
→ Research Coordinator: Analyzing query
  Topic Analyzer (Level 2) → Identified topic: AI
  Keyword Extractor (Level 3) → Extracted: machine, learning, algorithms
  Research Planner → Generated research plan

Final Analysis:
- Topic: AI
- Keywords: machine, learning, algorithms
- Research Plan: [Plan based on AI topic]
```

### What to Learn

- How to nest subgraphs recursively
- How state propagates through multiple levels
- When to use deep hierarchies vs flat composition

## Example 04: Graph Factory Pattern

**File**: `04_graph_factory_pattern.py` (~240 lines)

### Purpose

Demonstrates factory functions for creating reusable, configurable subgraph components.

### Key Concepts

- Factory functions accept configuration parameters
- Same factory creates different validators
- Component library pattern

### What It Demonstrates

- `create_validator_subgraph(name, rules)` factory
- Length, profanity, and format validators
- Configurable validation rules

### How to Run

```bash
uv run python ../examples/04_graph_factory_pattern.py
```

### Expected Output

```
--- Validation Pipeline ---
  Length Validator: ✓ PASS
  Profanity Validator: ✓ PASS
  Format Validator: ✓ PASS

→ Content Validator: All checks passed
Status: approved

--- Testing Edge Cases ---
  Length Validator: ✗ FAIL (too short)
  Format Validator: ✗ FAIL (missing [REVIEW] prefix)
  Profanity Validator: ✗ FAIL (contains "spam")
```

### What to Learn

- How to create factory functions for reusable components
- How to parametrize subgraph behavior
- How to build component libraries

## Example 05: Complete Support System

**File**: `05_complete_support_system.py` (~250 lines)

### Purpose

**Production-ready example** demonstrating all 4 core concepts in one cohesive multi-agent system.

### Key Concepts

1. **Compiled graphs as nodes** - 3 subgraphs integrated
2. **Shared schema** - Intent classifier and response generator use `MessagesState`
3. **Different schema** - Knowledge retriever uses `RetrievalState` with wrapper
4. **Factory pattern** - Intent classifier created with configurable intents

### What It Demonstrates

- Customer support workflow
- Intent classification → Knowledge retrieval → Response generation
- State transformation between different schemas
- Factory-created components

### How to Run

```bash
uv run python ../examples/05_complete_support_system.py
```

### Expected Output

```
→ Support System: Initialized session session-001
  Intent Classifier → Detected: billing
  Knowledge Retriever → Found 3 articles for billing
  Response Generator → Generated response

--- Conversation ---
HumanMessage: How do I get a refund?
AIMessage: Here's what I found:

1. Billing: We charge on the 1st of each month
2. Billing: You can update payment methods in Settings → Billing
3. Billing: Refunds are processed within 5-7 business days

Is there anything else I can help you with?
```

### What to Learn

- How all 4 concepts work together
- Production-ready system architecture
- Best practices for multi-agent composition

**Note**: Detailed documentation in `references/complete-examples.md`.

## Example 06: Order Processing Validation System

**File**: `06_order_processing_validation.py` (~380 lines)

### Purpose

**Production-like system** with unit tests and integration tests, demonstrating validation and testing strategies.

### Key Concepts

- 4 subgraphs: fraud detection, inventory checking, payment processing, notifications
- Unit tests for each subgraph
- Integration tests for full pipeline
- Error handling and routing

### What It Demonstrates

- E-commerce order processing workflow
- Parallel and sequential subgraph execution
- Comprehensive testing approach
- Production-ready error handling

### How to Run

```bash
uv run python ../examples/06_order_processing_validation.py
```

### Expected Output

```
======================================================================
Order Processing Validation System
======================================================================

--- Unit Test: Fraud Detector ---
  Fraud Detector → Score: 0.00
✓ Test 1 passed: Normal order
  Fraud Detector → Score: 0.40
✓ Test 2 passed: High amount detection

--- Unit Test: Inventory Checker ---
  Inventory Checker → All available: True
✓ Test passed: Inventory available

--- Unit Test: Payment Processor ---
  Payment Processor → Success: True
✓ Test passed: Successful payment

--- Integration Test: Successful Order ---
→ Order Processor: Processing order ORD-001
  Fraud Detector → Score: 0.00
  Inventory Checker → All available: True
  Payment Processor → Success: True
  Notification Dispatcher → Sent 2 notifications
✓ Integration test passed: Successful order

--- Integration Test: Fraud Rejection ---
→ Order Processor: Processing order ORD-002
  Fraud Detector → Score: 0.70
  Notification Dispatcher → Sent 1 notifications
✓ Integration test passed: Fraud rejection

======================================================================
✓ All tests passed successfully!
======================================================================

🎯 All 4 Epic Concepts Validated:
  1. ✓ Compiled graphs as nodes (4 subgraphs + wrappers)
  2. ✓ Communication (fraud/notify shared, inventory/payment different)
  3. ✓ State management (wrappers for inventory & payment)
  4. ✓ Reusable components (fraud detector factory)
```

### What to Learn

- How to structure production-like systems
- How to test subgraphs independently (unit tests)
- How to test full workflows (integration tests)
- How to handle errors and routing

## Progression Path

Recommended learning order:

1. **Start**: Example 01 (basic shared state)
2. **Next**: Example 02 (different schemas)
3. **Then**: Example 03 (multi-level nesting)
4. **After**: Example 04 (factory pattern)
5. **Study**: Example 05 (complete system - all concepts)
6. **Advanced**: Example 06 (production testing patterns)

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'langgraph'`

**Solution**:
```bash
# Ensure you're in test-env directory
cd test-env

# Re-install dependencies
uv add langgraph langchain-core

# Verify
uv run python -c "import langgraph; print('OK')"
```

### Version Mismatch

**Problem**: Examples fail with API errors

**Solution**:
```bash
# Check versions
uv run python -c "import langgraph; print(langgraph.__version__)"

# Should be 1.0.6+, if not:
uv add langgraph@latest langchain-core@latest
```

### Syntax Errors

**Problem**: `SyntaxError: invalid syntax`

**Solution**:
- Ensure Python 3.12+ is being used
- Check UV is using correct Python version: `uv run python --version`

### StateGraph Not Found

**Problem**: `ImportError: cannot import name 'StateGraph'`

**Solution**:
```bash
# LangGraph 1.x uses different imports than 0.x
# Verify you have 1.x: uv run python -c "import langgraph; print(langgraph.__version__)"
```

## Additional Resources

- **SKILL.md**: Core concepts and quick reference
- **references/core-patterns.md**: Pattern catalog with 11 patterns
- **references/complete-examples.md**: Detailed documentation of Example 05
- **references/best-practices.md**: Best practices with good/bad examples
- **LangGraph Docs**: [https://docs.langchain.com/oss/python/langgraph/use-subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)

## Verification

All examples have been verified to execute successfully:

| Example | Exit Code | Status |
|---------|-----------|--------|
| 01_basic_subgraph_shared_state.py | 0 | ✅ PASS |
| 02_subgraph_different_schema.py | 0 | ✅ PASS |
| 03_multi_level_nesting.py | 0 | ✅ PASS |
| 04_graph_factory_pattern.py | 0 | ✅ PASS |
| 05_complete_support_system.py | 0 | ✅ PASS |
| 06_order_processing_validation.py | 0 | ✅ PASS (all tests) |

**Test Environment**:
- UV: 0.7.14
- Python: 3.12.7
- LangGraph: 1.0.6
- LangChain Core: 1.2.7
- Date: 2026-01-13
