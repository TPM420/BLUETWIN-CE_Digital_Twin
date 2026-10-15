"""
pilot_loader.py

Preprost loader za pilotne podatke (npr. pilot_data/svidnik.yaml).

Naloga tega modula je SAMO branje YAML datoteke in pretvorba v
"raw_values" slovar oblike {"x11": 0.3, "x12": None, ...}, ki ga
obstojece modelno jedro (layer_scoring.py) ze razume.

Namenoma je preprost - brez zapletenih razredov - ker je to
zacetniski projekt in loader mora biti lahko berljiv.
"""

from pathlib import Path
import yaml


def load_pilot_data(path: str | Path) -> dict:
    """
    Prebere pilotno YAML datoteko (npr. pilot_data/svidnik.yaml) in vrne
    CELOTNO vsebino kot slovar (code, name, data_version, indicators, ...).

    To ni se raw_values - za to uporabi extract_raw_values().
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"Datoteka '{path}' je prazna ali napacna.")

    return data


def extract_raw_values(pilot_data: dict) -> dict:
    """
    Iz celotne pilotne vsebine (glej load_pilot_data) izlusci samo
    {"indicator_id": value} slovar, ki ga potrebuje layer_scoring.py.

    Ce vrednost manjka (null v YAML), bo v slovarju None - to je
    pricakovano in ga compute_layer_scores() ze zna obravnavati
    (tak indikator se preprosto preskoci).
    """
    indicators = pilot_data.get("indicators", {})

    raw_values = {}
    for ind_id, payload in indicators.items():
        raw_values[ind_id] = payload.get("value")

    return raw_values


def load_raw_values(path: str | Path) -> dict:
    """
    Prirocna funkcija "dva-v-enem": prebere YAML in takoj vrne
    raw_values slovar, pripravljen za compute_layer_scores(config, raw_values).
    """
    pilot_data = load_pilot_data(path)
    return extract_raw_values(pilot_data)
