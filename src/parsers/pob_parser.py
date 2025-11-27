"""Parser for Path of Building import codes.

Implements the complete pipeline: Base64 → zlib → XML → BuildData
Reference: tech-spec-epic-1.md:272-313, workflow at lines 390-426
"""

import base64
import logging
import zlib
from typing import Set, List, Optional

from .xml_utils import parse_xml
from .exceptions import PoBParseError, InvalidFormatError, UnsupportedVersionError
from ..models.build_data import BuildData, CharacterClass, Item, Skill


logger = logging.getLogger(__name__)


# Constants
MAX_CODE_SIZE_KB = 100
MAX_CODE_SIZE_BYTES = MAX_CODE_SIZE_KB * 1024


def parse_pob_code(code: str) -> BuildData:
    """Parse Base64-encoded PoB code into BuildData object.

    Implements complete parsing pipeline with defensive error handling:
    1. Validate input size (<100KB)
    2. Base64 decode
    3. zlib decompress
    4. XML parse
    5. Extract build data
    6. Validate PoE 2 version
    7. Construct BuildData

    Args:
        code: Base64 string (PoB import code)

    Returns:
        BuildData object with all build information

    Raises:
        PoBParseError: If code is invalid, corrupted, or unsupported
        InvalidFormatError: If code is malformed or corrupted
        UnsupportedVersionError: If code is from PoE 1 or unsupported version

    Example:
        >>> code = "eNqVVktv..."
        >>> build = parse_pob_code(code)
        >>> print(f"{build.character_class.value}, Level {build.level}")
        Witch, Level 90
    """
    # Step 1: Validate input size
    code_size_bytes = len(code.encode('utf-8'))
    if code_size_bytes > MAX_CODE_SIZE_BYTES:
        size_kb = code_size_bytes / 1024
        raise PoBParseError(
            f"Build code too large: {size_kb:.1f} KB. Maximum: {MAX_CODE_SIZE_KB} KB. "
            f"Please verify the code is complete and not corrupted."
        )

    # Step 2: Base64 decode
    try:
        compressed_data = base64.b64decode(code)
    except Exception as e:
        raise InvalidFormatError(
            f"Invalid Base64 encoding. The PoB code appears to be corrupted. "
            f"Cause: {e}"
        ) from e

    # Step 3: zlib decompress
    try:
        xml_str = zlib.decompress(compressed_data).decode('utf-8')
    except Exception as e:
        raise InvalidFormatError(
            f"Failed to decompress (corrupted data). The PoB code may be incomplete or damaged. "
            f"Cause: {e}"
        ) from e

    # Step 4: XML parse
    try:
        data = parse_xml(xml_str)
    except InvalidFormatError:
        # Re-raise with original context
        raise
    except Exception as e:
        raise InvalidFormatError(f"Unable to parse XML structure: {e}") from e

    # Step 5: Extract build data from dict
    try:
        # Support both PoE 1 (<PathOfBuilding>) and PoE 2 (<PathOfBuilding2>) formats
        pob_root = data.get("PathOfBuilding2") or data.get("PathOfBuilding")
        if not pob_root:
            raise InvalidFormatError("Missing PathOfBuilding or PathOfBuilding2 root element in XML")

        build_section = pob_root.get("Build")
        if not build_section:
            raise InvalidFormatError("Missing Build section in PoB XML")

        # Step 6: Validate PoE 2 version (reject PoE 1 codes)
        tree_version = _extract_tree_version(pob_root)
        if not _is_poe2_version(tree_version):
            raise UnsupportedVersionError(
                f"This optimizer only supports PoE 2 builds. "
                f"Detected version: {tree_version}. "
                f"Please export your build from the PoE 2 version of Path of Building."
            )

        # Extract character data
        character_class = _extract_character_class(build_section)
        level = _extract_level(build_section)
        ascendancy = build_section.get("@ascendClassName")

        # Extract passive tree
        passive_nodes = _extract_passive_nodes(pob_root)

        # Extract items
        items = _extract_items(pob_root)

        # Extract skills
        skills = _extract_skills(pob_root)

        # Extract configuration
        config = _extract_config(pob_root)

        # Extract metadata
        build_name = build_section.get("@buildName")
        notes = pob_root.get("Notes")

        # Step 7: Construct BuildData object
        return BuildData(
            character_class=character_class,
            level=level,
            ascendancy=ascendancy,
            passive_nodes=passive_nodes,
            items=items,
            skills=skills,
            tree_version=tree_version,
            build_name=build_name,
            notes=notes,
            config=config
        )

    except (InvalidFormatError, UnsupportedVersionError):
        # Re-raise custom exceptions
        raise
    except Exception as e:
        raise PoBParseError(f"Failed to extract build data: {e}") from e


