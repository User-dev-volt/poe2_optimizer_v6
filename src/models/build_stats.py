"""Data models for calculated build statistics"""

from dataclasses import dataclass, field
from typing import Dict
import math


@dataclass
class BuildStats:
    """
    Calculated character statistics from PoB calculation engine.

    All stats are extracted from env.player.output after running
    PoB's calculation modules (calcs.initEnv + calcs.perform).

    Fields:
        total_dps: Total combined DPS (float, 0 if no skills configured)
        effective_hp: Effective HP considering defenses (float)
        life: Maximum life pool (int)
        energy_shield: Maximum energy shield (int)
        mana: Maximum mana pool (int)
        resistances: Elemental and chaos resistances (dict with fire/cold/lightning/chaos keys)
        armour: Total armour rating (int, optional)
        evasion: Total evasion rating (int, optional)
        block_chance: Block chance % (float, optional)
        spell_block_chance: Spell block chance % (float, optional)
        movement_speed: Movement speed % (float, optional)

    Validation:
        All numeric fields must be valid numbers (not NaN or infinity).
        Validation is performed on initialization via __post_init__.

    Example:
        >>> stats = BuildStats(
        ...     total_dps=125000.5,
        ...     effective_hp=50000.0,
        ...     life=4500,
        ...     energy_shield=2000,
        ...     mana=1200,
        ...     resistances={"fire": 75, "cold": 75, "lightning": 75, "chaos": 20}
        ... )
        >>> stats.to_dict()
        {'total_dps': 125000.5, 'effective_hp': 50000.0, ...}

    References:
        - Tech Spec Epic 1: Lines 180-229 (BuildStats data model)
        - Story 1.5 Task 1: Design BuildStats Data Model
    """

    # Core stats (required)
    total_dps: float
    effective_hp: float
    life: int
    energy_shield: int
    mana: int
    resistances: Dict[str, int] = field(default_factory=dict)

    # Defense stats (optional)
    armour: int = 0
    evasion: int = 0
    block_chance: float = 0.0
    spell_block_chance: float = 0.0
    movement_speed: float = 0.0

    def __post_init__(self):
        """
        Validate numeric fields after initialization.

        Ensures:
            - No NaN values
            - No infinity values
            - Resistances dict has expected keys

        Raises:
            ValueError: If validation fails
        """
        # Validate float fields
        float_fields = [
            ('total_dps', self.total_dps),
            ('effective_hp', self.effective_hp),
            ('block_chance', self.block_chance),
            ('spell_block_chance', self.spell_block_chance),
            ('movement_speed', self.movement_speed)
        ]

        for field_name, value in float_fields:
            if math.isnan(value):
                raise ValueError(f"{field_name} cannot be NaN")
            if math.isinf(value):
                raise ValueError(f"{field_name} cannot be infinity")

        # Validate int fields (int can't be NaN/inf in Python, but check for sanity)
        int_fields = [
            ('life', self.life),
            ('energy_shield', self.energy_shield),
            ('mana', self.mana),
            ('armour', self.armour),
            ('evasion', self.evasion)
        ]

        for field_name, value in int_fields:
            if not isinstance(value, int):
                raise ValueError(f"{field_name} must be an integer, got {type(value)}")

        # Ensure resistances dict has expected keys (if not empty)
        if self.resistances:
            expected_keys = {'fire', 'cold', 'lightning', 'chaos'}
            missing_keys = expected_keys - set(self.resistances.keys())
            if missing_keys:
                # Fill missing keys with 0
                for key in missing_keys:
                    self.resistances[key] = 0

            # Validate resistance values are integers
            for res_type, res_value in self.resistances.items():
                if not isinstance(res_value, int):
                    raise ValueError(
                        f"Resistance '{res_type}' must be an integer, got {type(res_value)}"
                    )

    def to_dict(self) -> Dict:
        """
        Convert BuildStats to dictionary for JSON serialization.

        Returns:
            Dictionary with all stats as key-value pairs

        Example:
            >>> stats.to_dict()
            {
                'total_dps': 125000.5,
                'effective_hp': 50000.0,
                'life': 4500,
                'energy_shield': 2000,
                'mana': 1200,
                'resistances': {'fire': 75, 'cold': 75, 'lightning': 75, 'chaos': 20},
                'armour': 5000,
                'evasion': 1000,
                'block_chance': 15.0,
                'spell_block_chance': 10.0,
                'movement_speed': 100.0
            }
        """
        return {
            'total_dps': self.total_dps,
            'effective_hp': self.effective_hp,
            'life': self.life,
            'energy_shield': self.energy_shield,
            'mana': self.mana,
            'resistances': self.resistances.copy(),  # Return a copy to prevent mutation
            'armour': self.armour,
            'evasion': self.evasion,
            'block_chance': self.block_chance,
            'spell_block_chance': self.spell_block_chance,
            'movement_speed': self.movement_speed
        }
