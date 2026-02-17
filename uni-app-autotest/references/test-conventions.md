# Test Conventions

## File Placement

1. Use `*.test.js` naming.
2. Place test files near the page under test when possible.
3. Follow page-level mapping, for example:
   - Page: `pages/login/login.uvue`
   - Test: `pages/login/login.test.js`

## Coding Conventions

1. Use standard Jest syntax (`test` or `it`).
2. Keep each test case independent.
3. Avoid hidden inter-test dependencies.
4. Prefer explicit setup and cleanup per test suite.

## Coverage Checklist

1. Basic render or open-page assertion.
2. Core interaction path (tap/input/navigation).
3. At least one negative or edge case for critical pages.
4. Stable assertion target (text/value/state) for deterministic runs.

## Failure Triage

1. Re-run only failed test file first with `--case`.
2. Confirm whether failure is app behavior or test expectation.
3. Patch minimal surface area and rerun platform suite.
