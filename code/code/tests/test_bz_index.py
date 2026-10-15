import pytest

from src.data_models import EngineConfig
from src.bz_index import compute_bz_index


def test_utezena_vsota_ko_so_bz_weights_podane():
    """Z utezmi P1=0.7, P2=0.3: 0.7*1.0 + 0.3*0.0 = 0.7."""
    config = EngineConfig(indicators={}, layers={}, power9={}, bz_weights={'P1':0.7, 'P2':0.3})
    power9_scores = {'P1':1.0, 'P2':0.0}
    assert compute_bz_index(config, power9_scores) == 0.7


def test_navadno_povprecje_ko_bz_weights_manjkajo():
    """Ce bz_weights ni podan (prazen slovar), je BZ indeks navadno povprecje vseh Power9 ocen."""
    config = EngineConfig(indicators={}, layers={}, power9={}, bz_weights={})
    power9_scores = {'P1':1.0, 'P2':0.0, 'P3':0.5}
    assert compute_bz_index(config, power9_scores) == 0.5


def test_manjkajoc_p_id_v_power9_scores_vrze_napako():
    """Ce bz_weights omenja Power9 dimenzijo, ki je v power9_scores ni, se izracun ne sme tiho izteci narobe."""
    config = EngineConfig(indicators={}, layers={}, power9={}, bz_weights={'P1':1.0})
    power9_scores = {} #manjka P1
    with pytest.raises(KeyError):
        compute_bz_index(config, power9_scores)