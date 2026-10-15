from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


@dataclass
class InterventionRecommendation:
    indicator_id: str
    indicator_name: str
    layer_id: str
    layer_name: str
    normalized_value: Optional[float]
    indicator_weight: float
    layer_score: float
    total_priority: float
    power9_links: List[Dict[str, Any]]
    interventions: List[str]

def load_interventions(config_path: str | Path) -> Dict[str, Any]:
    path = Path(config_path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_indicator_to_power9_map(config) -> Dict[str, List[Dict[str, Any]]]:
    """
    Builds a reverse map:
        indicator_id -> list of impacted Power9 dimensions with weights.

    Impact path:
        indicator -> layer (indicator.weight)
        layer -> power9 (power9.layer_weights[layer_id])
        power9 -> BZ (config.bz_weights or equal weights)
    """
    if config.bz_weights:
        bz_weights = dict(config.bz_weights)
    else:
        equal_weight = 1.0 / len(config.power9) if config.power9 else 0.0
        bz_weights = {p_id: equal_weight for p_id in config.power9}

    reverse_map: Dict[str, List[Dict[str, Any]]] = {}

    for indicator_id, indicator in config.indicators.items():
        layer_id = indicator.layer_id
        reverse_map[indicator_id] = []

        for p_id, p_def in config.power9.items():
            layer_weight = p_def.layer_weights.get(layer_id, 0.0)
            if layer_weight <= 0:
                continue

            reverse_map[indicator_id].append(
                {
                    "power9_id": p_id,
                    "power9_name": p_def.name,
                    "layer_weight": layer_weight,
                    "bz_weight": bz_weights.get(p_id, 0.0),
                }
            )

    return reverse_map

def estimate_indicator_priority(
    indicator_id: str,
    config,
    normalized_values: Dict[str, Optional[float]],
    layer_scores: Dict[str, float],
    indicator_to_power9: Dict[str, List[Dict[str, Any]]],
    deficit_mode: str = "gap",
) -> Dict[str, Any]:
    """
    Computes a simple intervention priority score.

    Default priority logic:
        deficit * indicator_weight * sum(layer_to_power9_weight * bz_weight)

    deficit_mode:
        - "gap": deficit = 1 - normalized_value
        - "shortfall_below_half": deficit = max(0, 0.5 - normalized_value) / 0.5
    """
    indicator = config.indicators[indicator_id]
    norm_value = normalized_values.get(indicator_id)
    layer_id = indicator.layer_id
    layer_score = layer_scores.get(layer_id, 0.0)

    if norm_value is None:
        deficit = 1.0
    else:
        if deficit_mode == "gap":
            deficit = 1.0 - norm_value
        elif deficit_mode == "shortfall_below_half":
            deficit = max(0.0, 0.5 - norm_value) / 0.5
        else:
            raise ValueError(f"Unsupported deficit_mode: {deficit_mode}")

    p_links = indicator_to_power9.get(indicator_id, [])
    structural_weight = sum(item["layer_weight"] * item["bz_weight"] for item in p_links)
    total_priority = deficit * indicator.weight * structural_weight

    return {
        "indicator_id": indicator_id,
        "indicator_name": indicator.name,
        "layer_id": layer_id,
        "layer_name": config.layers[layer_id].name,
        "normalized_value": norm_value,
        "indicator_weight": indicator.weight,
        "layer_score": layer_score,
        "deficit": deficit,
        "structural_weight": structural_weight,
        "total_priority": total_priority,
        "power9_links": p_links,
    }

def find_low_indicators(
    normalized_values: Dict[str, Optional[float]],
    threshold: float = 0.40,
    include_missing: bool = False,
) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {}
    for indicator_id, value in normalized_values.items():
        if value is None:
            if include_missing:
                out[indicator_id] = value
            continue
        if value < threshold:
            out[indicator_id] = value
    return out


def generate_intervention_recommendations(
    config,
    normalized_values: Dict[str, Optional[float]],
    layer_scores: Dict[str, float],
    interventions_catalog: Dict[str, Any],
    threshold: float = 0.40,
    include_missing: bool = False,
    top_n: Optional[int] = None,
    deficit_mode: str = "gap",
) -> List[InterventionRecommendation]:
    indicator_to_power9 = get_indicator_to_power9_map(config)
    low_indicators = find_low_indicators(
        normalized_values=normalized_values,
        threshold=threshold,
        include_missing=include_missing,
    )

    recommendations: List[InterventionRecommendation] = []

    for indicator_id in low_indicators:
        priority = estimate_indicator_priority(
            indicator_id=indicator_id,
            config=config,
            normalized_values=normalized_values,
            layer_scores=layer_scores,
            indicator_to_power9=indicator_to_power9,
            deficit_mode=deficit_mode,
        )

        intervention_entry = interventions_catalog.get(indicator_id, {})
        interventions = intervention_entry.get("interventions", [])

        recommendations.append(
            InterventionRecommendation(
                indicator_id=priority["indicator_id"],
                indicator_name=priority["indicator_name"],
                layer_id=priority["layer_id"],
                layer_name=priority["layer_name"],
                normalized_value=priority["normalized_value"],
                indicator_weight=priority["indicator_weight"],
                layer_score=priority["layer_score"],
                total_priority=priority["total_priority"],
                power9_links=priority["power9_links"],
                interventions=interventions,
            )
        )

    recommendations.sort(key=lambda x: x.total_priority, reverse=True)

    if top_n is not None:
        recommendations = recommendations[:top_n]

    return recommendations

def recommendations_to_dict(recommendations: List[InterventionRecommendation]) -> List[Dict[str, Any]]:
    return [
        {
            "indicator_id": r.indicator_id,
            "indicator_name": r.indicator_name,
            "layer_id": r.layer_id,
            "layer_name": r.layer_name,
            "normalized_value": r.normalized_value,
            "indicator_weight": r.indicator_weight,
            "layer_score": r.layer_score,
            "total_priority": r.total_priority,
            "power9_links": r.power9_links,
            "interventions": r.interventions,
        }
        for r in recommendations
    ]

def print_recommendations(recommendations: List[InterventionRecommendation]) -> None:
    print("=== INTERVENTION RECOMMENDATIONS ===")
    if not recommendations:
        print("No weak indicators detected for the selected threshold.")
        return

    for idx, rec in enumerate(recommendations, start=1):
        norm_str = "None" if rec.normalized_value is None else f"{rec.normalized_value:.4f}"
        print(
            f"{idx}. {rec.indicator_id} - {rec.indicator_name}"
            f"   Layer: {rec.layer_id} - {rec.layer_name}"
            f"   Normalized value: {norm_str}"
            f"   Layer score: {rec.layer_score:.4f}"
            f"   Indicator weight: {rec.indicator_weight:.4f}"
            f"   Priority score: {rec.total_priority:.6f}"
        )

        if rec.power9_links:
            print("   Impacts Power9:")
            for p in rec.power9_links:
                print(
                    f"     - {p['power9_id']} ({p['power9_name']}): "
                    f"layer_weight={p['layer_weight']:.4f}, bz_weight={p['bz_weight']:.4f}"
                )

        if rec.interventions:
            print("   Recommended actions:")
            for action in rec.interventions:
                print(f"     • {action}")
        else:
            print("   Recommended actions: none defined in interventions catalog.")