from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional
from copy import deepcopy
import yaml

from src.layer_scoring import compute_layer_scores
from src.power9_scoring import compute_power9_scores
from src.bz_index import compute_bz_index

@dataclass
class ScenarioRunResult:
    scenario_id: str
    scenario_name: str
    baseline_raw_values: Dict[str, Optional[float]]
    scenario_raw_values: Dict[str, Optional[float]]
    baseline_layer_scores: Dict[str, float]
    scenario_layer_scores: Dict[str, float]
    baseline_power9_scores: Dict[str, float]
    scenario_power9_scores: Dict[str, float]
    baseline_bz_index: float
    scenario_bz_index: float
    delta_indicators: Dict[str, Optional[float]]
    delta_layers: Dict[str, float]
    delta_power9: Dict[str, float]
    delta_bz: float
    applied_actions: List[Dict[str, Any]]


def load_scenarios(config_path: str | Path) -> Dict[str, Any]:
    path = Path(config_path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _clip_to_indicator_bounds(value: float, indicator) -> float:
    return max(indicator.min_value, min(indicator.max_value, value))



def _apply_single_effect(current_value: Optional[float], effect: Dict[str, Any], indicator) -> Optional[float]:
    mode = effect["mode"]
    value = effect["value"]

    if current_value is None and mode != "set":
        return None

    if mode == "absolute":
        new_value = current_value + value
    elif mode == "relative":
        new_value = current_value * (1.0 + value)
    elif mode == "set":
        new_value = value
    else:
        raise ValueError(f"Unsupported scenario effect mode: {mode}")

    return _clip_to_indicator_bounds(new_value, indicator)

def apply_scenario_actions(
    config,
    raw_values: Dict[str, Optional[float]],
    scenario_def: Dict[str, Any],
) -> tuple[Dict[str, Optional[float]], List[Dict[str, Any]]]:
    updated = deepcopy(raw_values)
    applied_actions: List[Dict[str, Any]] = []

    affected = scenario_def.get("affected_indicators", {})

    for indicator_id, effect in affected.items():
        if indicator_id not in config.indicators:
            raise ValueError(
                f"Scenario '{scenario_def.get('name', 'unknown')}' references unknown indicator '{indicator_id}'"
            )

        indicator = config.indicators[indicator_id]
        before = updated.get(indicator_id)
        after = _apply_single_effect(before, effect, indicator)
        updated[indicator_id] = after

        applied_actions.append(
            {
                "indicator_id": indicator_id,
                "indicator_name": indicator.name,
                "mode": effect["mode"],
                "value": effect["value"],
                "before": before,
                "after": after,
            }
        )

    return updated, applied_actions

def run_scenario(
    config,
    raw_values: Dict[str, Optional[float]],
    scenario_id: str,
    scenario_def: Dict[str, Any],
) -> ScenarioRunResult:
    baseline_layer_scores, _ = compute_layer_scores(config, raw_values)
    baseline_power9_scores = compute_power9_scores(config, baseline_layer_scores)
    baseline_bz_index = compute_bz_index(config, baseline_power9_scores)

    scenario_raw_values, applied_actions = apply_scenario_actions(config, raw_values, scenario_def)
    scenario_layer_scores, _ = compute_layer_scores(config, scenario_raw_values)
    scenario_power9_scores = compute_power9_scores(config, scenario_layer_scores)
    scenario_bz_index = compute_bz_index(config, scenario_power9_scores)

    delta_indicators: Dict[str, Optional[float]] = {}
    all_indicator_ids = set(raw_values.keys()) | set(scenario_raw_values.keys())
    for indicator_id in all_indicator_ids:
        before = raw_values.get(indicator_id)
        after = scenario_raw_values.get(indicator_id)
        if before is None or after is None:
            delta_indicators[indicator_id] = None
        else:
            delta_indicators[indicator_id] = after - before

    delta_layers = {
        k: scenario_layer_scores[k] - baseline_layer_scores[k]
        for k in baseline_layer_scores
    }
    delta_power9 = {
        k: scenario_power9_scores[k] - baseline_power9_scores[k]
        for k in baseline_power9_scores
    }
    delta_bz = scenario_bz_index - baseline_bz_index

    return ScenarioRunResult(
        scenario_id=scenario_id,
        scenario_name=scenario_def.get("name", scenario_id),
        baseline_raw_values=deepcopy(raw_values),
        scenario_raw_values=scenario_raw_values,
        baseline_layer_scores=baseline_layer_scores,
        scenario_layer_scores=scenario_layer_scores,
        baseline_power9_scores=baseline_power9_scores,
        scenario_power9_scores=scenario_power9_scores,
        baseline_bz_index=baseline_bz_index,
        scenario_bz_index=scenario_bz_index,
        delta_indicators=delta_indicators,
        delta_layers=delta_layers,
        delta_power9=delta_power9,
        delta_bz=delta_bz,
        applied_actions=applied_actions,
    )

def run_multiple_scenarios(
    config,
    raw_values: Dict[str, Optional[float]],
    scenarios_catalog: Dict[str, Any],
    scenario_ids: Optional[List[str]] = None,
) -> List[ScenarioRunResult]:
    if scenario_ids is None:
        scenario_ids = list(scenarios_catalog.keys())

    results: List[ScenarioRunResult] = []
    for scenario_id in scenario_ids:
        if scenario_id not in scenarios_catalog:
            raise ValueError(f"Unknown scenario_id '{scenario_id}'")
        results.append(
            run_scenario(config, raw_values, scenario_id, scenarios_catalog[scenario_id])
        )

    results.sort(key=lambda r: r.delta_bz, reverse=True)
    return results

def print_scenario_result(result: ScenarioRunResult) -> None:
    print("=== SCENARIO RESULT ===")
    print(f"Scenario: {result.scenario_id} - {result.scenario_name}")
    print(f"Baseline BZ: {result.baseline_bz_index:.4f}")
    print(f"Scenario BZ: {result.scenario_bz_index:.4f}")
    print(f"Delta BZ:    {result.delta_bz:+.4f}")

    print("Applied changes:")
    for item in result.applied_actions:
        print(
            f"  {item['indicator_id']} ({item['indicator_name']}): "
            f"{item['before']} -> {item['after']} [{item['mode']} {item['value']}]"
        )

    print("Layer changes:")
    for k, v in result.delta_layers.items():
        print(f"  {k}: {v:+.4f}")

    print("Power9 changes:")
    for k, v in result.delta_power9.items():
        print(f"  {k}: {v:+.4f}")



def print_scenario_ranking(results: List[ScenarioRunResult]) -> None:
    print("=== SCENARIO RANKING BY DELTA BZ ===")
    for idx, result in enumerate(results, start=1):
        print(f"{idx}. {result.scenario_id} - {result.scenario_name}: delta_bz={result.delta_bz:+.4f}")


