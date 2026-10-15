import pytest
import yaml

from src.config_loader import load_engine_config

def test_prva_konfiguracija_brez_napake():
    """Prava konfiguracija v mapi config/ se mora nalozit brez napake."""
    config = load_engine_config('config')
    assert config is not None


def test_vsi_indikatorji_v_slojih_dejansko_obstajajo():
    """Vsak indicator_id, ki ga omenja kaksen sloj, mora obstajati v indicators.yaml."""
    config = load_engine_config('config')
    for layer in config.layers.values():
        for ind_id in layer.indicator_ids:
            assert ind_id in config.indicators


def test_vsak_power9_referencira_obstojec_sloj():
    """Vsak layer_id, ki ga omenja kaksna Power9 dimenzija, mora obstajati v layers.yaml."""
    config = load_engine_config('config')
    for p9 in config.power9.values():
        for layer_id in p9.layer_weights:
            assert layer_id in config.layers


def test_manjkajoc_indikator_v_sloju_vrze_napako(tmp_path):
    """Ce sloj referencira indikator, ki ne obstaja, mora load_engine_config to zaznati."""
    (tmp_path / 'indicators.yaml').write_text(yaml.dump({
        'x1': {'name': 'Test', 'layer_id': 'L1', 'direction': 'positive', 'weight': '1.0', 'min_value':0, 'max_value': 1}
    }))
    (tmp_path / 'layers.yaml').write_text(yaml.dump({
        'L1': {'name': 'Testni sloj', 'indicator_ids': ['x1', 'x_ne_obstaja']}
    }))
    (tmp_path / 'power9.yaml').write_text(yaml.dump({'P1': {'name': 'Testni P9', 'layer_weights': {'L1': 1.0}}}))
    (tmp_path / 'bz_weights.yaml').write_text(yaml.dump({'P1': 1.0}))

    with pytest.raises(ValueError):
        load_engine_config(tmp_path)