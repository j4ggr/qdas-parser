"""Tests for _models.py — KField and Feature."""

import pytest

from qdas_parser._models import KField, Feature


# ===========================================================================
# KField
# ===========================================================================

class TestKFieldParsing:
    def test_header_line_key(self):
        kf = KField('K0100 9\n')
        assert kf.key == 'K0100'

    def test_header_line_value(self):
        kf = KField('K0100 9\n')
        assert kf.value == '9'

    def test_header_line_no_feature_number(self):
        kf = KField('K0100 9\n')
        assert kf.feature_number == 0

    def test_feature_line_key(self):
        kf = KField('K2002/1 Merkmalname\n')
        assert kf.key == 'K2002'

    def test_feature_line_feature_number(self):
        kf = KField('K2002/1 Merkmalname\n')
        assert kf.feature_number == 1

    def test_feature_line_value(self):
        kf = KField('K2002/1 Merkmalname\n')
        assert kf.value == 'Merkmalname'

    def test_feature_number_10(self):
        kf = KField('K2002/10 Merkmal 10\n')
        assert kf.feature_number == 10


class TestKFieldDunder:
    def test_bool_false_for_header(self):
        kf = KField('K0100 9\n')
        assert not kf

    def test_bool_true_for_feature(self):
        kf = KField('K2002/1 Name\n')
        assert kf

    def test_eq_by_key_string(self):
        kf = KField('K0100 9\n')
        assert kf == 'K0100'
        assert kf != 'K2002'

    def test_int_returns_numeric_key(self):
        kf = KField('K0100 9\n')
        assert int(kf) == 100

    def test_str_contains_key(self):
        kf = KField('K0100 9\n')
        assert 'K0100' in str(kf)


class TestKFieldDecode:
    def test_required_field_name(self):
        kf = KField('K1001 1234567\n')
        name, value = kf.decode()
        assert name == 'Teilenummer'
        assert value == '1234567'

    def test_defined_field_name_and_value(self):
        # K2004 = Merkmalart; value '0' = 'variabel'
        kf = KField('K2004/1 0\n')
        name, value = kf.decode()
        assert name == 'Merkmalart'
        assert value == 'variabel'

    def test_other_field_returns_raw(self):
        kf = KField('K9004/1 F-Teilenummer\n')
        name, value = kf.decode()
        assert name == 'K9004'
        assert value == 'F-Teilenummer'

    def test_required_k0100_decodes(self):
        kf = KField('K0100 3\n')
        name, value = kf.decode()
        assert name == 'Merkmalanzahl'


class TestKFieldCategory:
    def test_k1xxx_is_part_data(self):
        kf = KField('K1001 x\n')
        assert kf.category == 'part_data'

    def test_k2xxx_is_feature_data(self):
        kf = KField('K2002/1 x\n')
        assert kf.category == 'feature_data'

    def test_k0xxx_is_description(self):
        kf = KField('K0100 1\n')
        assert kf.category == 'description'


# ===========================================================================
# Feature
# ===========================================================================

class TestFeatureInit:
    def test_defaults(self):
        f = Feature(1)
        assert f.number == 1
        assert f.label == ''
        assert f.unit == ''
        assert f.id == ''
        assert f.columns == []

    def test_eq_by_number(self):
        f = Feature(3)
        assert f == 3
        assert f != 4


class TestFeatureLabel:
    def test_spaces_become_underscores(self):
        f = Feature(1)
        f.label = 'Station 1 Pressure'
        assert f.label == 'Station_1_Pressure'

    def test_double_underscore_collapsed(self):
        f = Feature(1)
        f.label = 'Foo  Bar'  # two spaces → '__' → '_'
        assert '__' not in f.label

    def test_setting_label_resets_columns(self):
        f = Feature(1)
        f.label = 'Torque'
        assert f.columns == ['Torque']


class TestFeatureExtend:
    def test_amount_one_adds_no_columns(self):
        f = Feature(1)
        f.label = 'Val'
        f.extend(1)
        assert f.columns == ['Val']

    def test_amount_two_adds_one_column(self):
        f = Feature(1)
        f.label = 'Val'
        f.extend(2)
        assert len(f.columns) == 2
        assert f.columns[1] == 'Val_Attribut'

    def test_amount_five_sets_id(self):
        f = Feature(1)
        f.label = 'Val'
        f.extend(5)
        # columns[3] (4th extra) = 'Val_Chargennummer' becomes id
        assert f.id == 'Val_Chargennummer'

    def test_amount_four_no_id(self):
        f = Feature(1)
        f.label = 'Val'
        f.extend(4)
        assert f.id == ''  # only 3 extra columns, not enough for id


class TestFeatureAdd:
    def test_add_k2002_sets_label(self):
        f = Feature(1)
        kf = KField('K2002/1 Force 1\n')
        f.add(kf)
        assert f.label == 'Force_1'

    def test_add_k2142_sets_unit(self):
        f = Feature(1)
        kf = KField('K2142/1 l/h\n')
        f.add(kf)
        assert f.unit == 'l/h'

    def test_add_k9004_appends_to_label(self):
        f = Feature(1)
        f.label = 'C1_Connector'
        kf = KField('K9004/1 Part_Number\n')
        f.add(kf)
        assert f.label == 'C1_Connector_Part_Number'

    def test_add_stores_decoded_kv_in_dict(self):
        f = Feature(1)
        kf = KField('K2004/1 0\n')
        f.add(kf)
        assert 'Merkmalart' in f
        assert f['Merkmalart'] == 'variabel'
