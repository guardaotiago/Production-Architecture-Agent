# User Story Writing Guide

## What is a User Story?

A user story is a short, informal description of a feature told from the perspective of the person who wants it. It is the smallest unit of work in an agile framework.

**Format:**
```
As a [user type], I want [action] so that [benefit].
```

The three parts answer:
- **Who** wants the functionality (role)
- **What** they want to do (action)
- **Why** they want it (value delivered)

---

## The INVEST Criteria

Every user story should meet INVEST criteria before it enters a sprint.

### I — Independent
Stories should not depend on each other. You should be able to build and deliver them in any order.

**Bad:** "As a user, I want to edit my profile (requires Story #3 for profile creation)"
**Good:** "As a user, I want to update my display name from the settings page"

### N — Negotiable
Stories are not contracts. The details should be flexible and refined through conversation between developers, designers, and stakeholders.

**Bad:** "As a user, I want a 400x200px blue button labeled 'Submit' in the top-right corner"
**Good:** "As a user, I want a clear way to submit my form"

### V — Valuable
Every story must deliver value to a user or stakeholder. If a story only benefits developers (e.g., "refactor the database layer"), reframe it in terms of user impact.

**Bad:** "Migrate database to PostgreSQL 16"
**Good:** "As a user, I want search results in under 200ms so I can find items quickly" (enabled by the migration)

### E — Estimable
The team must be able to estimate the effort. If a story is too vague to estimate, it needs refinement or a spike.

**Bad:** "As a user, I want the app to be fast"
**Good:** "As a user, I want the dashboard to load in under 2 seconds on a 4G connection"

### S — Small
Stories should fit within a single sprint (typically 1-5 days of work). Large stories are called epics and must be split.

**Bad:** "As a user, I want a complete authentication system"
**Good:** "As a user, I want to log in with my email and password"

### T — Testable
Every story must have clear acceptance criteria that can be verified. If you cannot test it, you cannot ship it.

**Bad:** "As a user, I want the app to be user-friendly"
**Good:** "As a user, I want to complete the checkout flow in 3 steps or fewer"

---

## Writing Acceptance Criteria

Acceptance criteria define exactly when a story is "done." Use the Given/When/Then format:

```
Given [some precondition or context],
When [the user takes an action],
Then [an observable outcome occurs].
```

### Rules for Good Acceptance Criteria
1. **Be specific** — No vague language ("should work well")
2. **Be testable** — A QA engineer must be able to verify each criterion
3. **Cover happy path AND edge cases** — What happens on success and failure?
4. **Keep them independent** — Each criterion tests one thing
5. **Include boundaries** — Specify limits, formats, and constraints

### Example: Login Story

**Story:** As a registered user, I want to log in with my email and password so that I can access my account.

**Acceptance Criteria:**
- Given I am on the login page, when I enter a valid email and password and click "Log In", then I am redirected to my dashboard.
- Given I am on the login page, when I enter an invalid email format, then I see an inline error "Please enter a valid email address."
- Given I am on the login page, when I enter a wrong password, then I see "Invalid email or password" (not revealing which is wrong).
- Given I have failed login 5 times, when I try again, then my account is locked for 15 minutes and I see a message explaining this.
- Given I am already logged in, when I navigate to the login page, then I am redirected to my dashboard.

---

## Good vs Bad Stories: Examples

### Example 1: E-commerce Search

**Bad:**
> As a user, I want to search for products.

Problems: No context on what "search" means, no acceptance criteria, too broad.

**Good:**
> As a shopper, I want to search for products by name or category so that I can quickly find what I need.
>
> Acceptance Criteria:
> - Given I am on any page, when I type in the search bar and press Enter, then I see results matching my query within 1 second.
> - Given I search for "blue shoes", when results load, then I see products sorted by relevance with the search term highlighted.
> - Given I search for a term with no matches, when results load, then I see "No results found" with suggested alternative searches.
> - Given I search for a term, when results load, then I can filter by price range, category, and rating.

### Example 2: Notifications

**Bad:**
> As a user, I want notifications.

Problems: What kind? When? Where? How?

**Good:**
> As a project member, I want to receive an in-app notification when a task assigned to me changes status so that I stay informed without checking manually.
>
> Acceptance Criteria:
> - Given I am assigned to a task, when its status changes, then I see a notification badge on the bell icon within 5 seconds.
> - Given I have unread notifications, when I click the bell icon, then I see a list of notifications with the most recent first.
> - Given I read a notification, when I click on it, then it is marked as read and I am taken to the relevant task.
> - Given I have more than 50 notifications, when I open the list, then I see the 20 most recent with a "Load more" option.

---

## Splitting Large Stories

When a story is too large for a single sprint, split it. Here are proven techniques:

### 1. Split by Workflow Step
**Epic:** As a user, I want to purchase a product online.
- Story A: As a shopper, I want to add items to my cart.
- Story B: As a shopper, I want to enter my shipping address.
- Story C: As a shopper, I want to pay with a credit card.
- Story D: As a shopper, I want to receive an order confirmation email.

### 2. Split by Data Variation
**Epic:** As a user, I want to log in.
- Story A: As a user, I want to log in with email and password.
- Story B: As a user, I want to log in with Google OAuth.
- Story C: As a user, I want to log in with a magic link.

### 3. Split by Business Rule
**Epic:** As an admin, I want to manage user permissions.
- Story A: As an admin, I want to assign a "viewer" role.
- Story B: As an admin, I want to assign an "editor" role.
- Story C: As an admin, I want to revoke access for a user.

### 4. Split by Happy Path vs Edge Cases
- Story A: As a user, I want to upload a profile photo (happy path: valid JPG under 5MB).
- Story B: Handle upload errors (file too large, wrong format, network failure).

### 5. Split by Performance / Polish
- Story A: As a user, I want to see a list of my orders (basic implementation).
- Story B: As a user, I want to see my orders load within 500ms with pagination.

---

## Estimation Tips

Use story points (Fibonacci: 1, 2, 3, 5, 8, 13) or T-shirt sizes (S, M, L, XL).

| Points | Meaning                  | Example                          |
|--------|--------------------------|----------------------------------|
| 1      | Trivial, well-understood | Change a button label            |
| 2      | Small, low uncertainty   | Add a new field to a form        |
| 3      | Medium, some unknowns    | Build a new API endpoint         |
| 5      | Large, moderate unknowns | Integrate with a third-party API |
| 8      | Very large, needs spike  | Build a real-time notification system |
| 13     | Too large, must be split | Implement full auth system       |

**If a story is 13 points, split it. Always.**

---

## Checklist Before Sprint

Before a story enters a sprint, verify:

- [ ] Follows "As a / I want / So that" format
- [ ] Meets all INVEST criteria
- [ ] Has 3+ acceptance criteria with Given/When/Then
- [ ] Covers at least one error/edge case
- [ ] Has been estimated by the team
- [ ] Is small enough for one sprint
- [ ] Designer has provided any necessary mockups
- [ ] Technical dependencies are identified