def _extract_tree_version(pob_root: dict) -> str:
    """Extract passive tree version from PoB data.

    Args:
        pob_root: PathOfBuilding root dictionary

    Returns:
        Tree version string (e.g., "0_1" for PoE 2 Early Access, "3_24" for PoE 2 release)
    """
    # First check Build element's targetVersion (PoE 2 format)
    build_section = pob_root.get("Build", {})
    if isinstance(build_section, dict):
        target_version = build_section.get("@targetVersion")
        if target_version:
            return target_version

    # Fallback: check Tree section's treeVersion (older format)
    tree_section = pob_root.get("Tree", {})
    if isinstance(tree_section, dict):
        # Check for Spec sub-element with treeVersion
        spec = tree_section.get("Spec")
        if isinstance(spec, dict):
            tree_version = spec.get("@treeVersion")
            if tree_version:
                return tree_version
        # Could also be a list of Specs
        elif isinstance(spec, list) and len(spec) > 0:
            tree_version = spec[0].get("@treeVersion")
            if tree_version:
                return tree_version

    return "0_1"  # Default to PoE 2 Early Access


def _is_poe2_version(tree_version: str) -> bool:
    """Check if tree version is PoE 2.

    Args:
        tree_version: Tree version string

    Returns:
        True if PoE 2, False if PoE 1 or unknown
    """
    # PoE 2 Early Access uses version "0_1" (from targetVersion attribute)
    # PoE 2 may also use "3_24" or higher in passive tree versions
    # PoE 1 uses versions like "3_23" or lower

    # Check for PoE 2 Early Access format (0_1, 0_2, etc.)
    if tree_version.startswith("0_"):
        return True

    # Check for PoE 2 release versions (3_24+)
    if tree_version.startswith("3_"):
        try:
            minor_version = int(tree_version.split("_")[1])
            return minor_version >= 24  # PoE 2 release starts at 3.24
        except (ValueError, IndexError):
            # Ambiguous format - reject for safety
            return False

    # Unknown version format - reject for safety
    return False


def _extract_character_class(build_section: dict) -> CharacterClass:
    """Extract character class from build section.

    Args:
        build_section: Build dictionary

    Returns:
        CharacterClass enum value

    Raises:
        InvalidFormatError: If class is missing or invalid
    """
    class_name = build_section.get("@className")
    if not class_name:
        raise InvalidFormatError("Missing character class in build data")

    try:
        return CharacterClass(class_name)
    except ValueError:
        # Try case-insensitive match
        for char_class in CharacterClass:
            if char_class.value.lower() == class_name.lower():
                return char_class
        raise InvalidFormatError(f"Unknown character class: {class_name}")


def _extract_level(build_section: dict) -> int:
    """Extract character level from build section.

    Args:
        build_section: Build dictionary

    Returns:
        Character level (1-100)

    Raises:
        InvalidFormatError: If level is missing or invalid
    """
    level_str = build_section.get("@level")
    if not level_str:
        raise InvalidFormatError("Missing character level in build data")

    try:
        level = int(level_str)
        if not 1 <= level <= 100:
            raise InvalidFormatError(f"Invalid character level: {level} (must be 1-100)")
        return level
    except ValueError as e:
        raise InvalidFormatError(f"Invalid level format: {level_str}") from e


