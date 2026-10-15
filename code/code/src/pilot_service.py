"""
pilot_service.py

To je "service" plast (razdelek 5.1 in 9 navodil): tukaj je VSA logika,
ki nalozi konfiguracijo, nalozi pilotne podatke in pozene model.

FastAPI endpointi (main.py) so namenoma "tanki" - samo kliknejo eno
od teh funkcij in vrnejo rezultat kot JSON. Tako lahko iste funkcije
kasneje uporabimo tudi v testih ali v ukazni vrstici (CLI), ne samo
v spletnem API-ju.

MODEL_VERSION spremenimo rocno, ce se spremeni sama metodologija
(npr. nov nacin racunanja BZ indeksa). CONFIG_VERSION ni potreben
posebej - namesto tega racunamo config_hash neposredno iz vsebine
config/*.yaml datotek (glej hashing.py).
"""

from pathlib import Path
from src.config_loader import load_engine_config
from src.pilot_loader import load_pilot_data, extract_raw_values
from src.pilot_validator import validate_pilot_data
from src.layer_scoring import compute_layer_scores
from src.power9_scoring import compute_power9_scores
from src.bz_index import compute_bz_index
from src.intervention_engine import (
    load_interventions,
    generate_intervention_recommendations,
    recommendations_to_dict,
)
from src.scenario_engine import load_scenarios, run_scenario
from src.hashing import sha256_of_file, sha256_of_files

MODEL_VERSION = "1.0.0"

CONFIG_DIR = Path("config")
PILOT_DATA_DIR = Path("pilot_data")
INTERVENTIONS_PATH = CONFIG_DIR / "interventions.yaml"
SCENARIOS_PATH = CONFIG_DIR / "scenario_actions.yaml"

CONFIG_FILES = [
    CONFIG_DIR / "indicators.yaml",
    CONFIG_DIR / "layers.yaml",
    CONFIG_DIR / "power9.yaml",
    CONFIG_DIR / "bz_weights.yaml",
]


class PilotNotFoundError(Exception):
    """Vrzemo, ce nekdo poprasa za pilot, ki ne obstaja (npr. /api/pilots/beltinci)."""
    pass


class ScenarioNotFoundError(Exception):
    """Vrzemo, ce nekdo poprasa za scenario_id, ki ne obstaja v scenario_actions.yaml."""
    pass


def _pilot_yaml_path(pilot: str) -> Path:
    return PILOT_DATA_DIR / f"{pilot}.yaml"


def list_pilots() -> list[str]:
    """Vrne seznam kod pilotov, za katere obstaja pilot_data/<pilot>.yaml (npr. ['svidnik'])."""
    if not PILOT_DATA_DIR.exists():
        return []
    return sorted(p.stem for p in PILOT_DATA_DIR.glob("*.yaml"))


def get_pilot_metadata(pilot: str) -> dict:
    """Vrne samo metapolja (code, name, data_version) - brez indikatorjev."""
    path = _pilot_yaml_path(pilot)
    if not path.exists():
        raise PilotNotFoundError(pilot)

    pilot_data = load_pilot_data(path)
    return {
        "code": pilot_data["code"],
        "name": pilot_data["name"],
        "data_version": pilot_data["data_version"],
        "config_hash": sha256_of_files(CONFIG_FILES),
        "pilot_data_hash": sha256_of_file(path),
        "model_version": MODEL_VERSION,
    }


def _compute_baseline(pilot: str):
    """
    Interna pomozna funkcija (ne uporabljaj je neposredno iz main.py) -
    naloz konfiguracijo + pilotne podatke in izracuna baseline.
    Vrne (config, pilot_data, raw_values, normalized, layer_scores,
    power9_scores, bz_index, validation_report).
    """
    path = _pilot_yaml_path(pilot)
    if not path.exists():
        raise PilotNotFoundError(pilot)

    config = load_engine_config(CONFIG_DIR)
    pilot_data = load_pilot_data(path)
    raw_values = extract_raw_values(pilot_data)

    validation_report = validate_pilot_data(config, pilot_data)

    layer_scores, normalized = compute_layer_scores(config, raw_values)
    power9_scores = compute_power9_scores(config, layer_scores)
    bz_index = compute_bz_index(config, power9_scores)

    return (
        config,
        pilot_data,
        raw_values,
        normalized,
        layer_scores,
        power9_scores,
        bz_index,
        validation_report,
    )


def _coverage_by_layer(config, raw_values: dict) -> dict:
    """Za vsak sloj izracuna delez utezi indikatorjev, ki imajo dejansko vrednost."""
    coverage = {}
    for layer_id, layer in config.layers.items():
        total_weight = 0.0
        covered_weight = 0.0
        for ind_id in layer.indicator_ids:
            indicator = config.indicators.get(ind_id)
            if indicator is None:
                continue
            total_weight += indicator.weight
            if raw_values.get(ind_id) is not None:
                covered_weight += indicator.weight
        coverage[layer_id] = round(covered_weight / total_weight, 4) if total_weight > 0 else 0.0
    return coverage

