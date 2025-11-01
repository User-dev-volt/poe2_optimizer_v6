"""Data models for Path of Building build representation"""

from dataclasses import dataclass, field
from typing import Optional, Set, List
from enum import Enum


class CharacterClass(Enum):
    """PoE 2 character classes"""
    WITCH = "Witch"
    WARRIOR = "Warrior"
    RANGER = "Ranger"
    MONK = "Monk"
    MERCENARY = "Mercenary"
    SORCERESS = "Sorceress"
    HUNTRESS = "Huntress"


@dataclass
class Item:
    """Equipment item"""
    slot: str  # "Weapon1", "BodyArmour", etc.
    name: str
    rarity: str  # "Normal", "Magic", "Rare", "Unique"
    item_level: int
    stats: dict  # Modifiers and stats


@dataclass
class Skill:
    """Active skill gem"""
    name: str
    level: int
    quality: int
    enabled: bool
    support_gems: List[str] = field(default_factory=list)


@dataclass
class BuildData:
    """Complete build configuration"""
    # Character identity
    character_class: CharacterClass
    level: int  # 1-100
    ascendancy: Optional[str] = None  # "Elementalist", "Blood Mage", etc.

    # Passive tree
    passive_nodes: Set[int] = field(default_factory=set)  # Set of allocated passive node IDs

    # Equipment and skills
    items: List[Item] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)

    # PoB metadata
    tree_version: str = "3_24"  # "3_24" for PoE 2
    build_name: Optional[str] = None
    notes: Optional[str] = None
    config: dict = field(default_factory=dict)  # Enemy/calculation configuration from PoB Config tab

    # Calculated properties
    @property
    def allocated_point_count(self) -> int:
        """Number of allocated passive points"""
        return len(self.passive_nodes)

    @property
    def unallocated_points(self) -> int:
        """Calculate unallocated points based on level.

        Formula: (level - 1) + 24 = level + 23
        - Characters gain 1 passive point per level from 2 to 100 (99 points total)
        - Campaign quest rewards provide 24 additional passive points
        - Total at level 100: 123 passive skill points
        Source: Path of Exile 2 campaign progression (2025)
        """
        max_points = self.level + 23  # PoE 2: (level - 1) from leveling + 24 from quests
        return max(0, max_points - self.allocated_point_count)
