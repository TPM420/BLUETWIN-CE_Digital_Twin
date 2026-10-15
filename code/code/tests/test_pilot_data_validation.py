import pytest

from src.data_models import IndicatorDefinition, LayerDefinition, EngineConfig
from src.pilot_validator import validate_pilot_data

@pytest.fixture
def config():
    """Majhna, izmisljena konfiguracija z enim indikatorjem v enem sloju - uporabljena v vseh testih spodaj."""
    indicators = {
        'x11': IndicatorDefinition(
            id='x11', name='Testni indikator', layer_id='L1',
            direction='positive', weight=1.0, min_value=0, max_value=100,
        )
    }
    layers = {
        'L1': LayerDefinition(id='L1', name='Testni sloj', indicator_ids=['x11'])
    }
    return EngineConfig(indicators=indicators, layers=layers, power9={}, bz_weights={})

def veljaven_indikator(**overrides):
    """Vrne veljaven vnos za en indikator; posamezna polja lahko prepises z overrides."""
    payload = {
        'value': 50,
        'year': 2024,
        'source': 'Test vir',
        'mapping_type': 'exact',
        'quality': 'official',
    }
    payload.update(overrides)
    return payload

def test_manjkajoce_metapolje_je_napaka(config):
    pilot_data = {
        'code': 'test',
        'indicators': {'x11': veljaven_indikator()},
    }
    report = validate_pilot_data(config, pilot_data)
    assert len(report['errors']) == 2  # manjkata 'name' in 'data_version'


def test_neznan_indicator_id_je_napaka(config):
    pilot_data = {
        'code': 'test', 'name': 'Test', 'data_version': '2026-01-01',
        'indicators': {'x99': veljaven_indikator()},
    }
    report = validate_pilot_data(config, pilot_data)
    assert any('neznan indicator_id' in e for e in report['errors'])


def test_null_vrednost_je_dovoljena(config):
    pilot_data = {
        'code': 'test', 'name': 'Test', 'data_version': '2026-01-01',
        'indicators': {'x11': veljaven_indikator(value=None, year=None, source=None)},
    }
    report = validate_pilot_data(config, pilot_data)
    assert report['errors'] == []


def test_besedilna_vrednost_je_napaka(config):
    pilot_data = {
        'code': 'test', 'name': 'Test', 'data_version': '2026-01-01',
        'indicators': {'x11': veljaven_indikator(value='ni stevilka')},
    }
    report = validate_pilot_data(config, pilot_data)
    assert any('ni niti stevilka niti null' in e for e in report['errors'])


def test_manjkajoc_year_je_opozorilo(config):
    pilot_data = {
        'code': 'test', 'name': 'Test', 'data_version': '2026-01-01',
        'indicators': {'x11': veljaven_indikator(year=None)},
    }
    report = validate_pilot_data(config, pilot_data)
    assert any("manjka 'year'" in w for w in report['warnings'])


def test_nedovoljen_mapping_type_je_napaka(config):
    pilot_data = {
        'code': 'test', 'name': 'Test', 'data_version': '2026-01-01',
        'indicators': {'x11': veljaven_indikator(mapping_type='izmisljen')},
    }
    report = validate_pilot_data(config, pilot_data)
    assert any('mapping_type' in e for e in report['errors'])

def test_vrednost_izven_obsega_je_opozorilo(config):
    pilot_data = {
        'code': 'test', 'name': 'Test', 'data_version': '2026-01-01',
        'indicators': {'x11': veljaven_indikator(value=999)},
    }
    report = validate_pilot_data(config, pilot_data)
    assert any("izven pricakovanega razpona" in w for w in report['warnings'])