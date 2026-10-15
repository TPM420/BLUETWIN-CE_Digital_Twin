import pytest

from src.data_models import IndicatorDefinition, LayerDefinition, EngineConfig
from src.layer_scoring import compute_layer_scores

@pytest.fixture
def config():
    """En sloj z dvema indikatorjema z razlicnima utezema (3 in 1)."""
    indicators = {
        'x1': IndicatorDefinition(
            id='x1', name='Prvi', layer_id='L1', direction='positive', weight=3.0, min_value=0, max_value=100,
        ),
        'x2': IndicatorDefinition(
            id='x2', name='Drugi', layer_id='L1', direction='positive', weight=1.0, min_value=0, max_value=100,
        )
    }
    layers = {
        'L1': LayerDefinition(id='L1', name='Testni sloj', indicator_ids=['x1', 'x2'])
    }
    return EngineConfig(indicators=indicators, layers=layers, power9={}, bz_weights={})


def test_utezeno_povprecje_dveh_indikatorjev(config):
    """x1 (utez 3) = 1.0, x2 (utez 1) = 0.0 -> utezeno povprecje = (3*1.0 + 1*0.0) / 4 = 0.75."""
    raw_values = {'x1': 100, 'x2': 0}
    layer_scores, normalized = compute_layer_scores(config, raw_values)
    assert layer_scores['L1'] == 0.75


def test_manjkajoca_vrednost_se_preskoci(config):
    """Ce x2 manjka (None), se sloj racuna samo iz x1 - kot da x2 sploh ne obstaja."""
    raw_values = {'x1': 50, 'x2': None}
    layer_scores, normalized = compute_layer_scores(config, raw_values)
    assert layer_scores['L1'] == 0.5


def test_vse_vrednosti_manjkajo_vrne_0(config):
    """Ce vsi indikatorji v sloju manjkajo, je ocena sloja 0 (namesto napake ali None)."""
    raw_values = {'x1': None, 'x2': None}
    layer_scores, normalized = compute_layer_scores(config, raw_values)
    assert layer_scores['L1'] == 0


def test_vrne_tudi_normalizirane_posamezne_vrednosti(config):
    """compute_layer_scores mora vrniti tudi slovar normaliziranih vrednosti za vsak indikator posebej."""
    raw_values = {'x1': 100, 'x2': 0}
    layer_scores, normalized = compute_layer_scores(config, raw_values)
    assert normalized == {'x1': 1.0, 'x2': 0.0}