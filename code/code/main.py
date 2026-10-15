"""
main.py

FastAPI aplikacija (Faza 6 iz navodil). To je TANKA plast nad
obstojeco kodo - vsak endpoint samo poklice ustrezno funkcijo iz
src/pilot_service.py in rezultat vrne kot JSON.

Kako pognati lokalno:
    pip install fastapi uvicorn
    uvicorn main:app --reload

Nato odpri v brskalniku:
    http://127.0.0.1:8000/docs
(FastAPI sam iz kode zgradi interaktivno dokumentacijo - to je
ena od prednosti FastAPI-ja, da je ni treba pisati rocno).
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from src import pilot_service as service
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BLUETWIN-CE API",
    description="Read-only API za Digital Twin model (baseline, priporocila, scenariji).",
    version=service.MODEL_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- oblika (schema) vhodnih podatkov za POST /api/simulations ---
class SimulationRequest(BaseModel):
    pilot: str
    scenario_id: str

@app.get('/')
def root():
    return RedirectResponse(url='/docs')

@app.get("/api/pilots")
def get_pilots():
    """Seznam vseh pilotov, za katere obstajajo podatki (npr. ['svidnik'])."""
    return {"pilots": service.list_pilots()}


@app.get("/api/pilots/{pilot}/metadata")
def get_pilot_metadata(pilot: str):
    """Osnovni podatki o pilotu (ime, data_version, hashi)."""
    try:
        return service.get_pilot_metadata(pilot)
    except service.PilotNotFoundError:
        raise HTTPException(status_code=404, detail=f"Pilot '{pilot}' ne obstaja.")


@app.get("/api/pilots/{pilot}/baseline")
def get_pilot_baseline(pilot: str):
    """Celoten baseline izracun: BZ indeks, layer scores, Power9, coverage, opozorila."""
    try:
        return service.get_baseline(pilot)
    except service.PilotNotFoundError:
        raise HTTPException(status_code=404, detail=f"Pilot '{pilot}' ne obstaja.")


@app.get("/api/pilots/{pilot}/recommendations")
def get_pilot_recommendations(pilot: str, threshold: float = 0.40, top_n: int = 10):
    """Prioritetni indikatorji in priporoceni ukrepi zanje."""
    try:
        return service.get_recommendations(pilot, threshold=threshold, top_n=top_n)
    except service.PilotNotFoundError:
        raise HTTPException(status_code=404, detail=f"Pilot '{pilot}' ne obstaja.")


@app.get("/api/scenarios")
def get_scenarios():
    """Seznam vseh fiksnih what-if scenarijev (iz scenario_actions.yaml)."""
    return service.list_scenarios()


@app.post("/api/simulations")
def post_simulation(request: SimulationRequest):
    """
    Pozene en scenarij na kopiji podatkov izbranega pilota in vrne
    primerjavo baseline vs scenarij (delta po slojih, Power9 in BZ).

    Primer telesa zahteve (POST body):
        {"pilot": "svidnik", "scenario_id": "walkability_package"}
    """
    try:
        return service.run_simulation(request.pilot, request.scenario_id)
    except service.PilotNotFoundError:
        raise HTTPException(status_code=404, detail=f"Pilot '{request.pilot}' ne obstaja.")
    except service.ScenarioNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Scenario '{request.scenario_id}' ne obstaja."
        )


@app.get("/api/model/version")
def get_model_version():
    """Verzija modelne metodologije in hash trenutne konfiguracije."""
    return service.get_model_version()