def _extract_passive_nodes(pob_root: dict) -> Set[int]:
    """Extract allocated passive node IDs from tree spec.

    Args:
        pob_root: PathOfBuilding root dictionary

    Returns:
        Set of allocated passive node IDs
    """
    tree_section = pob_root.get("Tree", {})
    if not isinstance(tree_section, dict):
        return set()

    spec = tree_section.get("Spec", {})
    if not isinstance(spec, dict):
        return set()

    # Node IDs may be in different formats depending on PoB version
    nodes_str = spec.get("@nodes", "")
    if not nodes_str:
        return set()

    # Parse comma-separated node IDs
    try:
        node_ids = set(int(node_id.strip()) for node_id in nodes_str.split(",") if node_id.strip())
        return node_ids
    except ValueError:
        # If parsing fails, return empty set (non-critical)
        return set()


def _extract_items(pob_root: dict) -> List[Item]:
    """Extract equipment items from PoB data.

    Story 2.9 Milestone 1: Enhanced to parse weapon stats for DPS calculations.
    Parses physical damage, attack speed, crit chance, and added damage from item text.

    Args:
        pob_root: PathOfBuilding root dictionary

    Returns:
        List of Item objects with weapon stats populated
    """
    import re

    items = []

    # Items section is directly under pob_root (which is already PathOfBuilding2)
    items_section = pob_root.get("Items", {})
    if not isinstance(items_section, dict):
        return items

    # Get Item elements from Items section
    item_elements = items_section.get("Item", [])
    if not item_elements:
        return items

    # Handle single item (dict) vs multiple items (list)
    if isinstance(item_elements, dict):
        item_elements = [item_elements]

    for item_data in item_elements:
        if not isinstance(item_data, dict):
            continue

        try:
            # Get item text content
            item_text = item_data.get("#text", "")
            item_id = item_data.get("@id", "Unknown")

            if not item_text:
                continue

            lines = item_text.strip().split('\n')
            if len(lines) < 2:
                continue

            # Parse rarity (first line: "Rarity: RARE")
            rarity = "Normal"
            if lines[0].startswith("Rarity:"):
                rarity = lines[0].split(":", 1)[1].strip()

            # Parse item name (second line after "Rarity:")
            name = lines[1].strip() if len(lines) > 1 else "Unknown Item"

            # Parse base type (third line, usually the base item type)
            base_type = lines[2].strip() if len(lines) > 2 else ""

            # Parse weapon stats from mod lines
            stats = {
                "slot": item_id,
                "name": name,
                "base_type": base_type,
                "rarity": rarity
            }

            # Extract weapon stats (for DPS calculation)
            for line in lines:
                line = line.strip()

                # Physical damage: "Adds X to Y Physical Damage"
                match = re.search(r'Adds (\d+) to (\d+) Physical Damage', line, re.IGNORECASE)
                if match:
                    stats["phys_min"] = stats.get("phys_min", 0) + int(match.group(1))
                    stats["phys_max"] = stats.get("phys_max", 0) + int(match.group(2))

                # Lightning damage
                match = re.search(r'Adds (\d+) to (\d+) Lightning [Dd]amage', line)
                if match:
                    stats["lightning_min"] = stats.get("lightning_min", 0) + int(match.group(1))
                    stats["lightning_max"] = stats.get("lightning_max", 0) + int(match.group(2))

                # Cold damage
                match = re.search(r'Adds (\d+) to (\d+) Cold [Dd]amage', line)
                if match:
                    stats["cold_min"] = stats.get("cold_min", 0) + int(match.group(1))
                    stats["cold_max"] = stats.get("cold_max", 0) + int(match.group(2))

                # Fire damage
                match = re.search(r'Adds (\d+) to (\d+) Fire [Dd]amage', line)
                if match:
                    stats["fire_min"] = stats.get("fire_min", 0) + int(match.group(1))
                    stats["fire_max"] = stats.get("fire_max", 0) + int(match.group(2))

                # Attack Speed: "X% increased Attack Speed"
                match = re.search(r'(\d+)% increased Attack Speed', line, re.IGNORECASE)
                if match:
                    stats["attack_speed_inc"] = stats.get("attack_speed_inc", 0) + int(match.group(1))

                # Critical Strike Chance
                match = re.search(r'\+(\d+)% to Critical Hit Chance', line, re.IGNORECASE)
                if match:
                    stats["crit_chance_add"] = stats.get("crit_chance_add", 0) + int(match.group(1))

            item = Item(
                slot=f"Weapon{item_id}" if _is_weapon_base(base_type) else f"Slot{item_id}",
                name=name,
                rarity=rarity,
                item_level=1,  # Not critical for calculations
                stats=stats
            )
            items.append(item)

        except (ValueError, KeyError) as e:
            # Skip malformed items (log for debugging)
            logger.debug(
                "Skipped malformed item during parsing: %s. Item data: %s",
                str(e), item_data
            )
            continue

    return items


