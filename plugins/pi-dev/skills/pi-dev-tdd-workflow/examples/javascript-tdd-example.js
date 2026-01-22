/**
 * Complete TDD Example: Shopping Cart
 *
 * This file demonstrates a full TDD cycle from start to finish using Jest.
 *
 * Requirement:
 * Create a shopping cart that:
 * 1. Starts empty
 * 2. Allows adding items
 * 3. Calculates total price
 * 4. Applies discount codes
 * 5. Handles quantity updates
 */

// =============================================================================
// STEP 1: WRITE FAILING TEST
// =============================================================================

describe('ShoppingCart', () => {
  test('should start empty', () => {
    // Requirement: New cart has no items
    // Given a new cart, when created, then has zero items

    const cart = new ShoppingCart();

    expect(cart.getItemCount()).toBe(0);
  });
});

// Run: npm test -- javascript-tdd-example.js
// Expected: FAILED - ReferenceError: ShoppingCart is not defined


// =============================================================================
// STEP 2: IMPLEMENT MINIMUM CODE TO PASS
// =============================================================================

class ShoppingCart {
  constructor() {
    this.items = [];
  }

  getItemCount() {
    return this.items.length;
  }
}

// Run: npm test -- javascript-tdd-example.js
// Expected: PASSED


// =============================================================================
// STEP 3: WRITE NEXT FAILING TEST
// =============================================================================

describe('ShoppingCart - adding items', () => {
  test('should add item to cart', () => {
    // Requirement: Can add items to cart
    // Given a cart, when item added, then cart contains item

    const cart = new ShoppingCart();
    const item = { name: 'Widget', price: 10.00 };

    cart.addItem(item);

    expect(cart.getItemCount()).toBe(1);
  });
});

// Run: npm test
// Expected: FAILED - TypeError: cart.addItem is not a function


// =============================================================================
// STEP 4: IMPLEMENT addItem METHOD
// =============================================================================

class ShoppingCartV2 {
  constructor() {
    this.items = [];
  }

  getItemCount() {
    return this.items.length;
  }

  addItem(item) {
    this.items.push(item);
  }
}

// Update test to use v2
describe('ShoppingCartV2', () => {
  test('should start empty', () => {
    const cart = new ShoppingCartV2();
    expect(cart.getItemCount()).toBe(0);
  });

  test('should add item to cart', () => {
    const cart = new ShoppingCartV2();
    const item = { name: 'Widget', price: 10.00 };

    cart.addItem(item);

    expect(cart.getItemCount()).toBe(1);
  });
});

// Run: npm test
// Expected: BOTH TESTS PASS


// =============================================================================
// STEP 5: ADD TEST FOR TOTAL CALCULATION
// =============================================================================

describe('ShoppingCartV3 - total calculation', () => {
  test('should calculate total price', () => {
    // Requirement: Cart calculates total of all items
    // Given cart with items, when getTotal called, then returns sum

    const cart = new ShoppingCartV3();
    cart.addItem({ name: 'Widget', price: 10.00 });
    cart.addItem({ name: 'Gadget', price: 15.00 });

    const total = cart.getTotal();

    expect(total).toBe(25.00);
  });

  test('should return zero for empty cart', () => {
    // Requirement: Empty cart has zero total
    // Given empty cart, when getTotal called, then returns 0

    const cart = new ShoppingCartV3();

    expect(cart.getTotal()).toBe(0);
  });
});

// Run: npm test
// Expected: FAILED - TypeError: cart.getTotal is not a function


// =============================================================================
// STEP 6: IMPLEMENT getTotal METHOD
// =============================================================================

class ShoppingCartV3 {
  constructor() {
    this.items = [];
  }

  getItemCount() {
    return this.items.length;
  }

  addItem(item) {
    this.items.push(item);
  }

  getTotal() {
    return this.items.reduce((sum, item) => sum + item.price, 0);
  }
}

// Run: npm test
// Expected: ALL TESTS PASS


// =============================================================================
// STEP 7: ADD TEST FOR QUANTITY SUPPORT
// =============================================================================

describe('ShoppingCartV4 - quantities', () => {
  test('should handle item quantities', () => {
    // Requirement: Items can have quantities greater than 1
    // Given item with quantity, when added, then total reflects quantity

    const cart = new ShoppingCartV4();
    const item = { name: 'Widget', price: 10.00 };

    cart.addItem(item, 3);

    expect(cart.getTotal()).toBe(30.00);
  });

  test('should default to quantity of 1', () => {
    // Requirement: If quantity not specified, defaults to 1
    // Given item without quantity, when added, then quantity is 1

    const cart = new ShoppingCartV4();
    const item = { name: 'Widget', price: 10.00 };

    cart.addItem(item);

    expect(cart.getTotal()).toBe(10.00);
  });
});

// Run: npm test
// Expected: FAILED


// =============================================================================
// STEP 8: IMPLEMENT QUANTITY SUPPORT
// =============================================================================

class ShoppingCartV4 {
  constructor() {
    this.items = [];
  }

