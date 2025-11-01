# Test Coverage Guide

This document explains how to use pytest-cov for test coverage reporting in the PoE2 Build Optimizer project.

## Quick Start

### Run Tests with Coverage

```bash
# Run all tests with coverage report
pytest --cov

# Run specific test directory with coverage
pytest tests/unit/ --cov=src

# Run with detailed missing lines report
pytest --cov --cov-report=term-missing

# Generate HTML coverage report (opens in browser)
pytest --cov --cov-report=html
# Then open: htmlcov/index.html
```

## Configuration

Coverage is configured in `pytest.ini`:

- **Source directory:** `src/` (all production code)
- **Omitted paths:** Tests, `__pycache__`, site-packages
- **HTML output:** `htmlcov/` directory
- **Minimum threshold:** 0% (fail_under setting, adjust as needed)

## Current Coverage Status

**As of Story 1.5 completion (2025-10-20):**

```
Overall Coverage: 63%

Module Breakdown:
- src/calculator/passive_tree.py:      92%  ✅ Excellent
- src/calculator/stub_functions.py:    97%  ✅ Excellent
- src/models/build_data.py:           100%  ✅ Perfect
- src/calculator/exceptions.py:       100%  ✅ Perfect
- src/parsers/xml_utils.py:            69%  ⚠️  Good
- src/parsers/pob_parser.py:           64%  ⚠️  Good
- src/models/build_stats.py:           47%  ⚠️  Moderate
- src/calculator/build_calculator.py:  37%  ❌ Low
- src/calculator/pob_engine.py:        12%  ❌ Very Low
```

**Note:** Low coverage for `pob_engine.py` and `build_calculator.py` is expected for Story 1.5 scope:
- Most code paths are in integration tests (not measured by unit test coverage)
- PoB engine integration requires full end-to-end execution
- Story 1.6 will add more unit-level tests for calculation accuracy

## Coverage Reports

### Terminal Report

Default coverage output shows summary by module:

```bash
pytest --cov=src

Name                                 Stmts   Miss  Cover
--------------------------------------------------------
src/calculator/build_calculator.py      30     19    37%
src/calculator/passive_tree.py         153     13    92%
...
--------------------------------------------------------
TOTAL                                  605    221    63%
```

### Detailed Report (Missing Lines)

Shows exactly which lines lack coverage:

```bash
pytest --cov=src --cov-report=term-missing

Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
src/calculator/build_calculator.py      30     19    37%   68-71, 116-154
src/calculator/passive_tree.py         153     13    92%   163-164, 169-170
...
```

### HTML Report (Interactive)

Generates browsable HTML with color-coded line coverage:

```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

Features:
- Click on any module to see line-by-line coverage
- Green = covered, Red = not covered
- Branch coverage highlighted
- Search and filter capabilities

## Improving Coverage

### Identify Gaps

1. Run coverage report with missing lines:
   ```bash
   pytest --cov=src --cov-report=term-missing
   ```

2. Review modules with <80% coverage

3. Identify critical uncovered code paths:
   - Error handling branches
   - Edge cases
   - Validation logic

### Add Tests

For uncovered lines in `src/calculator/build_calculator.py:116-154`:

1. Check what those lines do (error handling? edge cases?)
2. Write unit tests targeting those code paths
3. Re-run coverage to verify improvement

Example:
```python
# If lines 116-118 are error handling for invalid build data:
def test_calculate_build_stats_invalid_data():
    """Test error handling for invalid BuildData"""
    invalid_build = BuildData(level=-1, ...)  # Triggers validation error

    with pytest.raises(ValidationError):
        calculate_build_stats(invalid_build)
```

## Coverage Goals

### Story 1.5 (Current)
- **Target:** 60%+ overall (achieved: 63% ✅)
- Focus: Core data models and parsers

### Story 1.6 (Validate Calculation Accuracy)
- **Target:** 75%+ overall
- Add: Calculation accuracy unit tests
- Improve: `pob_engine.py` and `build_calculator.py` coverage

### Epic 2 (Optimization Algorithm)
- **Target:** 85%+ overall
- Add: Algorithm unit tests, performance tests
- Maintain: High coverage on critical paths

### Epic 3 (Production)
- **Target:** 90%+ overall
- Add: API endpoint tests, integration tests
- Enforce: Minimum coverage on all new code

## Best Practices

### 1. Run Coverage Regularly

Add to development workflow:
```bash
# Before committing changes
pytest --cov=src --cov-report=term-missing
```

### 2. Focus on Critical Code

Prioritize coverage for:
- Error handling paths
- Data validation
- Business logic
- Public APIs

Less critical:
- Debug/logging code (can mark with `# pragma: no cover`)
- `__repr__` methods
- Type checking blocks (`if TYPE_CHECKING:`)

### 3. Don't Game the Metrics

Coverage percentage is a tool, not a goal:
- ✅ Write meaningful tests that verify behavior
- ❌ Write tests just to hit lines without verifying correctness
- ✅ Focus on edge cases and error paths
- ❌ Skip important tests because they're hard to write

### 4. Use Coverage to Find Bugs

Coverage reveals:
- Uncovered error paths → potential bugs when errors occur
- Uncovered validation → potential invalid data bugs
- Uncovered edge cases → potential corner case bugs

## Excluding Code from Coverage

Use `# pragma: no cover` for code that shouldn't be tested:

```python
def debug_function():  # pragma: no cover
    """Only used for debugging, not in production"""
    print(internal_state)

if __name__ == "__main__":  # pragma: no cover
    # Script entry point, not part of library API
    main()
```

Already configured exclusions in `pytest.ini`:
- `raise NotImplementedError` (abstract methods)
- `def __repr__` (string representations)
- `if TYPE_CHECKING:` (type-only imports)
- `if __name__ == .__main__.:` (script entry points)

## Integration with CI/CD

Future integration (Epic 3):

```yaml
# .github/workflows/tests.yml
- name: Run tests with coverage
  run: pytest --cov=src --cov-report=xml

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    fail_ci_if_error: true
```

## Troubleshooting

### Coverage shows 0% for all files

**Cause:** Source path mismatch
**Fix:** Ensure `pytest.ini` has `pythonpath = src`

### Coverage doesn't include integration tests

**Expected behavior:** Integration tests run full stack, hard to attribute to specific lines
**Solution:** Run separate unit and integration coverage reports

### HTML report not generating

**Cause:** Missing `--cov-report=html` flag
**Fix:**
```bash
pytest --cov=src --cov-report=html
```

### Coverage lower than expected

**Check:**
1. Are tests actually running? (`pytest -v`)
2. Are tests importing from `src/` correctly?
3. Are there untested code paths (check HTML report)?

## References

- **pytest-cov documentation:** https://pytest-cov.readthedocs.io/
- **Coverage.py documentation:** https://coverage.readthedocs.io/
- **Project pytest.ini:** `pytest.ini` (coverage configuration)
- **Story 1.5 Review:** Optional Enhancement #3 (docs/stories/story-1.5.md:1798-1804)

---

**Last Updated:** 2025-10-20 (Story 1.5 completion)
