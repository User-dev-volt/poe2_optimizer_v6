"""Unit tests for encode_pob_code (Story 3.7, Encoder track).

These tests exercise the round-trip-and-patch encoder. They need NO LuaJIT /
calculation engine, so they run fast: decode -> patch Spec @nodes -> re-encode,
then re-decode with parse_pob_code and assert semantic (re-parsed) equality.
"""

import base64
import zlib
from pathlib import Path

import pytest

from src.parsers.pob_parser import encode_pob_code, parse_pob_code
from src.parsers.xml_utils import parse_xml, build_xml
from src.models.build_data import CharacterClass


# A real PoB CODE fixture (base64 -> zlib -> XML), NOT raw XML. The .txt sibling
# of build_01_witch_90.xml is the encoded import code (starts with "eJyt" =
# zlib header 0x78 0x9c in base64).
FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "parity_builds"
    / "build_01_witch_90.txt"
)


def _load_code() -> str:
    """Load the raw base64 PoB import code fixture."""
    return FIXTURE.read_text(encoding="utf-8")


def _spec_nodes_from_code(code: str):
    """Decode a code and return its active Spec @nodes string (helper)."""
    data = parse_xml(zlib.decompress(base64.b64decode(code)).decode("utf-8"))
    root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    return root["Tree"]["Spec"]["@nodes"]


def test_fixture_is_a_base64_code_not_raw_xml():
    """Guard: confirm the fixture really is an encoded code, not XML."""
    code = _load_code()
    assert not code.lstrip().startswith("<"), "fixture should be base64, not XML"
    # Decodes + decompresses to XML without error.
    xml = zlib.decompress(base64.b64decode(code)).decode("utf-8")
    assert "PathOfBuilding" in xml


def test_round_trip_passive_nodes_semantic_equality():
    """encode -> parse_pob_code should yield exactly the node set we passed in."""
    code = _load_code()
    new_nodes = {1, 2, 100, 9999, 54447}

    encoded = encode_pob_code(code, new_nodes)
    rebuilt = parse_pob_code(encoded)

    # Semantic equality on the re-parsed node set (NOT byte-identical strings).
    assert rebuilt.passive_nodes == new_nodes


def test_encode_replaces_original_nodes():
    """The encoded tree must differ from the original allocation."""
    code = _load_code()
    original = parse_pob_code(code)
    new_nodes = {7, 8, 9}
    assert original.passive_nodes != new_nodes  # precondition

    rebuilt = parse_pob_code(encode_pob_code(code, new_nodes))

    assert rebuilt.passive_nodes == new_nodes
    assert rebuilt.passive_nodes != original.passive_nodes


def test_non_tree_sections_preserved():
    """Patching the tree must leave class / level / ascendancy untouched."""
    code = _load_code()
    original = parse_pob_code(code)

    rebuilt = parse_pob_code(encode_pob_code(code, {42, 43, 44}))

    # Character class (a non-tree section) is preserved.
    assert rebuilt.character_class == original.character_class
    assert rebuilt.character_class == CharacterClass.WITCH
    # Level and tree version preserved too.
    assert rebuilt.level == original.level == 90
    assert rebuilt.tree_version == original.tree_version


def test_output_is_standard_base64_not_urlsafe():
    """Output must use the standard alphabet (parse_pob_code drops -/_)."""
    code = _load_code()
    encoded = encode_pob_code(code, {42})

    # urlsafe-only characters must never appear.
    assert "-" not in encoded
    assert "_" not in encoded
    # validate=True raises if ANY non-standard-alphabet char is present.
    decoded = base64.b64decode(encoded, validate=True)
    # And it decompresses to valid XML (proves the codec round-trips).
    assert b"PathOfBuilding" in zlib.decompress(decoded)


def test_nodes_written_sorted_and_comma_joined():
    """@nodes must be numerically sorted and comma-joined in the output XML."""
    code = _load_code()
    # Deliberately unsorted input order.
    encoded = encode_pob_code(code, [54447, 2, 1, 9999, 100])

    assert _spec_nodes_from_code(encoded) == "1,2,100,9999,54447"


def test_accepts_set_or_list_input():
    """Both a set and a list should produce the same re-parsed node set."""
    code = _load_code()
    from_set = parse_pob_code(encode_pob_code(code, {3, 1, 2})).passive_nodes
    from_list = parse_pob_code(encode_pob_code(code, [2, 3, 1])).passive_nodes
    assert from_set == from_list == {1, 2, 3}


def test_empty_node_set_round_trips():
    """An empty optimization result should encode and decode to an empty set."""
    code = _load_code()
    rebuilt = parse_pob_code(encode_pob_code(code, set()))
    assert rebuilt.passive_nodes == set()


def test_patches_active_spec_when_spec_is_a_list():
    """When Tree>Spec is a LIST, only the @activeSpec-selected spec is patched."""
    code = _load_code()
    # Synthesize a 2-spec tree with activeSpec=2 (1-indexed) from the fixture.
    data = parse_xml(zlib.decompress(base64.b64decode(code)).decode("utf-8"))
    root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
    tree = root["Tree"]
    spec_inactive = dict(tree["Spec"])
    spec_inactive["@nodes"] = "111,222"  # spec index 1 (activeSpec=1)
    spec_active = dict(tree["Spec"])
    spec_active["@nodes"] = "333,444"    # spec index 2 (activeSpec=2)
    tree["Spec"] = [spec_inactive, spec_active]
    tree["@activeSpec"] = "2"
    multi_code = base64.b64encode(
        zlib.compress(build_xml(data).encode("utf-8"), 9)
    ).decode("ascii")

    encoded = encode_pob_code(multi_code, {7, 8, 9})

    # parse_pob_code only reads dict specs, so inspect the XML directly.
    out = parse_xml(zlib.decompress(base64.b64decode(encoded)).decode("utf-8"))
    out_root = out.get("PathOfBuilding2") or out.get("PathOfBuilding")
    out_specs = out_root["Tree"]["Spec"]
    assert out_specs[0]["@nodes"] == "111,222"  # inactive spec untouched
    assert out_specs[1]["@nodes"] == "7,8,9"    # active spec patched


def test_invalid_base64_raises_invalid_format():
    """Garbage input should raise InvalidFormatError, not a raw exception."""
    from src.parsers.exceptions import InvalidFormatError

    with pytest.raises(InvalidFormatError):
        encode_pob_code("!!!not base64 zlib!!!", {1, 2, 3})
