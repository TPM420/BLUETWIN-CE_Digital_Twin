def compute_power9_scores(config, layer_scores):
    scores = {}

    for p_id, p_def in config.power9.items():
        value = 0.0

        for layer_id, weight in p_def.layer_weights.items():
            if layer_id not in layer_scores:
                raise ValueError(
                    f"Power9 '{p_id}' references missing layer score '{layer_id}'. "
                    f"Available layer scores: {list(layer_scores.keys())}"
                )
            value += weight * layer_scores[layer_id]

        scores[p_id] = value

    return scores