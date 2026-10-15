import pytest
import yaml

from src.pilot_loader import load_pilot_data, extract_raw_values, load_raw_values

def test_load_pilot_data_prebere_celotno_vsebino(tmp_path):
    """load_pilot_data mora vrniti CELOTNO vsebino YAML datoteke kot slovar."""
    pilot_file = tmp_path / 'test_pilot.yaml'
    pilot_file.write_text(yaml.dump({
        'code': 'testpilot',
        'name': 'Testni pilot',
        'data_version': '2026-01-01',
        'indicators': {
            'x11': {'value': 0.3},
            'x12': {'value': None},
        },
    }))

    data = load_pilot_data(pilot_file)

    assert data['code'] == 'testpilot'
    assert data['name'] == 'Testni pilot'
    assert 'indicators' in data

def test_load_pilot_data_na_prazni_datoteki_vrze_napako(tmp_path):
    """Prazna YAML datoteka mora vreci ValueError."""
    empty_file = tmp_path / 'prazna.yaml'
    empty_file.write_text('')

    with pytest.raises(ValueError):
        load_pilot_data(empty_file)

def test_extract_raw_values_izlusci_samo_vrednosti():
    """extract_raw_values mora iz {"indicators": {...}} narediti preprost {id: value} slovar."""
    pilot_data = {
        'indicators': {
            'x11': {'value': 0.3, 'unit': 'something', 'year': 2024},
            'x12': {'value': None},
        }
    }

    raw_values = extract_raw_values(pilot_data)

    assert raw_values == {'x11': 0.3, 'x12': None}

def test_load_raw_values_je_kombinacija_obeh_korakov(tmp_path):
    """load_raw_values mora delovati enako kot extract_raw_values(load_pilot_data(path))."""
    pilot_file = tmp_path / 'test_pilot.yaml'
    pilot_file.write_text(yaml.dump({
        'indicators': {
            'x41': {'value': 0.55},
        }
    }))

    assert load_raw_values(pilot_file) == {'x41': 0.55}

def test_prava_svidnik_yaml_se_prebere_brez_napake():
    """Dejanska datoteka pilot_data/svidnik.yaml se mora prebrati brez napake."""
    raw_values = load_raw_values('pilot_data/svidnik.yaml')
    assert isinstance(raw_values, dict)
    assert len(raw_values) > 0