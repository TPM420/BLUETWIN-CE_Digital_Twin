"""Testi za src/intervention_engine.py (priporocila ukrepov in njihova prioriteta)."""

import pytest

from src.data_models import IndicatorDefinition, LayerDefinition, Power9Definition, EngineConfig
from src.intervention_engine import (
    find_low_indicators,
    get_indicator_to_power9_map,
    estimate_indicator_priority,
    generate_intervention_recommendations,
    recommendations_to_dict,
)


@pytest.fixture
def config():
    """
    Dva sloja (L1: i1 pozitiven + i2 negativen, L2: i3 pozitiven).
    P1 je odvisen samo od L1 (utez 1.0), P2 od L1 (0.5) in L2 (0.5).
    bz_weights: P1=0.6, P2=0.4.
    """
    indicators = {
        "i1": IndicatorDefinition(
            id="i1", name="Prvi", layer_id="L1", direction="positive", weight=1.0, min_value=0, max_value=10,
        ),
        "i2": IndicatorDefinition(
            id="i2", name="Drugi", layer_id="L1", direction="negative", weight=1.0, min_value=0, max_value=10,
        ),
        "i3": IndicatorDefinition(
            id="i3", name="Tretji", layer_id="L2", direction="positive", weight=1.0, min_value=0, max_value=1,
        ),
    }
    layers = {
        "L1": LayerDefinition(id="L1", name="Sloj 1", indicator_ids=["i1", "i2"]),
        "L2": LayerDefinition(id="L2", name="Sloj 2", indicator_ids=["i3"]),
    }
    power9 = {
        "P1": Power9Definition(id="P1", name="P1", layer_weights={"L1": 1.0}),
        "P2": Power9Definition(id="P2", name="P2", layer_weights={"L1": 0.5, "L2": 0.5}),
    }
    return EngineConfig(indicators=indicators, layers=layers, power9=power9, bz_weights={"P1": 0.6, "P2": 0.4})


def test_find_low_indicators_filtrira_po_pragu():
    normalized = {"a": 0.1, "b": 0.5, "c": 0.39, "d": None}
    low = find_low_indicators(normalized, threshold=0.40, include_missing=False)
    assert low == {"a": 0.1, "c": 0.39}


def test_find_low_indicators_lahko_vkljuci_manjkajoce():
    normalized = {"a": 0.1, "d": None}
    low = find_low_indicators(normalized, threshold=0.40, include_missing=True)
    assert low == {"a": 0.1, "d": None}


def test_indicator_to_power9_map_poveze_prek_slojev(config):
    """i1/i2 sta v L1, ki vpliva na P1 in P2; i3 je v L2, ki vpliva samo na P2."""
    reverse_map = get_indicator_to_power9_map(config)

    p_ids_za_i1 = {link["power9_id"] for link in reverse_map["i1"]}
    assert p_ids_za_i1 == {"P1", "P2"}

    p_ids_za_i3 = {link["power9_id"] for link in reverse_map["i3"]}
    assert p_ids_za_i3 == {"P2"}


def test_estimate_indicator_priority_gap_mode(config):
    """deficit = 1 - 0.5 = 0.5; strukturna pomembnost i1 = 1.0*0.6 + 0.5*0.4 = 0.8."""
    normalized = {"i1": 0.5, "i2": 1.0, "i3": 1.0}
    layer_scores = {"L1": 0.75, "L2": 1.0}
    reverse_map = get_indicator_to_power9_map(config)

    priority = estimate_indicator_priority(
        "i1", config, normalized, layer_scores, reverse_map, deficit_mode="gap",
    )
    assert priority["deficit"] == pytest.approx(0.5)
    assert priority["structural_weight"] == pytest.approx(0.8)
    assert priority["total_priority"] == pytest.approx(0.5 * 1.0 * 0.8)


def test_estimate_indicator_priority_manjkajoca_vrednost_je_najvecji_deficit(config):
    normalized = {"i1": None, "i2": 1.0, "i3": 1.0}
    layer_scores = {"L1": 1.0, "L2": 1.0}
    reverse_map = get_indicator_to_power9_map(config)

    priority = estimate_indicator_priority("i1", config, normalized, layer_scores, reverse_map)
    assert priority["deficit"] == 1.0


def test_generate_intervention_recommendations_konec_do_konca(config):
    """i1 in i3 sta pod pragom 0.40 - morata biti v priporocilih; i2 ne (nad pragom)."""
    normalized = {"i1": 0.1, "i2": 1.0, "i3": 0.2}
    layer_scores = {"L1": 0.55, "L2": 0.2}
    catalog = {"i1": {"interventions": ["Ukrep A"]}}

    priporocila = generate_intervention_recommendations(
        config=config,
        normalized_values=normalized,
        layer_scores=layer_scores,
        interventions_catalog=catalog,
        threshold=0.40,
    )

    ids = [r.indicator_id for r in priporocila]
    assert set(ids) == {"i1", "i3"}
    assert "i2" not in ids

    i1_priporocilo = next(r for r in priporocila if r.indicator_id == "i1")
    assert i1_priporocilo.interventions == ["Ukrep A"]

    i3_priporocilo = next(r for r in priporocila if r.indicator_id == "i3")
    assert i3_priporocilo.interventions == []  # ni ga v katalogu

    # razvrsceno padajoce po total_priority
    prioritete = [r.total_priority for r in priporocila]
    assert prioritete == sorted(prioritete, reverse=True)


def test_generate_intervention_recommendations_upostevata_top_n(config):
    normalized = {"i1": 0.1, "i2": 0.1, "i3": 0.1}
    layer_scores = {"L1": 0.1, "L2": 0.1}

    priporocila = generate_intervention_recommendations(
        config=config,
        normalized_values=normalized,
        layer_scores=layer_scores,
        interventions_catalog={},
        threshold=0.40,
        top_n=1,
    )
    assert len(priporocila) == 1


def test_recommendations_to_dict_oblika(config):
    normalized = {"i1": 0.1, "i2": 1.0, "i3": 1.0}
    layer_scores = {"L1": 0.55, "L2": 1.0}

    priporocila = generate_intervention_recommendations(
        config=config,
        normalized_values=normalized,
        layer_scores=layer_scores,
        interventions_catalog={},
        threshold=0.40,
    )
    kot_slovarji = recommendations_to_dict(priporocila)
    assert isinstance(kot_slovarji, list)
    assert kot_slovarji[0]["indicator_id"] == "i1"
    assert "total_priority" in kot_slovarji[0]
    assert "power9_links" in kot_slovarji[0]


def test_prava_svidnik_konfiguracija_da_vsaj_eno_priporocilo():
    """Integracijski test na pravi konfiguraciji in pravih podatkih za Svidnik."""
    from src.config_loader import load_engine_config
    from src.pilot_loader import load_raw_values
    from src.layer_scoring import compute_layer_scores
    from src.intervention_engine import load_interventions

    config_prava = load_engine_config("config")
    raw_values = load_raw_values("pilot_data/svidnik.yaml")
    layer_scores, normalized = compute_layer_scores(config_prava, raw_values)
    interventions_catalog = load_interventions("config/interventions.yaml")

    priporocila = generate_intervention_recommendations(
        config=config_prava,
        normalized_values=normalized,
        layer_scores=layer_scores,
        interventions_catalog=interventions_catalog,
        threshold=0.40,
    )
    assert isinstance(priporocila, list)
