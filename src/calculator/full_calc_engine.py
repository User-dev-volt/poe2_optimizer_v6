"""FullCalcEngine -- the Truth Engine behind ``calculate_build_stats`` (Story 4.2).

Graduates Story 4.1's spike-grade ``driver.lua`` lane into a production calculator
reachable via the keyword selector ``calculate_build_stats(build, engine="full")``.
It computes GUI-accurate stats through PoB's REAL calc chain (closing the
~4%-of-GUI MinimalCalc reporting gap) by:

  1. serializing the build to PoB XML via
     :func:`~src.parsers.pob_parser.patch_passive_nodes_to_xml` (writing the
     allocated ``@nodes`` AND the resolved ``Build @mainSocketGroup`` -- G2), then
  2. running it through the respawnable :class:`~src.calculator.worker_pool.WorkerPool`
     (XML-direct into PoB's own PassiveSpec; ADR-007), then
  3. mapping the ``GET_STATS`` JSON dict to :class:`BuildStats` with the same
     int-cast / ``__post_init__``-safe shape as ``full_pob_engine._extract_stats``,
     extended with a Python-side first-nonzero DPS fallback.

It COEXISTS with the MinimalCalc/Subprocess hybrid (``engine="auto"``); item 8
retires MinimalCalc. This engine is a THIRD coexisting route.

Fences (both raise :class:`CalculationError`, which the two-track reporting guard
downgrades to MinimalCalc reporting -- never a mixed-scale pair):
  * ``build.source_xml is None`` -> FullCalc unavailable for this build.
  * ``build.is_multi_spec`` -> the item-3 ``activeSpec`` READ fix has not landed,
    so ``passive_nodes`` is an empty set and patching would report an unallocated
    tree (G3). MANDATORY fence, not a nicety.

[Source: src/calculator/full_pob_engine.py:257-306 (_extract_stats shape);
 src/calculator/driver.lua:356-377 (GET_STATS reader); src/models/build_stats.py:86-103
 (__post_init__ int/NaN guards); src/parsers/pob_parser.py (patch_passive_nodes_to_xml)]
"""

from __future__ import annotations

import logging
import math
import threading
from typing import Any, Dict, List, Optional

from ..models.build_data import BuildData
from ..models.build_stats import BuildStats
from .exceptions import CalculationError
from .worker_pool import get_worker_pool

logger = logging.getLogger(__name__)

# The explicit stat list requested from the worker. driver.lua's GET_STATS returns
# only the keys present in mainOutput, so we ask for every field the BuildStats
# map reads (its DEFAULT_STATS omits armour/evasion/block/movement).
_FULLCALC_STATS: List[str] = [
    "TotalDPS", "CombinedDPS", "FullDPS", "TotalDot",
    "Life", "EnergyShield", "Mana", "TotalEHP", "EHP",
    "FireResist", "ColdResist", "LightningResist", "ChaosResist",
    "Armour", "Evasion",
    "BlockChance", "EffectiveBlockChance",
    "SpellBlockChance", "EffectiveSpellBlockChance",
    "MovementSpeed", "EffectiveMovementSpeedMod",
]


class FullCalcEngine:
    """Real-PoB calculator driven by the respawnable worker pool."""

    def calculate(self, build: BuildData) -> BuildStats:
        """Compute GUI-accurate :class:`BuildStats` for ``build`` via a worker.

        Raises:
            CalculationError: if ``source_xml`` is unavailable, the build is
                multi-``<Spec>`` (fenced until item 3), or the worker fails after
                its one automatic retry.
        """
        source_xml = getattr(build, "source_xml", None)
        if source_xml is None:
            raise CalculationError(
                "FullCalcEngine requires build.source_xml, which is unavailable "
                "for this build (engine='full' cannot run; reporting falls back "
                "to MinimalCalc)."
            )
        if getattr(build, "is_multi_spec", False):
            raise CalculationError(
                "FullCalcEngine does not yet support multi-<Spec> builds (the "
                "activeSpec READ fix is Epic 4 item 3); reporting falls back to "
                "MinimalCalc."
            )

        # Serialize with the resolved main socket group (G2) so the worker calcs
        # the SAME main skill the Python search chose.
        from ..parsers.pob_parser import patch_passive_nodes_to_xml

        xml = patch_passive_nodes_to_xml(
            source_xml,
            build.passive_nodes,
            main_socket_group=build.main_socket_group,
        )

        pool = get_worker_pool()
        stats_dict = pool.calculate(
            xml,
            name=build.build_name or "fullcalc",
            stats=_FULLCALC_STATS,
        )
        return self._stats_from_mainoutput(stats_dict)

    @staticmethod
    def _stats_from_mainoutput(out: Dict[str, Any]) -> BuildStats:
        """Map a ``GET_STATS`` dict to :class:`BuildStats`.

        Ported from ``full_pob_engine._extract_stats`` but DICT-safe: ``GET_STATS``
        returns a JSON dict (not a Lua table) and OMITS absent stats entirely, so
        every read goes through ``.get(key, default)``. The ``int(...)`` casts are
        KEPT -- ``BuildStats.__post_init__`` hard-rejects non-int life/ES/mana/
        armour/evasion, so a verbatim float copy would trip it. The headline DPS is
        the Python-side first-nonzero(TotalDPS, CombinedDPS, FullDPS, TotalDot);
        driver.lua stays a verbatim reader (no fallback logic in Lua).
        """
        def num(key: str, default: float = 0.0) -> float:
            v = out.get(key)
            if v is None:
                return default
            try:
                f = float(v)
            except (TypeError, ValueError):
                return default
            # PoB can emit NaN/Infinity and json.loads parses those tokens; a
            # non-finite value would make int(...) raise ValueError/OverflowError
            # (or trip BuildStats.__post_init__) OUT of calculate() as an
            # unclassified error rather than a CalculationError. Coerce to default.
            if not math.isfinite(f):
                return default
            return f

        # first-nonzero DPS fallback (AC-4.2.2 row f), computed Python-side.
        total_dps = (
            num("TotalDPS")
            or num("CombinedDPS")
            or num("FullDPS")
            or num("TotalDot")
        )

        life = int(num("Life"))
        energy_shield = int(num("EnergyShield"))
        mana = int(num("Mana"))
        ehp = num("TotalEHP") or num("EHP") or float(life)

        resistances = {
            "fire": int(num("FireResist")),
            "cold": int(num("ColdResist")),
            "lightning": int(num("LightningResist")),
            "chaos": int(num("ChaosResist")),
        }

        armour = int(num("Armour"))
        evasion = int(num("Evasion"))
        block_chance = num("BlockChance") or num("EffectiveBlockChance")
        spell_block = num("SpellBlockChance") or num("EffectiveSpellBlockChance")
        movement_speed = num("MovementSpeed") or num("EffectiveMovementSpeedMod")

        return BuildStats(
            total_dps=total_dps,
            effective_hp=ehp,
            life=life,
            energy_shield=energy_shield,
            mana=mana,
            resistances=resistances,
            armour=armour,
            evasion=evasion,
            block_chance=block_chance,
            spell_block_chance=spell_block,
            movement_speed=movement_speed,
        )


# =========================================================================== #
# Module singleton
# =========================================================================== #
_engine_lock = threading.Lock()
_engine: Optional[FullCalcEngine] = None


def get_full_calc_engine() -> FullCalcEngine:
    """Return the process-wide :class:`FullCalcEngine` singleton.

    Stateless apart from the shared worker pool, so a single instance is safe
    across threads (the pool is process-based, not thread-local).
    """
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = FullCalcEngine()
        return _engine