def _is_weapon_base(base_type: str) -> bool:
    """Check if base type is a weapon.

    Story 2.9: Simple heuristic for weapon detection.
    """
    weapon_keywords = [
        "Bow", "Staff", "Wand", "Sword", "Axe", "Mace", "Claw",
        "Dagger", "Sceptre", "Crossbow", "Quarterstaff", "Flail"
    ]
    return any(kw in base_type for kw in weapon_keywords)


def _is_minion_skill(skill_id: str) -> bool:
    """Check if skill is a minion/summon skill.

    Story 2.9: Temporary filter - minion skills cause calcs.initEnv() crash.
    TODO: Implement proper minion support in MinimalCalc.lua
    """
    minion_keywords = ["Summon", "Raise", "Animate", "Companion"]
    return any(kw in skill_id for kw in minion_keywords)


def _extract_skills(pob_root: dict) -> List[Skill]:
    """Extract active skills from PoB data.

    Story 2.9 Phase 2: Enhanced to capture skillId, supports, and all gem data
    needed for MinimalCalc.lua skill processing.

    Args:
        pob_root: PathOfBuilding root dictionary

    Returns:
        List of Skill objects with full gem data
    """
    skills = []
    skills_section = pob_root.get("Skills", {})
    if not isinstance(skills_section, dict):
        return skills

    # Handle SkillSet wrapper (PoE 2 format)
    skill_set = skills_section.get("SkillSet", {})
    if isinstance(skill_set, list):
        skill_set = skill_set[0] if skill_set else {}
    elif not isinstance(skill_set, dict):
        skill_set = {}

    # Skills may be in SkillSet or directly in Skills section
    skill_elements = skill_set.get("Skill", []) if skill_set else skills_section.get("Skill", [])
    if not skill_elements:
        return skills

    # Handle single skill (dict) vs multiple skills (list)
    if isinstance(skill_elements, dict):
        skill_elements = [skill_elements]

    for skill_data in skill_elements:
        if not isinstance(skill_data, dict):
            continue

        # Skip disabled skills
        if skill_data.get("@enabled", "true").lower() != "true":
            continue

        try:
            # Get all gems in this skill group
            gems = skill_data.get("Gem", [])
            if isinstance(gems, dict):
                gems = [gems]
            elif not isinstance(gems, list):
                gems = []

            if not gems:
                continue

            # First gem is the active skill, rest are supports
            active_gem = gems[0]
            support_gems = []

            # Parse active gem
            skill_id = active_gem.get("@skillId", "")
            if not skill_id:
                # Fallback to variantId or nameSpec
                skill_id = active_gem.get("@variantId", active_gem.get("@nameSpec", "Unknown"))

            # Parse support gems (all gems after the first)
            for support in gems[1:]:
                if isinstance(support, dict) and support.get("@enabled", "true").lower() == "true":
                    support_id = support.get("@skillId", support.get("@variantId", ""))
                    if support_id:
                        support_gems.append({
                            "skillId": support_id,
                            "level": int(support.get("@level", 1)),
                            "quality": int(support.get("@quality", 0)),
                            "nameSpec": support.get("@nameSpec", "")
                        })

            # Story 2.9: Skip minion skills (temporary workaround)
            if _is_minion_skill(skill_id):
                logger.debug(f"Skipping minion skill: {skill_id} (not yet supported)")
                continue

            skill = Skill(
                name=active_gem.get("@nameSpec", "Unknown Skill"),
                level=int(active_gem.get("@level", 1)),
                quality=int(active_gem.get("@quality", 0)),
                enabled=True,
                support_gems=support_gems,
                skill_id=skill_id  # Added for MinimalCalc.lua integration
            )
            skills.append(skill)
        except (ValueError, KeyError) as e:
            # Skip malformed skills (log for debugging)
            logger.debug(
                "Skipped malformed skill during parsing: %s. Skill data: %s",
                str(e), skill_data
            )
            continue

    return skills