  getItemCount() {
    return this.items.length;
  }

  addItem(item, quantity = 1) {
    this.items.push({
      ...item,
      quantity: quantity
    });
  }

  getTotal() {
    return this.items.reduce((sum, item) => {
      return sum + (item.price * item.quantity);
    }, 0);
  }
}

// Run: npm test
// Expected: ALL TESTS PASS


// =============================================================================
// STEP 9: ADD DISCOUNT CODE FEATURE
// =============================================================================

describe('ShoppingCartV5 - discount codes', () => {
  test('should apply discount code', () => {
    // Requirement: Discount code reduces total by percentage
    // Given cart with items and 10% discount, when applied, then total reduced

    const cart = new ShoppingCartV5();
    cart.addItem({ name: 'Widget', price: 100.00 });

    cart.applyDiscount('SAVE10'); // 10% off

    expect(cart.getTotal()).toBe(90.00);
  });

  test('should handle invalid discount code', () => {
    // Requirement: Invalid codes don't change total
    // Given invalid code, when applied, then total unchanged

    const cart = new ShoppingCartV5();
    cart.addItem({ name: 'Widget', price: 100.00 });

    cart.applyDiscount('INVALID');

    expect(cart.getTotal()).toBe(100.00);
  });

  test('should only apply one discount', () => {
    // Requirement: Only one discount code can be active
    // Given existing discount, when new code applied, then replaces old

    const cart = new ShoppingCartV5();
    cart.addItem({ name: 'Widget', price: 100.00 });

    cart.applyDiscount('SAVE10'); // 10% off
    cart.applyDiscount('SAVE20'); // 20% off

    expect(cart.getTotal()).toBe(80.00); // Only 20% applied
  });
});

// Run: npm test
// Expected: FAILED


// =============================================================================
// STEP 10: IMPLEMENT DISCOUNT CODES
// =============================================================================

class ShoppingCartV5 {
  constructor() {
    this.items = [];
    this.discountPercent = 0;

    // Discount code database (in real app, would be external)
    this.discountCodes = {
      'SAVE10': 10,
      'SAVE20': 20,
      'SAVE50': 50
    };
  }

  getItemCount() {
    return this.items.length;
  }

  addItem(item, quantity = 1) {
    this.items.push({
      ...item,
      quantity: quantity
    });
  }

  applyDiscount(code) {
    if (this.discountCodes[code]) {
      this.discountPercent = this.discountCodes[code];
    }
  }

  getTotal() {
    const subtotal = this.items.reduce((sum, item) => {
      return sum + (item.price * item.quantity);
    }, 0);

    const discount = subtotal * (this.discountPercent / 100);
    return subtotal - discount;
  }
}

// Run: npm test
// Expected: ALL TESTS PASS


// =============================================================================
// STEP 11: REFACTOR (KEEPING TESTS GREEN)
// =============================================================================

class ShoppingCartFinal {
  constructor(discountCodes = null) {
    this.items = [];
    this.discountPercent = 0;

    // Allow dependency injection for testing
    this.discountCodes = discountCodes || {
      'SAVE10': 10,
      'SAVE20': 20,
      'SAVE50': 50
    };
  }

  /**
   * Get number of unique items in cart (not total quantity)
   */
  getItemCount() {
    return this.items.length;
  }

  /**
   * Get total quantity of all items
   */
  getTotalQuantity() {
    return this.items.reduce((sum, item) => sum + item.quantity, 0);
  }

  /**
   * Add item to cart with optional quantity
   */
  addItem(item, quantity = 1) {
    if (!item || typeof item.price !== 'number') {
      throw new Error('Invalid item');
    }

    if (quantity < 1) {
      throw new Error('Quantity must be at least 1');
    }

    this.items.push({
      ...item,
      quantity: quantity
    });
  }

  /**
   * Apply discount code to cart
   */
  applyDiscount(code) {
    if (!code) {
      return;
    }

    const discountValue = this.discountCodes[code];
    if (discountValue !== undefined) {
      this.discountPercent = discountValue;
    }
  }

  /**
   * Remove discount code
   */
  removeDiscount() {
    this.discountPercent = 0;
  }

  /**
   * Get subtotal before discount
   */
  getSubtotal() {
    return this.items.reduce((sum, item) => {
      return sum + (item.price * item.quantity);
    }, 0);
  }

  /**
   * Get discount amount
   */
  getDiscountAmount() {
    const subtotal = this.getSubtotal();
    return subtotal * (this.discountPercent / 100);
  }

  /**
   * Get total after discount
   */
  getTotal() {
    const subtotal = this.getSubtotal();
    const discount = this.getDiscountAmount();
    return subtotal - discount;
  }
}

// Run tests to verify refactoring didn't break anything
// Expected: ALL TESTS STILL PASS


// =============================================================================
// STEP 12: COMPREHENSIVE TEST SUITE
// =============================================================================

