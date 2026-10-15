from src.pilot_service import get_baseline


def test_isti_klic_da_bajtno_enak_rezultat():
    """Dva zaporedna klica get_baseline za isti pilot na isti konfiguraciji morata dati popolnoma enak rezultat."""
    prvi = get_baseline('svidnik')
    drugi = get_baseline('svidnik')
    assert prvi == drugi


def test_bz_index_je_vedno_enako_stevilo():
    """BZ indeks mora biti reproducibilen - ne sme se spreminjati med zagoni."""
    rezultat1 = get_baseline('svidnik')
    rezultat2 = get_baseline('svidnik')
    assert rezultat1['bz_index'] == rezultat2['bz_index']


def test_baseline_vsebuje_pricakovana_polja():
    """Osnovna preverba oblike odgovora - da vsa pricakovana polja obstajajo."""
    rezultat = get_baseline('svidnik')
    for polje in [
        'pilot', 'pilot_name', 'data_version', 'bz_index', 'layer_scores', 'power9_scores',
        'data_coverage', 'warnings', 'indicators', 'config_hash', 'pilot_data_hash',
    ]:
        assert polje in rezultat