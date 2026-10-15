import pytest

from src.data_models import Power9Definition, EngineConfig
from src.power9_scoring import compute_power9_scores


@pytest.fixture
def config():
    """Dve Power9 dimenziji, vsaka sestavljena iz dveh slojev z razlicnimi utezmi."""
    power9 = {
        'P1': Power9Definition(id='P1', name='Test P1', layer_weights={'L1': 0.6, 'L2': 0.4}),
        'P2': Power9Definition(id='P2', name='Test P2', layer_weights={'L1':0.0, 'L2': 1.0}),
    }
    return EngineConfig(indicators={}, layers={}, power9=power9, bz_weights={})


def test_utezena_vsota_dveh_slojev(config):
    """P1 = 0.6*L1 + 0.4*L2 = 0.6*1.0 + 0.4*0.0 = 0.6."""
    layer_scores = {'L1': 1.0, 'L2': 0.0}
    scores = compute_power9_scores(config, layer_scores)
    assert scores['P1'] == 0.6


def test_vec_power9_dimenzij_je_neodvisnih(config):
    """P2 ima drugacne utezi kot P1, zato mora na istih layer_scores dati drugacen rezultat."""
    layer_scores = {'L1': 1.0, 'L2': 0.0}
    scores = compute_power9_scores(config, layer_scores)
    assert scores['P2'] == 0.0

def test_manjkajoc_sloj_v_layer_scores_vrze_napako(config):
    """Ce layer_scores ne vsebuje sloja, ki ga Power9 potrebuje, mora funkcija to zaznati."""
    layer_scores = {'L1': 1.0} #manjka L2
    with pytest.raises(ValueError):
        compute_power9_scores(config, layer_scores)