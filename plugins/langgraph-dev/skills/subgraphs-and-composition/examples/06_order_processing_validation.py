"""
Example 06: E-commerce Order Processing Validation System

This production-like example validates all 4 epic concepts with comprehensive
testing:
1. Compiled graphs as nodes (all 4 subgraphs)
2. Communication (fraud/notification share state, inventory/payment transform)
3. State management (explicit mapping for inventory and payment)
4. Reusable components (factory function for fraud detector)

Includes unit tests for each subgraph and integration tests for full pipeline.
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
import operator


# ============================================================================
# STATE SCHEMAS
# ============================================================================

class OrderState(TypedDict):
    """Parent state schema for order processing (shared with some subgraphs)."""
    order_id: str
    customer_id: str
    items: list[dict]  # [{"product_id": str, "quantity": int, "price": float}]
    total_amount: float
    status: str  # pending, fraud_check, inventory_check, payment, completed, failed
    fraud_score: float  # 0.0 = safe, 1.0 = fraudulent
    inventory_available: bool
    payment_successful: bool
    notifications_sent: list[str]


class InventoryState(TypedDict):
    """Different schema for inventory checking subgraph."""
    product_ids: list[str]
    quantities: dict[str, int]  # product_id → quantity needed
    availability: dict[str, bool]  # product_id → available
    all_available: bool


class PaymentState(TypedDict):
    """Different schema for payment processing subgraph."""
    amount: float
    customer_id: str
    payment_method: str
    transaction_id: str
    success: bool
    error_message: str


# ============================================================================
# CONCEPT 4: Reusable Components - Fraud Detector Factory
# ============================================================================

def create_fraud_detector(rules: dict):
    """
    Factory function for creating fraud detection subgraphs.

    Demonstrates CONCEPT 4: Reusable component via factory pattern.

    Args:
        rules: Dictionary with threshold values for fraud detection
    """

    def check_fraud(state: OrderState) -> dict:
        """Assess fraud risk based on configurable rules."""
        fraud_score = 0.0

        # Rule 1: High amount threshold
        if state["total_amount"] > rules.get("max_amount", 10000):
            fraud_score += 0.4

        # Rule 2: Too many items
        total_items = sum(item["quantity"] for item in state["items"])
        if total_items > rules.get("max_items", 10):
            fraud_score += 0.3

        # Rule 3: Customer history (mock check)
        if state["customer_id"] in rules.get("flagged_customers", []):
            fraud_score += 0.5

        print(f"  Fraud Detector → Score: {fraud_score:.2f}")

        return {
            "fraud_score": fraud_score,
            "status": "inventory_check" if fraud_score < 0.5 else "failed"
        }

    subgraph = StateGraph(OrderState)
    subgraph.add_node("assess", check_fraud)
    subgraph.add_edge(START, "assess")
    subgraph.add_edge("assess", END)

    return subgraph.compile()


# ============================================================================
# CONCEPT 3: Different Schema - Inventory Checker
# ============================================================================

def check_stock(state: InventoryState) -> dict:
    """
    Check inventory availability for all products.

    This subgraph has a different state schema.
    """
    # Mock inventory database
    mock_inventory = {
        "PROD-001": 100,
        "PROD-002": 50,
        "PROD-003": 0,  # Out of stock
        "PROD-004": 25
    }

    availability = {}
    for product_id, needed in state["quantities"].items():
        available_qty = mock_inventory.get(product_id, 0)
        availability[product_id] = available_qty >= needed

    all_available = all(availability.values())

    print(f"  Inventory Checker → All available: {all_available}")

    return {
        "availability": availability,
        "all_available": all_available
    }


def create_inventory_checker():
    """Create inventory checking subgraph with different schema."""
    subgraph = StateGraph(InventoryState)
    subgraph.add_node("check", check_stock)
    subgraph.add_edge(START, "check")
    subgraph.add_edge("check", END)

    return subgraph.compile()


# ============================================================================
# CONCEPT 3: Different Schema - Payment Processor
# ============================================================================

def process_payment_transaction(state: PaymentState) -> dict:
    """
    Process payment transaction.

    This subgraph has a different state schema.
    """
    # Mock payment processing
    success = state["amount"] < 5000  # Payments over $5000 fail (mock)

    transaction_id = f"TXN-{state['customer_id']}-{int(state['amount'])}"
    error_message = "" if success else "Payment declined by provider"

    print(f"  Payment Processor → Success: {success}")

    return {
        "transaction_id": transaction_id,
        "success": success,
        "error_message": error_message
    }


def create_payment_processor():
    """Create payment processing subgraph with different schema."""
    subgraph = StateGraph(PaymentState)
    subgraph.add_node("process", process_payment_transaction)
    subgraph.add_edge(START, "process")
    subgraph.add_edge("process", END)

    return subgraph.compile()


# ============================================================================
# CONCEPT 2: Shared Schema - Notification Dispatcher
# ============================================================================

def send_notifications(state: OrderState) -> dict:
    """
    Send notifications based on order status.

    This subgraph shares the OrderState schema.
    """
    notifications = []

    if state["status"] == "completed":
        notifications.append(f"Order {state['order_id']} confirmed")
        notifications.append(f"Payment processed: ${state['total_amount']:.2f}")
    elif state["status"] == "failed":
        notifications.append(f"Order {state['order_id']} failed")

    print(f"  Notification Dispatcher → Sent {len(notifications)} notifications")

    return {"notifications_sent": notifications}


def create_notification_dispatcher():
    """Create notification subgraph with shared schema."""
    subgraph = StateGraph(OrderState)
    subgraph.add_node("send", send_notifications)
    subgraph.add_edge(START, "send")
    subgraph.add_edge("send", END)

    return subgraph.compile()


# ============================================================================
# CONCEPT 1 & 3: Parent Graph with State Mapping Wrappers
# ============================================================================

def initialize_order(state: OrderState) -> dict:
    """Initialize order processing."""
    print(f"→ Order Processor: Processing order {state['order_id']}")
    return {"status": "fraud_check"}


def create_inventory_wrapper():
    """Wrapper for inventory checker (different schema)."""
    checker = create_inventory_checker()

    def check_inventory(state: OrderState) -> dict:
        """CONCEPT 3: State transformation for inventory checking."""
        # Transform OrderState → InventoryState
        product_ids = [item["product_id"] for item in state["items"]]
        quantities = {item["product_id"]: item["quantity"] for item in state["items"]}

        inventory_input = {
            "product_ids": product_ids,
            "quantities": quantities,
            "availability": {},
            "all_available": False
        }

        # Invoke subgraph
        result = checker.invoke(inventory_input)

        # Transform back to OrderState
        return {
            "inventory_available": result["all_available"],
            "status": "payment" if result["all_available"] else "failed"
        }

    return check_inventory


def create_payment_wrapper():
    """Wrapper for payment processor (different schema)."""
    processor = create_payment_processor()

    def process_payment(state: OrderState) -> dict:
        """CONCEPT 3: State transformation for payment processing."""
        # Transform OrderState → PaymentState
        payment_input = {
            "amount": state["total_amount"],
            "customer_id": state["customer_id"],
            "payment_method": "credit_card",
            "transaction_id": "",
            "success": False,
            "error_message": ""
        }

        # Invoke subgraph
        result = processor.invoke(payment_input)

        # Transform back to OrderState
        return {
            "payment_successful": result["success"],
            "status": "completed" if result["success"] else "failed"
        }

    return process_payment


def create_order_processor():
    """
    Create the main order processing workflow.

    Demonstrates CONCEPT 1: Adding compiled graphs as nodes.
    """
    # Create subgraphs
    fraud_detector = create_fraud_detector(rules={
        "max_amount": 1000,
        "max_items": 10,
        "flagged_customers": ["CUST-999"]
    })
    inventory_wrapper = create_inventory_wrapper()
    payment_wrapper = create_payment_wrapper()
    notification_dispatcher = create_notification_dispatcher()

    # Create parent graph
    processor = StateGraph(OrderState)

    # CONCEPT 1: Add compiled graphs and wrappers as nodes
    processor.add_node("init", initialize_order)
    processor.add_node("fraud", fraud_detector)  # Shared schema
    processor.add_node("inventory", inventory_wrapper)  # Wrapper for different schema
    processor.add_node("payment", payment_wrapper)  # Wrapper for different schema
    processor.add_node("notify", notification_dispatcher)  # Shared schema

    # Define routing logic
    def route_after_fraud(state: OrderState) -> Literal["inventory", "notify"]:
        """Route based on fraud check."""
        return "inventory" if state["status"] == "inventory_check" else "notify"

    def route_after_inventory(state: OrderState) -> Literal["payment", "notify"]:
        """Route based on inventory check."""
        return "payment" if state["status"] == "payment" else "notify"

    def route_after_payment(state: OrderState) -> Literal["notify"]:
        """Always proceed to notifications."""
        return "notify"

    # Build graph
    processor.add_edge(START, "init")
    processor.add_edge("init", "fraud")
    processor.add_conditional_edges("fraud", route_after_fraud)
    processor.add_conditional_edges("inventory", route_after_inventory)
    processor.add_conditional_edges("payment", route_after_payment)
    processor.add_edge("notify", END)

    return processor.compile()


# ============================================================================
# UNIT TESTS
# ============================================================================

def test_fraud_detector():
    """Unit test for fraud detector subgraph."""
    print("\n--- Unit Test: Fraud Detector ---")

    detector = create_fraud_detector(rules={"max_amount": 500, "max_items": 5})

    # Test 1: Normal order (should pass)
    result = detector.invoke({
        "order_id": "TEST-001",
        "customer_id": "CUST-001",
        "items": [{"product_id": "PROD-001", "quantity": 2, "price": 100}],
        "total_amount": 200,
        "status": "pending",
        "fraud_score": 0.0,
        "inventory_available": False,
        "payment_successful": False,
        "notifications_sent": []
    })

    assert result["fraud_score"] < 0.5, "Normal order should pass fraud check"
    assert result["status"] == "inventory_check", "Should proceed to inventory"
    print("✓ Test 1 passed: Normal order")

    # Test 2: High amount (should flag)
    result = detector.invoke({
        "order_id": "TEST-002",
        "customer_id": "CUST-001",
        "items": [{"product_id": "PROD-001", "quantity": 1, "price": 1000}],
        "total_amount": 1000,
        "status": "pending",
        "fraud_score": 0.0,
        "inventory_available": False,
        "payment_successful": False,
        "notifications_sent": []
    })

    assert result["fraud_score"] >= 0.4, "High amount should increase fraud score"
    print("✓ Test 2 passed: High amount detection")


def test_inventory_checker():
    """Unit test for inventory checker subgraph."""
    print("\n--- Unit Test: Inventory Checker ---")

    checker = create_inventory_checker()

    # Test: Available inventory
    result = checker.invoke({
        "product_ids": ["PROD-001", "PROD-002"],
        "quantities": {"PROD-001": 10, "PROD-002": 5},
        "availability": {},
        "all_available": False
    })

    assert result["all_available"] == True, "Should have available inventory"
    print("✓ Test passed: Inventory available")


def test_payment_processor():
    """Unit test for payment processor subgraph."""
    print("\n--- Unit Test: Payment Processor ---")

    processor = create_payment_processor()

    # Test: Successful payment
    result = processor.invoke({
        "amount": 100.00,
        "customer_id": "CUST-001",
        "payment_method": "credit_card",
        "transaction_id": "",
        "success": False,
        "error_message": ""
    })

    assert result["success"] == True, "Payment should succeed"
    assert result["transaction_id"] != "", "Should have transaction ID"
    print("✓ Test passed: Successful payment")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_successful_order():
    """Integration test: Successful order flow."""
    print("\n--- Integration Test: Successful Order ---")

    processor = create_order_processor()

    result = processor.invoke({
        "order_id": "ORD-001",
        "customer_id": "CUST-001",
        "items": [
            {"product_id": "PROD-001", "quantity": 2, "price": 50.00},
            {"product_id": "PROD-002", "quantity": 1, "price": 75.00}
        ],
        "total_amount": 175.00,
        "status": "pending",
        "fraud_score": 0.0,
        "inventory_available": False,
        "payment_successful": False,
        "notifications_sent": []
    })

    assert result["status"] == "completed", "Order should complete successfully"
    assert result["fraud_score"] < 0.5, "Should pass fraud check"
    assert result["inventory_available"] == True, "Inventory should be available"
    assert result["payment_successful"] == True, "Payment should succeed"
    assert len(result["notifications_sent"]) > 0, "Should send notifications"

    print("✓ Integration test passed: Successful order")


def test_fraud_rejection():
    """Integration test: Order rejected due to fraud."""
    print("\n--- Integration Test: Fraud Rejection ---")

    processor = create_order_processor()

    result = processor.invoke({
        "order_id": "ORD-002",
        "customer_id": "CUST-001",
        "items": [{"product_id": "PROD-001", "quantity": 50, "price": 100.00}],
        "total_amount": 5000.00,  # High amount + many items = fraud
        "status": "pending",
        "fraud_score": 0.0,
        "inventory_available": False,
        "payment_successful": False,
        "notifications_sent": []
    })

    assert result["status"] == "failed", "Order should fail fraud check"
    assert result["fraud_score"] >= 0.5, "Should have high fraud score"

    print("✓ Integration test passed: Fraud rejection")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all tests and demonstrations."""
    print("=" * 70)
    print("Order Processing Validation System")
    print("=" * 70)

    # Run unit tests
    test_fraud_detector()
    test_inventory_checker()
    test_payment_processor()

    # Run integration tests
    test_successful_order()
    test_fraud_rejection()

    print("\n" + "=" * 70)
    print("✓ All tests passed successfully!")
    print("=" * 70)
    print("\n🎯 All 4 Epic Concepts Validated:")
    print("  1. ✓ Compiled graphs as nodes (4 subgraphs + wrappers)")
    print("  2. ✓ Communication (fraud/notify shared, inventory/payment different)")
    print("  3. ✓ State management (wrappers for inventory & payment)")
    print("  4. ✓ Reusable components (fraud detector factory)")


if __name__ == "__main__":
    main()
