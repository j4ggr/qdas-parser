"""Tests for _config.py — TOML loading."""

from qdas_parser._config import QDAS_CONFIG
from qdas_parser._constants import QDAS


def test_config_is_dict():
    assert isinstance(QDAS_CONFIG, dict)


def test_config_has_required_fields():
    assert 'K0100' in QDAS_CONFIG['fields']['required']
    assert 'K1001' in QDAS_CONFIG['fields']['required']
    assert 'K2002' in QDAS_CONFIG['fields']['required']


def test_qdas_sep_f_is_15():
    assert ord(QDAS.SEP_F) == 15


def test_qdas_sep_e_is_20():
    assert ord(QDAS.SEP_E) == 20


def test_qdas_extensions_order():
    assert QDAS.EXTENSIONS[0] == 'Wert'
    assert QDAS.EXTENSIONS[4] == 'Chargennummer'
