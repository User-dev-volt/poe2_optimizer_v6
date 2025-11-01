"""
Calculator Module Exceptions

Custom exception hierarchy for PoB calculation engine errors.

Story 1.4 Scope:
    - CalculationError: General calculation failures (Lua errors, missing files)
    - CalculationTimeout: Calculation exceeds time limit (Story 1.5)

References:
    - Tech Spec Epic 1: Lines 601-648 (Error Handling Strategy)
"""


class CalculationError(Exception):
    """
    Raised when PoB calculation engine encounters an error.

    Examples:
        - HeadlessWrapper.lua loading fails
        - Lua runtime error during calculation
        - Missing or corrupt PoB data files
        - Invalid BuildData input

    Story 1.4: Used for module loading errors.
    Story 1.5: Extended for calculation execution errors.
    """
    pass


class CalculationTimeout(CalculationError):
    """
    Raised when PoB calculation exceeds maximum allowed time.

    Story 1.5: 5-second timeout for single build calculation.
    Story 1.8: Batch calculation timeout handling.
    """
    pass
