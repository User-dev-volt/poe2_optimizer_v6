"""Fast unit tests for patch_passive_nodes_to_xml (Story 4.2 AC-4.2.7/4.2.8, T8).

The primitive extracted from encode_pob_code, now shared with FullCalcEngine.
NO LuaJIT. Covers @nodes patching, the G2 @mainSocketGroup write (and its
preservation when None), multi-<Spec> activeSpec selection, error paths, and the
encode_pob_code refactor's byte-behaviour (must NOT touch @mainSocketGroup).
"""

import base64
import zlib

import pytest

from src.parsers.exceptions import InvalidFormatError
from src.parsers.pob_parser import patch_passive_nodes_to_xml, encode_pob_code
from src.parsers.xml_utils import parse_xml

_XML = (
    '<PathOfBuilding2><Build level="90" className="Witch" mainSocketGroup="2"/>'
    '<Tree activeSpec="1"><Spec nodes="10,20"/></Tree></PathOfBuilding2>'
)


def _root(xml):
    d = parse_xml(xml)
    return d.get("PathOfBuilding2") or d.get("PathOfBuilding")


def test_writes_nodes_sorted_comma_joined():
    out = patch_passive_nodes_to_xml(_XML, {30, 5, 100})
    assert _root(out)["Tree"]["Spec"]["@nodes"] == "5,30,100"


def test_accepts_list_and_set_equally():
    a = _root(patch_passive_nodes_to_xml(_XML, [3, 1, 2]))["Tree"]["Spec"]["@nodes"]
    b = _root(patch_passive_nodes_to_xml(_XML, {1, 2, 3}))["Tree"]["Spec"]["@nodes"]
    assert a == b == "1,2,3"


def test_main_socket_group_preserved_when_none():
    out = patch_passive_nodes_to_xml(_XML, {1})  # default main_socket_group=None
    assert _root(out)["Build"]["@mainSocketGroup"] == "2"  # untouched


def test_g2_writes_main_socket_group_when_given():
    out = patch_passive_nodes_to_xml(_XML, {1}, main_socket_group=5)
    assert _root(out)["Build"]["@mainSocketGroup"] == "5"


def test_multi_spec_patches_only_active():
    xml = (
        '<PathOfBuilding2><Build level="90" className="Witch"/>'
        '<Tree activeSpec="2"><Spec nodes="1,2"/><Spec nodes="3,4"/></Tree></PathOfBuilding2>'
    )
    out = patch_passive_nodes_to_xml(xml, {7, 8, 9})
    specs = _root(out)["Tree"]["Spec"]
    assert specs[0]["@nodes"] == "1,2"       # inactive untouched
    assert specs[1]["@nodes"] == "7,8,9"     # active patched


def test_missing_tree_raises():
    with pytest.raises(InvalidFormatError):
        patch_passive_nodes_to_xml("<PathOfBuilding2><Build/></PathOfBuilding2>", {1})


def test_missing_build_only_raises_when_writing_main_socket_group():
    xml = '<PathOfBuilding2><Tree><Spec nodes="1"/></Tree></PathOfBuilding2>'
    # No Build section: fine when we are NOT writing @mainSocketGroup.
    out = patch_passive_nodes_to_xml(xml, {2})
    assert _root(out)["Tree"]["Spec"]["@nodes"] == "2"
    # But raises when asked to write @mainSocketGroup into a missing Build.
    with pytest.raises(InvalidFormatError):
        patch_passive_nodes_to_xml(xml, {2}, main_socket_group=1)


def test_encode_pob_code_refactor_preserves_main_socket_group():
    """The encode_pob_code refactor (call the shared primitive with
    main_socket_group=None) must NOT change @mainSocketGroup -- export stays
    byte-behaviour-identical apart from the allocated nodes."""
    code = base64.b64encode(zlib.compress(_XML.encode("utf-8"), 9)).decode("ascii")
    out_code = encode_pob_code(code, {1, 2})
    out_xml = zlib.decompress(base64.b64decode(out_code)).decode("utf-8")
    assert _root(out_xml)["Build"]["@mainSocketGroup"] == "2"
    assert _root(out_xml)["Tree"]["Spec"]["@nodes"] == "1,2"
