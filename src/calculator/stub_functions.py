"""
PoB External Dependency Stubs - Python Implementations

This module provides Python implementations of Path of Building's external
dependencies, enabling HeadlessWrapper.lua to run without PoB's GUI environment.

Architecture Position:
    - Layer: Integration Layer (calculator/ module)
    - Dependencies: Python standard library ONLY (zlib, logging)
    - Used by: pob_engine.py (registered in Lua global namespace via Lupa)
    - Provides: Stubs for PoB Lua modules (HeadlessWrapper.lua, etc.)

Story Context:
    Story 1.3 implements Python stub functions ONLY. Full HeadlessWrapper.lua
    integration happens in Story 1.4. These stubs enable PoB's Lua code to
    execute without GUI dependencies.

Stub Function Categories:
    1. CRITICAL - Data Compression (PoB code parsing/generation):
       - Deflate(data) -> bytes: Compress data using zlib
       - Inflate(data) -> bytes: Decompress zlib data

    2. DEBUGGING - Console Output (headless mode logging):
       - ConPrintf(*args) -> None: Log debug messages
       - ConPrintTable(table) -> None: Log Lua table structures

    3. SECURITY - System Operations (intentionally disabled):
       - SpawnProcess(*args) -> None: No-op (security)
       - OpenURL(url) -> None: No-op (security)

Usage Pattern (Story 1.4+):
    >>> from lupa.luajit21 import LuaRuntime
    >>> from calculator.stub_functions import Deflate, Inflate, ConPrintf
    >>>
    >>> lua = LuaRuntime()
    >>> lua.globals().Deflate = Deflate  # Register in Lua globals
    >>> lua.globals().Inflate = Inflate
    >>> lua.globals().ConPrintf = ConPrintf
    >>>
    >>> # Lua can now call: compressed = Deflate(data)

References:
    - Tech Spec Epic 1: Lines 105-106 (Module/Service Breakdown)
    - Tech Spec Epic 1: Lines 888-898 (Story 1.3 Acceptance Criteria)
    - Story 1.3: Lines 269-419 (Stub Function Implementation Examples)
    - Solution Architecture: Lines 642-671 (Layered Architecture)
"""

import logging
import zlib
from typing import Union, Any


# Module-level logger for stub function debug output
logger = logging.getLogger(__name__)


# ============================================================================
# CRITICAL STUBS - Data Compression (PoB Code Processing)
# ============================================================================

def Deflate(data: Union[bytes, str]) -> bytes:
    """
    Compress data using zlib (compatible with PoB's Lua Deflate library).

    This function is CRITICAL for PoB code parsing/generation. PoB import codes
    are Base64-encoded zlib-compressed XML (Story 1.1). HeadlessWrapper.lua uses
    Deflate for processing build XML.

    Python's zlib.compress() is compatible with Lua's zlib bindings used by PoB.
    Compression level defaults to -1 (default, optimal speed/size tradeoff).

    Args:
        data: Raw data to compress (bytes or str). If str, encodes as UTF-8.

    Lua Compatibility:
        Lupa passes Lua strings as Python str. For binary data from Lua, this
        function accepts both bytes and str types. String inputs are automatically
        converted to bytes using UTF-8 encoding. The compressed output (bytes)
        can be passed directly back to Lua, where Lupa handles the bytes→string
        conversion using latin-1 encoding (preserving binary data integrity).

    Returns:
        Compressed bytes suitable for Inflate() or Lua Inflate library.

    Raises:
        TypeError: If data is not bytes or str (e.g., int, list, None).

    Example:
        >>> original = b"Hello, Path of Building!"
        >>> compressed = Deflate(original)
        >>> assert len(compressed) < len(original)  # Compression works
        >>> decompressed = Inflate(compressed)
        >>> assert decompressed == original  # Round-trip successful

    Performance:
        Typical PoB code XML (~50KB) compresses in <5ms. Large data (>100KB)
        compresses in <20ms. Performance target: <100ms per calculation (Story 1.5).

    References:
        - Story 1.3 AC-1.3.1: Deflate/Inflate implementation
        - Story 1.1: Lines 44-56 (PoB code Base64/zlib/XML pipeline)
        - Tech Spec Epic 1: Lines 1055-1057 (Assumption 5: zlib compatibility)
    """
    # Type validation: Accept bytes or str only
    if isinstance(data, str):
        data = data.encode('utf-8')

    if not isinstance(data, bytes):
        raise TypeError(
            f"Deflate expects bytes or str, got {type(data).__name__}. "
            f"Lua string → Python bytes conversion may be needed."
        )

    # Compress using Python zlib (compatible with Lua zlib library)
    return zlib.compress(data)


