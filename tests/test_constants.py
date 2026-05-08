"""Tests for _constants.py — frozen dataclass QDAS."""

import re
from dataclasses import FrozenInstanceError

import pytest

from qdas_parser._constants import QDAS


# ---------------------------------------------------------------------------
# Separator characters
# ---------------------------------------------------------------------------

def test_sep_f_is_chr15():
    assert QDAS.SEP_F == chr(15)


def test_sep_e_is_chr20():
    assert QDAS.SEP_E == chr(20)


# ---------------------------------------------------------------------------
# PART_ID, ORDER and TIMESTAMP constants
# ---------------------------------------------------------------------------

def test_part_id_is_seriennummer():
    assert QDAS.PART_ID == 'Seriennummer'


def test_order_is_auftrag():
    assert QDAS.ORDER == 'Auftragsnummer'


def test_timestamp_is_zeitstempel():
    assert QDAS.TIMESTAMP == 'Zeitstempel'

# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------

def test_qdas_frozen_raises_on_assignment():
    with pytest.raises(FrozenInstanceError):
        QDAS.SEP_F = 'X'  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Compiled regexes
# ---------------------------------------------------------------------------

def test_re_header_matches_header_line():
    m = QDAS.RE_HEADER.match('K0100 9')
    assert m is not None
    assert m.group(1) == 'K0100'
    assert m.group(2) is None
    assert m.group(3) == '9'


def test_re_header_matches_feature_line():
    m = QDAS.RE_HEADER.match('K2002/1 Merkmalname')
    assert m is not None
    assert m.group(1) == 'K2002'
    assert m.group(2) == '1'
    assert m.group(3) == 'Merkmalname'


def test_re_clean_line_matches_kfield():
    assert QDAS.RE_CLEAN_LINE.match('K0100 9') is not None


def test_re_clean_line_rejects_value_line():
    assert QDAS.RE_CLEAN_LINE.match('1.234\x0f5.678') is None
