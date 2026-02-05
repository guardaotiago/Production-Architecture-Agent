# Testing Pyramid

## The Pyramid

The testing pyramid is a strategy for balancing speed, cost, and confidence across your test suite.

```
          /   E2E    \          ~10% | Slow, expensive, high confidence
         /  (browser)  \
        /----------------\
       /   Integration    \     ~20% | Medium speed, real dependencies
      /  (API, DB, services) \
     /------------------------\
    /       Unit Tests         \    ~70% | Fast, cheap, isolated
   /  (functions, modules, logic) \
  /--------------------------------\
```

### Why a Pyramid?

- **Unit tests** are fast (milliseconds), easy to write, and pinpoint failures exactly. You want many of them.
- **Integration tests** verify that components work together. They catch interface mismatches that unit tests miss, but they are slower and more complex to maintain.
- **E2E tests** simulate real user behavior. They catch issues in the full stack, but they are slow, flaky-prone, and expensive. Keep them focused on critical user journeys.

An inverted pyramid (many E2E, few unit) leads to slow pipelines, flaky failures, and debugging nightmares.

---

## Unit Test Best Practices

### The AAA Pattern

Structure every unit test with three clear phases:

```python
def test_calculate_discount_for_premium_user():
    # Arrange — set up the inputs and dependencies
    user = User(tier="premium")
    cart = Cart(items=[Item(price=100)])

    # Act — execute the behavior under test
    result = calculate_discount(user, cart)

    # Assert — verify the outcome
    assert result.discount_percentage == 15
    assert result.final_price == 85
```

### Naming Conventions

Use descriptive names that explain the scenario and expected behavior:

```
test_<unit>_<scenario>_<expected_result>
```

Good examples:
- `test_login_with_invalid_email_returns_validation_error`
- `test_cart_total_with_discount_code_applies_percentage`
- `test_payment_processor_timeout_retries_three_times`

Bad examples:
- `test_login` (what about login?)
- `test_1` (meaningless)
- `test_it_works` (what works?)

### Mocking and Stubbing

Mock external dependencies to keep unit tests fast and isolated.

**When to mock:**
- External APIs and HTTP calls
- Database queries (in unit tests)
- File system access
- Time-dependent behavior (`datetime.now()`)
- Random number generation

**When NOT to mock:**
- The unit under test itself
- Pure utility functions with no side effects
- Data structures and value objects

```python
# Good: Mock the external dependency
def test_user_service_creates_user(mocker):
    mock_db = mocker.patch("app.db.save_user")
    mock_db.return_value = User(id=1, name="Alice")

    result = user_service.create("Alice")

    assert result.name == "Alice"
    mock_db.assert_called_once()

# Bad: Mocking the thing you're testing
def test_user_service_creates_user(mocker):
    mocker.patch("app.user_service.create", return_value=User(id=1))  # This tests nothing
```

### What Makes a Good Unit Test

- **Fast** — runs in milliseconds
- **Isolated** — no shared state, no dependency on execution order
- **Repeatable** — same result every time, on any machine
- **Self-validating** — pass or fail, no manual inspection
- **Timely** — written close to the code it tests (ideally before or alongside)

---

## Integration Test Strategies

### What to Test at the Integration Level

- API endpoint contracts (request/response shapes)
- Database queries with real or in-memory databases
- Service-to-service communication
- Message queue producers and consumers
- Authentication and authorization flows
- File upload/download pipelines

### Test Database Strategies

1. **In-memory database** (e.g., SQLite in-memory): Fast, no cleanup, but may differ from production DB behavior.
2. **Docker test database**: Real database engine (Postgres, MySQL) in a container. Slower startup but accurate behavior.
3. **Transaction rollback**: Run each test in a transaction that rolls back. Fast cleanup, real DB behavior.

### API Integration Testing

