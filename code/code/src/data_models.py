from dataclasses import dataclass
from typing import Dict, List, Optional, Literal

Direction = Literal["positive", "negative"]


@dataclass
class IndicatorDefinition:
    id: str
    name: str
    layer_id: str
    direction: Direction
    weight: float
    min_value: float
    max_value: float


@dataclass
class LayerDefinition:
    id: str
    name: str
    indicator_ids: List[str]


@dataclass
class Power9Definition:
    id: str
    name: str
    layer_weights: Dict[str, float]


@dataclass
class EngineConfig:
    indicators: Dict[str, IndicatorDefinition]
    layers: Dict[str, LayerDefinition]
    power9: Dict[str, Power9Definition]
    bz_weights: Dict[str, float]