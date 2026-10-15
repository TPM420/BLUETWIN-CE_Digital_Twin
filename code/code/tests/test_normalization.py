import pytest

from src.data_models import IndicatorDefinition
from src.normalization import minmax_normalize, normalize_indicator

def test_minmax_normalize_sredina_obsega():
    """Vrednost na sredini obsega [0, 100] se mora normalizirati na 0.5."""
    assert minmax_normalize(50, 0, 100) == 0.5

def test_minmax_normalize_spodnja_meja():
    assert minmax_normalize(0, 0, 100) == 0.0

def test_minmax_normalize_zgornja_meja():
    assert minmax_normalize(100, 0, 100) == 1.0

def test_minmax_normalize_none_ostane_none():
    assert minmax_normalize(None, 0, 100) is None

def test_minmax_normalize_obrezovanje_pod_min():
    """Vrednost pod min_value mora biti 'obrezana' (clipped) na 0.0, ne negativna."""
    assert minmax_normalize(-20, 0, 100) == 0.0

def test_minmax_normalize_obrezovanje_nad_max():
    """Vrednost nad max_value mora biti obrezana na 1.0, ne vec."""
    assert minmax_normalize(150, 0, 100) == 1.0

def test_minmax_normalize_neveljaven_obseg_vrze_napako():
    """Ce sta min_value in max_value enaka, je obseg neveljaven (delenje z 0)."""
    with pytest.raises(ValueError):
        minmax_normalize(50, 10, 10)

def test_normalize_indicator_pozitivna_smer():
    """Pri direction='positive' visja surova vrednost pomeni visjo normalizirano oceno."""
    indikator = IndicatorDefinition(
        id='x1', name='Test', layer_id='L1', direction='positive', weight=1.0, min_value=0, max_value=100,
    )
    assert normalize_indicator(75, indikator) == 0.75

def test_normalize_indicator_negativna_smer():
    """Pri direction='negative' se lestvica obrne - visja surova vrednost pomeni NIZJO oceno."""
    indikator = IndicatorDefinition(
        id='x2', name='Test', layer_id='L1', direction='negative', weight=1.0, min_value=0, max_value=100,
    )
    assert normalize_indicator(75, indikator) == 0.25

def test_normalize_indicator_none_ostane_none():
    indikator = IndicatorDefinition(
        id='x3', name='Test', layer_id='L1', direction='positive', weight=1.0, min_value=0, max_value=100,
    )
    assert normalize_indicator(None, indikator) is None