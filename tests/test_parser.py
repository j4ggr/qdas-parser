"""Tests for _parser.py — ProductionOrder and QDASFileParser.

Uses two pre-parsed fixture parsers from conftest.py:
  - bd_parser: batch-data file pair (3 features, 5 extensions each)
  - pc_parser: process-data file pair (3 features, 5 extensions on feature 1)
"""

from pathlib import Path
import pytest
import pandas as pd

from qdas_parser._models import ProductionOrder
from qdas_parser._parser import QDASFileParser

FIXTURES = Path(__file__).parent / 'fixtures'
BD_DFD = FIXTURES / 'bd/2603160002.dfd'


# ===========================================================================
# ProductionOrder
# ===========================================================================

class TestProductionOrder:
    def test_str_is_12_digits_zero_padded(self):
        assert str(ProductionOrder('1234567')) == '000001234567'

    def test_int_input_is_formatted(self):
        assert str(ProductionOrder(1234567)) == '000001234567'

    def test_empty_string_is_valid(self):
        assert str(ProductionOrder('')) == ''

    def test_bool_false_when_empty(self):
        assert not ProductionOrder('')

    def test_bool_true_when_set(self):
        assert ProductionOrder('1234567')

    def test_eq_normalises_both_sides(self):
        assert ProductionOrder('1234567') == '000001234567'
        assert ProductionOrder('1234567') == 1234567

    def test_repr_contains_order(self):
        assert '000001234567' in repr(ProductionOrder('1234567'))

    def test_repr_empty_shows_all(self):
        assert 'all' in repr(ProductionOrder(''))

    def test_int_roundtrip(self):
        assert int(ProductionOrder('1234567')) == 1234567

    def test_hash_equal_for_same_order(self):
        assert hash(ProductionOrder('1234567')) == hash(ProductionOrder(1234567))


# ===========================================================================
# Static helpers
# ===========================================================================

class TestStaticHelpers:
    def test_ensure_path_from_string(self):
        p = QDASFileParser.ensure_path('some/path.dfd')
        assert isinstance(p, Path)

    def test_ensure_path_from_path(self):
        p = Path('some/path.dfd')
        assert QDASFileParser.ensure_path(p) is p


# ===========================================================================
# BD fixture — batch data, 3 features with 5 extensions each
# ===========================================================================

class TestBDDescription:
    def test_head_data_has_teilenummer(self, bd_parser):
        assert bd_parser.head_data.get('Teilenummer') == '1234567'

    def test_head_data_has_teilebezeichnung(self, bd_parser):
        assert bd_parser.head_data.get('Teilebezeichnung') == 'Widget-Type-A-Rev2'

    def test_feature_count(self, bd_parser):
        assert len(bd_parser.features) == 3

    def test_feature_labels(self, bd_parser):
        labels = [f.label for f in bd_parser.features]
        assert labels[0] == 'C1_Connector_Part_Number'
        assert labels[1] == 'C1_Connector_Supplier'
        assert labels[2] == 'C1_Connector_Revision'

    def test_feature_identity_set_from_chargennummer(self, bd_parser):
        # 5 extensions → identity = columns[3] = label_Chargennummer
        assert bd_parser.features[0].identity == 'C1_Connector_Part_Number_Chargennummer'

    def test_order_is_empty_no_auftrag_kfield(self, bd_parser):
        assert str(bd_parser.order) == ''

    def test_module_name(self, bd_parser):
        assert bd_parser.module.name == 'm01_bd'

    def test_vfile_suffix_is_dfb(self, bd_parser):
        assert bd_parser.vfile.suffix == '.dfb'


class TestBDValues:
    def test_data_has_two_rows(self, bd_parser):
        assert len(bd_parser.data) == 2

    def test_first_row_charge_value(self, bd_parser):
        # Feature 1 has 5 extensions; Chargennummer is index 4 of the inner list
        # After flatten: index_cols (3) + feature1_vals (5) + ...
        # Position of Chargennummer for feature 1: 3 + 4 = index 7
        row = bd_parser.data[0]
        assert 'LOT0001' in row

    def test_second_row_charge_value(self, bd_parser):
        row = bd_parser.data[1]
        assert 'LOT0002' in row


