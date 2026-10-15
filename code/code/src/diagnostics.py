from typing import Dict, Any


def compute_layer_diagnostics(config, raw_values, normalized_values, layer_scores):
    diagnostics = {}

    for layer_id, layer in config.layers.items():
        items = []
        weighted_sum = 0.0
        total_weight = 0.0

        for ind_id in layer.indicator_ids:
            indicator = config.indicators[ind_id]
            raw_value = raw_values.get(ind_id)
            norm_value = normalized_values.get(ind_id)
            weight = indicator.weight

            if norm_value is None:
                contribution = None
            else:
                contribution = weight * norm_value
                weighted_sum += contribution
                total_weight += weight

            items.append(
                {
                    "indicator_id": ind_id,
                    "indicator_name": indicator.name,
                    "raw_value": raw_value,
                    "normalized_value": norm_value,
                    "weight": weight,
                    "weighted_contribution": contribution,
                }
            )

        diagnostics[layer_id] = {
            "layer_name": layer.name,
            "layer_score": layer_scores[layer_id],
            "total_weight_used": total_weight,
            "weighted_sum": weighted_sum,
            "indicators": items,
        }

    return diagnostics

def compute_power9_diagnostics(config, layer_scores, power9_scores):
    diagnostics = {}

    for p_id, p_def in config.power9.items():
        items = []
        for layer_id, weight in p_def.layer_weights.items():
            items.append(
                {
                    "layer_id": layer_id,
                    "layer_name": config.layers[layer_id].name,
                    "layer_score": layer_scores[layer_id],
                    "weight": weight,
                    "weighted_contribution": weight * layer_scores[layer_id],
                }
            )

        diagnostics[p_id] = {
            "power9_name": p_def.name,
            "power9_score": power9_scores[p_id],
            "layers": items,
        }

    return diagnostics


def build_full_diagnostics(config, raw_values, normalized_values, layer_scores, power9_scores, bz_index):
    return {
        "normalized_indicators": normalized_values,
        "layers": compute_layer_diagnostics(config, raw_values, normalized_values, layer_scores),
        "power9": compute_power9_diagnostics(config, layer_scores, power9_scores),
        "bz_index": bz_index,
    }



def print_diagnostics(report: Dict[str, Any]) -> None:
    print("=== NORMALIZED INDICATORS ===")
    for k, v in report["normalized_indicators"].items():
        print(f"{k}: {v}")

    print("=== LAYER DIAGNOSTICS ===")
    for layer_id, layer_data in report["layers"].items():
        print(f" {layer_id} - {layer_data['layer_name']} | score={layer_data['layer_score']:.4f}")
        for item in layer_data["indicators"]:
            print(
                f"  {item['indicator_id']} | raw={item['raw_value']} | norm={item['normalized_value']} | "
                f"w={item['weight']} | contrib={item['weighted_contribution']}"
            )

    print("=== POWER9 DIAGNOSTICS ===")
    for p_id, p_data in report["power9"].items():
        print(f" {p_id} - {p_data['power9_name']} | score={p_data['power9_score']:.4f}")
        for item in p_data["layers"]:
            print(
                f"  {item['layer_id']} | layer_score={item['layer_score']:.4f} | "
                f"w={item['weight']} | contrib={item['weighted_contribution']:.4f}"
            )

    print(f" === BLUE ZONE INDEX === BZ = {report['bz_index']:.4f}")