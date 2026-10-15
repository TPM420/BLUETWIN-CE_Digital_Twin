import pytest

from src.data_models import IndicatorDefinition, LayerDefinition, Power9Definition, EngineConfig
from src.scenario_engine import run_scenario


@pytest.fixture
def config():
    """En indikator (x1) v enem sloju (L1), ki v celoti sestavlja eno Power9 dimenzijo (P1)."""
    indicators = {
        'x1': IndicatorDefinition(
            id='x1', name='Test', layer_id='L1', direction='positive', weight=1.0, min_value=0, max_value=100,
        )
    }
    layers = {
        'L1': LayerDefinition(id='L1', name='Testni sloj', indicator_ids=['x1'])
    }
    power9 = {
        'P1': Power9Definition(id='P1', name='Test P1', layer_weights={'L1': 1.0})
    }
    return EngineConfig(indicators=indicators, layers=layers, power9=power9, bz_weights={})


def test_delta_bz_je_razlika_scenarija_in_baseline(config):
    """x1 gre iz 50 na 70 (absolute +20) -> normalizirano 0.5 -> 0.7, torej delta_bz = 0.2."""
    raw_values = {'x1': 50}
    scenario_def = {
        'name': 'Testni scenarij',
        'affected_indicators': {'x1': {'mode': 'absolute', 'value': 20}},
    }

    result = run_scenario(config, raw_values, 'test_scenario', scenario_def)

    assert result.baseline_bz_index == 0.5
    assert result.scenario_bz_index == 0.7
    assert result.delta_bz == pytest.approx(0.2)


def test_delta_layers_odraza_spremembo(config):
    """Sloj L1 se mora premakniti za enak znesek kot BZ indeks, ker je edini sloj."""
    raw_values = {'x1': 50}
    scenario_def = {
        'name': 'Test',
        'affected_indicators': {'x1': {'mode': 'absolute', 'value': 20}},
    }

    result = run_scenario(config, raw_values, 'test_scenario', scenario_def)

    assert result.delta_layers['L1'] == pytest.approx(0.2)


def test_applied_actions_vsebuje_pravilne_podatke(config):
    """applied_actions mora natancno povedati, kateri indikator je bil spremenjen, iz cesa v kaj."""
    raw_values =  {'x1': 50}
    scenario_def = {
        'name': 'Test',
        'affected_indicators': {'x1': {'mode': 'absolute', 'value': 20}},
    }

    result = run_scenario(config, raw_values, 'test_scenario', scenario_def)

    assert len(result.applied_actions) == 1
    action = result.applied_actions[0]
    assert action['indicator_id'] == 'x1'
    assert action['mode'] == 'absolute'
    assert action['before'] == 50
    assert action['after'] == 70