"""Unit tests for PoB parser module.

Tests cover all acceptance criteria for Story 1.1:
- AC-1.1.1: Decode Base64 PoB codes successfully
- AC-1.1.2: Decompress zlib-encoded XML without errors
- AC-1.1.3: Parse XML into Python data structure (BuildData object)
- AC-1.1.4: Extract character level, class, allocated passive nodes, items, skills
- AC-1.1.5: Validate PoB code format (detect corrupted codes)
- AC-1.1.6: Reject codes >100KB with clear error message
"""

import base64
import zlib
import pytest

from src.parsers.pob_parser import parse_pob_code
from src.parsers.exceptions import PoBParseError, InvalidFormatError, UnsupportedVersionError
from src.models.build_data import BuildData, CharacterClass


def create_valid_pob_code(
    class_name: str = "Witch",
    level: int = 90,
    tree_version: str = "3_24",
    passive_nodes: str = "12345,12346,12347"
) -> str:
    """Helper to create a valid PoB code for testing.

    Args:
        class_name: Character class name
        level: Character level
        tree_version: Tree version (3_24 for PoE 2)
        passive_nodes: Comma-separated node IDs

    Returns:
        Base64-encoded PoB code
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<PathOfBuilding>
  <Build className="{class_name}" level="{level}" buildName="Test Build"/>
  <Tree activeSpec="{tree_version}">
    <Spec nodes="{passive_nodes}"/>
  </Tree>
  <Items/>
  <Skills/>
</PathOfBuilding>"""

    compressed = zlib.compress(xml.encode('utf-8'))
    return base64.b64encode(compressed).decode('ascii')


def create_poe1_code() -> str:
    """Helper to create a PoE 1 code (should be rejected)."""
    return create_valid_pob_code(tree_version="3_23")  # PoE 1 version


# AC-1.1.1: Decode Base64 PoB codes successfully
# AC-1.1.2: Decompress zlib-encoded XML without errors
# AC-1.1.3: Parse XML into Python data structure (BuildData object)
def test_parse_valid_pob_code():
    """Test parsing a valid PoB code succeeds."""
    code = create_valid_pob_code()
    build = parse_pob_code(code)

    assert isinstance(build, BuildData)
    assert build.character_class == CharacterClass.WITCH
    assert build.level == 90


def test_parse_valid_codes_various_classes():
    """Test parsing valid codes for different character classes."""
    classes = ["Witch", "Warrior", "Ranger", "Monk", "Mercenary", "Sorceress"]

    for class_name in classes:
        code = create_valid_pob_code(class_name=class_name, level=50)
        build = parse_pob_code(code)

        assert build.character_class.value == class_name
        assert build.level == 50


# AC-1.1.4: Extract character level, class, allocated passive nodes, items, skills
def test_extract_character_class_and_level():
    """Test extracting character class and level."""
    code = create_valid_pob_code(class_name="Ranger", level=75)
    build = parse_pob_code(code)

    assert build.character_class == CharacterClass.RANGER
    assert build.level == 75


def test_extract_passive_nodes():
    """Test extracting allocated passive node IDs."""
    nodes = "11111,22222,33333,44444,55555"
    code = create_valid_pob_code(passive_nodes=nodes)
    build = parse_pob_code(code)

    expected_nodes = {11111, 22222, 33333, 44444, 55555}
    assert build.passive_nodes == expected_nodes
    assert build.allocated_point_count == 5


def test_extract_build_metadata():
    """Test extracting build metadata like tree version."""
    code = create_valid_pob_code(tree_version="3_24")
    build = parse_pob_code(code)

    assert build.tree_version == "3_24"


# AC-1.1.5: Validate PoB code format (detect corrupted codes)
def test_reject_invalid_base64():
    """Test that invalid Base64 encoding is rejected.

    Note: Python's base64 module is lenient and will decode most strings,
    so the actual failure happens at zlib decompression stage.
    """
    invalid_code = "!!!This is not valid Base64!!!"

    with pytest.raises(InvalidFormatError, match="decompress"):
        parse_pob_code(invalid_code)


def test_reject_corrupted_zlib():
    """Test that corrupted zlib data is rejected."""
    # Valid Base64 but not valid zlib data
    corrupted_code = base64.b64encode(b"This is not zlib compressed data").decode('ascii')

    with pytest.raises(InvalidFormatError, match="Failed to decompress"):
        parse_pob_code(corrupted_code)


def test_reject_malformed_xml():
    """Test that malformed XML is rejected."""
    xml = "<?xml version='1.0'?><InvalidXML><NotClosed>"
    compressed = zlib.compress(xml.encode('utf-8'))
    code = base64.b64encode(compressed).decode('ascii')

    with pytest.raises(InvalidFormatError, match="parse XML"):
        parse_pob_code(code)