def _extract_config(pob_root: dict) -> dict:
    """Extract configuration values from PoB Config section.

    Parses both Input and Placeholder tags for enemy and calculation settings.
    Keeps them separate as PoB engine expects.

    Args:
        pob_root: PathOfBuilding root dictionary

    Returns:
        Dictionary with "input" and "placeholder" keys containing config values
    """
    result = {"input": {}, "placeholder": {}}
    config_section = pob_root.get("Config", {})
    if not isinstance(config_section, dict):
        return result

    # Get the active config set
    config_set = config_section.get("ConfigSet")
    if not config_set:
        return result

    # Handle single or multiple config sets
    if isinstance(config_set, list):
        # Use first config set if multiple exist
        config_set = config_set[0] if config_set else {}

    if not isinstance(config_set, dict):
        return result

    # Parse Input tags (user-modified values)
    inputs = config_set.get("Input", [])
    logger.debug(f"Found {len(inputs) if isinstance(inputs, list) else 1 if inputs else 0} Input tags")
    if isinstance(inputs, dict):
        inputs = [inputs]
    elif not isinstance(inputs, list):
        inputs = []

    for input_elem in inputs:
        logger.debug(f"Processing Input: {input_elem}")
        if isinstance(input_elem, dict):
            name = input_elem.get("@name")
            value = input_elem.get("@number") or input_elem.get("@string")
            if name and value is not None:
                try:
                    # Convert to appropriate type
                    if isinstance(value, (int, float)):
                        result["input"][name] = value
                    elif isinstance(value, str):
                        result["input"][name] = int(value) if value.lstrip('-').isdigit() else float(value)
                    else:
                        result["input"][name] = value
                except (ValueError, AttributeError, TypeError):
                    result["input"][name] = value

    # Parse Placeholder tags (default values)
    placeholders = config_set.get("Placeholder", [])
    if isinstance(placeholders, dict):
        placeholders = [placeholders]
    elif not isinstance(placeholders, list):
        placeholders = []

    for placeholder in placeholders:
        if isinstance(placeholder, dict):
            name = placeholder.get("@name")
            value = placeholder.get("@number") or placeholder.get("@string")
            if name and value is not None:
                try:
                    # Convert to appropriate type
                    if isinstance(value, (int, float)):
                        result["placeholder"][name] = value
                    elif isinstance(value, str):
                        result["placeholder"][name] = int(value) if value.lstrip('-').isdigit() else float(value)
                    else:
                        result["placeholder"][name] = value
                except (ValueError, AttributeError, TypeError):
                    result["placeholder"][name] = value

    return result