class TestBDDataframe:
    def test_returns_dataframe(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        assert isinstance(df, pd.DataFrame)

    def test_index_has_two_levels(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        assert df.index.nlevels == 2

    def test_index_names(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        assert list(df.index.names) == ['Auftragsnummer', 'Seriennummer']

    def test_part_id_from_chargennummer(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        part_ids = df.index.get_level_values('Seriennummer').tolist()
        assert 'LOT0001' in part_ids
        assert 'LOT0002' in part_ids

    def test_two_data_rows(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        assert len(df) == 2

    def test_column_multiindex_modul_level(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        assert df.columns.names == ['Modul', 'Merkmal']

    def test_feature_columns_present(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        merkmal_cols = df.columns.get_level_values('Merkmal').tolist()
        assert 'C1_Connector_Part_Number' in merkmal_cols
        assert 'C1_Connector_Supplier' in merkmal_cols


# ===========================================================================
# BD metadata
# ===========================================================================

class TestBDMetadata:
    def test_returns_dataframe(self, bd_parser):
        mdf = bd_parser.metadata()
        assert isinstance(mdf, pd.DataFrame)

    def test_columns_are_feature_labels(self, bd_parser):
        mdf = bd_parser.metadata()
        col_labels = mdf.columns.get_level_values('Merkmal').tolist()
        assert 'C1_Connector_Part_Number' in col_labels

    def test_index_has_three_levels(self, bd_parser):
        mdf = bd_parser.metadata()
        assert mdf.index.nlevels == 3


# ===========================================================================
# PC fixture — process data, 3 features (feature 1 has 5 extensions)
# ===========================================================================

class TestPCDescription:
    def test_head_data_has_teilenummer(self, pc_parser):
        assert pc_parser.head_data.get('Teilenummer') == '7654321'

    def test_feature_count(self, pc_parser):
        assert len(pc_parser.features) == 3

    def test_feature_labels(self, pc_parser):
        labels = [f.label for f in pc_parser.features]
        assert labels[0] == 'Meas_ID'
        assert labels[1] == 'Force_1'
        assert labels[2] == 'Force_2'

    def test_feature_units(self, pc_parser):
        assert pc_parser.features[1].unit == 'N'
        assert pc_parser.features[2].unit == 'N'

    def test_identity_set_from_chargennummer(self, pc_parser):
        assert pc_parser.features[0].identity == 'Meas_ID_Chargennummer'

    def test_vfile_suffix_is_dfx(self, pc_parser):
        assert pc_parser.vfile.suffix == '.dfx'

    def test_module_name(self, pc_parser):
        assert pc_parser.module.name == 'm21_pc'


class TestPCValues:
    def test_data_has_two_rows(self, pc_parser):
        assert len(pc_parser.data) == 2

    def test_first_row_contains_values(self, pc_parser):
        row = pc_parser.data[0]
        assert '1500.0' in row
        assert '25.300' in row

    def test_second_row_contains_values(self, pc_parser):
        row = pc_parser.data[1]
        assert '1520.0' in row


class TestPCDataframe:
    def test_returns_dataframe(self, pc_parser):
        df = pc_parser.dataframe(add_head=False)
        assert isinstance(df, pd.DataFrame)

    def test_two_data_rows(self, pc_parser):
        df = pc_parser.dataframe(add_head=False)
        assert len(df) == 2

    def test_feature_columns_present(self, pc_parser):
        df = pc_parser.dataframe(add_head=False)
        merkmal_cols = df.columns.get_level_values('Merkmal').tolist()
        assert 'Meas_ID' in merkmal_cols
        assert 'Force_1' in merkmal_cols
        assert 'Force_2' in merkmal_cols

    def test_feature_values(self, pc_parser):
        df = pc_parser.dataframe(add_head=False)
        force_vals = df[('m21_pc', 'Force_1')].tolist()
        assert '25.300' in force_vals
        assert '28.100' in force_vals


# ===========================================================================
# mtime
# ===========================================================================

class TestMtime:
    def test_bd_mtime_is_float(self, bd_parser):
        assert isinstance(bd_parser.mtime, float)

    def test_bd_fn_date(self, bd_parser):
        assert bd_parser.fn_date == '260316'

    def test_pc_fn_date(self, pc_parser):
        assert pc_parser.fn_date == '260402'


# ===========================================================================
# Custom index_columns
# ===========================================================================

class TestCustomIndexColumns:
    def test_default_index_columns(self):
        p = QDASFileParser(BD_DFD, 'ACT1', kind='bd')
        assert p.index_columns == ['Auftragsnummer', 'Seriennummer']

    def test_custom_index_columns_stored(self):
        custom = ['Teilenummer', 'Seriennummer']
        p = QDASFileParser(BD_DFD, 'ACT1', kind='bd', index_columns=custom)
        assert p.index_columns == custom

    def test_custom_index_columns_used_in_dataframe(self):
        p = QDASFileParser(BD_DFD, 'ACT1', kind='bd',
                           index_columns=['Seriennummer'])
        p.parse_description()
        p.parse_values()
        df = p.dataframe(add_head=False)
        assert df.index.names == ['Seriennummer']
