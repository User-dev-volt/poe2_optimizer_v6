# Test Suite Documentation

## Overview

This directory contains the test suite for the PoE2 Build Optimizer, focusing on Story 1.1: Parse PoB Import Code functionality.

## Test Structure

```
tests/
├── fixtures/           # Test data and sample PoB codes
├── unit/              # Unit tests for individual components
│   └── test_pob_parser.py  # Tests for PoB parser module
└── README.md          # This file
```

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/ -v
```

### Run Specific Tests

```bash
# Run only parser tests
pytest tests/unit/test_pob_parser.py -v

# Run a specific test
pytest tests/unit/test_pob_parser.py::test_parse_valid_pob_code -v

# Run tests matching a pattern
pytest tests/ -k "parse" -v
```

## Test Coverage

### Story 1.1: Parse PoB Import Code

All acceptance criteria are covered by automated tests:

- **AC-1.1.1**: System decodes Base64 PoB codes successfully
  - Tests: `test_parse_valid_pob_code`, `test_parse_valid_codes_various_classes`

- **AC-1.1.2**: System decompresses zlib-encoded XML without errors
  - Tests: `test_parse_valid_pob_code`, `test_reject_corrupted_zlib`

- **AC-1.1.3**: System parses XML into Python data structure (BuildData object)
  - Tests: `test_parse_valid_pob_code`, `test_parse_minimal_valid_build`

- **AC-1.1.4**: System extracts: character level, class, allocated passive nodes, items, skills
  - Tests: `test_extract_character_class_and_level`, `test_extract_passive_nodes`, `test_extract_build_metadata`

- **AC-1.1.5**: System validates PoB code format (detect corrupted codes)
  - Tests: `test_reject_invalid_base64`, `test_reject_corrupted_zlib`, `test_reject_malformed_xml`, `test_reject_missing_required_fields`

- **AC-1.1.6**: System rejects codes >100KB with clear error message
  - Tests: `test_reject_oversized_code`, `test_reject_exactly_oversized_code`

### Additional Test Coverage

- PoE 1 code rejection: `test_reject_poe1_code`
- Ambiguous version rejection: `test_reject_ambiguous_version` (addresses review finding M1)
- Error message structure validation: `test_error_messages_include_context`
- Edge cases: `test_empty_passive_nodes`, `test_whitespace_in_passive_nodes`
- Calculated properties: `test_calculated_properties`

## Known Limitations (Story 1.1 Scope)

### Item and Skill Parsing

The current implementation (Story 1.1) provides **basic** Item and Skill extraction with the following limitations:

**Item Parsing:**
- `Item.stats` is currently an empty dict `{}`
- Only basic metadata is extracted: slot, name, rarity, item_level
- Detailed stat parsing (modifiers, affixes, numerical values) is deferred to future stories (Epic 1 Story 1.5+)
- See `src/parsers/pob_parser.py:301` for placeholder comment

**Skill Parsing:**
- `Skill.support_gems` is currently an empty list `[]`
- Only primary gem data is extracted: name, level, quality, enabled state
- Support gem parsing (links, gem quality, awakened gems) is deferred to future stories (Epic 1 Story 1.5+)
- See `src/parsers/pob_parser.py:353` for placeholder comment

**Rationale:**
These limitations are **intentional** for Story 1.1 scope, which focuses on establishing the parsing pipeline foundation (Base64 → zlib → XML → BuildData). Detailed stat extraction will be implemented when Epic 1 requires full build calculation (Stories 1.5-1.7).

**Impact on Tests:**
Test helpers (`create_valid_pob_code()`) generate synthetic PoB XML without detailed item/skill data. This is sufficient for validating the parsing pipeline, but future stories will require test fixtures with real PoB exports containing complete stat data.

## Test Results Summary

Current test results (Story 1.1):

```
✅ 19 tests passing (updated post-review)
✅ 0 tests failing
✅ All acceptance criteria validated
```

## Writing New Tests

### Unit Test Template

```python
import pytest
from src.parsers.pob_parser import parse_pob_code
from src.parsers.exceptions import PoBParseError

def test_my_new_test():
    """Test description following AC reference."""
    # Arrange
    code = create_valid_pob_code(level=50)

    # Act
    build = parse_pob_code(code)

    # Assert
    assert build.level == 50
```

### Test Helper Functions

Use the helper functions in `test_pob_parser.py`:

- `create_valid_pob_code()`: Generate valid PoB codes for testing
- `create_poe1_code()`: Generate PoE 1 codes for rejection testing

## Continuous Integration

Tests should be run:

- On every commit (pre-commit hook)
- In CI/CD pipeline before merge
- Nightly for full regression suite

## Future Test Additions

As Epic 1 progresses, add:

- Integration tests for Lupa/LuaJIT (Story 1.2-1.4)
- Parity tests against PoB GUI (Story 1.6)
- Performance benchmarks (Story 1.8)

## Troubleshooting

### Tests Failing

1. Ensure all dependencies installed: `pip install -r requirements.txt`
2. Verify Python version: `python --version` (requires 3.10+)
3. Check for module import errors
4. Review test output for specific failure details

### Import Errors

If you see `ModuleNotFoundError`, ensure you're running from the project root:

```bash
cd /path/to/poe2_optimizer_v6
pytest tests/
```

## References

- Story 1.1 Acceptance Criteria: `docs/stories/story-1.1.md`
- Technical Specification: `docs/tech-spec-epic-1.md`
- Test Strategy: `docs/tech-spec-epic-1.md:1076-1151`