```python
def test_create_user_endpoint(client, db):
    response = client.post("/api/users", json={
        "name": "Alice",
        "email": "alice@example.com"
    })

    assert response.status_code == 201
    assert response.json()["name"] == "Alice"

    # Verify the side effect
    user = db.query(User).filter_by(email="alice@example.com").first()
    assert user is not None
```

### Contract Testing

When services communicate over APIs, use contract tests to verify that providers honor the interface consumers expect. Tools: Pact, Schemathesis.

---

## E2E Test Tools

### Playwright (Recommended)

- Cross-browser (Chromium, Firefox, WebKit)
- Auto-wait for elements (reduces flakiness)
- Built-in tracing and video recording
- Excellent TypeScript/JavaScript support
- `npx playwright test`

### Cypress

- Real-time browser preview during development
- Time-travel debugging
- Good for single-page applications
- JavaScript only
- `npx cypress run`

### Selenium

- Widest browser and language support
- Mature ecosystem
- More verbose API, more flakiness
- Good for legacy or polyglot environments

### When to Use E2E Tests

Write E2E tests for:
- **Critical user journeys**: signup, login, checkout, payment
- **Cross-cutting concerns**: navigation, permissions, session management
- **Smoke tests**: verify the app loads and core paths work after deploy

Do NOT write E2E tests for:
- Individual form validations (unit test these)
- API logic (integration test these)
- Edge cases in business logic (unit test these)

---

## Fixtures and Factories

### Fixtures

Pre-defined test data that is set up before tests run.

```python
@pytest.fixture
def sample_user(db):
    user = User(name="Alice", email="alice@test.com", role="admin")
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()

def test_admin_can_delete_posts(sample_user, client):
    response = client.delete("/posts/1", headers=auth_headers(sample_user))
    assert response.status_code == 200
```

### Factories

Dynamic test data generators that let you customize only the fields you care about.

```python
# Using factory_boy (Python) or fishery (TypeScript)
class UserFactory(factory.Factory):
    class Meta:
        model = User
    name = factory.Faker("name")
    email = factory.Faker("email")
    role = "user"

def test_premium_users_see_dashboard():
    user = UserFactory(role="premium")
    # ...
```

**Prefer factories over fixtures** when you need varied test data. Fixtures are better for shared, static resources (database connections, API clients).

---

## Flaky Test Prevention

Flaky tests are tests that sometimes pass and sometimes fail without code changes. They erode trust and slow teams down.

### Common Causes and Fixes

| Cause | Fix |
|-------|-----|
| Timing/race conditions | Use explicit waits, not `sleep()`. Playwright and Cypress auto-wait. |
| Shared mutable state | Isolate test data. Each test creates its own data. |
| Order-dependent tests | Run tests in random order to catch dependencies. |
| External service calls | Mock external services in tests. |
| Floating-point comparisons | Use `pytest.approx()` or tolerance-based assertions. |
| Time-zone issues | Pin timezone in tests. Use UTC consistently. |
| Random data without seeds | Seed random generators or use deterministic factories. |

### Strategies

1. **Quarantine flaky tests**: Tag them (`@pytest.mark.flaky`) and track them. Fix or delete within a sprint.
2. **Retry with caution**: Retrying flaky tests masks the root cause. Use retries only as a temporary measure.
3. **Run in isolation**: If a test fails only when run with others, it has shared state. Find and eliminate it.
4. **Deterministic IDs**: Use predictable IDs in test data instead of auto-generated UUIDs.
5. **CI stability tracking**: Monitor test pass rates over time. A test with < 99% pass rate is flaky.

---

## Test Organization

```
tests/
  unit/
    test_user_service.py
    test_cart_calculator.py
    test_validators.py
  integration/
    test_user_api.py
    test_payment_flow.py
    test_database_queries.py
  e2e/
    test_signup_journey.py
    test_checkout_journey.py
  fixtures/
    users.py
    products.py
  conftest.py             # Shared fixtures and config
```

Keep tests mirroring the source structure when it helps navigation. Group by type at the top level, by feature within each type.
