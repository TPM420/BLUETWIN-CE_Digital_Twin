"""Testi za src/hashing.py (SHA-256 sledljivost config/podatkovnih datotek)."""

import hashlib

from src.hashing import sha256_of_file, sha256_of_files


def test_sha256_of_file_se_ujema_z_navadnim_hashlib(tmp_path):
    """sha256_of_file mora vrniti isti hash kot rocni izracun s hashlib, samo s predpono 'sha256:'."""
    datoteka = tmp_path / "a.txt"
    datoteka.write_text("hello world")

    pricakovano = f"sha256:{hashlib.sha256(b'hello world').hexdigest()}"
    assert sha256_of_file(datoteka) == pricakovano


def test_sha256_of_file_se_spremeni_z_vsebino(tmp_path):
    """Ce se vsebina datoteke spremeni, se mora spremeniti tudi hash - to je bistvo sledljivosti."""
    datoteka = tmp_path / "a.txt"
    datoteka.write_text("v1")
    prvi_hash = sha256_of_file(datoteka)

    datoteka.write_text("v2")
    drugi_hash = sha256_of_file(datoteka)

    assert prvi_hash != drugi_hash


def test_sha256_of_files_ni_odvisen_od_vrstnega_reda(tmp_path):
    """Hash vec datotek skupaj mora biti enak, ne glede na vrstni red podanih poti (abecedno urejanje)."""
    datoteka1 = tmp_path / "a.txt"
    datoteka2 = tmp_path / "b.txt"
    datoteka1.write_text("aaa")
    datoteka2.write_text("bbb")

    naprej = sha256_of_files([datoteka1, datoteka2])
    obratno = sha256_of_files([datoteka2, datoteka1])

    assert naprej == obratno


def test_sha256_of_files_se_spremeni_ce_katerakoli_datoteka_spremeni(tmp_path):
    """Ce se spremeni ena sama izmed vec datotek, se mora spremeniti tudi skupni hash."""
    datoteka1 = tmp_path / "a.txt"
    datoteka2 = tmp_path / "b.txt"
    datoteka1.write_text("aaa")
    datoteka2.write_text("bbb")

    pred = sha256_of_files([datoteka1, datoteka2])
    datoteka2.write_text("spremenjeno")
    po = sha256_of_files([datoteka1, datoteka2])

    assert pred != po


def test_config_hash_pravih_datotek_je_reproducibilen():
    """Hash prave config/ mape (kot ga uporablja main.py) mora biti pri dveh zaporednih klicih enak."""
    from pathlib import Path

    config_files = [
        Path("config") / "indicators.yaml",
        Path("config") / "layers.yaml",
        Path("config") / "power9.yaml",
        Path("config") / "bz_weights.yaml",
    ]
    assert sha256_of_files(config_files) == sha256_of_files(config_files)
