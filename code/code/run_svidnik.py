"""
run_svidnik.py

To je "Naloga 2" skripta: namesto testnega example_data (glej run.py)
zdaj model pozenemo na PRAVIH podatkih za Svidník iz pilot_data/svidnik.yaml.

Koraki:
  1) nalozi modelno konfiguracijo (config/*.yaml) - profesorjeva koda
  2) nalozi pilotne podatke (pilot_data/svidnik.yaml) - najin loader
  3) validira pilotne podatke (pilot_validator.py) in izpise PASS/WARN/ERROR
  4) izracuna baseline (layer scores, Power9, Blue Zone index)
  5) izpise diagnostiko in priporocila ukrepov
  6) rezultat shrani kot JSON v outputs/ (za "Reproducibilen baseline JSON")
"""

import json
from pathlib import Path

from src.config_loader import load_engine_config
from src.pilot_loader import load_pilot_data, extract_raw_values
from src.pilot_validator import validate_pilot_data, print_validation_report
from src.layer_scoring import compute_layer_scores
from src.power9_scoring import compute_power9_scores
from src.bz_index import compute_bz_index
from src.diagnostics import build_full_diagnostics, print_diagnostics
from src.intervention_engine import (
    load_interventions,
    generate_intervention_recommendations,
    print_recommendations,
    recommendations_to_dict,
)

# --- 1) konfiguracija modela (nespremenjena, profesorjeva) ---
config = load_engine_config("config")
interventions_catalog = load_interventions("config/interventions.yaml")

# --- 2) pilotni podatki za Svidnik ---
pilot_data = load_pilot_data("pilot_data/svidnik.yaml")
raw_values = extract_raw_values(pilot_data)

print(f"Pilot: {pilot_data['name']} (code={pilot_data['code']}, "
      f"data_version={pilot_data['data_version']})")
print(f"Razpolozljivih indikatorjev: "
      f"{sum(1 for v in raw_values.values() if v is not None)} / {len(config.indicators)}\n")

# --- 3) validacija ---
report = validate_pilot_data(config, pilot_data)
print_validation_report(report)
print()

if report["errors"]:
    print("Model se NE zazene, ker so prisotne hude napake (glej zgoraj).")
    raise SystemExit(1)

# --- 4) baseline izracun ---
layer_scores, normalized = compute_layer_scores(config, raw_values)
power9_scores = compute_power9_scores(config, layer_scores)
bz = compute_bz_index(config, power9_scores)

diagnostics = build_full_diagnostics(
    config=config,
    raw_values=raw_values,
    normalized_values=normalized,
    layer_scores=layer_scores,
    power9_scores=power9_scores,
    bz_index=bz,
)

# --- 5) izpis ---
print_diagnostics(diagnostics)

recommendations = generate_intervention_recommendations(
    config=config,
    normalized_values=normalized,
    layer_scores=layer_scores,
    interventions_catalog=interventions_catalog,
    threshold=0.40,
    include_missing=False,
    top_n=10,
    deficit_mode="gap",
)
print_recommendations(recommendations)

# --- 6) shrani rezultat kot JSON (reproducibilen baseline) ---
Path("outputs").mkdir(exist_ok=True)

output = {
    "pilot_code": pilot_data["code"],
    "pilot_name": pilot_data["name"],
    "data_version": pilot_data["data_version"],
    "raw_values": raw_values,
    "normalized_indicators": normalized,
    "layer_scores": layer_scores,
    "power9_scores": power9_scores,
    "bz_index": bz,
    "validation_warnings": report["warnings"],
    "recommendations": recommendations_to_dict(recommendations),
}

out_path = Path("outputs") / f"baseline_{pilot_data['code']}_{pilot_data['data_version']}.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nBaseline rezultat shranjen v: {out_path}")