describe('ShoppingCartFinal - Comprehensive', () => {
  let cart;

  beforeEach(() => {
    // Fresh cart for each test
    cart = new ShoppingCartFinal();
  });

  describe('Initialization', () => {
    test('should start empty', () => {
      expect(cart.getItemCount()).toBe(0);
      expect(cart.getTotal()).toBe(0);
    });
  });

  describe('Adding Items', () => {
    test('should add single item', () => {
      cart.addItem({ name: 'Widget', price: 10 });
      expect(cart.getItemCount()).toBe(1);
    });

    test('should add multiple items', () => {
      cart.addItem({ name: 'Widget', price: 10 });
      cart.addItem({ name: 'Gadget', price: 20 });
      expect(cart.getItemCount()).toBe(2);
    });

    test('should handle quantity', () => {
      cart.addItem({ name: 'Widget', price: 10 }, 3);
      expect(cart.getTotalQuantity()).toBe(3);
    });

    test('should reject invalid item', () => {
      expect(() => {
        cart.addItem(null);
      }).toThrow('Invalid item');
    });

    test('should reject invalid quantity', () => {
      expect(() => {
        cart.addItem({ name: 'Widget', price: 10 }, 0);
      }).toThrow('Quantity must be at least 1');
    });
  });

  describe('Price Calculation', () => {
    test('should calculate subtotal', () => {
      cart.addItem({ name: 'Widget', price: 10 }, 2);
      cart.addItem({ name: 'Gadget', price: 15 });
      expect(cart.getSubtotal()).toBe(35);
    });

    test('should calculate total with discount', () => {
      cart.addItem({ name: 'Widget', price: 100 });
      cart.applyDiscount('SAVE10');
      expect(cart.getTotal()).toBe(90);
    });

    test('should calculate discount amount', () => {
      cart.addItem({ name: 'Widget', price: 100 });
      cart.applyDiscount('SAVE20');
      expect(cart.getDiscountAmount()).toBe(20);
    });
  });

  describe('Discount Codes', () => {
    test('should apply valid code', () => {
      cart.addItem({ name: 'Widget', price: 100 });
      cart.applyDiscount('SAVE10');
      expect(cart.getTotal()).toBe(90);
    });

    test('should ignore invalid code', () => {
      cart.addItem({ name: 'Widget', price: 100 });
      cart.applyDiscount('INVALID');
      expect(cart.getTotal()).toBe(100);
    });

    test('should remove discount', () => {
      cart.addItem({ name: 'Widget', price: 100 });
      cart.applyDiscount('SAVE10');
      cart.removeDiscount();
      expect(cart.getTotal()).toBe(100);
    });
  });
});


// =============================================================================
// STEP 13: DEMONSTRATE SACRED RULE - NEVER ADJUST TESTS
// =============================================================================

describe('Sacred Rule Example', () => {
  test('demonstrates what NOT to do when test fails', () => {
    // Requirement: Discount should reduce total by percentage
    // Test expects 10% off $100 = $90

    const cart = new ShoppingCartBroken();
    cart.addItem({ name: 'Widget', price: 100 });
    cart.applyDiscount('SAVE10');

    const expected = 90; // From requirements

    // Broken implementation returns 95 (applies only 5% discount)
    const actual = cart.getTotal();

    // ❌ WRONG: "I'll change expected to 95 to match the code"
    // ✅ CORRECT: "Code returns 95, should return 90 - fixing code"

    expect(actual).toBe(expected); // Test stays unchanged!
  });
});

class ShoppingCartBroken {
  constructor() {
    this.items = [];
    this.discountPercent = 0;
    this.discountCodes = {
      'SAVE10': 5  // BUG: Should be 10, not 5
    };
  }

  addItem(item) {
    this.items.push(item);
  }

  applyDiscount(code) {
    this.discountPercent = this.discountCodes[code] || 0;
  }

  getTotal() {
    const subtotal = this.items.reduce((sum, item) => sum + item.price, 0);
    return subtotal - (subtotal * this.discountPercent / 100);
  }
}

// Run: npm test -- --testNamePattern="Sacred Rule"
// Expected: FAILED
// Action: Fix ShoppingCartBroken (change 5 to 10), NOT the test


// =============================================================================
// SUMMARY: TDD CYCLE DEMONSTRATED
// =============================================================================

/**
 * TDD Cycle Summary:
 *
 * 1. Write failing test (cart starts empty)
 * 2. Write minimum code (empty constructor)
 * 3. Write next test (add item)
 * 4. Implement feature (addItem method)
 * 5. Continue cycle:
 *    - Calculate total
 *    - Handle quantities
 *    - Apply discounts
 * 6. Refactor with tests as safety net
 * 7. Add comprehensive test suite
 * 8. Demonstrate sacred rule
 *
 * Key Principles Demonstrated:
 * - Tests derived from requirements
 * - Red-Green-Refactor cycle
 * - Minimum code to pass tests
 * - Refactoring with green tests
 * - Tests define the contract
 * - Never adjust tests to match code
 *
 * Run all tests:
 * npm test -- javascript-tdd-example.js
 *
 * Run with coverage:
 * npm test -- javascript-tdd-example.js --coverage
 */
