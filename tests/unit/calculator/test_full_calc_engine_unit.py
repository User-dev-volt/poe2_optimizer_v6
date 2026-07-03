"""Fast/unmarked FullCalcEngine tests: stat mapping + fences (Story 4.2, T8).

NO LuaJIT: the GET_STATS->BuildStats map is a pure function; the source_xml and
multi-<Spec> fences raise BEFORE any worker is touched; the happy path runs
through a fake pool. The real-engine ±0.1% seam parity lives in the gui_parity
integration test (tests/integration/test_full_calc_engine.py).
"""

import pytest

from src.calculator.exceptions import CalculationError
from src.calculator.full_calc_engine import FullCalcEngine, get_full_calc_engine
from src.models.build_data import BuildData, CharacterClass

_XML = (
    '<PathOfBuilding2><Build level="90" className="Witch" mainSocketGroup="1"/>'
    '<Tree activeSpec="1"><Spec nodes="10,20,30"/></Tree></PathOfBuilding2>'
)


# ----- GET_STATS dict -> BuildStats mapping (AC-4.2.2) --------------------- #
def test_map_headline_dps_first_nonzero_falls_through():
    # TotalDPS absent -> CombinedDPS; the first-nonzero chain is computed here.
    stats = FullCalcEngine._stats_from_mainoutput({"CombinedDPS": 5000.0, "Life": 4200})
    assert stats.total_dps == 5000.0
    assert stats.life == 4200


def test_map_dot_build_uses_total_dot():
    stats = FullCalcEngine._stats_from_mainoutput({"TotalDPS": 0, "TotalDot": 23752.2})
    assert stats.total_dps == pytest.approx(23752.2)


def test_map_full_dps_when_only_full_present():
    stats = FullCalcEngine._stats_from_mainoutput({"FullDPS": 188475.0})
    assert stats.total_dps == pytest.approx(188475.0)


def test_map_omitted_keys_default_to_zero():
    # GET_STATS OMITS absent stats entirely -> dict-safe .get must default them.
    stats = FullCalcEngine._stats_from_mainoutput({})
    assert stats.total_dps == 0.0
    assert stats.life == 0 and stats.energy_shield == 0 and stats.armour == 0
    assert stats.effective_hp == 0.0


def test_map_int_casts_survive_post_init():
    # BuildStats.__post_init__ hard-rejects non-int life/ES/mana/armour/evasion,
    # so the int(...) casts MUST be kept (a verbatim float copy would trip it).
    stats = FullCalcEngine._stats_from_mainoutput(
        {"TotalDPS": 1.0, "Life": 4200.9, "EnergyShield": 100.5, "Mana": 50.2,
         "Armour": 7.7, "Evasion": 3.3, "FireResist": 75.0}
    )
    assert isinstance(stats.life, int) and stats.life == 4200
    assert isinstance(stats.energy_shield, int) and stats.energy_shield == 100
    assert isinstance(stats.armour, int) and stats.armour == 7
    assert isinstance(stats.resistances["fire"], int) and stats.resistances["fire"] == 75


def test_map_ehp_falls_back_to_life():
    stats = FullCalcEngine._stats_from_mainoutput({"Life": 5000})
    assert stats.effective_hp == 5000.0  # no TotalEHP/EHP -> life


# ----- fences (AC-4.2.7 / G3) --------------------------------------------- #
def test_calculate_raises_without_source_xml():
    b = BuildData(character_class=CharacterClass.WITCH, level=50, passive_nodes={1})
    assert b.source_xml is None
    with pytest.raises(CalculationError, match="source_xml"):
        get_full_calc_engine().calculate(b)


def test_calculate_raises_for_multi_spec():
    b = BuildData(
        character_class=CharacterClass.WITCH, level=50, passive_nodes=set(),
        source_xml=_XML, is_multi_spec=True,
    )
    with pytest.raises(CalculationError, match="multi-<Spec>"):
        get_full_calc_engine().calculate(b)


# ----- happy path through a fake pool ------------------------------------- #
def test_calculate_serializes_and_maps(monkeypatch):
    captured = {}

    class FakePool:
        def calculate(self, xml, name="fullcalc", stats=None):
            captured["xml"] = xml
            captured["name"] = name
            captured["stats"] = stats
            return {"TotalDPS": 23003.0, "Life": 4000}

    monkeypatch.setattr(
        "src.calculator.full_calc_engine.get_worker_pool", lambda: FakePool()
    )
    b = BuildData(
        character_class=CharacterClass.WITCH, level=90, passive_nodes={30, 10, 20},
        source_xml=_XML, main_socket_group=3, build_name="deadeye",
    )
    stats = FullCalcEngine().calculate(b)

    assert stats.total_dps == pytest.approx(23003.0)
    assert stats.life == 4000
    # G2: the serialized XML carries the allocated nodes AND the resolved
    # @mainSocketGroup=3 (not the file's original 1).
    assert 'nodes="10,20,30"' in captured["xml"]
    assert 'mainSocketGroup="3"' in captured["xml"]
    assert captured["name"] == "deadeye"
    assert "TotalDPS" in captured["stats"]  # explicit stat list requested
