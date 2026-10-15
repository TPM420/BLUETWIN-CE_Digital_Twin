"""
pilot_validator.py

Preveri, ali je pilotna datoteka (npr. pilot_data/svidnik.yaml) v redu,
preden jo uporabimo v modelu. Sledi zahtevam iz razdelka 5.2 navodil:

  - obvezna metadata polja: code, name, data_version
  - ali so vsi indicator ID-ji znani v config/indicators.yaml
  - ali so value numericne ali null (nic drugega)
  - ali imajo razpolozljive vrednosti leto (year) in vir (source)
  - ali je mapping_type dovoljen (exact/proxy/derived/unmapped)
  - ali je quality dovoljena vrednost
  - ali je value zunaj min_value/max_value iz indicators.yaml -> warning
  - pokritost (coverage) po slojih -> warning, ce je prenizka

Rezultat je slovar z dvema seznamoma: "errors" (hude napake, model se
ne bi smel zagnati) in "warnings" (opozorila, model se lahko zazene,
a uporabnik mora vedeti zanje).
"""

ALLOWED_MAPPING_TYPES = {"exact", "proxy", "derived", "unmapped"}
ALLOWED_QUALITY = {
    "official",
    "national_proxy",
    "estimated",
    "needs_review",
    "corrected",
    "missing",
    "rejected",
    "context",
    "calculated",
}

REQUIRED_METADATA_FIELDS = ["code", "name", "data_version"]

# Kaksna pokritost (delez utezi z dejansko vrednostjo) v enem sloju je
# se "dovolj dobra". Pod to mejo damo opozorilo (warning), ne napake.
LOW_COVERAGE_WARNING_THRESHOLD = 0.40


def validate_pilot_data(config, pilot_data: dict) -> dict:
    errors = []
    warnings = []

    # 1) obvezna metadata polja
    for field in REQUIRED_METADATA_FIELDS:
        if not pilot_data.get(field):
            errors.append(f"Manjka obvezno metapolje '{field}' na vrhu pilotne YAML datoteke.")

    indicators = pilot_data.get("indicators", {})
    if not indicators:
        errors.append("Pilotna datoteka ne vsebuje nobenega indikatorja ('indicators' je prazen).")
        return {"errors": errors, "warnings": warnings}

    known_ids = set(config.indicators.keys())

    # 2)-6) preverjanje vsakega indikatorja posebej
    for ind_id, payload in indicators.items():

        # ali je ID sploh znan v indicators.yaml
        if ind_id not in known_ids:
            errors.append(f"'{ind_id}': neznan indicator_id (ni v config/indicators.yaml).")
            continue

        value = payload.get("value")

        # value mora biti numericna ali None (null)
        if value is not None and not isinstance(value, (int, float)):
            errors.append(f"'{ind_id}': value '{value}' ni niti stevilka niti null.")

        # ce vrednost obstaja, morata biti izpolnjena year in source
        if value is not None:
            if not payload.get("year"):
                warnings.append(f"'{ind_id}': ima vrednost, a manjka 'year'.")
            if not payload.get("source"):
                warnings.append(f"'{ind_id}': ima vrednost, a manjka 'source'.")

        # mapping_type mora biti eden od dovoljenih
        mapping_type = payload.get("mapping_type")
        if mapping_type not in ALLOWED_MAPPING_TYPES:
            errors.append(
                f"'{ind_id}': mapping_type '{mapping_type}' ni dovoljen "
                f"(dovoljeno: {sorted(ALLOWED_MAPPING_TYPES)})."
            )

        # quality mora biti ena od dovoljenih
        quality = payload.get("quality")
        if quality not in ALLOWED_QUALITY:
            errors.append(
                f"'{ind_id}': quality '{quality}' ni dovoljena "
                f"(dovoljeno: {sorted(ALLOWED_QUALITY)})."
            )

        # ali je vrednost izven min/max razpona iz indicators.yaml -> warning
        if value is not None and isinstance(value, (int, float)) and ind_id in known_ids:
            indicator = config.indicators[ind_id]
            if value < indicator.min_value or value > indicator.max_value:
                warnings.append(
                    f"'{ind_id}': value={value} je izven pricakovanega razpona "
                    f"[{indicator.min_value}, {indicator.max_value}] iz indicators.yaml."
                )

    # 7) pokritost po slojih (coverage)
    raw_values = {ind_id: payload.get("value") for ind_id, payload in indicators.items()}
    for layer_id, layer in config.layers.items():
        total_weight = 0.0
        covered_weight = 0.0
        for ind_id in layer.indicator_ids:
            indicator = config.indicators.get(ind_id)
            if indicator is None:
                continue
            total_weight += indicator.weight
            if raw_values.get(ind_id) is not None:
                covered_weight += indicator.weight

        coverage = covered_weight / total_weight if total_weight > 0 else 0.0
        if coverage < LOW_COVERAGE_WARNING_THRESHOLD:
            warnings.append(
                f"Sloj '{layer_id}' ({layer.name}): nizka pokritost podatkov "
                f"({coverage:.0%}) - manjka vecina indikatorjev v tem sloju."
            )

    return {"errors": errors, "warnings": warnings}


def print_validation_report(report: dict) -> None:
    print("=== VALIDACIJA PILOTNIH PODATKOV ===")

    if not report["errors"] and not report["warnings"]:
        print("PASS - brez napak in opozoril.")
        return

    if report["errors"]:
        print(f"\nNAPAKE ({len(report['errors'])}) - te je treba popraviti:")
        for e in report["errors"]:
            print(f"  [ERROR] {e}")
    else:
        print("\nNi hudih napak (PASS na ravni napak).")

    if report["warnings"]:
        print(f"\nOPOZORILA ({len(report['warnings'])}) - model se lahko zazene, a bodi pozoren:")
        for w in report["warnings"]:
            print(f"  [WARN] {w}")
