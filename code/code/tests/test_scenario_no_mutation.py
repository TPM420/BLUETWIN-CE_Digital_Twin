import pytest

from src.data_models import IndicatorDefinition, EngineConfig
from src.scenario_engine import apply_scenario_actions


@pytest.fixture
def config():
    indicators = {
        'x1': IndicatorDefinition(
            id='x1', name='Test', layer_id='L1', direction='positive', weight=1.0, min_value=0, max_value=100,
        )
    }
    return EngineConfig(indicators=indicators, layers={}, power9={}, bz_weights={})


def test_apply_scenario_actions_ne_spremeni_izvirnega_slovarja(config):
    """Vhodni raw_values slovar se ne sme spremeniti - apply_scenario_actions mora vrniti NOVEGA."""
    raw_values = {'x1': 50}
    scenario_def = {
        'name': 'Testni scenarij',
        'affected_indicators': {'x1': {'mode': 'absolute', 'value': 20}},
    }

    updated, applied_actions = apply_scenario_actions(config, raw_values, scenario_def)

    assert raw_values == {'x1': 50} #nedotaknjen izvirnik
    assert updated == {'x1': 70}    #nespremenjena nova kopija


def test_updated_je_dejansko_druga_instanca_slovarja(config):
    """updated ne sme biti kar isti objekt kot raw_values - drugace bi sprememba udarila oboje."""
    raw_values = {'x1': 50}
    scenario_def = {'name': 'Test', 'affected_indicators': {'x1': {'mode': 'absolute', 'value': 20}}}

    updated, _ = apply_scenario_actions(config, raw_values, scenario_def)

    assert updated is not raw_values