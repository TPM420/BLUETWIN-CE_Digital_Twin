"""
Dodatni integracijski testi za src/pilot_service.py - pokrivajo funkcije,
ki jih test_baseline_snapshot.py se ne pokriva: metadata, priporocila,
seznam scenarijev, simulacije (uspesne in neuspesne) ter verzijo modela.

Tecejo na pravih podatkih za Svidnik (pilot_data/svidnik.yaml + config/).
"""

import pytest

from src.pilot_service import (
    list_pilots,
    get_pilot_metadata,
    get_baseline,
    get_recommendations,
    list_scenarios,
    run_simulation,
    get_model_version,
    PilotNotFoundError,
    ScenarioNotFoundError,
    MODEL_VERSION,
)

PILOT = "svidnik"


def test_list_pilots_vsebuje_svidnik():
    assert PILOT in list_pilots()


def test_get_pilot_metadata_neobstojec_pilot_vrze_napako():
    with pytest.raises(PilotNotFoundError):
        get_pilot_metadata("neobstojec")


def test_get_pilot_metadata_vrne_pricakovana_polja():
    meta = get_pilot_metadata(PILOT)
    assert meta["code"] == PILOT
    assert meta["model_version"] == MODEL_VERSION
    assert meta["config_hash"].startswith("sha256:")
    assert meta["pilot_data_hash"].startswith("sha256:")


def test_get_recommendations_vrne_seznam_pod_kljucem():
    rezultat = get_recommendations(PILOT)
    assert rezultat["pilot"] == PILOT
    assert isinstance(rezultat["recommendations"], list)


def test_get_recommendations_upoteva_top_n():
    rezultat = get_recommendations(PILOT, threshold=1.0, top_n=2)
    # pri pragu 1.0 so skoraj vsi indikatorji "nizki" -> top_n mora omejiti stevilo
    assert len(rezultat["recommendations"]) <= 2


def test_list_scenarios_vrne_neprazen_katalog():
    scenariji = list_scenarios()
    assert len(scenariji) > 0
    for scenario_id, definicija in scenariji.items():
        assert "name" in definicija
        assert "affected_indicators" in definicija


def test_run_simulation_neobstojec_pilot_vrze_napako():
    katerikoli_scenarij = next(iter(list_scenarios()))
    with pytest.raises(PilotNotFoundError):
        run_simulation("neobstojec", katerikoli_scenarij)


def test_run_simulation_neobstojec_scenarij_vrze_napako():
    with pytest.raises(ScenarioNotFoundError):
        run_simulation(PILOT, "ne_obstaja")


def test_run_simulation_delta_je_skladna_z_baseline():
    katerikoli_scenarij = next(iter(list_scenarios()))
    baseline = get_baseline(PILOT)
    rezultat = run_simulation(PILOT, katerikoli_scenarij)

    assert rezultat["baseline_bz_index"] == pytest.approx(baseline["bz_index"])
    assert rezultat["scenario_bz_index"] == pytest.approx(
        rezultat["baseline_bz_index"] + rezultat["delta_bz"]
    )
    assert isinstance(rezultat["applied_actions"], list)


def test_get_model_version():
    verzija = get_model_version()
    assert verzija["model_version"] == MODEL_VERSION
    assert verzija["config_hash"].startswith("sha256:")
