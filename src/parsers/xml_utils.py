"""XML parsing utilities for PoB data structures.

Wraps xmltodict for consistent XML handling throughout the parser module.
"""

import xmltodict
from typing import Dict, Any
from .exceptions import InvalidFormatError


def parse_xml(xml_str: str) -> Dict[str, Any]:
    """Parse XML string into Python dictionary.

    Args:
        xml_str: XML string to parse

    Returns:
        Dictionary representation of XML structure

    Raises:
        InvalidFormatError: If XML is malformed or cannot be parsed

    Example:
        >>> xml = '<PathOfBuilding><Build level="90"/></PathOfBuilding>'
        >>> data = parse_xml(xml)
        >>> data['PathOfBuilding']['Build']['@level']
        '90'
    """
    try:
        return xmltodict.parse(xml_str)
    except Exception as e:
        raise InvalidFormatError(f"Unable to parse XML structure: {e}") from e


def build_xml(data: Dict[str, Any]) -> str:
    """Convert Python dictionary to XML string.

    Args:
        data: Dictionary to convert to XML

    Returns:
        XML string representation

    Raises:
        InvalidFormatError: If data cannot be serialized to XML

    Example:
        >>> data = {'PathOfBuilding': {'Build': {'@level': '90'}}}
        >>> xml = build_xml(data)
        >>> '<PathOfBuilding><Build level="90"/></PathOfBuilding>' in xml
        True
    """
    try:
        return xmltodict.unparse(data, pretty=False)
    except Exception as e:
        raise InvalidFormatError(f"Unable to build XML from data: {e}") from e
