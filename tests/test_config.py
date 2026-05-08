"""Tests for _config.py — TOML loading."""

from qdas_parser._config import QDAS_CONFIG


def test_config_is_dict():
    assert isinstance(QDAS_CONFIG, dict)


def test_config_has_features_sep():
    assert QDAS_CONFIG['features']['sep']['dec'] == 15


def test_config_has_extensions_sep():
    assert QDAS_CONFIG['extensions']['sep']['dec'] == 20


def test_config_has_required_fields():
    assert 'K0100' in QDAS_CONFIG['fields']['required']
    assert 'K1001' in QDAS_CONFIG['fields']['required']
    assert 'K2002' in QDAS_CONFIG['fields']['required']


def test_config_has_extensions_order():
    order = QDAS_CONFIG['extensions']['order']
    assert order['1'] == 'Wert'
    assert order['5'] == 'Chargennummer'
