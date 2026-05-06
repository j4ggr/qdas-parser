"""Tests for _module.py — AssemblyLineModule."""

import pytest

from qdas_parser._module import AssemblyLineModule


TC_MODULES = {
    'ACT1': {
        'act1_as1': ['tc1_bd', 'tc2_bd', 'tc3_bd'],
    }
}


class TestModuleBasic:
    def test_name_normalised_to_kind_suffix(self):
        m = AssemblyLineModule('m01_bd', 'ACT1', 'act1_as1', 'bd')
        assert m.name == 'm01_bd'

    def test_name_strips_extra_segments(self):
        # only the first underscore-delimited segment + kind is kept
        m = AssemblyLineModule('tc1_bd_extra', 'ACT1', 'act1_as1', 'bd')
        assert m.name == 'tc1_bd'

    def test_product_uppercased(self):
        m = AssemblyLineModule('m01', 'act1', 'act1_as1', 'bd')
        assert m.product == 'ACT1'

    def test_not_test_cell_by_default(self):
        m = AssemblyLineModule('m01', 'ACT1', 'act1_as1', 'bd')
        assert not m.is_test_cell
        assert m.tc_number is None

    def test_bool_false_for_regular_module(self):
        m = AssemblyLineModule('m01', 'ACT1', 'act1_as1', 'bd')
        assert not m

    def test_str_returns_name_for_regular(self):
        m = AssemblyLineModule('m01', 'ACT1', 'act1_as1', 'bd')
        assert str(m) == m.name


class TestModuleTestCell:
    def test_detected_as_test_cell(self):
        m = AssemblyLineModule('tc1_bd', 'ACT1', 'act1_as1', 'bd', TC_MODULES)
        assert m.is_test_cell

    def test_tc_number_one_based(self):
        m = AssemblyLineModule('tc1_bd', 'ACT1', 'act1_as1', 'bd', TC_MODULES)
        assert m.tc_number == 1

    def test_tc_number_third(self):
        m = AssemblyLineModule('tc3_bd', 'ACT1', 'act1_as1', 'bd', TC_MODULES)
        assert m.tc_number == 3

    def test_bool_true_for_test_cell(self):
        m = AssemblyLineModule('tc1_bd', 'ACT1', 'act1_as1', 'bd', TC_MODULES)
        assert m

    def test_description_returns_shortcut_and_number(self):
        m = AssemblyLineModule('tc2_bd', 'ACT1', 'act1_as1', 'bd', TC_MODULES)
        assert m.description == 'TC2'

    def test_custom_shortcut(self):
        m = AssemblyLineModule(
            'tc1_bd', 'ACT1', 'act1_as1', 'bd', TC_MODULES, tc_shortcut='PZ')
        assert m.description == 'PZ1'

    def test_str_returns_shortcut_for_test_cell(self):
        m = AssemblyLineModule('tc1_bd', 'ACT1', 'act1_as1', 'bd', TC_MODULES)
        assert str(m) == 'TC'


class TestModuleEdgeCases:
    def test_unknown_product_no_error(self):
        m = AssemblyLineModule('m01', 'UNKNOWN', 'some_line', 'bd', TC_MODULES)
        assert m.tc_modules == []
        assert not m.is_test_cell

    def test_unknown_line_no_error(self):
        m = AssemblyLineModule('m01', 'ACT1', 'unknown_line', 'bd', TC_MODULES)
        assert m.tc_modules == []

    def test_empty_tc_modules_no_detection(self):
        m = AssemblyLineModule('tc1_bd', 'ACT1', 'act1_as1', 'bd', {})
        assert not m.is_test_cell

    def test_description_regular_returns_name(self):
        m = AssemblyLineModule('m21', 'ACT1', 'act1_as1', 'pc')
        assert m.description == m.name