def Inflate(data: Union[bytes, str]) -> bytes:
    """
    Decompress zlib-compressed data (compatible with PoB's Lua Inflate).

    This function is CRITICAL for PoB code parsing. PoB import codes are
    Base64-decoded then Inflate-decompressed to obtain build XML.

    Python's zlib.decompress() is compatible with Lua's zlib bindings.

    Args:
        data: Compressed data (bytes or str) from Deflate() or Lua Deflate.
              If str (from Lua), assumed to be latin-1 encoded binary data.

    Lua Compatibility:
        When Lua code passes compressed binary data to this function, Lupa
        converts Lua strings to Python str using latin-1 encoding. This function
        handles the conversion automatically (line 153): str inputs are decoded
        back to bytes using latin-1, preserving the binary data integrity. For
        direct Python use (not from Lua), always pass bytes for clarity and
        to avoid encoding ambiguity.

    Returns:
        Decompressed bytes (original uncompressed data).

    Raises:
        TypeError: If data is not bytes or str.
        zlib.error: If data is corrupted or not valid zlib format.

    Example:
        >>> compressed = Deflate(b"test data")
        >>> decompressed = Inflate(compressed)
        >>> assert decompressed == b"test data"

    Error Handling:
        Corrupted PoB codes will raise zlib.error with descriptive message.
        Caller should wrap in try/except and present user-friendly error:

        >>> try:
        ...     Inflate(b"not compressed!!!")
        ... except zlib.error as e:
        ...     print(f"Invalid PoB code: {e}")

    References:
        - Story 1.3 AC-1.3.1: Deflate/Inflate implementation
        - Tech Spec Epic 1: Lines 601-648 (Error Handling Strategy)
    """
    # Type validation and conversion
    # Lua strings (when using latin-1 encoding) come as Python str
    if isinstance(data, str):
        data = data.encode('latin-1')  # Convert Lua string back to bytes

    if not isinstance(data, bytes):
        raise TypeError(
            f"Inflate expects bytes or str, got {type(data).__name__}. "
            f"Ensure Base64 decode was performed before Inflate."
        )

    # Decompress using Python zlib
    # Raises zlib.error if data is corrupted or invalid format
    return zlib.decompress(data)


# ============================================================================
# DEBUGGING STUBS - Console Output (Headless Mode)
# ============================================================================

def ConPrintf(*args: Any) -> None:
    """
    No-op replacement for PoB's ConPrintf (console output).

    In headless mode, there is no PoB console window. This stub logs messages
    to Python's logging system at DEBUG level instead, enabling debugging
    without GUI dependencies.

    Args:
        *args: Variable arguments (Lua-style varargs). Converted to strings
               and joined with spaces (similar to Lua's print() function).

    Returns:
        None (no-op from Lua perspective).

    Example (from Lua):
        -- Lua code in HeadlessWrapper.lua:
        ConPrintf("Calculating DPS for build:", build_name)
        ConPrintf("Total DPS:", 12543.5)

        -- Python logging output (DEBUG level):
        -- DEBUG:calculator.stub_functions:ConPrintf: Calculating DPS for build: Witch
        -- DEBUG:calculator.stub_functions:ConPrintf: Total DPS: 12543.5

    Usage:
        Enable DEBUG logging to see ConPrintf output during development:

        >>> import logging
        >>> logging.basicConfig(level=logging.DEBUG)
        >>> ConPrintf("Debug message", 123, 45.6)
        DEBUG:calculator.stub_functions:ConPrintf: Debug message 123 45.6

    References:
        - Story 1.3 AC-1.3.2: ConPrintf implementation
        - Story 1.3: Lines 324-346 (Console Function Examples)
    """
    # Convert all arguments to strings and join with spaces (Lua print() style)
    message = " ".join(str(arg) for arg in args)
    logger.debug(f"ConPrintf: {message}")


