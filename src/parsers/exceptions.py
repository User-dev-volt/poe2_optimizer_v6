"""Custom exceptions for PoB parsing operations"""


class PoBParseError(Exception):
    """Base exception for all PoB parsing errors.

    All parsing operations should raise this or a subclass
    with context about what failed and why.
    """
    pass


class InvalidFormatError(PoBParseError):
    """Raised when PoB code is corrupted or malformed.

    Examples:
    - Invalid Base64 encoding
    - Corrupted zlib compression
    - Malformed XML structure
    - Missing required fields
    """
    pass


class UnsupportedVersionError(PoBParseError):
    """Raised when PoB code is from unsupported game version.

    Examples:
    - PoE 1 codes (this optimizer only supports PoE 2)
    - Future PoE versions with incompatible formats
    """
    pass
