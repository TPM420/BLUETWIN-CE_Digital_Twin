"""
hashing.py

Preprosta pomozna funkcija za racunanje SHA-256 hasha datotek.

Zakaj to potrebujemo (razdelek 3.3 navodil): ker (se) nimamo baze,
sledljivost resujemo z verzijami in hashi. Vsak API odgovor naj
vsebuje hash konfiguracije in hash pilotnih podatkov, da je vedno
jasno, s katero TOCNO razlicico datotek je bil rezultat izracunan.
"""

import hashlib
from pathlib import Path


def sha256_of_file(path: str | Path) -> str:
    """Vrne 'sha256:<hex>' za vsebino ene datoteke."""
    path = Path(path)
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"


def sha256_of_files(paths: list[str | Path]) -> str:

    hasher = hashlib.sha256()
    for path in sorted(str(p) for p in paths):
        hasher.update(Path(path).read_bytes())
    return f"sha256:{hasher.hexdigest()}"

"""
    Vrne EN skupni hash za VEC datotek skupaj (npr. vse config/*.yaml).
    Datoteke zdruzimo v vedno enakem (abecednem) vrstnem redu, da je
    rezultat vedno enak, ne glede na to, v kaksnem vrstnem redu jih
    podamo.
    """