"""
Dodatni testi za main.py (FastAPI) - pokrivajo endpointe in primere, ki jih
test_api_contract.py se ne pokriva: metadata, priporocila, seznam scenarijev,
verzija preko root redirecta, CORS glave in 422 validacija vhoda.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

PILOT = "svidnik"


def test_root_preusmeri_na_docs():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/docs"


def test_get_pilot_metadata_endpoint():
    response = client.get(f"/api/pilots/{PILOT}/metadata")
    assert response.status_code == 200
    assert response.json()["code"] == PILOT


def test_get_pilot_metadata_endpoint_404():
    response = client.get("/api/pilots/neobstojec/metadata")
    assert response.status_code == 404


def test_get_pilot_recommendations_endpoint():
    response = client.get(f"/api/pilots/{PILOT}/recommendations")
    assert response.status_code == 200
    assert "recommendations" in response.json()


def test_get_pilot_recommendations_endpoint_404():
    response = client.get("/api/pilots/neobstojec/recommendations")
    assert response.status_code == 404


def test_get_scenarios_endpoint():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_post_simulation_manjkajoce_polje_vrne_422():
    """Ce POST /api/simulations dobi telo brez obveznega polja, mora FastAPI vrniti 422 (ne 500)."""
    response = client.post("/api/simulations", json={"pilot": PILOT})
    assert response.status_code == 422


def test_cors_glava_je_prisotna_za_dovoljen_izvor():
    """Frontend na localhost:5173 mora dobiti CORS dovoljenje (nastavljeno v main.py)."""
    response = client.get("/api/pilots", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