def _indicator_details(config, pilot_data:dict) -> list[dict]:
    """
        Pripravi seznam vseh indikatorjev z metapodatki (vrednost, enota, leto,
        vir, tip mapiranja, kakovost) - za prikaz na frontend strani, kjer mora
        biti vidno OD KOD prihaja vsaka stevilka, ne samo koncni rezultat.
        """
    details = []
    for ind_id, entry in pilot_data['indicators'].items():
        indicator = config.indicators.get(ind_id)
        details.append({
            'id':ind_id,
            'name': indicator.name if indicator else ind_id,
            'value': entry.get('value'),
            'unit': entry.get('unit'),
            'year': entry.get('year'),
            'source': entry.get('source'),
            'mapping_type': entry.get('mapping_type'),
            'quality': entry.get('quality'),
        })
    return details

def get_baseline(pilot: str) -> dict:
    """Glavni endpoint /api/pilots/{pilot}/baseline - celoten baseline rezultat."""
    (
        config,
        pilot_data,
        raw_values,
        normalized,
        layer_scores,
        power9_scores,
        bz_index,
        validation_report,
    ) = _compute_baseline(pilot)

    path = _pilot_yaml_path(pilot)

    return {
        "pilot": pilot_data["code"],
        "pilot_name": pilot_data["name"],
        "data_version": pilot_data["data_version"],
        "model_version": MODEL_VERSION,
        "config_hash": sha256_of_files(CONFIG_FILES),
        "pilot_data_hash": sha256_of_file(path),
        "bz_index": round(bz_index, 4),
        "layer_scores": {k: round(v, 4) for k, v in layer_scores.items()},
        "layer_names": {layer_id: layer.name for layer_id, layer in config.layers.items()},
        "power9_scores": {k: round(v, 4) for k, v in power9_scores.items()},
        "normalized_indicators": normalized,
        "raw_values": raw_values,
        "data_coverage": _coverage_by_layer(config, raw_values),
        "warnings": validation_report["warnings"],
        "indicators": _indicator_details(config, pilot_data),
        "indicator_names": {ind_id: ind.name for ind_id, ind in config.indicators.items()}
    }


def get_recommendations(pilot: str, threshold: float = 0.40, top_n: int = 10) -> dict:
    """Endpoint /api/pilots/{pilot}/recommendations."""
    config, pilot_data, raw_values, normalized, layer_scores, _, _, _ = _compute_baseline(pilot)
    interventions_catalog = load_interventions(INTERVENTIONS_PATH)

    recommendations = generate_intervention_recommendations(
        config=config,
        normalized_values=normalized,
        layer_scores=layer_scores,
        interventions_catalog=interventions_catalog,
        threshold=threshold,
        include_missing=False,
        top_n=top_n,
        deficit_mode="gap",
    )

    return {
        "pilot": pilot_data["code"],
        "data_version": pilot_data["data_version"],
        "recommendations": recommendations_to_dict(recommendations),
    }


def list_scenarios() -> dict:
    """Endpoint /api/scenarios - seznam vseh razpolozljivih what-if paketov."""
    scenarios_catalog = load_scenarios(SCENARIOS_PATH)
    return {
        scenario_id: {
            "name": definition.get("name", scenario_id),
            "description": definition.get("description", ""),
            "affected_indicators": definition.get("affected_indicators", {}),
        }
        for scenario_id, definition in scenarios_catalog.items()
    }


def run_simulation(pilot: str, scenario_id: str) -> dict:
    """Endpoint POST /api/simulations - primerja baseline in scenarij."""
    config, pilot_data, raw_values, _, _, _, _, _ = _compute_baseline(pilot)

    scenarios_catalog = load_scenarios(SCENARIOS_PATH)
    if scenario_id not in scenarios_catalog:
        raise ScenarioNotFoundError(scenario_id)

    result = run_scenario(
        config=config,
        raw_values=raw_values,
        scenario_id=scenario_id,
        scenario_def=scenarios_catalog[scenario_id],
    )

    path = _pilot_yaml_path(pilot)

    return {
        "pilot": pilot_data["code"],
        "scenario_id": scenario_id,
        "scenario_name": result.scenario_name,
        "data_version": pilot_data["data_version"],
        "baseline_bz_index": round(result.baseline_bz_index, 4),
        "scenario_bz_index": round(result.scenario_bz_index, 4),
        "delta_bz": round(result.delta_bz, 4),
        "delta_layers": {k: round(v, 4) for k, v in result.delta_layers.items()},
        "delta_power9": {k: round(v, 4) for k, v in result.delta_power9.items()},
        "applied_actions": result.applied_actions,
        "config_hash": sha256_of_files(CONFIG_FILES),
        "pilot_data_hash": sha256_of_file(path),
    }


def get_model_version() -> dict:
    """Endpoint /api/model/version."""
    return {
        "model_version": MODEL_VERSION,
        "config_hash": sha256_of_files(CONFIG_FILES),
    }