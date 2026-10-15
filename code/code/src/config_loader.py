from pathlib import Path
import yaml

from src.data_models import (
    IndicatorDefinition,
    LayerDefinition,
    Power9Definition,
    EngineConfig,
)


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_engine_config(config_dir: str | Path) -> EngineConfig:
    config_dir = Path(config_dir)

    indicators_raw = _load_yaml(config_dir / "indicators.yaml")
    layers_raw = _load_yaml(config_dir / "layers.yaml")
    power9_raw = _load_yaml(config_dir / "power9.yaml")
    bz_weights_raw = _load_yaml(config_dir / "bz_weights.yaml")

    indicators = {
        ind_id: IndicatorDefinition(
            id=ind_id,
            name=payload["name"],
            layer_id=payload["layer_id"],
            direction=payload["direction"],
            weight=payload["weight"],
            min_value=payload["min_value"],
            max_value=payload["max_value"],
        )
        for ind_id, payload in indicators_raw.items()
    }

    layers = {
        layer_id: LayerDefinition(
            id=layer_id,
            name=payload["name"],
            indicator_ids=payload["indicator_ids"],
        )
        for layer_id, payload in layers_raw.items()
    }

    power9 = {
        p_id: Power9Definition(
            id=p_id,
            name=payload["name"],
            layer_weights=payload["layer_weights"],
        )
        for p_id, payload in power9_raw.items()
    }

    for layer_id, layer in layers.items():
        for ind_id in layer.indicator_ids:
            if ind_id not in indicators:
                raise ValueError(
                    f"Layer '{layer_id}' references missing indicator '{ind_id}'"
                )

    for p_id, p_def in power9.items():
        for layer_id in p_def.layer_weights:
            if layer_id not in layers:
                raise ValueError(
                    f"Power9 '{p_id}' references missing layer '{layer_id}'"
                )

    return EngineConfig(
        indicators=indicators,
        layers=layers,
        power9=power9,
        bz_weights=bz_weights_raw,
    )