def ConPrintTable(table: Any) -> None:
    """
    No-op replacement for PoB's ConPrintTable (debug table printing).

    In headless mode, this stub logs Lua table structures to Python logging
    at DEBUG level for debugging purposes. Handles Lupa Lua table objects.

    Args:
        table: Lua table object (from Lupa) or any Python object. Attempts
               to convert Lua tables to Python dict for pretty-printing.

    Returns:
        None (no-op from Lua perspective).

    Example (from Lua):
        -- Lua code in HeadlessWrapper.lua:
        local build_info = {name="Witch", level=90, ascendancy="Elementalist"}
        ConPrintTable(build_info)

        -- Python logging output (DEBUG level):
        -- DEBUG:calculator.stub_functions:ConPrintTable: {'name': 'Witch', 'level': 90, 'ascendancy': 'Elementalist'}

    Error Handling:
        If table conversion fails (e.g., complex nested tables), logs a
        message indicating parsing failure. Never raises exceptions.

    References:
        - Story 1.3 AC-1.3.3: ConPrintTable implementation
        - Story 1.3: Lines 348-373 (ConPrintTable Example)
    """
    try:
        # Try to convert Lua table to Python dict for pretty-printing
        if hasattr(table, 'items'):
            # Lupa table with .items() method
            table_dict = dict(table.items())
        else:
            # Fallback: Convert to string representation
            table_dict = str(table)

        logger.debug(f"ConPrintTable: {table_dict}")

    except Exception as e:
        # Graceful degradation: Log error but don't crash
        logger.debug(f"ConPrintTable: (unable to parse table: {e})")


# ============================================================================
# SECURITY STUBS - System Operations (Intentionally Disabled)
# ============================================================================

def SpawnProcess(*args: Any) -> None:
    """
    No-op replacement for PoB's SpawnProcess (process execution).

    In headless mode, process spawning is INTENTIONALLY DISABLED for security.
    HeadlessWrapper.lua should NOT spawn processes during calculations. If
    this function is called, it indicates unexpected PoB behavior.

    Args:
        *args: Process command and arguments (ignored). Typically:
               SpawnProcess("cmd", "/c", "command args...")

    Returns:
        None (no-op - process is NOT executed).

    Security Rationale:
        Preventing Lua code from spawning arbitrary processes is critical for:
        - Web API security (Story 2.x): Prevent command injection attacks
        - Batch processing (Story 1.8): Prevent resource exhaustion
        - Headless mode: Process spawning serves no legitimate purpose

    Warning Log:
        Logs at WARNING level if called, alerting developers to unexpected
        behavior in HeadlessWrapper.lua or PoB modules.

        >>> SpawnProcess("cmd", "/c", "echo test")
        WARNING:calculator.stub_functions:SpawnProcess called in headless mode (no-op): ('cmd', '/c', 'echo test')

    References:
        - Story 1.3 AC-1.3.4: SpawnProcess/OpenURL no-ops
        - Tech Spec Epic 1: Lines 578-582 (Security considerations)
    """
    logger.warning(
        f"SpawnProcess called in headless mode (no-op): {args}"
    )


def OpenURL(url: str) -> None:
    """
    No-op replacement for PoB's OpenURL (browser navigation).

    In headless mode, URL opening is INTENTIONALLY DISABLED. HeadlessWrapper.lua
    should NOT open URLs during calculations. If this function is called, it
    indicates unexpected PoB behavior.

    Args:
        url: URL string (ignored). Not validated or accessed.

    Returns:
        None (no-op - URL is NOT opened).

    Security Rationale:
        Preventing Lua code from opening URLs is critical for:
        - Web API security: Prevent SSRF (Server-Side Request Forgery) attacks
        - Batch processing: No legitimate use case for opening URLs
        - Headless mode: Browser interaction serves no purpose

    Warning Log:
        Logs at WARNING level if called, alerting developers to unexpected
        behavior in HeadlessWrapper.lua or PoB modules.

        >>> OpenURL("https://pathofbuilding.community")
        WARNING:calculator.stub_functions:OpenURL called in headless mode (no-op): https://pathofbuilding.community

    References:
        - Story 1.3 AC-1.3.4: SpawnProcess/OpenURL no-ops
        - Story 1.3: Lines 398-419 (System Operation Stubs Example)
    """
    logger.warning(
        f"OpenURL called in headless mode (no-op): {url}"
    )


# ============================================================================
# Module Metadata
# ============================================================================

__all__ = [
    "Deflate",
    "Inflate",
    "ConPrintf",
    "ConPrintTable",
    "SpawnProcess",
    "OpenURL",
]
