import math


def minmax_normalize(value, min_value, max_value):
    if value is None:
        return None

    if math.isclose(min_value, max_value):
        raise ValueError("Invalid normalization range")

    v = (value - min_value) / (max_value - min_value)
    return max(0.0, min(1.0, v))


def normalize_indicator(value, indicator):
    v = minmax_normalize(value, indicator.min_value, indicator.max_value)

    if v is None:
        return None

    if indicator.direction == "negative":
        v = 1 - v

    return v