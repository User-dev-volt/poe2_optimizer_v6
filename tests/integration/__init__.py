"""
Integration Tests - Lupa/LuaJIT and External Dependencies

This package contains integration tests that require external dependencies
(Lupa/LuaJIT) and are slower than unit tests.

Test Categories:
    - test_lupa_basic.py: Core Lupa/LuaJIT integration (Story 1.2)
    - Future: PoB module loading tests (Story 1.4)
    - Future: End-to-end calculation tests (Story 1.5)

Running Integration Tests:
    # All integration tests
    pytest tests/integration/

    # Skip slow tests during development
    pytest -m "not slow"

    # Specific test file
    pytest tests/integration/test_lupa_basic.py -v

Test Markers:
    @pytest.mark.slow - External dependency tests (can be skipped)

References:
    - Solution Architecture: Lines 1221-1234 (Testing Pyramid: 30% integration tests)
    - Tech Spec Epic 1: Lines 876-885 (Story 1.2 Acceptance Criteria)
"""
