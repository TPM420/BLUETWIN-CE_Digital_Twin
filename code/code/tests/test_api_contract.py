from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_pilots_vrne_seznam_ki_vsebuje_svidnik():
    response = client.get('/api/pilots')
    assert response.status_code == 200
    assert 'svidnik' in response.json()['pilots']


def test_get_baseline_vrne_pricakovana_polja():
    response = client.get('/api/pilots/svidnik/baseline')
    assert response.status_code == 200
    data = response.json()
    for polje in ['bz_index', 'layer_scores', 'power9_scores', 'data_version', 'config_hash', 'pilot_data_hash']:
        assert polje in data



def test_get_baseline_za_neobstojec_pilot_vrne_404():
    response = client.get('/api/pilots/neobstojec/baseline')
    assert response.status_code == 404



def test_get_model_version_vrne_verzijo_in_hash():
    response = client.get('/api/model/version')
    assert response.status_code == 200
    data = response.json()
    assert 'model_version' in data
    assert 'config_hash' in data


def test_post_simulation_z_veljavnim_scenarijem_vrne_200():
    response = client.post('/api/simulations', json={'pilot': 'svidnik', 'scenario_id': 'walkability_package'})
    assert response.status_code == 200
    data = response.json()
    assert 'delta_bz' in data
    assert 'applied_actions' in data


def test_post_simulation_z_neobstojecim_scenarijem_vrne_404():
    response = client.post('/api/simulations', json={'pilot': 'svidnik', 'scenario_id': 'ne obstaja'})
    assert response.status_code == 404