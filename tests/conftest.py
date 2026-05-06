"""Shared pytest fixtures for qdas_parser tests."""

from pathlib import Path
import pytest

# Root of the fixture file tree (mirrors the real directory convention)
FIXTURES = Path(__file__).parent / 'fixtures'

BD_DFD = FIXTURES / 'bd/2603160002.dfd'
PC_DFD = FIXTURES / 'pc/2604020002.dfd'


# ---------------------------------------------------------------------------
# Parser instances — pre-parsed so individual tests don't repeat the I/O
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def bd_parser():
    """QDASFileParser for the batch-data (bd) fixture — fully parsed."""
    from qdas_parser import QDASFileParser
    p = QDASFileParser(BD_DFD, 'ACT1', kind='bd', module_name='m01', line='as1')
    p.parse_description()
    p.parse_values()
    return p


@pytest.fixture(scope='session')
def pc_parser():
    """QDASFileParser for the process-data (pc) fixture — fully parsed."""
    from qdas_parser import QDASFileParser
    p = QDASFileParser(PC_DFD, 'ACT1', kind='pc', module_name='m21', line='as1')
    p.parse_description()
    p.parse_values()
    return p