def test_reject_missing_required_fields():
    """Test that XML missing required fields is rejected."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<PathOfBuilding>
  <Build level="50"/>
</PathOfBuilding>"""
    compressed = zlib.compress(xml.encode('utf-8'))
    code = base64.b64encode(compressed).decode('ascii')

    with pytest.raises(InvalidFormatError, match="character class"):
        parse_pob_code(code)


# AC-1.1.6: Reject codes >100KB with clear error message
def test_reject_oversized_code():
    """Test that codes >100KB are rejected with clear error.

    Note: Creating incompressible data to ensure the base64 code size exceeds 100KB.
    """
    # Create incompressible random-looking data to prevent zlib from shrinking it too much
    import random
    random.seed(42)
    random_data = ''.join(random.choice('0123456789abcdef') for _ in range(150 * 1024))
    huge_xml = f"<?xml version='1.0'?><PathOfBuilding><Data>{random_data}</Data></PathOfBuilding>"
    compressed = zlib.compress(huge_xml.encode('utf-8'))
    oversized_code = base64.b64encode(compressed).decode('ascii')

    with pytest.raises(PoBParseError, match="too large"):
        parse_pob_code(oversized_code)


def test_reject_exactly_oversized_code():
    """Test rejection at exact boundary (101KB)."""
    # Create a code exactly 101KB
    size_bytes = 101 * 1024
    huge_code = "A" * size_bytes

    with pytest.raises(PoBParseError, match="too large"):
        parse_pob_code(huge_code)


# PoE 1 code rejection (FR-1.5)
def test_reject_poe1_code():
    """Test that PoE 1 codes are rejected with clear message."""
    poe1_code = create_poe1_code()

    with pytest.raises(UnsupportedVersionError, match="only supports PoE 2"):
        parse_pob_code(poe1_code)


def test_reject_ambiguous_version():
    """Test that ambiguous or unknown version formats are rejected.

    AC-1.1.5: Ensure version detection rejects non-standard formats
    for safety (addresses M1 review finding).
    """
    # Test ambiguous format with non-numeric minor version
    ambiguous_code = create_valid_pob_code(tree_version="3_abc")
    with pytest.raises(UnsupportedVersionError, match="only supports PoE 2"):
        parse_pob_code(ambiguous_code)

    # Test unknown version format (not "3_X" pattern)
    unknown_code = create_valid_pob_code(tree_version="unknown")
    with pytest.raises(UnsupportedVersionError, match="only supports PoE 2"):
        parse_pob_code(unknown_code)

    # Test future major version (4_0)
    future_code = create_valid_pob_code(tree_version="4_0")
    with pytest.raises(UnsupportedVersionError, match="only supports PoE 2"):
        parse_pob_code(future_code)


# Error message structure validation (FR-1.3)
def test_error_messages_include_context():
    """Test that all exceptions include problem summary, cause, and suggested action."""
    # Test InvalidFormatError
    with pytest.raises(InvalidFormatError) as exc_info:
        parse_pob_code("invalid")
    assert "Invalid Base64" in str(exc_info.value)

    # Test UnsupportedVersionError
    poe1_code = create_poe1_code()
    with pytest.raises(UnsupportedVersionError) as exc_info:
        parse_pob_code(poe1_code)
    assert "only supports PoE 2" in str(exc_info.value)
    assert "Path of Building" in str(exc_info.value)


# Additional edge cases
def test_parse_minimal_valid_build():
    """Test parsing a minimal valid build with no items or skills."""
    code = create_valid_pob_code(passive_nodes="")
    build = parse_pob_code(code)

    assert build.character_class == CharacterClass.WITCH
    assert build.level == 90
    assert len(build.passive_nodes) == 0
    assert len(build.items) == 0
    assert len(build.skills) == 0


def test_calculated_properties():
    """Test BuildData calculated properties."""
    code = create_valid_pob_code(level=50, passive_nodes="1,2,3,4,5")
    build = parse_pob_code(code)

    # Level 50: max points = 50 + 23 = 73 (verified PoE 2 formula)
    # Allocated: 5
    # Unallocated: 73 - 5 = 68
    assert build.allocated_point_count == 5
    assert build.unallocated_points == 68


def test_various_character_levels():
    """Test parsing builds with various character levels."""
    for level in [1, 50, 90, 100]:
        code = create_valid_pob_code(level=level)
        build = parse_pob_code(code)
        assert build.level == level


def test_whitespace_in_passive_nodes():
    """Test that whitespace in passive node list is handled correctly."""
    nodes_with_whitespace = " 12345 , 12346 , 12347 "
    code = create_valid_pob_code(passive_nodes=nodes_with_whitespace)
    build = parse_pob_code(code)

    expected_nodes = {12345, 12346, 12347}
    assert build.passive_nodes == expected_nodes


def test_empty_passive_nodes():
    """Test parsing build with no allocated passive nodes."""
    code = create_valid_pob_code(passive_nodes="")
    build = parse_pob_code(code)

    assert len(build.passive_nodes) == 0
    assert build.allocated_point_count == 0
