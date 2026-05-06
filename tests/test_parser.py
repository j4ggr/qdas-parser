"""Tests for _parser.py — ProductionOrder and QDASFileParser.

Uses two pre-parsed fixture parsers from conftest.py:
  - bd_parser: batch-data file pair (3 features, 5 extensions each)
  - pc_parser: process-data file pair (3 features, 5 extensions on feature 1)
"""

from pathlib import Path
import pytest
import pandas as pd

from qdas_parser._parser import ProductionOrder, QDASFileParser


# ===========================================================================
# ProductionOrder
# ===========================================================================

class TestProductionOrder:
    def test_is_str_subclass(self):
        assert isinstance(ProductionOrder('1234567'), str)

    def test_str_roundtrip(self):
        assert str(ProductionOrder('1234567')) == '1234567'

    def test_empty_is_valid(self):
        assert str(ProductionOrder('')) == ''


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

    def test_feature_id_set_from_chargennummer(self, bd_parser):
        # 5 extensions → id = columns[3] = label_Chargennummer
        assert bd_parser.features[0].id == 'C1_Connector_Part_Number_Chargennummer'

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

    def test_index_has_three_levels(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        assert df.index.nlevels == 3

    def test_index_names(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        assert list(df.index.names) == ['Teilenummer', 'Auftrag', 'Teile ID']

    def test_teilenummer_in_index(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        assert '1234567' in df.index.get_level_values('Teilenummer')

    def test_part_id_from_chargennummer(self, bd_parser):
        df = bd_parser.dataframe(add_head=False)
        part_ids = df.index.get_level_values('Teile ID').tolist()
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

    def test_id_set_from_chargennummer(self, pc_parser):
        assert pc_parser.features[0].id == 'Meas_ID_Chargennummer'

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

    def test_teilenummer_in_index(self, pc_parser):
        df = pc_parser.dataframe(add_head=False)
        assert '7654321' in df.index.get_level_values('Teilenummer')

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
