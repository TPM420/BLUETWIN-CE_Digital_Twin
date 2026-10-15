from src.config_loader import load_engine_config
from src.layer_scoring import compute_layer_scores
from src.power9_scoring import compute_power9_scores
from src.bz_index import compute_bz_index
from src.diagnostics import build_full_diagnostics, print_diagnostics
from src.intervention_engine import (
    load_interventions,
    generate_intervention_recommendations,
    print_recommendations,
)

config = load_engine_config("config")
interventions_catalog = load_interventions("config/interventions.yaml")

example_data = {
    "x11": 0.3,
    "x12": 0.2,
    "x13": 0.4,
    "x14": 0.1,
    "x15": 0.05,
    "x16": 0.6,
    "x21": 0.3,
    "x22": 0.2,
    "x23": 0.8,
    "x24": 0.1,
    "x25": 0.7,
    "x26": 8.0,
    "x31": 0.6,
    "x32": 0.7,
    "x33": 0.6,
    "x34": 0.3,
    "x35": 0.1,
    "x36": 0.7,
    "x41": 30,
    "x42": 10,
    "x43": 0.4,
    "x44": 80,
    "x45": 90,
    "x46": 0.6,
    "x51": 0.5,
    "x52": 0.2,
    "x53": 7,
    "x54": 0.3,
    "x55": 0.7,
    "x56": 0.6,
    "x61": 60,
    "x62": 20,
    "x63": 0.5,
    "x64": 0.7,
    "x65": 0.6,
    "x66": 0.7,
    "x71": 0.7,
    "x72": 0.8,
    "x73": 6000,
    "x74": 0.6,
    "x75": 0.7,
    "x76": 0.8,
}

layer_scores, normalized = compute_layer_scores(config, example_data)
power9_scores = compute_power9_scores(config, layer_scores)
bz = compute_bz_index(config, power9_scores)

report = build_full_diagnostics(
    config=config,
    raw_values=example_data,
    normalized_values=normalized,
    layer_scores=layer_scores,
    power9_scores=power9_scores,
    bz_index=bz,
)
print_diagnostics(report)

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