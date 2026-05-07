"""Benchmarks comparing the pure-Python and Cython implementations of the
two hot-path functions: ``rows_fast`` and ``flatten_fast``.

Run with::

    pytest tests/bench_fast.py --benchmark-only -v

Adjust ``N_ROWS``, ``N_FEATURES``, and ``N_EXTENSIONS`` to tune the
synthetic workload. The fixture writes a temporary value file so that
I/O is included in the ``rows_fast`` measurement (as it would be in
production). ``flatten_fast`` is measured separately on the nested list
already in memory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

# ---------------------------------------------------------------------------
# Synthetic workload parameters
# ---------------------------------------------------------------------------
N_ROWS = 30_000
N_FEATURES = 10
N_EXTENSIONS = 5   # extensions per feature (including the base value)

SEP_F = chr(15)
SEP_E = chr(20)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_row(feat_idx: int, row_idx: int) -> str:
    """Build one text row: N_FEATURES features x N_EXTENSIONS extensions."""
    features = []
    for f in range(N_FEATURES):
        extensions = [f"{feat_idx + f}.{row_idx:04d}"] + [''] * (N_EXTENSIONS - 1)
        features.append(SEP_E.join(extensions))
    return SEP_F.join(features)


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def synthetic_vfile(tmp_path_factory) -> Path:
    """Write a large synthetic value file to a temp location once per session."""
    tmp = tmp_path_factory.mktemp('bench') / 'synthetic.dfx'
    lines = [_make_row(i % N_FEATURES, i) + '\r\n' for i in range(N_ROWS)]
    tmp.write_bytes(''.join(lines).encode('utf-8'))
    return tmp


@pytest.fixture(scope='session')
def sample_nested_row() -> list:
    """A single nested row as rows_fast would yield it — used for flatten benchmarks."""
    return [_make_row(0, 0).split(SEP_F)[f].split(SEP_E)
            for f in range(N_FEATURES)]


def _load_py() -> tuple[Callable, Callable]:
    """Import the pure-Python implementations directly (bypass any compiled ext)."""
    import sys
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(
        'qdas_parser._fast_py',
        Path(__file__).parents[1] / 'src/qdas_parser/_fast.py',)
    mod = ilu.module_from_spec(spec)
    mod.__package__ = 'qdas_parser'
    sys.modules['qdas_parser._fast_py'] = mod
    spec.loader.exec_module(mod)
    return mod.rows_fast, mod.flatten_fast


# ---------------------------------------------------------------------------
# Load implementations once — avoids import overhead inside the benchmark loop
# ---------------------------------------------------------------------------

_rows_py, _flatten_py = _load_py()


# ---------------------------------------------------------------------------
# Consume the generator fully (rows_fast is lazy)
# ---------------------------------------------------------------------------

def _exhaust_rows(rows_fn, vfile):
    return list(rows_fn(vfile, SEP_F, SEP_E))


# ---------------------------------------------------------------------------
# rows_fast benchmarks
# ---------------------------------------------------------------------------

class TestRowsFastBench:
    def test_rows_pure_python(self, benchmark, synthetic_vfile):
        result = benchmark(_exhaust_rows, _rows_py, synthetic_vfile)
        assert len(result) == N_ROWS


# ---------------------------------------------------------------------------
# flatten_fast benchmarks
# ---------------------------------------------------------------------------

class TestFlattenFastBench:
    def test_flatten_pure_python(self, benchmark, sample_nested_row):
        result = benchmark(_flatten_py, 3, sample_nested_row)
        assert len(result) == 3 + N_FEATURES * N_EXTENSIONS
