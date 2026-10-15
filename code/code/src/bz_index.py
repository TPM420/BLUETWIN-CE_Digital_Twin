def compute_bz_index(config, power9_scores):

    if config.bz_weights:
        total = 0

        for p_id, weight in config.bz_weights.items():
            total += weight * power9_scores[p_id]

        return total

    return sum(power9_scores.values()) / len(power9_scores)