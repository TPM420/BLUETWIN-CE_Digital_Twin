from src.normalization import normalize_indicator

def compute_layer_scores(config, raw_values):

    normalized = {}

    for ind_id, ind in config.indicators.items():
        normalized[ind_id] = normalize_indicator(raw_values.get(ind_id), ind)

    layer_scores = {}

    for layer_id, layer in config.layers.items():

        weighted_sum = 0
        total_weight = 0

        for ind_id in layer.indicator_ids:

            indicator = config.indicators[ind_id]
            value = normalized[ind_id]

            if value is None:
                continue

            w = indicator.weight

            weighted_sum += w * value
            total_weight += w

        if total_weight == 0:
            layer_scores[layer_id] = 0
        else:
            layer_scores[layer_id] = weighted_sum / total_weight

    return layer_scores, normalized